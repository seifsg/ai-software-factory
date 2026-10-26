"""Shared fixtures for the speed-work regressions: synthetic reviewer, owner and manual receipts;
real commands, Git, locks, hashes and state files."""

from copy import deepcopy
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch
import test_delivery_v2 as v2
import test_tickets as tickets
from safe_engine.storage import atomic_json
from safe_engine.workflow import DELEGATION

BUNDLE = Path(__file__).resolve().parents[1]
DOUBLE = "Synthetic double; no actual independent acceptance"
REAL_WHICH = shutil.which


def report(verdict="PASS", findings=()):
    return {"verdict": verdict, "summary": DOUBLE, "method_followed": True,
            "criteria": [{"id": "A1", "status": "PASS", "evidence": DOUBLE}], "findings": list(findings)}


def finding(severity="HIGH", disposition="blocking", exception=None):
    return {"severity": severity, "location": "README.md:1", "description": "Synthetic finding",
            "disposition": disposition, "exception": exception, "layer": "product",
            "evidence_status": "valid", "evidence": DOUBLE, "action": "Synthetic action",
            "worth": {"notice": 1, "harm": 1, "minutes": 10, "required": disposition == "blocking", "reason": DOUBLE}}


def deferral(owner="owner", authority=DELEGATION):
    return {"owner": owner, "reason": "Synthetic reason", "scope": "local", "revisit": "Before release",
            "authority": authority, "destination": "synthetic:followup-1"}


def reconcile_double(body, state):
    """Explicit synthetic reconciliation for existing lifecycle tests; omission regressions bypass this helper."""
    if not isinstance(body, dict) or not isinstance(body.get("findings"), list) or not state.get("fix_rounds"):
        return body
    body = deepcopy(body)
    owed = {(receipt["sha256"], f"F{index}"): item for receipt in state["fix_rounds"]
            for index, item in enumerate(receipt["report"]["findings"], 1)}
    body.update(retained=[], resolved=[])
    for (digest, number), item in owed.items():
        entry = {"report_sha256": digest, "finding": number}
        if item in body["findings"]:
            body["retained"].append({**entry, "current_finding": f"F{body['findings'].index(item) + 1}"})
        else:
            body["resolved"].append({**entry, "evidence": DOUBLE})
    return body


REVIEWER_BINARIES = {"codex", "claude", "agent", "cursor-agent"}


def codex(present):
    """Make shutil.which see (or not see) a Codex CLI and no other reviewer agent; other lookups stay real."""
    return patch("shutil.which", side_effect=lambda name, *a, **k: sys.executable if name == "codex" and present
                 else None if name in REVIEWER_BINARIES else REAL_WHICH(name, *a, **k))


class Base(unittest.TestCase):
    def fixture(self, ids=("A1",)):
        """A disposable v2 consumer whose criteria are all manual."""
        f = v2.DeliveryV2Tests(methodName="runTest")
        f.setUp()
        self.addCleanup(f.doCleanups)
        f.task["acceptance"] = [{"id": i, "text": f"Criterion {i} holds", "mode": "manual", "checks": []}
                                for i in ids]
        return f

    def ticket_fixture(self):
        f = tickets.TicketTests(methodName="runTest")
        f.setUp()
        self.addCleanup(f.doCleanups)
        return f

    def seal_with(self, f, checks=(), parallel=None):
        """Seal the final contract (optionally with real checks) and record the batch."""
        task, profile = deepcopy(f.task), deepcopy(f.profile)
        if checks:
            profile.update(protected_paths=sorted({"tests/" + c["script"] for c in checks}),
                           checks=[{k: v for k, v in c.items() if k != "script"} for c in checks])
            task["acceptance"][0].update(mode="mixed", checks=[c["id"] for c in checks])
        if parallel is not None:
            profile["parallel_checks"] = parallel
        f.task, f.profile = task, profile
        f.flow.seal(task, profile, f.review_double(task, profile))
        f.artifact("batch")

    def to_review(self, ids=("A1",)):
        f = self.fixture(ids)
        f.start_build()
        f.finish_manual()
        self.seal_with(f)
        self.assertTrue(f.flow.check()["checks_passed"])
        return f

    def codex_review(self, f, body):
        body = reconcile_double(body, f.flow.load())
        def double(argv, cwd, timeout, log, stdin):
            atomic_json(Path(argv[argv.index("--output-last-message") + 1]), body)
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(DOUBLE, encoding="utf-8")
            return {"passed": True, "synthetic": DOUBLE}
        with codex(True), patch("safe_engine.workflow.run_command", side_effect=double):
            return f.flow.review(10)

    def redo(self, f):
        """One full correction cycle back to the review phase."""
        f.repair("Synthetic correction")
        f.finish_manual()
        f.artifact("batch")
        self.assertTrue(f.flow.check()["checks_passed"])

    def set_state(self, f, **values):
        state = f.flow.load()
        state.update(values)
        atomic_json(f.flow.directory / "state.json", state)


def script(f, name, body):
    folder = f.root / "tests"
    folder.mkdir(exist_ok=True)
    (folder / name).write_text(body, encoding="utf-8")


def command(identifier, name, *args, artifacts=()):
    return {"id": identifier, "kind": "unit", "script": name, "timeout_seconds": 30,
            "argv": ["{python}", f"tests/{name}", *args], "artifacts": list(artifacts)}


RENDEZVOUS = ("import sys, time\nfrom pathlib import Path\n"
              "mine, other = Path(sys.argv[1]), Path(sys.argv[2])\nmine.write_text('x')\n"
              "end = time.time() + 12\n"
              "while time.time() < end:\n    if other.exists(): sys.exit(0)\n    time.sleep(0.02)\nsys.exit(1)\n")
PAUSE = ("import sys, time\nfrom pathlib import Path\ntime.sleep(0.4)\n"
         "Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)\nPath(sys.argv[1]).write_text('out')\n")
