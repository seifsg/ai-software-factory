"""Browser setup failures must never reuse a successful calibration report."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "optional browser calibration needs Node")
class VisualCalibrationTests(unittest.TestCase):
    def run_failure(self, arguments):
        """Run the public command over an old pass without requiring a browser."""
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "out"
            out.mkdir()
            report = out / "report.json"
            report.write_text('{"passed": true}', encoding="utf-8")
            env = {key: value for key, value in os.environ.items() if key != "NODE_PATH"}
            result = subprocess.run([NODE, str(ROOT / "evals/visual/run.cjs"), "--out", str(out),
                                     *arguments], capture_output=True, text=True, timeout=30, env=env)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            observed = json.loads(report.read_text(encoding="utf-8"))
            self.assertIs(observed["passed"], False)
            self.assertTrue(observed["error"])
            return observed

    def test_missing_labels_replace_a_stale_pass(self):
        self.assertIn("ENOENT", self.run_failure(["--expected", "missing-labels.json"])["error"])

    def test_incomplete_labels_fail_before_browser_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            labels = Path(folder) / "labels.json"
            labels.write_text('{}', encoding="utf-8")
            self.assertIn("Invalid expected labels", self.run_failure(["--expected", str(labels)])["error"])

    def test_unavailable_browser_cannot_preserve_a_pass(self):
        self.run_failure(["--browser", "missing-browser-executable"])
