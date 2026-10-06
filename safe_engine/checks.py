"""Version and feature check batches plus their stale-evidence gate."""

from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
import threading

from .project import EngineError, command_argv, file_hash, inside, reject_path_aliases, rescan
from .storage import atomic_json


class CheckMixin:
    def check(self, fresh=False):
        state = self.load()
        self.require_ticket(state)
        self.require_phase(state, "verify", "final-verify")
        if state.get("checks") and not state["checks"]["passed"]:
            raise EngineError("Completed failed checks require correction; use repair before another check batch")
        self.integrity(state)
        self.require_manual(state)
        current = self.current(state)
        anchor = "batch" if state["phase"] == "verify" else "improvement"
        if state["artifacts"][anchor]["fingerprint"] != current:
            raise EngineError(f"Candidate changed after the {anchor} record; enter repair and record the new batch")
        if (state["phase"] == "final-verify" and not fresh
                and state["profile"].get("reuse_unchanged_checks", False)
                and state.get("checks") and state["checks"]["fingerprint"] == current):
            self.require_checks(state)
            state["phase"] = "review"
            self.persist(state, "Revalidated unchanged full version checks; no commands repeated")
            return {**self.status(state), "checks_reused": True, "results": state["checks"]["results"]}
        state["checks"] = None
        state["review"] = None
        state["pending_operation"] = "checks"
        self.persist(state, "Started check batch; previous acceptance invalidated")
        results = self.execute_checks(state, state["profile"]["checks"])
        unchanged = self.current(state) == current
        self.integrity(state)
        passed = unchanged and all(result["passed"] for result in results)
        state["checks"] = {"fingerprint": current, "passed": passed, "inputs_unchanged": unchanged, "results": results}
        state["pending_operation"] = None
        if passed:
            state["phase"] = ("review" if state.get("delivery_version") == 2
                              else "improve" if state["phase"] == "verify" else "review")
        self.persist(state, "Check batch passed" if passed else "Check batch failed; correction required")
        return {**self.status(state), "checks_reused": False, "results": results}

    def execute_checks(self, state, configured):
        """Serial by default; reviewed parallel_checks runs independent commands at once."""
        try:
            if not (state.get("profile", {}).get("parallel_checks") and len(configured) > 1):
                return [self.run_check(state, check, self.prepare_outputs(check)) for check in configured]
            prepared = [(check, self.prepare_outputs(check)) for check in configured]
            stop = threading.Event()
            with ThreadPoolExecutor(min(len(prepared), 32)) as pool:
                futures = [pool.submit(self.run_check, state, check, outputs, stop) for check, outputs in prepared]
                try:
                    pending = set(futures)
                    while pending:  # Timed waits keep Ctrl+C responsive on Windows.
                        pending = wait(pending, timeout=0.1).not_done
                except BaseException:
                    stop.set()
                    raise
            return [future.result() for future in futures]
        finally:
            rescan()

    def prepare_outputs(self, check):
        """Remove only declared outputs so each check must produce fresh files."""
        outputs = [inside(self.project, name) for name in check.get("artifacts", [])]
        output_root = (self.directory / "outputs").absolute()
        reject_path_aliases(output_root, self.project)
        for output in outputs:
            reject_path_aliases(output, self.project)
            if not output.absolute().is_relative_to(output_root):
                raise EngineError("Check output escaped the generated output directory")
            if output.exists():
                if not output.is_file():
                    raise EngineError(f"Declared output is not a file: {output}")
                output.unlink()
        return outputs

    def run_check(self, state, check, outputs, stop=None):
        log = self.directory / "logs" / f"{state['sequence']:04d}-{check['id']}.log"
        result = self.launch(command_argv(check, self.project, self.directory), self.project,
                            check["timeout_seconds"], log, **({"stop": stop} if stop else {}))
        artifacts = []
        for output in outputs:
            try:
                reject_path_aliases(output, self.project)
                artifacts.append({"path": str(output), "sha256": file_hash(output)})
            except EngineError as error:
                result["passed"] = False
                result.setdefault("artifact_errors", []).append(str(error))
        result["artifacts"] = artifacts
        return {"id": check["id"], "kind": check["kind"], **result, "log_sha256": file_hash(log)}

    def feature_check(self, check_ids, source):
        """Partial feedback for a completed capability; never version acceptance."""
        state = self.load()
        if state.get("delivery_version") == 2:
            raise EngineError("All testing waits until finished implementation and final manual QA")
        self.require_phase(state, "build")
        self.integrity(state)
        if state.get("feature_checks") and not state["feature_checks"]["passed"]:
            raise EngineError("Failed feature feedback requires a correction; use repair before another batch")
        configured = {check["id"]: check for check in state["profile"]["checks"]}
        if (not check_ids or len(set(check_ids)) != len(check_ids)
                or any(identifier not in configured for identifier in check_ids)):
            raise EngineError("Select unique configured check IDs for this feature batch")
        current = self.current(state)
        kind = f"feature-{state['sequence'] + 1:04d}"
        self.capture_artifact(state, kind, source, current)
        state["checks"] = None
        state["review"] = None
        state["feature_checks"] = None
        state["pending_operation"] = "feature-checks"
        self.persist(state, "Started partial feature checks; no version acceptance")
        selected = [check for check in state["profile"]["checks"] if check["id"] in check_ids]
        results = self.execute_checks(state, selected)
        unchanged = self.current(state) == current
        self.integrity(state)
        evidence = {"fingerprint": current, "passed": unchanged and all(r["passed"] for r in results),
                    "inputs_unchanged": unchanged, "results": results,
                    "missing_required_checks": [identifier for identifier in configured if identifier not in check_ids]}
        state["feature_checks"] = evidence
        relative = f"artifacts/{state['sequence']:04d}-feature-results.json"
        atomic_json(self.directory / relative, evidence)
        state["artifacts"][f"feature-results-{state['sequence']:04d}"] = {
            "path": relative, "sha256": file_hash(self.directory / relative), "fingerprint": current}
        state["pending_operation"] = None
        self.persist(state, "Feature feedback passed; version checks still required" if evidence["passed"]
             else "Feature feedback failed; correction required")
        return {**self.status(state), "feature_checks_passed": evidence["passed"],
                "missing_required_checks": evidence["missing_required_checks"], "results": results}

    def require_checks(self, state):
        self.require_ticket(state)
        self.integrity(state)
        self.require_manual(state)
        correction = state.get("record_correction")
        if correction:
            prior = correction["prior_review"]
            if (correction["fingerprint"] != self.current(state)
                    or file_hash(Path(prior["report"])) != prior["sha256"]):
                raise EngineError("Records-only provenance changed; ordinary repair is required")
        evidence = state.get("checks")
        if not evidence or not evidence["passed"] or evidence["fingerprint"] != self.current(state):
            raise EngineError("Passing checks for the current inputs are required; earlier evidence is missing or stale")
        expected = {check["id"] for check in state["profile"]["checks"]}
        if (len(evidence["results"]) != len(expected)
                or {result["id"] for result in evidence["results"]} != expected):
            raise EngineError("Required command results are missing")
        for result in evidence["results"]:
            if not result["passed"] or file_hash(Path(result["log"])) != result["log_sha256"]:
                raise EngineError("Check evidence was modified or did not pass")
            configured = next(check for check in state["profile"]["checks"] if check["id"] == result["id"])
            if (result.get("argv") != command_argv(configured, self.project, self.directory)
                    or result.get("kind") != configured["kind"]):
                raise EngineError("Check command evidence differs from the reviewed profile")
            expected_outputs = {str(inside(self.project, name)) for name in configured.get("artifacts", [])}
            if {item["path"] for item in result.get("artifacts", [])} != expected_outputs:
                raise EngineError("Required check output artifacts are missing")
            for artifact in result.get("artifacts", []):
                if file_hash(Path(artifact["path"])) != artifact["sha256"]:
                    raise EngineError("Check output evidence was modified")
