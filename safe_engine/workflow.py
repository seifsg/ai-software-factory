"""Explicit delivery transitions around Seif's analysis and execution methods."""

from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
import shutil
import threading
import uuid

from . import __version__
from .project import (EngineError, bundle_revision, command_argv, digest, file_hash, fingerprint, git, inside,
                      protected_inputs, reject_path_aliases, rescan, validate_profile, validate_task)
from .runner import run_command
from .storage import atomic_json, now, read_json, save
from .acceptance import (contract_candidate_digest, validate_contract_review,
                         validate_manual_receipt)
from .project import production_fingerprint
from .proof import deferred_findings, handoff_table, proof_draft
from .review_packet import review_prompt, schema_errors
from .tickets import TicketStore, ticket_key


REVIEW_ROUNDS = 3  # Seif, 6 Oct: failed reviews before the owner decides
DELEGATION = "Seif 6 Oct delegation"  # LOW, and MEDIUM at local exposure, may be deferred
EXTERNAL = "external reviewer; independence not verified by the controller"
PHASES = {"analyze", "plan", "build", "manual", "testing", "verify", "improve", "final-verify", "review", "ready", "cancelled"}


class Workflow:
    def __init__(self, project, ticket=None):
        self.project = project
        self.ticket_key = ticket_key(ticket) if ticket is not None else None
        self.directory = project / ".factory"
        if self.ticket_key:
            self.directory /= "runs/" + self.ticket_key
        reject_path_aliases(self.directory, self.project)
        self._store = None

    @property
    def store(self):
        """One TicketStore (one git-common-dir read) per workflow."""
        if self._store is None:
            self._store = TicketStore(self.project)
        return self._store

    @staticmethod
    def contract_digest(task, profile, ticket=None):
        value = {"task": task, "profile": profile}
        if ticket is not None:
            value["ticket"] = ticket
        return digest(value)

    def ticket_proposal(self, task, profile):
        prefix = self.directory.relative_to(self.project).as_posix() + "/outputs/"
        for check in profile.get("checks", []):
            if any(not name.startswith(prefix) for name in check.get("artifacts", [])):
                raise EngineError("Output artifacts must belong to the selected run, never another ticket")
        if not self.ticket_key:
            return None, None
        capture, ticket = self.store.ready(self.ticket_key)
        if profile.get("version") != 2:
            raise EngineError("Ticket delivery requires the complete version 2 factory cycle")
        criteria = lambda items: {item["id"]: item["text"] for item in items}
        if (task["request"] != ticket["scope"]["original_request"]
                or criteria(task["acceptance"]) != criteria(ticket["scope"]["acceptance"])):
            raise EngineError("Task request/criteria must match the owner-confirmed canonical ticket")
        return capture, ticket

    def require_ticket(self, state, fresh=False):
        store = self.store
        if not self.ticket_key:
            store.block_legacy_writer()
            return
        capture, ticket = self.ticket_proposal(state["task"], state["profile"])
        if ticket != state.get("ticket"):
            raise EngineError("Confirmed ticket changed; preserve evidence and use reviewed amend before proceeding")
        if fresh and capture["sequence"] <= state.get("ticket_observation", 0):
            raise EngineError("This boundary needs a new complete MCP ticket/activity refresh")
        store.dependencies(self.ticket_key, after=state["updated_at"] if fresh else None)
        store.claim(self.ticket_key, state["run_id"], self.directory)
        if fresh:
            state["ticket_observation"] = capture["sequence"]
            atomic_json(self.directory / "ticket-observations" / f"{capture['sequence']:06d}.json", capture)

    def initialize(self, task, profile, max_repairs=None, session=None):
        if (self.directory / "state.json").exists():
            raise EngineError("This project already has a run. Resume it; use a fresh worktree for another task.")
        if any((self.directory / "history").glob("*.json")):
            raise EngineError("Current state is missing; recover the preserved run history instead of reinitializing")
        modern = isinstance(profile, dict) and profile.get("version") == 2
        validate_profile(profile, draft=modern)
        validate_task(task, profile, draft=modern)
        capture, ticket = self.ticket_proposal(task, profile)
        store = self.store
        if ticket:
            if not isinstance(session, str) or not session.strip():
                raise EngineError("Ticket initialization needs its dedicated builder session identity")
            legacy = self.project / ".factory/state.json"
            if legacy.exists():
                raise EngineError("A legacy run owns this checkout; use an independent worktree")
            store.dependencies(self.ticket_key)
        else:
            store.block_legacy_writer()
        if max_repairs is not None and (type(max_repairs) is not int or max_repairs < 0):
            raise EngineError("Deprecated max-repairs metadata must be a nonnegative integer")
        if git(self.project, "status", "--porcelain", "--untracked-files=normal"):
            raise EngineError("Initialize from a clean, committed project; preserve existing work before starting")
        state = {"schema_version": 1, "bundle_version": __version__, "run_id": str(uuid.uuid4()),
                 "project": str(self.project), "task": task, "profile": profile,
                 "contract_digest": self.contract_digest(task, profile, ticket),
                 "base_commit": git(self.project, "rev-parse", "HEAD"), "phase": "analyze",
                 "max_repairs": max_repairs, "repairs_used": 0, "sequence": 0, "history": [],
                 "artifacts": {}, "checks": None, "review": None, "pending_operation": None,
                 "protected": protected_inputs(self.project, profile), "created_at": now()}
        if modern:
            state.update(delivery_version=2, contract_sealed=False, contract_revision=0,
                         original_task=task, contract_history=[], manual=None)
        if ticket:
            state.update(ticket=ticket, ticket_observation=capture["sequence"], builder_session=session)
        state["initial_fingerprint"] = self.current(state)
        if ticket:
            store.claim(self.ticket_key, state["run_id"], self.directory)
        try:
            if ticket:
                atomic_json(self.directory / "ticket-observations" / f"{capture['sequence']:06d}.json", capture)
            save(self.directory, state, "Initialized reviewed task and project profile")
        except OSError:
            if ticket:
                store.abandon_empty_reservation(self.ticket_key, state["run_id"], self.directory)
            raise
        return self.status(state)

    def load(self):
        state = read_json(self.directory / "state.json")
        if not isinstance(state, dict) or state.get("schema_version") != 1 or state.get("phase") not in PHASES:
            raise EngineError("Invalid or unsupported task record; inspect the saved history")
        if state.get("project") != str(self.project) or state.get("bundle_version") != __version__:
            raise EngineError("Project or bundle version differs from the saved run")
        draft = state.get("delivery_version") == 2 and not state["contract_sealed"]
        validate_profile(state["profile"], draft=draft)
        validate_task(state["task"], state["profile"], draft=draft)
        prefix = self.directory.relative_to(self.project).as_posix() + "/outputs/"
        if any(not name.startswith(prefix) for check in state["profile"]["checks"] for name in check.get("artifacts", [])):
            raise EngineError("Saved outputs differ from the selected run namespace")
        if bool(state.get("ticket")) != bool(self.ticket_key) or (self.ticket_key and state["ticket"]["key"] != self.ticket_key):
            raise EngineError("Select the saved ticket run with --ticket; never patch its binding")
        if state.get("contract_digest") != self.contract_digest(state["task"], state["profile"], state.get("ticket")):
            raise EngineError("Task or profile changed after initialization; start a reviewed run in a fresh worktree")
        return state

    def current(self, state):
        return fingerprint(self.project, state["profile"], state["task"], self.directory,
                           draft=state.get("delivery_version") == 2 and not state["contract_sealed"],
                           ticket=state.get("ticket"))

    def require_phase(self, state, *phases):
        if state["phase"] not in phases:
            raise EngineError(f"This action requires {', '.join(phases)}; current phase is {state['phase']}")

    def integrity(self, state):
        if protected_inputs(self.project, state["profile"]) != state["protected"]:
            raise EngineError("Protected acceptance files changed; restore them. Do not weaken checks to pass.")
        for kind, artifact in state["artifacts"].items():
            if file_hash(self.directory / artifact["path"]) != artifact["sha256"]:
                raise EngineError(f"Recorded {kind} artifact changed; preserve the original evidence")

    def status(self, state=None):
        state = state or self.load()
        current = self.current(state)
        evidence = state.get("checks")
        feature = state.get("feature_checks")
        ticket_status, ticket_error, ticket_current = None, None, True
        if self.ticket_key:
            try:
                store = self.store
                ticket_status = store.status(self.ticket_key)
                ticket_current = (ticket_status["valid"] and ticket_status["confirmed"] and not ticket_status["pending"]
                                  and store.ready(self.ticket_key)[1] == state["ticket"])
            except EngineError as error:
                ticket_error, ticket_current = str(error), False
        return {"run_id": state["run_id"], "phase": state["phase"], "project": str(self.project),
                "ticket": ticket_status, "ticket_error": ticket_error, "ticket_current": bool(ticket_current),
                "repair_policy": "continuous", "repairs_used": state["repairs_used"],
                "max_repairs": None, "historical_max_repairs": state.get("max_repairs"),
                "failed_reviews": state.get("failed_reviews", 0),
                "review_rounds": state.get("review_rounds", REVIEW_ROUNDS),
                "checks_current": bool(ticket_current and evidence and evidence["fingerprint"] == current),
                "checks_passed": bool(evidence and evidence["passed"]),
                "feature_checks_current": bool(feature and feature["fingerprint"] == current),
                "feature_checks_passed": bool(feature and feature["passed"]),
                "review_current": bool(ticket_current and state.get("review") and state["review"]["fingerprint"] == current),
                "builder_session": state.get("builder_session"),
                "delivery_version": state.get("delivery_version", 1),
                "contract_sealed": state.get("contract_sealed", True),
                "contract_revision": state.get("contract_revision", 0),
                "manual_candidate": state.get("manual_candidate"),
                "bundle_root": str(Path(__file__).resolve().parent.parent),
                "bundle_revision": bundle_revision(Path(__file__).resolve().parent.parent),
                "review_execution": self.review_kind(state.get("review")),
                "review_packet": state.get("review_packet"),
                "prior_manual_receipts": [{"receipt_sha256": item["sha256"],
                                           "passed": [o["criterion"] for o in item["observations"]]}
                                          for item in state.get("manual_receipts", [])],
                "pending_operation": state.get("pending_operation"),
                "history_entries": len(state["history"]), "state": str(self.directory / "state.json")}

    def record(self, kind, source):
        state = self.load()
        self.require_ticket(state, fresh=kind == "implementation")
        if state.get("delivery_version") == 2:
            return self.record_delivery(state, kind, source)
        expected = {"analysis": "analyze", "plan": "plan", "batch": "build", "improvement": "improve"}
        if kind not in expected:
            raise EngineError(f"'{kind}' is a version 2 stage; this legacy run records analysis, plan, batch, improvement")
        self.require_phase(state, expected[kind])
        if state.get("pending_operation"):
            raise EngineError("An operation is incomplete; reconcile or rerun it before recording a stage")
        if kind == "batch" and state.get("feature_checks") and not state["feature_checks"]["passed"]:
            raise EngineError("Failed feature feedback requires repair before the version batch")
        self.integrity(state)
        current = self.current(state)
        if kind in ("analysis", "plan") and current != state["initial_fingerprint"]:
            raise EngineError("Code or declared inputs changed during analysis/planning; restore the starting candidate")
        self.capture_artifact(state, kind, source, current)
        state["phase"] = {"analysis": "plan", "plan": "build", "batch": "verify", "improvement": "final-verify"}[kind]
        state["review"] = None
        save(self.directory, state, f"Recorded {kind}")
        return self.status(state)

    def record_delivery(self, state, kind, source):
        expected = {"analysis": "analyze", "plan": "plan", "implementation": "build",
                    "manual": "manual", "batch": "testing"}
        if kind not in expected:
            raise EngineError("New delivery records improvement within implementation, before all testing")
        self.require_phase(state, expected[kind])
        if state.get("pending_operation"):
            raise EngineError("Reconcile the pending operation before recording a stage")
        self.integrity(state)
        current = self.current(state)
        if kind in ("analysis", "plan") and current != state["initial_fingerprint"]:
            raise EngineError("Code or declared inputs changed during analysis/planning")
        if kind == "implementation":
            state["manual_candidate"] = production_fingerprint(self.project, state["profile"], state.get("ticket"))
        if kind == "manual":
            if production_fingerprint(self.project, state["profile"], state.get("ticket")) != state["manual_candidate"]:
                raise EngineError("Implementation changed; repair and finish it before manual QA")
            state["manual"] = validate_manual_receipt(
                read_json(source), state["manual_candidate"], state["task"], self.project,
                state.get("manual_receipts", []))
        if kind == "batch":
            if not state["contract_sealed"]:
                raise EngineError("Seal the reviewed final acceptance contract before the test batch")
            self.require_manual(state)
        self.capture_artifact(state, kind, source, current)
        state["phase"] = {"analysis": "plan", "plan": "build", "implementation": "manual",
                          "manual": "testing", "batch": "verify"}[kind]
        state["review"] = None
        save(self.directory, state, f"Recorded final-stage {kind}")
        return self.status(state)

    def require_manual(self, state):
        if state.get("delivery_version") != 2:
            return
        receipt = state.get("manual")
        if not receipt or receipt["candidate"] != production_fingerprint(self.project, state["profile"], state.get("ticket")):
            raise EngineError("Current final manual QA evidence is required; repair changed implementation")
        required = {c["id"] for c in state["task"]["acceptance"] if c.get("mode", "automated") in ("manual", "mixed")}
        covered = {o["criterion"] for o in receipt["observations"] if o["status"] == "PASS"}
        if not required <= covered:
            raise EngineError("Manual criteria lack current PASS observations")
        for observation in receipt["observations"]:
            for evidence in observation["evidence"]:
                path = inside(self.project, evidence["path"])
                reject_path_aliases(path, self.project)
                if file_hash(path) != evidence["sha256"]:
                    raise EngineError("Manual evidence changed; repeat the affected final QA")

    def contract_proposal(self, task, profile):
        """Read-only binding for an independent reviewer, not approval by this command."""
        state = self.load()
        draft = state.get("delivery_version") == 2 and not state["contract_sealed"]
        validate_profile(profile, draft=draft)
        validate_task(task, profile, draft=draft)
        protected = protected_inputs(self.project, profile)
        _, ticket = self.ticket_proposal(task, profile)
        return {"old_digest": state["contract_digest"],
                "new_digest": contract_candidate_digest(task, profile, protected, ticket),
                "protected": protected, "task": task, "profile": profile, "ticket": ticket}

    def seal(self, task, profile, review):
        state = self.load()
        self.require_ticket(state)
        self.require_phase(state, "testing")
        if state.get("delivery_version") != 2 or state["contract_sealed"]:
            raise EngineError("Only a draft new-delivery contract can be sealed")
        if state.get("pending_operation"):
            raise EngineError("Reconcile the pending operation before sealing")
        self.integrity(state)
        self.require_manual(state)
        if not isinstance(profile, dict) or profile.get("version") != 2:
            raise EngineError("New delivery requires a version 2 profile")
        validate_profile(profile)
        validate_task(task, profile)
        # The final test contract cannot silently reclassify implementation as tests.
        for key in ("interface", "test_paths", "environment_inputs", "input_files", "review_scopes", "exposure"):
            if profile.get(key, []) != state["profile"].get(key, []):
                raise EngineError(f"Seal cannot change {key}; use a reviewed amendment")
        self.preserve_requirements(state["task"], task)
        proposal = self.contract_proposal(task, profile)
        validate_contract_review(review, proposal["old_digest"], proposal["new_digest"])
        self.require_manual({**state, "task": task, "profile": profile})
        self.save_contract(state, task, profile, proposal["protected"], review, "Sealed final acceptance")
        return self.status(state)

    @staticmethod
    def preserve_requirements(previous, proposed):
        if proposed.get("request") != previous["request"]:
            raise EngineError("Preserve the original request; a new product scope needs a new task")
        old = {item["id"]: item["text"] for item in previous["acceptance"]}
        new = {item["id"]: item["text"] for item in proposed.get("acceptance", [])}
        if old != new:
            raise EngineError("Preserve acceptance IDs/text; seal changes only evidence bindings")

    def save_contract(self, state, task, profile, protected, review, event, sealed=True, ticket=None):
        state["contract_history"].append({"task": state["task"], "profile": state["profile"],
            **({"ticket": state["ticket"]} if state.get("ticket") else {}),
            "protected": state["protected"], "digest": state["contract_digest"],
            "revision": state["contract_revision"], "review": review, "at": now()})
        state.update(task=task, profile=profile, protected=protected,
                     contract_digest=self.contract_digest(task, profile, ticket or state.get("ticket")),
                     contract_sealed=sealed, contract_revision=state["contract_revision"] + 1,
                     checks=None, review=None)
        if ticket is not None:
            state["ticket"] = ticket
        save(self.directory, state, event)

    def amend(self, task, profile, review, reason):
        state = self.load()
        if state.get("delivery_version") != 2 or state["phase"] == "cancelled" or (not self.ticket_key and state["phase"] in ("analyze", "plan")):
            raise EngineError("Amend a new-delivery build or final-stage contract; preserve cancelled runs")
        if state.get("pending_operation") or not reason.strip():
            raise EngineError("Amendment needs a reason and no pending operation")
        if not isinstance(profile, dict) or profile.get("version") != 2:
            raise EngineError("Amendment requires a version 2 profile")
        proposal = self.contract_proposal(task, profile)
        validate_contract_review(review, proposal["old_digest"], proposal["new_digest"])
        changed_scope = proposal["ticket"] != state.get("ticket")
        if self.ticket_key:
            store = self.store
            capture, _ = store.ready(self.ticket_key)
            store.dependencies(self.ticket_key)
            store.claim(self.ticket_key, state["run_id"], self.directory)
            if changed_scope:
                text_authority = review.get("acceptance_change_authority")
                if not isinstance(text_authority, str) or not text_authority.strip():
                    raise EngineError("Rebinding a ticket needs explicit owner scope-change authority in the review")
            state["ticket_observation"] = capture["sequence"]
            atomic_json(self.directory / "ticket-observations" / f"{capture['sequence']:06d}.json", capture)
        if task["request"] != state["original_task"]["request"]:
            raise EngineError("Amendment cannot replace the original request")
        old_criteria = {c["id"]: c["text"] for c in state["task"]["acceptance"]}
        new_criteria = {c["id"]: c["text"] for c in task["acceptance"]}
        authority = review.get("acceptance_change_authority")
        if old_criteria != new_criteria and (not isinstance(authority, str) or not authority.strip()):
            raise EngineError("Changed requirements need explicit acceptance_change_authority in the review")
        # A contract correction may repair protected tests; retain their prior hashes/history.
        for artifact in state["artifacts"].values():
            if file_hash(self.directory / artifact["path"]) != artifact["sha256"]:
                raise EngineError("Recorded evidence changed; preserve it before amendment")
        restart = changed_scope or state["phase"] in ("analyze", "plan")
        state["phase"] = "analyze" if restart else "build"
        state["manual"] = None
        for key in ("record_correction", "manual_candidate", "manual_receipts", "review_packet"):
            state.pop(key, None)
        for key in ("implementation", "manual", "batch", "improvement"):
            state["artifacts"].pop(key, None)
        if restart:
            for key in ("analysis", "plan"):
                state["artifacts"].pop(key, None)
            state["initial_fingerprint"] = self.current({**state, "task": task, "profile": profile,
                                                        "ticket": proposal["ticket"]})
        state["repairs_used"] += 1
        self.save_contract(state, task, profile, proposal["protected"], review, f"Reviewed amendment: {reason}",
                           sealed=state["contract_sealed"], ticket=proposal["ticket"])
        return self.status(state)

    def ticket_proof(self, source):
        state = self.load()
        self.require_ticket(state)
        self.require_phase(state, "review")
        if not self.ticket_key:
            raise EngineError("Ticket proof requires a bound ticket run")
        proof = read_json(source)
        ticket = state["ticket"]
        if proof.get("scope_digest") != ticket["scope_digest"] or proof.get("revision") != ticket["revision"]:
            raise EngineError("Proof must map the latest confirmed ticket revision/digest")
        expected = {c["id"] for c in ticket["scope"]["acceptance"]}
        rows = proof.get("criteria")
        if not isinstance(rows, list) or len(rows) != len(expected) or {row.get("id") for row in rows} != expected:
            raise EngineError("Map every latest ticket criterion exactly once")
        for row in rows:
            if row.get("status") != "PASS":
                raise EngineError("Unmet/unknown ticket expectations block acceptance")
            for field in ("before", "after", "implementation"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    raise EngineError(f"Ticket proof needs {field} per criterion")
            evidence = row.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                raise EngineError("Ticket proof needs actual evidence files per criterion")
            from .project import relative_input_path
            for item in evidence:
                name = relative_input_path(item["path"], allow_factory=True)
                path = inside(self.project, name)
                reject_path_aliases(path, self.project)
                if file_hash(path) != item.get("sha256"):
                    raise EngineError("Ticket proof evidence hash differs")
            deviations = row.get("deviations")
            if not isinstance(deviations, list):
                raise EngineError("Declare deviations explicitly, including an empty array")
            for deviation in deviations:
                if any(not isinstance(deviation.get(f), str) or not deviation[f].strip()
                       for f in ("change", "reason", "authority")):
                    raise EngineError("Approved deviations need change/reason/owner authority")
        self.capture_artifact(state, "ticket-proof", source, self.current(state))
        save(self.directory, state, "Mapped latest confirmed ticket expectations to before/after evidence")
        return self.status(state)

    def require_ticket_proof(self, state):
        if not self.ticket_key:
            return
        artifact = state["artifacts"].get("ticket-proof")
        if not artifact or artifact["fingerprint"] != self.current(state):
            raise EngineError("Map current confirmed ticket criteria with ticket-proof before review/handoff")
        proof = read_json(self.directory / artifact["path"])
        for row in proof["criteria"]:
            for item in row["evidence"]:
                path = inside(self.project, item["path"])
                reject_path_aliases(path, self.project)
                if file_hash(path) != item["sha256"]:
                    raise EngineError("Mapped ticket evidence changed")

    def ticket_proof_draft(self, out):
        """Pre-fill ticket-proof from recorded receipts/checks; the agent writes before/after."""
        state = self.load()
        self.require_ticket(state)
        self.require_phase(state, "review")
        if not self.ticket_key:
            raise EngineError("Ticket proof requires a bound ticket run")
        self.require_checks(state)
        draft = proof_draft(state, self.project)
        atomic_json(Path(out).absolute(), draft)
        return {"draft": str(out), "complete": ["before", "after"],
                "unknown": [row["id"] for row in draft["criteria"] if row["status"] != "PASS"]}

    def capture_artifact(self, state, kind, source, current):
        content = Path(source).read_text(encoding="utf-8-sig")
        if len(content.strip()) < 40:
            raise EngineError("Provide a substantive artifact, not an empty completion claim")
        relative = f"artifacts/{state['sequence'] + 1:04d}-{kind}.md"
        target = self.directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        state["artifacts"][kind] = {"path": relative, "sha256": file_hash(target), "fingerprint": current}

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
            save(self.directory, state, "Revalidated unchanged full version checks; no commands repeated")
            return {**self.status(state), "checks_reused": True, "results": state["checks"]["results"]}
        state["checks"] = None
        state["review"] = None
        state["pending_operation"] = "checks"
        save(self.directory, state, "Started check batch; previous acceptance invalidated")
        results = self.execute_checks(state, state["profile"]["checks"])
        unchanged = self.current(state) == current
        self.integrity(state)
        passed = unchanged and all(result["passed"] for result in results)
        state["checks"] = {"fingerprint": current, "passed": passed, "inputs_unchanged": unchanged, "results": results}
        state["pending_operation"] = None
        if passed:
            state["phase"] = ("review" if state.get("delivery_version") == 2
                              else "improve" if state["phase"] == "verify" else "review")
        save(self.directory, state, "Check batch passed" if passed else "Check batch failed; correction required")
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
        result = run_command(command_argv(check, self.project, self.directory), self.project,
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
        save(self.directory, state, "Started partial feature checks; no version acceptance")
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
        save(self.directory, state, "Feature feedback passed; version checks still required" if evidence["passed"]
             else "Feature feedback failed; correction required")
        return {**self.status(state), "feature_checks_passed": evidence["passed"],
                "missing_required_checks": evidence["missing_required_checks"], "results": results}

    def repair(self, reason, records_only=False):
        state = self.load()
        self.require_ticket(state)
        if records_only:
            return self.repair_records(state, reason)
        if state["phase"] == "build":
            if not state.get("feature_checks") or state["feature_checks"]["passed"]:
                raise EngineError("Build repair requires actual failed feature feedback")
        else:
            self.require_phase(state, "manual", "testing", "verify", "improve", "final-verify", "review", "ready")
        if not reason.strip():
            raise EngineError("Record the reason for correction")
        state["repairs_used"] += 1
        state["phase"] = "build"
        state["checks"] = None
        state["review"] = None
        state["feature_checks"] = None
        state["pending_operation"] = None
        state["artifacts"].pop("batch", None)
        state["artifacts"].pop("improvement", None)
        state.pop("record_correction", None)
        state.pop("review_packet", None)
        if state.get("delivery_version") == 2:
            if state.get("manual") and "manual" in state["artifacts"]:
                # Unaffected criteria may later be carried from this receipt; see acceptance.py.
                state.setdefault("manual_receipts", []).append(
                    {"sha256": state["artifacts"]["manual"]["sha256"], "observations": state["manual"]["observations"]})
            state["manual"] = None
            state.pop("manual_candidate", None)
            state["artifacts"].pop("implementation", None)
            state["artifacts"].pop("manual", None)
        save(self.directory, state, f"Repair batch: {reason}")
        return self.status(state)

    def repair_records(self, state, reason):
        """Keep original exact-input proof; discard its assessment, never mint a new pass."""
        self.require_phase(state, "review", "ready")
        if (state.get("delivery_version") != 2 or not state.get("contract_sealed")
                or state["profile"].get("reuse_record_evidence") is not True):
            raise EngineError("Records-only repair requires sealed version 2 reviewed-profile opt-in")
        if not reason.strip() or state.get("pending_operation"):
            raise EngineError("Records-only repair needs a reason and reconciled operations")
        self.require_ticket(state, fresh=True)
        self.require_checks(state)
        review = state.get("review")
        current = self.current(state)
        if (not review or review.get("fingerprint") != current
                or file_hash(Path(review["report"])) != review["sha256"]):
            raise EngineError("Records-only repair needs intact review evidence for exact current inputs")
        report = read_json(review["report"])
        self.validate_review(report, state)
        if (report["method_followed"] is not True
                or (report["verdict"] == "FAIL" and not report["findings"])
                or any(criterion["status"] != "PASS" for criterion in report["criteria"])
                or any(finding.get("layer", "product") not in ("evidence", "report")
                       or finding.get("evidence_status") != "valid"
                       or not all(isinstance(finding.get(key), str) and finding[key].strip()
                                  for key in ("evidence", "action"))
                       for finding in report["findings"])):
            raise EngineError("Product findings, challenged proof or failed/unknown criteria need ordinary repair")
        # History retains the old report; these references expose reuse provenance to the next reviewer.
        state["record_correction"] = {"reason": reason, "fingerprint": current,
                                      "prior_review": review, "origin_sequence": state["sequence"],
                                      "manual_artifact": state["artifacts"].get("manual")}
        state["repairs_used"] += 1
        state["phase"] = "review"
        state["review"] = None
        state["artifacts"].pop("ticket-proof", None)
        save(self.directory, state, f"Records-only correction; original raw evidence retained: {reason}")
        return self.status(state)

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

    def require_reviewable(self, state):
        self.require_phase(state, "review")
        if state.get("review") and not state["review"]["passed"]:
            raise EngineError("Completed review requires correction; use repair before another review")
        if state.get("failed_reviews", 0) >= state.get("review_rounds", REVIEW_ROUNDS):
            raise EngineError("Review round cap reached; Seif decides: extend-reviews, amend or cancel")
        self.require_checks(state)
        self.require_ticket_proof(state)

    def review(self, timeout=None, report=None, reviewer=None):
        state = self.load()
        self.require_reviewable(state)
        codex = shutil.which("codex")
        if report is not None or reviewer is not None:
            return self.external_review(state, report, reviewer, codex)
        if type(timeout) is not int or not 1 <= timeout <= 3600:
            raise EngineError("Specify a review timeout between 1 and 3600 seconds")
        if not codex:
            raise EngineError("Codex CLI is unavailable; issue review-packet to a fresh read-only host subagent, "
                              "then review --report <file.json> --reviewer <id>")
        current = self.current(state)
        package = Path(__file__).resolve().parent
        output = self.directory / f"review-{state['sequence'] + 1:04d}.json"
        state["review"] = None
        state["pending_operation"] = "independent-review"
        prompt = review_prompt(state, self.directory, package.parent)
        save(self.directory, state, "Started fresh read-only Codex review")
        log = self.directory / "logs" / f"{state['sequence']:04d}-review.log"
        result = run_command([codex, "exec", "--sandbox", "read-only", "--ephemeral", "-C", str(self.project),
                              "--output-schema", str(self.schema_path(state)),
                              "--output-last-message", str(output), "-"], self.project, timeout, log, prompt)
        rescan()
        state["pending_operation"] = None
        if not result["passed"] or not output.exists() or self.current(state) != current:
            save(self.directory, state, "Independent review failed or inputs changed; no acceptance")
            raise EngineError(f"Independent review did not complete on unchanged inputs; inspect {log}")
        return self.conclude_review(state, read_json(output), output, current, result)

    @staticmethod
    def schema_path(state):
        package = Path(__file__).resolve().parent
        return package / ("review-schema-v2.json" if state.get("delivery_version") == 2 else "review-schema.json")

    def review_packet(self, out):
        """Prompt for a host subagent when no Codex CLI exists; binds the current inputs and state."""
        state = self.load()
        self.require_reviewable(state)
        prompt = review_prompt(state, self.directory, Path(__file__).resolve().parent.parent)
        prompt += (f"\nReturn only JSON matching the schema at {self.schema_path(state)}. "
                   "Run as a fresh, read-only, separately spawned reviewer.\n")
        Path(out).write_text(prompt, encoding="utf-8")
        state["review_packet"] = {"fingerprint": self.current(state), "sha256": file_hash(Path(out)),
                                  "path": str(Path(out).resolve()), "sequence": state["sequence"] + 1}
        save(self.directory, state, "Issued external review packet")
        return {**self.status(state), "packet": str(out)}

    def external_review(self, state, source, reviewer, codex):
        if codex:
            raise EngineError("Codex CLI is available and stays the default; run review --timeout <seconds>")
        if source is None or not isinstance(reviewer, str) or not reviewer.strip():
            raise EngineError("External review needs --report <file.json> and --reviewer <host/agent id/model>")
        packet = state.get("review_packet")
        current = self.current(state)
        if not packet:
            raise EngineError("Issue review-packet first and hand it to a fresh read-only subagent")
        if packet["sequence"] != state["sequence"] or packet["fingerprint"] != current:
            raise EngineError("Inputs or records changed since the review packet; issue a fresh review-packet")
        report = read_json(source)
        errors = schema_errors(report, read_json(self.schema_path(state)))
        if errors:
            raise EngineError("Review report does not match its schema: " + "; ".join(errors[:5]))
        output = self.directory / f"review-{state['sequence'] + 1:04d}.json"
        atomic_json(output, report)
        state.pop("review_packet")
        return self.conclude_review(state, report, output, current,
                                    {"kind": "external", "reviewer": reviewer.strip(),
                                     "packet_sha256": packet["sha256"], "note": EXTERNAL})

    def conclude_review(self, state, report, output, current, execution):
        self.validate_review(report, state)
        passed = (report["verdict"] == "PASS" and report["method_followed"]
                  and all(c["status"] == "PASS" for c in report["criteria"])
                  and not any(self.finding_blocks(f, state) for f in report["findings"]))
        state["review"] = {"fingerprint": current, "passed": passed, "report": str(output),
                           "sha256": file_hash(output), "execution": execution}
        state["phase"] = "ready" if passed else "review"
        if not passed:
            state["failed_reviews"] = state.get("failed_reviews", 0) + 1
        save(self.directory, state, "Independent review passed" if passed else "Independent review requires correction")
        return {**self.status(state), "report": report}

    @staticmethod
    def review_kind(review):
        if not review:
            return None
        execution = review.get("execution") or {}
        if execution.get("kind") == "external":
            return f"{execution['reviewer']}: {EXTERNAL}"
        return "codex"

    @staticmethod
    def finding_blocks(finding, state):
        if state.get("delivery_version") != 2:
            return finding["severity"] in ("CRITICAL", "HIGH", "MEDIUM")
        if finding["severity"] in ("CRITICAL", "HIGH") or finding["disposition"] == "blocking":
            return True
        exposed = (state["profile"].get("exposure", "local") != "local"
                   or "release" in state["profile"].get("review_scopes", []))
        exception = finding.get("exception") or {}
        if exception.get("authority") == DELEGATION and (
                exception.get("owner") != "Seif" or (finding["severity"] == "MEDIUM" and exposed)):
            return True  # The delegation covers LOW, and MEDIUM only at local exposure.
        return finding["disposition"] == "before-exposure" and exposed

    @staticmethod
    def validate_review(report, state):
        expected = {criterion["id"] for criterion in state["task"]["acceptance"]}
        if not isinstance(report, dict) or report.get("verdict") not in ("PASS", "FAIL"):
            raise EngineError("Invalid independent review report")
        if type(report.get("method_followed")) is not bool or not isinstance(report.get("summary"), str) or not report["summary"].strip():
            raise EngineError("Review must assess the method and explain its verdict")
        criteria = report.get("criteria")
        if not isinstance(criteria, list) or len(criteria) != len(expected):
            raise EngineError("Review must assess every criterion exactly once")
        if any(not isinstance(c, dict) for c in criteria) or {c.get("id") for c in criteria} != expected:
            raise EngineError("Review criterion IDs do not match the original task")
        for criterion in criteria:
            if criterion.get("status") not in ("PASS", "FAIL", "UNKNOWN") or not isinstance(criterion.get("evidence"), str) or not criterion["evidence"].strip():
                raise EngineError("Review requires supported criterion outcomes")
        if not isinstance(report.get("findings"), list):
            raise EngineError("Review must include its findings, including an empty list for a clean result")
        for finding in report["findings"]:
            if not isinstance(finding, dict) or finding.get("severity") not in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                raise EngineError("Malformed review finding")
            if not all(isinstance(finding.get(key), str) and finding[key].strip() for key in ("location", "description")):
                raise EngineError("A finding needs its location and explanation")
            if state.get("delivery_version") == 2:
                for field in ("layer", "evidence_status"):
                    allowed = ("product", "evidence", "report") if field == "layer" else ("valid", "missing", "challenged")
                    if field in finding and finding[field] not in allowed:
                        raise EngineError(f"Malformed finding {field}")
                for field in ("evidence", "action"):
                    if field in finding and (not isinstance(finding[field], str) or not finding[field].strip()):
                        raise EngineError(f"Finding needs nonempty {field}")
                if finding.get("disposition") not in ("blocking", "before-exposure", "accepted-deferral"):
                    raise EngineError("Finding needs an explicit disposition")
                if finding["disposition"] != "blocking":
                    exception = finding.get("exception")
                    if (finding["severity"] in ("CRITICAL", "HIGH") or not isinstance(exception, dict)
                            or not all(isinstance(exception.get(key), str) and exception[key].strip()
                                       for key in ("owner", "reason", "scope", "revisit", "authority"))):
                        raise EngineError("Nonblocking findings need bounded actual authority; high severity cannot be deferred")
                    if "destination" in exception and (not isinstance(exception["destination"], str) or not exception["destination"].strip()):
                        raise EngineError("Deferral needs a destination ticket")

    def handoff(self):
        state = self.load()
        self.require_ticket(state, fresh=True)
        self.require_ticket_proof(state)
        self.require_phase(state, "ready")
        self.require_checks(state)
        review = state.get("review")
        if not review or not review["passed"] or review["fingerprint"] != self.current(state):
            raise EngineError("Fresh independent review is required for the current candidate")
        if file_hash(Path(review["report"])) != review["sha256"]:
            raise EngineError("Independent review evidence changed")
        lines = ["# Safe Engine checked handoff", "", state["task"]["request"], "",
                 f"Run: {state['run_id']}", f"Base: {state['base_commit']}",
                 f"Candidate inputs: {review['fingerprint']}", "", "## Executed checks", ""]
        for check in state["checks"]["results"]:
            lines.append(f"- {check['id']}: exit {check['exit_code']} in {check['duration_seconds']}s; log {check['log']}")
        proof = state["artifacts"].get("ticket-proof")
        proof = read_json(self.directory / proof["path"]) if proof else None
        lines += ["", "## Criterion → change → proof → gap", "", *handoff_table(state, self.project, proof)]
        lines += deferred_findings(read_json(review["report"]))
        lines += ["", f"Independent review: {review['report']} ({self.review_kind(review)})", "", "Ready for the agreed human handoff. No push, merge, release, or deployment was performed by the controller.",
                  "", "PR delivery requires how-to-make-a-pr and full how-to-review-a-pr in a separate cloud/remote environment with fresh context. Local review is not PR approval; await the owner's cloud review before merge.",
                  "", "Evidence covers the declared checks and inputs. Local state is not a tamper-resistant receipt."]
        path = self.directory / "handoff.md"
        if state.get("ticket"):
            ticket = state["ticket"]
            lines += ["", "## Confirmed ticket", "", ticket["identity"]["url"],
                      f"Revision: {ticket['revision']}; scope: {ticket['scope_digest']}",
                      f"Builder session: {state['builder_session']}",
                      f"Criterion proof: {self.directory / state['artifacts']['ticket-proof']['path']}",
                      "Latest confirmed criteria must map to implementation, before/after proof, actual evidence and deviations in the PR.",
                      "Local handoff is not remote review, integrated dependency acceptance, or ticket closure."]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        save(self.directory, state, "Prepared checked local handoff")
        if self.ticket_key:
            self.store.release(self.ticket_key, state["run_id"])
        return {"handoff": str(path), **self.status(state)}

    def extend_reviews(self, rounds, reason):
        """Owner-approved extra review rounds after the cap; the reason stays in history."""
        state = self.load()
        self.require_ticket(state)
        if state["phase"] == "cancelled":
            raise EngineError("Cancelled runs cannot be extended")
        if type(rounds) is not int or not 1 <= rounds <= 3 or not isinstance(reason, str) or not reason.strip():
            raise EngineError("Extend by 1-3 rounds with the owner's reason")
        state["review_rounds"] = state.get("failed_reviews", 0) + rounds
        save(self.directory, state, f"Owner extended review rounds by {rounds}: {reason}")
        return self.status(state)

    def cancel(self, reason):
        state = self.load()
        if not isinstance(reason, str) or not reason.strip():
            raise EngineError("Cancellation needs a reason; retain the ticket's run history")
        if self.ticket_key:
            self.store.claim(self.ticket_key, state["run_id"], self.directory)
        else:
            self.store.block_legacy_writer()
        state["phase"] = "cancelled"
        state["review"] = None
        state["pending_operation"] = None
        save(self.directory, state, f"Cancelled: {reason}")
        if self.ticket_key:
            self.store.release(self.ticket_key, state["run_id"])
        return self.status(state)
