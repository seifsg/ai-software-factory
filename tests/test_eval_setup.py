"""Real exported selection and conservative reporting of gate activation."""
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
        self.temp = tempfile.TemporaryDirectory(prefix="eval-selection-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "work"
        self.work.mkdir()
        self.home = self.root / "home"
        self.selected = {"bundle_root": str(self.root / "factory"), "revision": "a" * 40}

    def state(self, **changes):
        return {"version": 1, "project": str(self.work.resolve()),
                "bundle": {"root": self.selected["bundle_root"], "revision": self.selected["revision"]},
                "check_selection": True, "show_first": False, "suite_policy": True, "closed": False, **changes}

    def write(self, name, value):
        path = self.home / "runs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def observe(self):
        return isolation.observed_run(self.home, self.work, self.selected)

    def test_factory_snapshot_has_actual_git_identity_and_canonical_receipt(self):
        bundle = isolation.read_bundle()
        factory = isolation.export_factory(bundle, self.root / "factory")
        runner.git_init(factory, origin=distribution.REPOSITORY)
        selected = distribution.select_for_project(self.work, factory, None, self.root / "cache", "safe-engine")
        actual = distribution.git("rev-parse", "HEAD", cwd=factory)
        self.assertEqual(selected["revision"], actual)
        pin = json.loads((self.work / ".factory/entry-bundle.json").read_text())
        self.assertEqual(pin["revision"], actual)
        self.assertEqual(pin["policy"], "explicit")
        self.assertEqual(set(distribution.git("ls-tree", "-r", "--name-only", "HEAD", cwd=factory).splitlines()), set(bundle))
        self.assertEqual(subprocess.check_output(['git', 'show', 'HEAD:AGENTS.md'], cwd=factory), bundle['AGENTS.md'])
        self.assertEqual(isolation.observed_run(self.home, self.work, selected), {"status": "not_observed"})
        bytecode = factory / 'safe_engine/__pycache__'
        bytecode.mkdir()
        (bytecode / 'generated.pyc').write_bytes(b'cache')
        self.assertFalse(distribution.git('status', '--porcelain', cwd=factory))
        (factory / 'AGENTS.md').write_bytes(b'changed source')
        self.assertTrue(distribution.git('status', '--porcelain', cwd=factory))

    def test_project_mirror_or_receipt_is_not_gate_activation(self):
        mirror = self.work / ".factory/fast/run.json"
        mirror.parent.mkdir(parents=True)
        mirror.write_text(json.dumps(self.state()), encoding="utf-8")
        self.assertEqual(self.observe(), {"status": "not_observed"})

    def test_state_must_match_project_revision_and_boolean_policies(self):
        for state in ([], self.state(version=True), self.state(project="foreign"), self.state(bundle={}),
                      self.state(suite_policy="true"), self.state(closed=1)):
            with self.subTest(state=state):
                self.write("state.json", state)
                self.assertEqual(self.observe(), {"status": "not_observed"})
        self.write("state.json", self.state(check_selection=False))
        self.assertFalse(self.observe()["policies"]["check_selection"])

    def test_stale_closed_state_cannot_hide_an_unknown_active_state(self):
        self.write("closed/state.json", self.state(closed=True))
        self.assertTrue(self.observe()["closed"])
        self.write("state.json", self.state(bundle={}))
        self.assertEqual(self.observe(), {"status": "not_observed"})

    def test_oversized_state_is_not_observed(self):
        self.write("state.json", self.state(extra="x" * 1_048_576))
        self.assertEqual(self.observe(), {"status": "not_observed"})

    def test_snapshot_git_failure_is_fatal_instead_of_an_unresolved_export(self):
        with patch.object(runner.subprocess, "run", side_effect=FileNotFoundError("git missing")):
            with self.assertRaisesRegex(RuntimeError, "factory snapshot"):
                runner.git_init(self.root, origin=distribution.REPOSITORY)
