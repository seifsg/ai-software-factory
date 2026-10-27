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
from suite_fixture import isolate_suite_queue


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        isolate_suite_queue(self)
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
        self.doCleanups()
        self.temp.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def start(self, historical_limit=None):
        self.flow.initialize(self.task, self.profile, historical_limit)
        state = self.flow.load()
        state.pop('suite_policy')  # This fixture exercises runs saved before suite reuse existed.
        atomic_json(self.flow.directory / 'state.json', state)

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
        self.git("-c", "user.name=Safe Engine Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "Configure initially failing check")
        self.start(historical_limit=1)
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

    def test_legacy_zero_limit_recovers_only_through_supported_repair(self):
        (self.root / "acceptance.py").write_text(
            "from pathlib import Path\n"
            "raise SystemExit(1 if Path('.factory/fail-check').exists() else 0)\n",
            encoding="utf-8")
        self.git("add", "acceptance.py")
        self.git("-c", "user.name=Safe Engine Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "Configure runtime failure scenario")
        self.start(historical_limit=0)
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
        self.assertEqual(resumed.load(), failed_state)
        result = resumed.repair("Runtime dependency recovered; fresh acceptance required")
        self.assertEqual(result["repairs_used"], 1)
        self.assertEqual(result["historical_max_repairs"], 0)
        self.assertIsNone(result["max_repairs"])
        self.assertIsNone(resumed.load()["checks"])
        self.assertIsNone(resumed.load()["review"])
        self.assertEqual(resumed.load()["task"], failed_state["task"])
        self.assertEqual(resumed.load()["profile"], failed_state["profile"])
        self.assertEqual(resumed.load()["history"][:-1], failed_state["history"])
        self.artifact("batch")
        self.assertTrue(resumed.check()["checks_passed"])

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
        self.assertNotIn("MODE=one", (self.root / ".factory/state.json").read_text(encoding="utf-8"))

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

    def test_continuous_repairs_preserve_cancellation(self):
        self.start(historical_limit=0)
        for kind in ("analysis", "plan", "batch"):
            self.artifact(kind)
        self.flow.repair("Actual supported correction")
        self.flow.cancel("User stopped the run")
        with self.assertRaises(EngineError):
            self.flow.check()
        with self.assertRaises(EngineError):
            self.flow.repair("Cannot revive a cancelled run")

    def test_continuous_changed_batches_continue_past_former_maximum(self):
        self.built()
        for correction in (0, *range(97, 105)):  # one real repair, then real ones across the former cap of 100
            if correction == 97:
                state = self.flow.load()
                state["repairs_used"] = correction
                atomic_json(self.flow.directory / "state.json", state)
            result = self.flow.repair(f"Correct documented fixture case {correction}")
            (self.root / "app.py").write_text(f"value = 1\n# corrected case {correction}\n")
            self.artifact("batch")
            self.assertEqual(result["repairs_used"], correction + 1)
            self.assertEqual(result["repair_policy"], "continuous")
            self.assertIsNone(result["max_repairs"])
        self.assertTrue(self.flow.check()["checks_passed"])
        self.assertEqual(Workflow(self.root).status()["repairs_used"], 105)

    def test_cli_prints_non_ascii_results_to_any_pipe(self):
        root = self.root / "caf\u00e9 \u2705"  # the status result prints this path
        subprocess.run(["git", "clone", "-q", str(self.root), str(root)], check=True, capture_output=True)
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
        env["PYTHONIOENCODING"] = "cp1252"  # what a Windows pipe gives by default
        (root / ".factory").mkdir()
        for filename, value in (("task.json", self.task), ("profile.json", self.profile)):
            (root / ".factory" / filename).write_text(json.dumps(value), encoding="utf-8")
        result = subprocess.run([sys.executable, "-m", "safe_engine", "--project", str(root), "init",
                                 "--task", str(root / ".factory/task.json"),
                                 "--profile", str(root / ".factory/profile.json")],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))  # no encoding crash
        self.assertIn("\u2705", json.loads(result.stdout.decode("utf-8"))["project"])

    def cli_init(self, *extra):
        for filename, value in (("task.json", self.task), ("profile.json", self.profile)):
            (self.root / ".factory").mkdir(exist_ok=True)
            (self.root / ".factory" / filename).write_text(json.dumps(value))
        result = subprocess.run([sys.executable, "-m", "safe_engine", "--project", str(self.root),
                                 "init", "--task", str(self.root / ".factory/task.json"),
                                 "--profile", str(self.root / ".factory/profile.json"), *extra],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        status = json.loads(result.stdout)
        self.assertEqual(status["repair_policy"], "continuous")
        self.assertIsNone(status["max_repairs"])
        return status

    def test_cli_initializes_without_an_allowance(self):
        self.cli_init()
        self.assertIsNone(self.flow.load()["max_repairs"])

    def test_cli_legacy_flag_is_historical_and_never_blocks_repair(self):
        status = self.cli_init("--max-repairs", "0")
        self.assertEqual(status["historical_max_repairs"], 0)
        for kind in ("analysis", "plan", "batch"):
            self.artifact(kind)
        self.assertEqual(self.flow.repair("Diagnosed correction")["repairs_used"], 1)

    def test_legacy_metadata_does_not_restore_the_former_one_hundred_ceiling(self):
        self.start(historical_limit=101)
        self.assertEqual(self.flow.status()["historical_max_repairs"], 101)
        self.assertIsNone(self.flow.status()["max_repairs"])

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

    def test_product_profiles_require_matching_behavior_evidence(self):
        for interface in ("desktop", "mobile", "game", "service"):
            with self.subTest(interface=interface):
                profile = json.loads(json.dumps(self.profile))
                profile["interface"] = interface
                with self.assertRaises(EngineError):
                    validate_profile(profile)
                profile["checks"][0]["kind"] = "api" if interface == "service" else "interaction"
                validate_profile(profile)
                profile["checks"][0]["kind"] = "performance"
                with self.assertRaises(EngineError):
                    validate_profile(profile)

    def test_game_profile_runs_configured_interaction_and_resource_checks(self):
        # Synthetic check transport only; this does not demonstrate a real game.
        self.profile["interface"] = "game"
        self.profile["checks"][0]["kind"] = "interaction"
        self.profile["checks"].append({"id": "resources", "kind": "performance",
                                        "argv": ["{python}", "acceptance.py"], "timeout_seconds": 10})
        self.task["acceptance"][0]["checks"].append("resources")
        self.built()
        self.assertEqual(self.flow.check()["phase"], "improve")
        (self.root / "app.py").write_text("value = 2\n")
        with self.assertRaises(EngineError):
            self.flow.require_checks(self.flow.load())

    def test_review_and_handoff_use_fresh_process_result(self):
        self.reviewed_input()
        report = {"verdict": "PASS", "summary": "Test double; not a real review", "method_followed": True,
                  "criteria": [{"id": "A1", "status": "PASS", "evidence": "acceptance.py fixture"}], "findings": []}
        def review_double(argv, cwd, timeout, log, stdin):
            self.assertIn("read-only", argv)
            self.assertIn("--ephemeral", argv)
            skills = Path(__file__).resolve().parents[1] / ".agents/skills"
            for relative in ("analyze-start/SKILL.md", "get-ready-to-code/SKILL.md", "ticketing/SKILL.md",
                             "deep-review/references/security.md",
                             "deep-review/references/performance.md",
                             "deep-review/references/journey.md",
                             "deep-review/references/change-guard.md",
                             "deep-review/references/compliance.md",
                             "safe-engine/references/product-bar.md",
                             "safe-engine/references/controller.md",
                             "database-schema/SKILL.md",
                             "ux-quality/SKILL.md",
                             "ux-quality/references/assets.md",
                             "research-market/SKILL.md"):
                required = skills / relative
                self.assertTrue(required.is_file(), relative)
                self.assertIn(str(required), stdin)
            self.assertIn(str(skills.parents[1] / "AGENTS.md"), stdin)
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
