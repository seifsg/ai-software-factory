"""Independent review: Codex launch, external packets/reports, verdict rules and the round cap."""

import os
from pathlib import Path
import shutil
import uuid

from .project import EngineError, digest, file_hash, rescan
from .review_packet import review_prompt, schema_errors
from .storage import atomic_json, read_json


VOLATILE = {"sequence", "history", "updated_at", "review_packet", "review_rounds", "failed_reviews",
            "pending_operation"}  # save counters and cap bookkeeping; not reviewed records
RESERVED = {"state.json", "lock", "handoff.md", "history", "outputs", "logs", "artifacts", "ticket-observations",
            "entry-bundle.json", "runs"}  # runs: legacy runs use .factory itself as the run dir
REVIEW_ROUNDS = 3  # Seif, 6 Oct: failed reviews before the owner decides
DELEGATION = "Seif 6 Oct delegation"  # LOW, and MEDIUM at local exposure, may be deferred
EXTERNAL = "external reviewer; independence not verified by the controller"


class ReviewMixin:
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
        self.persist(state, "Started fresh read-only Codex review")
        log = self.directory / "logs" / f"{state['sequence']:04d}-review.log"
        result = self.launch([codex, "exec", "--sandbox", "read-only", "--ephemeral", "-C", str(self.project),
                             "--output-schema", str(self.schema_path(state)),
                             "--output-last-message", str(output), "-"], self.project, timeout, log, prompt)
        rescan()
        state["pending_operation"] = None
        if not result["passed"] or not output.exists() or self.current(state) != current:
            self.persist(state, "Independent review failed or inputs changed; no acceptance")
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
        out = self.outside_inputs(out)
        if state.get("review_packet"):
            state["failed_reviews"] = state.get("failed_reviews", 0) + 1  # an unsubmitted verdict counts as failed
            self.require_reviewable(state)
        nonce = uuid.uuid4().hex
        prompt = review_prompt(state, self.directory, Path(__file__).resolve().parent.parent)
        prompt += (f"\nReturn only JSON matching the schema at {self.schema_path(state)}. "
                   "Run as a fresh, read-only, separately spawned reviewer. "
                   f"Start your summary with review nonce {nonce}.\n")
        out.write_text(prompt, encoding="utf-8")
        state["review_packet"] = {"fingerprint": self.current(state), "sha256": file_hash(out), "nonce": nonce,
                                  "path": str(out), "sequence": state["sequence"] + 1,
                                  "records": self.records_digest(state)}
        self.persist(state, "Issued external review packet")
        return {**self.status(state), "packet": str(out)}

    @staticmethod
    def records_digest(state):
        """Binds a review packet to the run records it judged, not to the save counter."""
        return digest({key: value for key, value in state.items() if key not in VOLATILE})

    def outside_inputs(self, path):
        """Packets/reports inside the project would change its fingerprint; keep them under .factory or outside."""
        path = Path(os.path.abspath(path))  # applies the OS's own trailing space/dot trimming, nothing more
        try:
            path = path.resolve()
        except OSError as error:
            raise EngineError(f"Use a plain, resolvable path: {path}") from error
        if str(path).startswith("\\\\?\\"):  # fail closed: resolve() keeps this prefix only for odd names
            raise EngineError(f"Use a plain path, not an extended-length path: {path}")
        project, run = self.project.resolve(), self.directory.resolve()
        if (path == project or project in path.parents) and run not in path.parents:
            raise EngineError(f"Use a path under {run} or outside the project: {path}")
        if run in path.parents:
            top = path.relative_to(run).parts[0].lower()
            if top in RESERVED or top.startswith("review-"):
                raise EngineError(f"{top} is reserved for the controller; pick another name in {run}")
        return path

    def external_review(self, state, source, reviewer, codex):
        if codex:
            raise EngineError("Codex CLI is available and stays the default; run review --timeout <seconds>")
        if source is None or not isinstance(reviewer, str) or not reviewer.strip():
            raise EngineError("External review needs --report <file.json> and --reviewer <host/agent id/model>")
        packet = state.get("review_packet")
        current = self.current(state)
        if not packet:
            raise EngineError("Issue review-packet first and hand it to a fresh read-only subagent")
        stale = (packet["records"] != self.records_digest(state) if "records" in packet
                 else packet["sequence"] != state["sequence"])
        if stale or packet["fingerprint"] != current:
            raise EngineError("Inputs or records changed since the review packet; issue a fresh review-packet")
        issued = Path(packet["path"])
        if issued.is_symlink() or not issued.is_file() or file_hash(issued) != packet["sha256"]:
            raise EngineError("Review packet changed or missing; issue a fresh review-packet")
        report = read_json(self.outside_inputs(source))
        if not isinstance(report, dict):
            raise EngineError("Review report must be a JSON object")
        if packet.get("nonce") and packet["nonce"] not in str(report.get("summary", "")):
            raise EngineError("Report lacks this packet's review nonce; old or foreign reports are rejected")
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
        self.persist(state, "Independent review passed" if passed else "Independent review requires correction")
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

    def extend_reviews(self, rounds, reason):
        """Owner-approved extra review rounds after the cap; the reason stays in history."""
        state = self.load()
        self.require_ticket(state)
        if state["phase"] == "cancelled":
            raise EngineError("Cancelled runs cannot be extended")
        if type(rounds) is not int or not 1 <= rounds <= 3 or not isinstance(reason, str) or not reason.strip():
            raise EngineError("Extend by 1-3 rounds with the owner's reason")
        state["review_rounds"] = max(state.get("review_rounds", REVIEW_ROUNDS), state.get("failed_reviews", 0)) + rounds
        self.persist(state, f"Owner extended review rounds by {rounds}: {reason}")
        return self.status(state)
