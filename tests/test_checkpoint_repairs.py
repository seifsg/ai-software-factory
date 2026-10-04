"""Regressions added after manual checkpoint QA; disposable processes and paths."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from safe_engine import distribution
from safe_engine.project import EngineError, validate_profile
from safe_engine.runner import LOG_LIMIT, run_command
from safe_engine.storage import locked
from safe_engine.workflow import Workflow


class CheckpointRepairs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="factory checkpoint ")
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def command(self, code, timeout=10, stdin=None):
        return run_command([sys.executable, "-c", code], self.root, timeout,
                           self.root / "command.log", stdin=stdin)

    def test_unread_large_input_cannot_delay_timeout_until_natural_exit(self):
        result = self.command("import time; time.sleep(8)", timeout=1, stdin="x" * 65536)
        self.assertTrue(result["timed_out"])
        self.assertFalse(result["passed"])
        self.assertLess(result["duration_seconds"], 6)

    def test_output_capture_retains_bounded_tail(self):
        result = self.command("import sys; sys.stdout.buffer.write(b'x' * 16_777_216 + b'TAIL-END')")
        output = Path(result["log"]).read_bytes()
        self.assertTrue(result["passed"])
        self.assertTrue(result["log_truncated"])
        self.assertEqual(len(output), LOG_LIMIT)
        self.assertTrue(output.endswith(b"TAIL-END"))

    def test_large_utf8_input_stderr_and_failure_status_survive(self):
        text = "caf\u00e9" * 20000
        result = self.command("import sys; data=sys.stdin.buffer.read(); "
                              "print(len(data)); print('failure-detail', file=sys.stderr); sys.exit(7)",
                              stdin=text)
        output = Path(result["log"]).read_text()
        self.assertIn(str(len(text.encode("utf-8"))), output)
        self.assertIn("failure-detail", output)
        self.assertEqual(result["exit_code"], 7)
        self.assertFalse(result["passed"])
        self.assertFalse(result["log_truncated"])

    def test_inherited_stdout_does_not_wait_for_child_eof(self):
        result = self.command("import subprocess,sys; subprocess.Popen([sys.executable, '-c', "
                              "'import time; time.sleep(3)'], cwd=sys.prefix); print('parent-done')")
        self.assertTrue(result["passed"])
        self.assertLess(result["duration_seconds"], 2)
        self.assertIn("parent-done", Path(result["log"]).read_text())

    def test_check_ids_cannot_collide_on_case_insensitive_storage(self):
        check = {"id": "unit", "kind": "unit", "argv": ["python", "acceptance.py"], "timeout_seconds": 10}
        profile = {"version": 1, "interface": "library", "checks": [check, {**check, "id": "UNIT"}],
                   "protected_paths": ["acceptance.py"], "environment_inputs": [], "input_files": []}
        with self.assertRaisesRegex(EngineError, "case-insensitive"):
            validate_profile(profile)
        profile["checks"][1]["id"] = "integration"
        validate_profile(profile)

    def junction(self, link, target):
        link.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       check=True, capture_output=True)
        # Remove only the link before TemporaryDirectory removes its fixture tree.
        self.addCleanup(lambda: os.rmdir(link) if link.exists() else None)

    @unittest.skipUnless(os.name == "nt", "Real NTFS junction regression")
    def test_run_and_launcher_reject_junction_without_external_write(self):
        app, outside = self.root / "app", self.root / "outside"
        app.mkdir()
        outside.mkdir()
        link = app / ".factory"
        self.junction(link, outside)
        try:
            with self.assertRaisesRegex(EngineError, "reparse"):
                with locked(link):
                    self.fail("Aliased run lock acquired")
            with self.assertRaisesRegex(RuntimeError, "reparse"):
                distribution.select_for_project(app, None, None, self.root / "cache", "safe-engine")
            self.assertEqual(list(outside.iterdir()), [])
        finally:
            os.rmdir(link)

    @unittest.skipUnless(os.name == "nt", "Real NTFS junction regression")
    def test_output_junctions_cannot_delete_source_or_launch_check(self):
        source = self.root / "source"
        source.mkdir()
        proof = source / "proof.txt"
        proof.write_text("keep source")
        for relative in (".factory/outputs", ".factory/outputs/nested"):
            with self.subTest(path=relative):
                link = self.root / relative
                self.junction(link, source)
                check = {"id": "unit", "kind": "unit", "argv": [sys.executable, "-c", "print('bad')"],
                         "timeout_seconds": 5, "artifacts": [relative + "/proof.txt"]}
                try:
                    with patch("safe_engine.workflow.run_command") as command:
                        with self.assertRaisesRegex(EngineError, "reparse"):
                            Workflow(self.root).execute_checks({"sequence": 1}, [check])
                        command.assert_not_called()
                    self.assertEqual(proof.read_text(), "keep source")
                finally:
                    os.rmdir(link)

    def test_actual_legacy_pilot_resumes_without_migration(self):
        repo = Path(__file__).resolve().parents[1]
        available = subprocess.run(["git", "cat-file", "-e", distribution.LEGACY_PILOT + "^{commit}"],
                                   cwd=repo, capture_output=True)
        if available.returncode:
            self.skipTest("Historical pilot object absent in this shallow checkout")
        bundle = self.root / "legacy"
        subprocess.run(["git", "clone", "--shared", "--no-checkout", str(repo), str(bundle)],
                       check=True, capture_output=True)
        subprocess.run(["git", "checkout", "--detach", distribution.LEGACY_PILOT],
                       cwd=bundle, check=True, capture_output=True)
        subprocess.run(["git", "remote", "set-url", "origin", distribution.REPOSITORY],
                       cwd=bundle, check=True, capture_output=True)
        app = self.root / "app"
        (app / ".factory").mkdir(parents=True)
        state = app / ".factory/state.json"
        state.write_bytes(b'{"progress":"in-flight"}')
        first = distribution.select_for_project(app, bundle, None, self.root / "cache", "safe-engine")
        receipt = Path(first["selection_record"]).read_bytes()
        with patch.object(distribution, "resolve_bundle", side_effect=AssertionError("No upgrade")):
            resumed = distribution.select_for_project(app, None, None, self.root / "cache", "safe-engine")
        self.assertEqual(first, resumed)
        self.assertEqual(Path(first["selection_record"]).read_bytes(), receipt)
        self.assertEqual(state.read_bytes(), b'{"progress":"in-flight"}')
        with self.assertRaisesRegex(RuntimeError, "cannot be upgraded"):
            distribution.select_for_project(app, None, "main", self.root / "cache", "safe-engine")
        with self.assertRaisesRegex(RuntimeError, "Incomplete"):
            distribution.inspect_bundle(bundle, entrypoint="improve-factory")
        (bundle / "safe_engine/runner.py").unlink()
        with self.assertRaisesRegex(RuntimeError, "Incomplete.*runner.py"):
            distribution.inspect_bundle(bundle, entrypoint="safe-engine")


if __name__ == "__main__":
    unittest.main()
