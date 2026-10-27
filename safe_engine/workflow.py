"""Explicit delivery transitions around the analysis and execution methods."""

from pathlib import Path
import re
import shutil  # noqa: F401 - patch seam: tests patch safe_engine.workflow.shutil.which
import uuid

from . import __version__
from .acceptance import validate_manual_receipt
from .checks import CheckMixin
from .contract import ContractMixin
from .project import (EngineError, bundle_revision, digest, file_hash, fingerprint, git, inside,
                      production_fingerprint, protected_inputs, reject_path_aliases, validate_profile, validate_task)
from .proof import deferred_findings, handoff_table
from .review import DELEGATION, EXTERNAL, RESERVED, REVIEW_ROUNDS, VOLATILE, ReviewMixin  # noqa: F401 - public names
from .runner import run_command
from .storage import atomic_json, now, read_json, save
from .tickets import TicketStore, ticket_key


PHASES = {"analyze", "plan", "build", "manual", "testing", "verify", "improve", "final-verify", "review", "ready", "cancelled"}


def resumable(saved):
    """Whether this bundle may load a run saved by bundle version `saved`: same MAJOR and never older (SemVer).
    0.1.0 is the label every bundle carried before 1.0.0 froze that surface."""
    def parse(text):
        return tuple(map(int, re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", "1.0.0" if text == "0.1.0" else text).groups()))
    try:
        old, new = parse(saved), parse(__version__)
    except (AttributeError, TypeError):  # not a version string
        return False
    return old[0] == new[0] and old <= new


class Workflow(ContractMixin, CheckMixin, ReviewMixin):
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

    # One seam per side effect: mixins resolve save/run_command here, so patching this module still applies.
    def persist(self, state, event):
        save(self.directory, state, event)

    @staticmethod
    def launch(*args, **kwargs):
        return run_command(*args, **kwargs)

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
        state = {"schema_version": 1, "suite_policy": 1, "bundle_version": __version__, "run_id": str(uuid.uuid4()), "checklist_required": True,
                 "project": str(self.project), "task": task, "profile": profile,
                 "contract_digest": self.contract_digest(task, profile, ticket),
                 "base_commit": git(self.project, "rev-parse", "HEAD"), "phase": "analyze",
                 "max_repairs": max_repairs, "repairs_used": 0, "sequence": 0, "history": [],
                 "artifacts": {}, "checks": None, "review": None, "pending_operation": None,
                 "protected": protected_inputs(self.project, profile), "created_at": now()}
        if modern:
            state.update(delivery_version=2, contract_sealed=False, contract_revision=0,
                         original_task=task, contract_history=[], manual=None, worth=True)
        if ticket:
            state.update(ticket=ticket, ticket_observation=capture["sequence"], builder_session=session)
        state["initial_fingerprint"] = self.current(state)
        if ticket:
            store.claim(self.ticket_key, state["run_id"], self.directory)
        try:
            if ticket:
                atomic_json(self.directory / "ticket-observations" / f"{capture['sequence']:06d}.json", capture)
            self.persist(state, "Initialized reviewed task and project profile")
        except OSError:
            if ticket:
                store.abandon_empty_reservation(self.ticket_key, state["run_id"], self.directory)
            raise
        return self.status(state)

    def load(self):
        state = read_json(self.directory / "state.json")
        if not isinstance(state, dict) or state.get("schema_version") != 1 or state.get("phase") not in PHASES:
            raise EngineError("Invalid or unsupported task record; inspect the saved history")
        if state.get("project") != str(self.project) or not resumable(state.get("bundle_version")):
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
                "feature_candidate": current if state.get('suite_policy') and state['phase'] == 'build' else None,
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
        self.persist(state, f"Recorded {kind}")
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
            if state.get('feature_checks') and not state['feature_checks']['passed']:
                raise EngineError('Failed feature feedback requires repair before final implementation')
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
        self.persist(state, f"Recorded final-stage {kind}")
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

    def capture_artifact(self, state, kind, source, current):
        content = Path(source).read_text(encoding="utf-8-sig")
        if len(content.strip()) < 40:
            raise EngineError("Provide a substantive artifact, not an empty completion claim")
        relative = f"artifacts/{state['sequence'] + 1:04d}-{kind}.md"
        target = self.directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        state["artifacts"][kind] = {"path": relative, "sha256": file_hash(target), "fingerprint": current}

    def repair(self, reason, records_only=False, findings=None, selected=None, finishing_authority=None):
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
        if state.get("worth"):
            self.select_repairs(state, findings, selected, finishing_authority)
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
        self.persist(state, f"Repair batch: {reason}")
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
        self.persist(state, f"Records-only correction; original raw evidence retained: {reason}")
        return self.status(state)

    def handoff(self):
        state = self.load()
        self.require_ticket(state, fresh=True)
        if self.ticket_key:
            checklist = self.store.get(self.ticket_key)["contract"].get("checklist", [])
            if state.get("checklist_required") and not checklist:  # runs started before this rule keep working
                raise EngineError("Write the ticket's checklist (the plan's todos) before handoff")
            open_items = [item["id"] for item in checklist if not item["done"]]
            if open_items:
                raise EngineError("Tick every checklist item in the ticket before handoff: " + ", ".join(open_items))
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
                  "", "PR delivery requires how-to-make-a-pr and a full deep-review PR review in a separate cloud/remote environment with fresh context. Local review is not PR approval; await the owner's cloud review before merge.",
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
        self.persist(state, "Prepared checked local handoff")
        if self.ticket_key:
            self.store.release(self.ticket_key, state["run_id"])
        return {"handoff": str(path), **self.status(state)}

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
        self.persist(state, f"Cancelled: {reason}")
        if self.ticket_key:
            self.store.release(self.ticket_key, state["run_id"])
        return self.status(state)
