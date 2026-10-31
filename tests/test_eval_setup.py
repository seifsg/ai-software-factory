"""The factory arm's export is a real local snapshot, pinned before the agent starts."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from evals import isolation, runner
from safe_engine import distribution


class EvalSetupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="eval-selection-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_snapshot_keeps_exported_bytes_and_is_pinned_explicitly(self):
        bundle = isolation.read_bundle()
        factory = isolation.export_factory(bundle, self.root / "factory")
        runner.git_init(factory, origin=distribution.REPOSITORY)
        work = self.root / "work"
        work.mkdir()
        selected = distribution.select_for_project(work, factory, None, self.root / "cache", "safe-engine")
        pin = json.loads((work / ".factory/entry-bundle.json").read_text(encoding="utf-8"))
        self.assertEqual((pin["revision"], pin["policy"]), (selected["revision"], "explicit"))
        self.assertEqual(subprocess.check_output(["git", "show", "HEAD:AGENTS.md"], cwd=factory), bundle["AGENTS.md"])

    def test_snapshot_git_failure_stops_the_trial(self):
        with patch.object(runner.subprocess, "run", side_effect=FileNotFoundError("git missing")):
            with self.assertRaisesRegex(RuntimeError, "factory snapshot"):
                runner.git_init(self.root, origin=distribution.REPOSITORY)
