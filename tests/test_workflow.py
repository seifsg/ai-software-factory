"""Controller fault scenarios. Review responses here are explicit test doubles."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from safe_engine.project import EngineError, fingerprint, validate_profile, validate_task
from safe_engine.runner import run_command
from safe_engine.storage import atomic_json, locked, read_json
from safe_engine.workflow import Workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.git("init", "-q")
        (self.root / ".gitignore").write_text(".factory/\n.env\n__pycache__/\n", encoding="utf-8")
        (self.root / "app.py").write_text("value = 1\n", encoding="utf-8")
        (self.root / "acceptance.py").write_text("from app import value\nassert value == 1\n", encoding="utf-8")
        self.git("add", ".")
        self.git("-c", "user.name=Safe Engine Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "baseline")
        self.profile = {"version": 1, "interface": "library", "checks": [
            {"id": "unit", "kind": "unit", "argv": ["{python}", "acceptance.py"], "timeout_seconds": 10}],
            "protected_paths": ["acceptance.py"], "environment_inputs": [], "input_files": []}
        self.task = {"request": "Preserve the fixture behavior", "acceptance": [{"id": "A1", "text": "Value remains one", "checks": ["unit"]}]}
        self.flow = Workflow(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def start(self, budget=2):
        self.flow.initialize(self.task, self.profile, budget)

    def artifact(self, kind):
        path = self.root / ".factory" / f"draft-{kind}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"# {kind}\nTest fixture artifact. Real skill behavior is assessed in the independent pilot review.\n", encoding="utf-8")
        return self.flow.record(kind, path)

    def built(self):
        self.start()
        for kind in ("analysis", "plan", "batch"):
            self.artifact(kind)

    def reviewed_input(self):
        self.built()
        self.flow.check()
        self.artifact("improvement")
        self.flow.check()

    def test_real_commands_and_saved_resume(self):
        self.built()
        result = self.flow.check()
        self.assertTrue(result["checks_passed"])
        self.assertEqual(Workflow(self.root).status()["phase"], "improve")
        self.assertEqual(result["results"][0]["exit_code"], 0)

    def test_phase_skip_and_code_during_analysis_are_rejected(self):
        self.start()
        with self.assertRaises(EngineError):
            self.artifact("plan")
        (self.root / "app.py").write_text("value = 2\n")
        with self.assertRaisesRegex(EngineError, "analysis/planning"):
            self.artifact("analysis")

    def test_failed_batch_cannot_advance(self):
        self.built()
        self.flow.repair("Create failure scenario")
        (self.root / "app.py").write_text("value = 2\n")
        self.artifact("batch")
        self.assertFalse(self.flow.check()["checks_passed"])
        with self.assertRaises(EngineError):
            self.artifact("improvement")

    def test_completed_failed_check_requires_repair_after_resume(self):
        (self.root / "acceptance.py").write_text(
            "from pathlib import Path\n"
            "marker = Path('.factory/first-attempt')\n"
            "if not marker.exists():\n"
            "    marker.write_text('failed')\n"
            "    raise SystemExit(1)\n", encoding="utf-8")
        self.git("add", "acceptance.py")
        self.git("commit", "-qm", "Configure initially failing check")
        self.start(budget=1)
        for kind in ("analysis", "plan", "batch"):
            self.artifact(kind)
        self.assertFalse(self.flow.check()["checks_passed"])
        failed_state = self.flow.load()
        resumed = Workflow(self.root)
        with self.assertRaisesRegex(EngineError, "repair"):
            resumed.check()
        self.assertEqual(resumed.load(), failed_state)
        resumed.repair("Investigated and corrected the transient check failure")
        self.artifact("batch")
        result = resumed.check()
        self.assertTrue(result["checks_passed"])
        self.assertEqual(result["repairs_used"], 1)

    def test_failed_final_check_cannot_reroll_with_zero_budget(self):
        (self.root / "acceptance.py").write_text(
            "from pathlib import Path\n"
            "raise SystemExit(1 if Path('.factory/fail-check').exists() else 0)\n",
            encoding="utf-8")
        self.git("add", "acceptance.py")
        self.git("commit", "-qm", "Configure runtime failure scenario")
        self.start(budget=0)
        for kind in ("analysis", "plan", "batch"):
            self.artifact(kind)
        self.assertTrue(self.flow.check()["checks_passed"])
        self.artifact("improvement")
        failure = self.root / ".factory/fail-check"
        failure.write_text("unavailable", encoding="utf-8")
        self.assertFalse(self.flow.check()["checks_passed"])
        failure.unlink()
        failed_state = self.flow.load()
        resumed = Workflow(self.root)
        with self.assertRaisesRegex(EngineError, "repair"):
            resumed.check()
        with self.assertRaisesRegex(EngineError, "budget exhausted"):
            resumed.repair("Runtime dependency recovered")
        self.assertEqual(resumed.load(), failed_state)

    def test_stale_code_and_declared_environment_rejected(self):
        self.profile["environment_inputs"] = ["SAFE_ENGINE_TEST_INPUT"]
        with patch.dict(os.environ, {"SAFE_ENGINE_TEST_INPUT": "before"}):
            self.reviewed_input()
            state = self.flow.load()
            with patch.dict(os.environ, {"SAFE_ENGINE_TEST_INPUT": "after"}):
                with self.assertRaisesRegex(EngineError, "stale"):
                    self.flow.require_checks(state)
            (self.root / "app.py").write_text("value = 1\n# Changed candidate\n")
            with self.assertRaisesRegex(EngineError, "stale"):
                self.flow.require_checks(state)

    def test_ignored_declared_file_is_bound(self):
        secret = self.root / ".env"
        secret.write_text("MODE=one\n")
        self.profile["input_files"] = [".env"]
        self.start()
        before = self.flow.current(self.flow.load())
        secret.write_text("MODE=two\n")
        self.assertNotEqual(before, self.flow.current(self.flow.load()))
        self.assertNotIn("MODE=one", (self.root / ".factory/state.json").read_text())

    def test_protected_check_changes_are_rejected(self):
        self.built()
        (self.root / "acceptance.py").write_text("print('fake pass')\n")
        with self.assertRaisesRegex(EngineError, "Protected acceptance"):
            self.flow.check()

    def test_missing_review_and_modified_logs_cannot_pass(self):
        self.reviewed_input()
        with self.assertRaises(EngineError):
            self.flow.handoff()
        state = self.flow.load()
        Path(state["checks"]["results"][0]["log"]).write_text("changed output")
        with self.assertRaisesRegex(EngineError, "evidence"):
            self.flow.require_checks(state)

    def test_repair_budget_is_shared_and_cancel_stops_progress(self):
        self.start(budget=0)
        for kind in ("analysis", "plan", "batch"):
            self.artifact(kind)
        with self.assertRaisesRegex(EngineError, "budget exhausted"):
            self.flow.repair("Any correction")
        self.flow.cancel("User stopped the run")
        with self.assertRaises(EngineError):
            self.flow.check()

    def test_contract_change_rejected_and_history_saved(self):
        self.start()
        state = self.flow.load()
        state["task"]["request"] = "Weakened request"
        atomic_json(self.root / ".factory/state.json", state)
        with self.assertRaisesRegex(EngineError, "Task or profile changed"):
            self.flow.load()
        self.assertTrue((self.root / ".factory/history/0001.json").is_file())

    def test_schema_requires_browser_and_real_criteria(self):
        self.profile["interface"] = "web"
        with self.assertRaisesRegex(EngineError, "browser"):
            validate_profile(self.profile)
        with self.assertRaises(EngineError):
            validate_task({"request": "Something", "acceptance": []}, self.profile)

    def test_duplicate_review_criteria_rejected(self):
        self.start()
        report = {"verdict": "PASS", "summary": "fixture", "method_followed": True,
                  "criteria": [{"id": "wrong", "status": "PASS", "evidence": "fixture"}], "findings": []}
        with self.assertRaisesRegex(EngineError, "IDs"):
            self.flow.validate_review(report, self.flow.load())

    def test_review_and_handoff_use_fresh_process_result(self):
        self.reviewed_input()
        report = {"verdict": "PASS", "summary": "Test double; not a real review", "method_followed": True,
                  "criteria": [{"id": "A1", "status": "PASS", "evidence": "acceptance.py fixture"}], "findings": []}
        def review_double(argv, cwd, timeout, log, stdin):
            self.assertIn("read-only", argv)
            self.assertIn("--ephemeral", argv)
            Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps(report))
            log.write_text("explicit test double")
            return {"passed": True, "exit_code": 0}
        with patch("safe_engine.workflow.shutil.which", return_value=sys.executable), patch("safe_engine.workflow.run_command", side_effect=review_double):
            self.assertEqual(self.flow.review(10)["phase"], "ready")
        self.assertTrue(Path(self.flow.handoff()["handoff"]).is_file())
        (self.root / "app.py").write_text("value = 2\n")
        with self.assertRaises(EngineError):
            self.flow.handoff()

    def test_concurrent_lock_refused_and_released(self):
        run = self.root / ".factory"
        with locked(run):
            with self.assertRaises(EngineError):
                with locked(run):
                    self.fail("Second writer acquired lock")
        with locked(run):
            pass

    def test_output_artifacts_must_be_fresh_and_remain_intact(self):
        output = self.root / ".factory/outputs/proof.txt"
        self.profile["checks"][0]["artifacts"] = [".factory/outputs/proof.txt"]
        script = self.root / "acceptance.py"
        script.write_text("from pathlib import Path\np = Path('.factory/outputs/proof.txt')\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text('current evidence')\n")
        self.git("add", "acceptance.py")
        self.git("-c", "user.name=Safe Engine Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Declare evidence")
        self.reviewed_input()
        state = self.flow.load()
        self.flow.require_checks(state)
        output.write_text("replaced evidence")
        with self.assertRaisesRegex(EngineError, "output evidence"):
            self.flow.require_checks(state)
        output.unlink()
        with self.assertRaisesRegex(EngineError, "not a file"):
            self.flow.require_checks(state)

    def test_old_artifact_cannot_replace_missing_fresh_output(self):
        self.profile["checks"][0]["artifacts"] = [".factory/outputs/proof.txt"]
        self.built()
        output = self.root / ".factory/outputs/proof.txt"
        output.parent.mkdir(parents=True)
        output.write_text("old evidence")
        result = self.flow.check()
        self.assertEqual(result["results"][0]["exit_code"], 0)
        self.assertFalse(result["checks_passed"])
        self.assertFalse(output.exists())

    def test_output_paths_cannot_target_state_or_escape(self):
        for value in (".factory/state.json", ".factory/outputs/../../app.py", ".factory/outputs/proof.txt:stream"):
            self.profile["checks"][0]["artifacts"] = [value]
            with self.assertRaisesRegex(EngineError, "Artifact paths"):
                validate_profile(self.profile)

    def test_completed_rejection_cannot_reroll_review_without_repair(self):
        self.reviewed_input()
        report = {"verdict": "FAIL", "summary": "Explicit rejection test double", "method_followed": True,
                  "criteria": [{"id": "A1", "status": "FAIL", "evidence": "Fixture rejection"}],
                  "findings": [{"severity": "HIGH", "location": "app.py", "description": "Fixture finding"}]}
        def review_double(argv, cwd, timeout, log, stdin):
            Path(argv[argv.index("--output-last-message") + 1]).write_text(json.dumps(report))
            log.write_text("explicit rejection test double")
            return {"passed": True, "exit_code": 0}
        with patch("safe_engine.workflow.shutil.which", return_value=sys.executable), patch("safe_engine.workflow.run_command", side_effect=review_double) as reviewer:
            self.assertEqual(self.flow.review(10)["phase"], "review")
            with self.assertRaisesRegex(EngineError, "use repair"):
                self.flow.review(10)
            self.assertEqual(reviewer.call_count, 1)
        self.flow.repair("Address the recorded finding")
        self.assertEqual(self.flow.status()["repairs_used"], 1)

    def test_command_timeout_is_a_failure(self):
        result = run_command([sys.executable, "-c", "import time; time.sleep(5)"], self.root, 1, self.root / "timeout.log")
        self.assertTrue(result["timed_out"])
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()
