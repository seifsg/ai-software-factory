"""Validate reviewed contract transitions and candidate-bound manual evidence."""

from pathlib import Path

from .project import EngineError, digest, file_hash, inside, reject_path_aliases, relative_input_path


def contract_candidate_digest(task, profile, protected, ticket=None):
    value = {"task": task, "profile": profile, "protected": protected}
    if ticket is not None:
        value["ticket"] = ticket
    return digest(value)


def validate_contract_review(review, old_digest, new_digest):
    if not isinstance(review, dict):
        raise EngineError("Contract review must be an object")
    if review.get("verdict") != "PASS" or review.get("independent") is not True:
        raise EngineError("Contract changes need a passing independent review")
    for field in ("reviewer", "reason", "authority"):
        if not isinstance(review.get(field), str) or not review[field].strip():
            raise EngineError(f"Contract review needs {field}")
    for field, expected in (("old_digest", old_digest), ("new_digest", new_digest)):
        if not isinstance(expected, str) or not expected or review.get(field) != expected:
            raise EngineError(f"Contract review does not match {field}")
    return {field: review[field] for field in
            ("verdict", "independent", "reviewer", "reason", "authority", "old_digest", "new_digest")}


def validate_manual_receipt(receipt, expected_candidate, task, project):
    """Read evidence without writes. Content presence is not independent verification."""
    if not isinstance(receipt, dict) or receipt.get("candidate") != expected_candidate:
        raise EngineError("Manual QA receipt must name the current production candidate")
    if not isinstance(expected_candidate, str) or not expected_candidate:
        raise EngineError("Manual QA needs a nonempty candidate identity")
    observations = receipt.get("observations")
    if not isinstance(observations, list) or not observations:
        raise EngineError("Manual QA needs at least one real action observation")
    criteria = {criterion["id"]: criterion for criterion in task["acceptance"]}
    required = {identifier for identifier, criterion in criteria.items()
                if criterion.get("mode", "automated") in ("manual", "mixed")}
    project = Path(project).resolve()
    normalized = []
    covered = set()
    for observation in observations:
        if not isinstance(observation, dict):
            raise EngineError("Each manual observation must be an object")
        identifier = observation.get("criterion")
        if not isinstance(identifier, str) or identifier not in criteria:
            raise EngineError("Manual observations must name an accepted criterion")
        for field in ("device", "action", "result"):
            if not isinstance(observation.get(field), str) or not observation[field].strip():
                raise EngineError(f"{identifier}: manual observation needs {field}")
        if observation.get("status") != "PASS":
            raise EngineError(f"{identifier}: unresolved manual observation cannot establish acceptance")
        evidence = observation.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise EngineError(f"{identifier}: manual observation needs evidence files")
        hashes = []
        seen = set()
        for name in evidence:
            relative_input_path(name, allow_factory=True)
            if name.casefold() in seen:
                raise EngineError(f"{identifier}: duplicate evidence path: {name}")
            seen.add(name.casefold())
            path = inside(project, name)
            reject_path_aliases(path, project)
            hashes.append({"path": name, "sha256": file_hash(path)})
        normalized.append({"criterion": identifier, "device": observation["device"],
                           "action": observation["action"], "result": observation["result"],
                           "status": "PASS", "evidence": hashes})
        covered.add(identifier)
    missing = required - covered
    if missing:
        raise EngineError(f"Manual QA missing criteria: {', '.join(sorted(missing))}")
    return {"candidate": expected_candidate, "observations": normalized}
