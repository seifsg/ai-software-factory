"""Exact-input record repairs. Review/owner assertions are explicit test doubles.

Real disposable Git inputs, command processes, counters, logs and output hashes
exercise controller behavior; no product, authenticated tracker or cloud approval.
Authored only after completed implementation and actual final manual QA.
"""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_delivery_v2 as v2
import test_tickets as tickets
import test_workflow as legacy
from safe_engine.project import EngineError, file_hash, validate_profile
from safe_engine.storage import atomic_json, save

BUNDLE = Path(__file__).resolve().parents[1]
DOUBLE = "Explicit synthetic record-review double; no actual independent acceptance"


class RecordRepairTests(unittest.TestCase):
    def fixture(self, opt_in=True):
        f = v2.DeliveryV2Tests(methodName="runTest")
        f.setUp()
        self.addCleanup(f.doCleanups)
        if opt_in is not None:
            f.profile["reuse_record_evidence"] = opt_in
        f.profile["environment_inputs"] = ["RECORD_REPAIR_CONTEXT"]
        (f.root / ".env").write_text("stable fixture config", encoding="utf-8")
        f.profile["input_files"] = [".env"]
        f.start_build()
        f.finish_manual()
        f.task, f.profile = f.configured_check()
        script = f.root / "tests/acceptance.py"
        script.write_text(script.read_text(encoding="utf-8") +
                          "out=Path('.factory/outputs/proof.txt')\n"
                          "out.parent.mkdir(parents=True, exist_ok=True)\n"
                          "out.write_text('Actual disposable command result; no product proof')\n"
                          "print('Actual fixture document command completed')\n", encoding="utf-8")
        f.profile["checks"][0]["artifacts"] = [".factory/outputs/proof.txt"]
        f.flow.seal(f.task, f.profile, f.review_double())
        f.artifact("batch")
        self.assertTrue(f.flow.check()["checks_passed"])
        self.install_review(f)
        return f

    def report(self):
        return {"verdict": "FAIL", "summary": DOUBLE, "method_followed": True,
                "criteria": [{"id": "A1", "status": "PASS", "evidence": DOUBLE}],
                "findings": [{"severity": "LOW", "location": "private-map:1",
                    "description": "Synthetic clerical pointer to intact raw proof",
                    "disposition": "blocking", "exception": None, "layer": "report",
                    "evidence_status": "valid", "evidence": DOUBLE, "action": "Correct pointer",
                    "worth": {"notice": 0, "harm": 0, "minutes": 5, "required": True, "reason": DOUBLE}}]}

    def install_review(self, f, report=None):
        report = self.report() if report is None else report
        state = f.flow.load()
        path = f.flow.directory / "synthetic-prior-review.json"
        atomic_json(path, report)
        state["review"] = {"fingerprint": f.flow.current(state), "passed": False,
                           "report": str(path), "sha256": file_hash(path),
                           "execution": {"synthetic": DOUBLE}}
        save(f.flow.directory, state, DOUBLE)
        return state

    def reject_unchanged(self, f):
        before = f.flow.load()
        with self.assertRaises(EngineError):
            f.flow.repair("Synthetic record correction", records_only=True)
        self.assertEqual(f.flow.load(), before)

    def test_success_keeps_raw_actions_commands_history_and_requires_fresh_review(self):
        f = self.fixture()
        before = f.flow.load()
        raw = {p: file_hash(Path(p)) for p in [before["review"]["report"],
               before["checks"]["results"][0]["log"], str(f.root / ".factory/outputs/proof.txt")]}
        result = f.flow.repair("Correct private pointer only", records_only=True)
        after = f.flow.load()
        self.assertEqual(result["phase"], "review")
        self.assertEqual(before["manual"], after["manual"])
        self.assertEqual(before["checks"], after["checks"])
        self.assertIsNone(after["review"])
        self.assertEqual(after["record_correction"]["origin_sequence"], before["sequence"])
        self.assertEqual(after["record_correction"]["prior_review"], before["review"])
        self.assertEqual(after["record_correction"]["manual_artifact"], before["artifacts"]["manual"])
        for name, expected in raw.items():
            self.assertEqual(file_hash(Path(name)), expected)
        self.assertEqual((f.root / ".factory/check-count").read_text(), "1")
        history = json.loads((f.flow.directory / "history" / f"{before['sequence']:04d}.json").read_text(encoding="utf-8"))
        self.assertEqual(history["review"], before["review"])
        with self.assertRaises(EngineError):
            f.flow.handoff()
        fresh = {**self.report(), "verdict": "PASS", "findings": []}
        def review_double(argv, cwd, timeout, log, stdin):
            self.assertIn("--ephemeral", argv)
            self.assertIn("read-only", argv)
            self.assertIn("record_correction", stdin)
            atomic_json(Path(argv[argv.index("--output-last-message") + 1]), fresh)
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(DOUBLE, encoding="utf-8")
            return {"passed": True, "synthetic": DOUBLE}
        with patch("safe_engine.workflow.shutil.which", return_value=sys.executable), \
                patch("safe_engine.workflow.run_command", side_effect=review_double) as reviewer:
            self.assertEqual(f.flow.review(10, builder="cursor")["phase"], "ready")
        self.assertEqual(reviewer.call_count, 1)
        self.assertEqual((f.root / ".factory/check-count").read_text(), "1")
        self.assertEqual(f.flow.handoff()["phase"], "ready")

    def test_absent_false_and_legacy_profiles_keep_ordinary_repair_policy(self):
        for opt_in in (None, False):
            with self.subTest(opt_in=opt_in):
                f = self.fixture(opt_in)
                self.reject_unchanged(f)
                self.assertEqual(f.repair("Ordinary correction")["phase"], "build")
                self.assertIsNone(f.flow.load()["manual"])
        f = legacy.WorkflowTests(methodName="runTest")
        f.setUp()
        self.addCleanup(f.tearDown)
        f.reviewed_input()
        self.reject_unchanged(f)
        p = deepcopy(f.profile)
        p["reuse_record_evidence"] = True
        with self.assertRaises(EngineError):
            validate_profile(p)
        for value in ("true", 1, None):
            p = {"version": 2, "interface": "library", "checks": [],
                 "environment_inputs": [], "input_files": [], "protected_paths": [],
                 "reuse_record_evidence": value}
            with self.subTest(value=value), self.assertRaises(EngineError):
                validate_profile(p, draft=True)

    def test_product_unclassified_missing_challenged_and_empty_proof_do_not_reuse(self):
        f = self.fixture()
        cases = [("layer", "product"), ("layer", None), ("evidence_status", "challenged"),
                 ("evidence_status", "missing"), ("evidence_status", None),
                 ("evidence", ""), ("action", "")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                report = self.report()
                if value is None:
                    del report["findings"][0][field]
                else:
                    report["findings"][0][field] = value
                self.install_review(f, report)
                self.reject_unchanged(f)
        for status in ("FAIL", "UNKNOWN"):
            report = self.report()
            report["criteria"][0]["status"] = status
            self.install_review(f, report)
            self.reject_unchanged(f)
        for report in ({**self.report(), "method_followed": False},
                       {**self.report(), "findings": []}):
            self.install_review(f, report)
            self.reject_unchanged(f)

    def test_documents_tests_config_environment_and_declared_inputs_invalidate(self):
        f = self.fixture()
        for name in ("README.md", "tests/acceptance.py", ".env"):
            with self.subTest(input=name):
                p = f.root / name
                original = p.read_bytes()
                p.write_bytes(original + b"\n# changed input\n")
                self.reject_unchanged(f)
                p.write_bytes(original)
        with patch.dict("os.environ", {"RECORD_REPAIR_CONTEXT": "changed"}):
            self.reject_unchanged(f)
        f.flow.repair("Inputs restored; correction records only", records_only=True)
        self.assertEqual((f.root / ".factory/check-count").read_text(), "1")

    def test_manual_log_output_report_artifact_and_command_binding_tamper_reject(self):
        f = self.fixture()
        state = f.flow.load()
        paths = [f.root / ".factory/manual-evidence.txt",
                 Path(state["checks"]["results"][0]["log"]),
                 f.root / ".factory/outputs/proof.txt", Path(state["review"]["report"]),
                 f.flow.directory / state["artifacts"]["manual"]["path"]]
        for p in paths:
            with self.subTest(path=p.name):
                original = p.read_bytes()
                p.write_bytes(original + b"\nmodified evidence")
                self.reject_unchanged(f)
                p.write_bytes(original)
        for field, value in (("argv", ["invented-pass"]), ("kind", "build"), ("artifacts", []),
                             ("passed", False)):
            changed = deepcopy(state)
            changed["checks"]["results"][0][field] = value
            atomic_json(f.flow.directory / "state.json", changed)
            self.reject_unchanged(f)
            atomic_json(f.flow.directory / "state.json", state)
        changed = deepcopy(state)
        changed["checks"]["passed"] = False
        atomic_json(f.flow.directory / "state.json", changed)
        self.reject_unchanged(f)

    def test_reused_provenance_tamper_blocks_and_ordinary_repair_recovers(self):
        f = self.fixture()
        f.flow.repair("Pointer correction", records_only=True)
        state = f.flow.load()
        prior = Path(state["record_correction"]["prior_review"]["report"])
        prior.write_text("Replaced prior report", encoding="utf-8")
        with self.assertRaises(EngineError):
            f.flow.require_checks(f.flow.load())
        f.repair("Provenance needs fresh full correction")
        self.assertNotIn("record_correction", f.flow.load())
        self.assertIsNone(f.flow.load()["checks"])
        self.assertIsNone(f.flow.load()["manual"])
        self.assertTrue(prior.exists())

    def test_pending_operation_reason_and_unsealed_contract_reject_without_mutation(self):
        f = self.fixture()
        for flag, value in (("pending_operation", "independent-review"), ("contract_sealed", False)):
            state = f.flow.load()
            changed = deepcopy(state)
            changed[flag] = value
            atomic_json(f.flow.directory / "state.json", changed)
            self.reject_unchanged(f)
            atomic_json(f.flow.directory / "state.json", state)
        before = f.flow.load()
        with self.assertRaises(EngineError):
            f.flow.repair(" ", records_only=True)
        self.assertEqual(f.flow.load(), before)
        f.flow.cancel("Fixture cancellation")
        self.reject_unchanged(f)

    def test_reviewed_amendment_clears_reuse_and_requires_new_full_cycle(self):
        f = self.fixture()
        f.flow.repair("Mapping correction", records_only=True)
        profile = deepcopy(f.profile)
        profile["reuse_record_evidence"] = False
        f.flow.amend(f.task, profile, f.review_double(f.task, profile), "Disable reuse after changed contract")
        state = f.flow.load()
        self.assertEqual(state["phase"], "build")
        self.assertNotIn("record_correction", state)
        self.assertIsNone(state["checks"])
        self.assertIsNone(state["manual"])

    def test_legacy_optional_review_fields_parse_but_do_not_enable_reuse(self):
        f = self.fixture()
        state = f.flow.load()
        state.pop("worth")  # Model a saved v2 run created before worth scoring.
        atomic_json(f.flow.directory / "state.json", state)
        old = self.report()
        for field in ("layer", "evidence_status", "evidence", "action"):
            old["findings"][0].pop(field)
        f.flow.validate_review(old, f.flow.load())
        self.install_review(f, old)
        self.reject_unchanged(f)
        for field, value in (("layer", "other"), ("evidence_status", "unproven"),
                             ("evidence", 42), ("action", "")):
            report = self.report()
            report["findings"][0][field] = value
            with self.subTest(field=field), self.assertRaises(EngineError):
                f.flow.validate_review(report, f.flow.load())
        deferred = self.report()
        finding = deferred["findings"][0]
        finding["disposition"] = "accepted-deferral"
        finding["exception"] = {k: DOUBLE for k in ("owner", "reason", "scope", "revisit", "authority")}
        f.flow.validate_review(deferred, f.flow.load())
        finding["exception"]["destination"] = ""
        with self.assertRaises(EngineError):
            f.flow.validate_review(deferred, f.flow.load())
        finding["exception"]["destination"] = "synthetic:followup"
        f.flow.validate_review(deferred, f.flow.load())

    def test_actual_cli_dispatch_preserves_commands_and_reports_bad_context(self):
        f = self.fixture()
        argv = [sys.executable, "-m", "safe_engine", "--project", str(f.root),
                "repair", "--records-only", "--reason", "Private mapping correction"]
        result = subprocess.run(argv, cwd=BUNDLE, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["phase"], "review")
        self.assertEqual((f.root / ".factory/check-count").read_text(), "1")
        again = subprocess.run(argv, cwd=BUNDLE, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("intact review", again.stderr)

    def test_ticket_freshness_proof_invalidation_and_changed_scope(self):
        f = tickets.TicketTests(methodName="runTest")
        f.setUp()
        self.addCleanup(f.doCleanups)
        f.profile["reuse_record_evidence"] = True
        evidence = f.verified()
        f.record_proof(f.proof(evidence))
        self.assertEqual(f.local_review()["phase"], "ready")
        self.reject_unchanged(f)  # No actual fresh capture after this review boundary.
        f.refresh()
        before = f.flow.load()
        f.flow.repair("Private ticket mapping correction", records_only=True)
        after = f.flow.load()
        self.assertNotIn("ticket-proof", after["artifacts"])
        self.assertEqual(before["checks"], after["checks"])
        self.assertEqual(before["manual"], after["manual"])
        self.assertEqual((f.flow.directory / "synthetic-check-count").read_text(), "1")
        with self.assertRaises(EngineError):
            f.flow.require_ticket_proof(after)
        f.record_proof(f.proof(evidence))
        f.local_review()
        changed = f.make_contract(revision=2)
        changed["scope"]["acceptance"][0]["text"] = "New owner outcome"
        f.confirm(changed)
        f.refresh(changed)
        self.reject_unchanged(f)


if __name__ == "__main__":
    unittest.main()
