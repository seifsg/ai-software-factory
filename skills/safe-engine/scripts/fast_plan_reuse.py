"""Reuse approved planning only after validating current scope, inputs and obligations."""
import hashlib
import json
import re
from urllib.parse import urlsplit

import fast_checks
import fast_design as evidence
import fast_record as record
import fast_show
from fast_diagnostics import validation

LIMIT = 1024 * 1024
FIELDS = {"version", "source", "record", "approval", "scope", "inputs", "proof_selection",
          "show_plan", "suite_plan", "design_input"}
SCOPE = ("kind", "ui", "data", "auth", "design_port")


def bounded(project, name):
    """Read a small project-local artifact once, rejecting path escape and oversized data."""
    path = evidence.local(project, name)
    evidence.require(path.stat().st_size <= LIMIT, f"{name}: plan artifact exceeds 1 MiB")
    return path.read_bytes()


def unique(pairs):
    """Duplicate JSON fields are ambiguous approval inputs, never last-wins overrides."""
    result = {}
    for key, value in pairs:
        evidence.require(key not in result, f"Duplicate plan field: {key}")
        result[key] = value
    return result


def shape(data, source, run):
    """Collect independent schema problems before reading dependent artifacts."""
    errors = []
    if not isinstance(data, dict):
        return ["plan-record must contain a JSON object"]
    extra = set(data) - FIELDS
    if extra:
        errors.append("remove unknown plan fields: " + ", ".join(sorted(extra)))
    if type(data.get("version")) is not int or data["version"] != 1:
        errors.append('write "version": 1')
    if data.get("source") != source or urlsplit(source).scheme != "https" or not urlsplit(source).netloc:
        errors.append('write "source": "<same approved https link as --from-plan>"')
    scope = data.get("scope")
    expected = {key: run.get(key, False) for key in SCOPE}
    if not isinstance(scope, dict) or set(scope) != set(SCOPE) or scope != expected or any(
            type(scope[key]) is not bool for key in SCOPE[1:]):
        errors.append("scope differs from start: write " + json.dumps(expected) + "; reconfirm changed scope first")
    for field, keys in (("record", {"path", "sha256"}), ("approval", {"actor", "source", "quote", "plan_sha256"})):
        value = data.get(field)
        if not isinstance(value, dict) or set(value) != keys:
            errors.append(f"{field}: write an object with " + ", ".join(sorted(keys)))
            continue
        for key in keys:
            try:
                evidence.text(value[key], f"{field}.{key}")
            except ValueError as error:
                errors.append(str(error))
    inputs = data.get("inputs")
    if not isinstance(inputs, dict) or not 1 <= len(inputs) <= 1000:
        errors.append('inputs: write 1..1000 current project paths as {"<path>": "<sha256>"}')
    if not isinstance(data.get("proof_selection"), dict):
        errors.append('proof_selection: use the public checks --plan JSON, including complete pasted ticket bodies')
    return errors


def bindings(project, data):
    """Check approved record bytes and each named current input; report every readable mismatch."""
    errors, raw = [], None
    expected = data["record"]["sha256"]
    if data["approval"]["plan_sha256"] != expected:
        errors.append("approval.plan_sha256 differs from record.sha256; resolve the approved plan again")
    try:
        raw = bounded(project, data["record"]["path"])
        if hashlib.sha256(raw).hexdigest() != expected:
            errors.append("record.sha256 changed; resolve the approved record, never relabel changed bytes as approved")
    except (OSError, ValueError) as error:
        errors.append(str(error))
    for name, wanted in data["inputs"].items():
        try:
            evidence.require(isinstance(wanted, str) and re.fullmatch(r"[0-9a-f]{64}", wanted),
                             f"inputs.{name}: write a lowercase sha256")
            if evidence.file_hash(evidence.local(project, name)) != wanted:
                errors.append(f"input changed: {name}; reconcile this input with the owner-approved scope")
        except (OSError, ValueError) as error:
            errors.append(str(error))
    return raw, errors


def obligations(project, run, data):
    """Import plans, never execution receipts; existing validators retain proof and coverage duties."""
    run["checks"] = {"plan": fast_checks.selection(data["proof_selection"], run)}
    if fast_show.enabled(run):
        run["show"] = {"plan": fast_show.plan(data.get("show_plan") or {})}
    elif "show_plan" in data:
        raise ValueError("show_plan is outside this run's scope")
    if run.get("suite_policy") and not run.get("ui"):
        run["suite"] = {"plan": fast_show.suite_plan(data.get("suite_plan"))}
    elif "suite_plan" in data:
        raise ValueError("suite_plan is outside this run's scope")
    if run.get("design_port"):
        path = evidence.local(project, data.get("design_input"))
        design = evidence.read(path)
        inventory = evidence.inventory(project, design)
        evidence.statuses(design)
        bound = {evidence.local(project, name) for name in data["inputs"]}
        required = {path, *(evidence.local(project, screen["reference"]["path"]) for screen in inventory["screens"])}
        evidence.require(required <= bound, "inputs must bind design_input and every reference image from the approved plan")
        run["design"] = {"path": path.relative_to(project).as_posix(), "inventory": inventory}
    elif "design_input" in data:
        raise ValueError("design_input is outside this run's scope")


@validation
def prepare(args, project, run, gate):
    """Validate completely in memory before start archives, registers or writes any run."""
    source, path = getattr(args, "from_plan", None), getattr(args, "plan_record", None)
    if not source and not path:
        return None
    evidence.require(source and path, "Use --from-plan <link> together with --plan-record <project-local JSON>")
    evidence.require(run.get("check_selection"), "Resolve current methods before reusing a plan")
    data = json.loads(bounded(project, path).decode("utf-8-sig"), object_pairs_hook=unique)
    errors = shape(data, source, run)
    evidence.require(not errors, "Plan reuse:\n- " + "\n- ".join(errors))
    raw, errors = bindings(project, data)
    evidence.require(not errors, "Plan reuse:\n- " + "\n- ".join(errors))
    text = raw.decode("utf-8-sig")
    sections = record.sections(text)
    planning = gate.steps_for(run)
    planning = planning[:planning.index("plan") + 1]
    epic, subs = record.ticket_urls(sections.get("tickets", ""))
    run["tickets"] = list(dict.fromkeys(epic + subs))
    obligations(project, run, data)
    run["todos"] = [f"T{number}" for number in record.todo_ids(sections)]
    run["ports"] = record.fast_briefs.ports(record.marker(sections.get("plan", ""), "Ports"))
    for step in planning:
        body = sections.get(gate.TITLES[step].lower(), "")
        errors += [f"{gate.TITLES[step]}: {problem}" for problem in record.CHECKS[step](
            run, body, project=project, all_sections=sections, offline=None, runs=gate.active_runs)]
    evidence.require(not errors, "Plan reuse:\n- " + "\n- ".join(dict.fromkeys(errors)))
    size = record.run_size(sections)
    if size:
        run.update(size=size, size_at="approved plan")
    fast_checks.freeze_ownership(run)
    run["plan_reuse"] = {"source": source, "record_sha256": data["record"]["sha256"],
                         "snapshot_sha256": evidence.digest(data), "approval": data["approval"], "inputs": data["inputs"]}
    for step in planning:
        run["done"][step] = {"at": gate.now(), "reused": source}
    # Render only validated planning; later proof and the new owner's request are never copied.
    result = gate.skeleton(run)
    for step in planning:
        heading = gate.TITLES[step]
        pattern = rf"(?m)(^## {re.escape(heading)}\n).*?(?=^## |\Z)"
        result = re.sub(pattern, lambda match: match[1] + "\n" + sections[heading.lower()].strip() + "\n\n",
                        result, flags=re.S)
    return result + f"\n## Reused plan\n\n{source}\n"
