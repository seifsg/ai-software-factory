"""Owner-authorized temp cleanup: real CLI effects and refusal boundaries."""
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from test_fast_gate import GateHarness, link, module


class CleanupTests(GateHarness, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.temp = self.root / "temp"
        self.temp.mkdir()
        self.env.update({name: str(self.temp) for name in ("TEMP", "TMP", "TMPDIR")})
        self.start("--no-ui", "--no-data", kind="change")
        self.target = self.temp / "obsolete QA ü"
        self.target.mkdir()
        (self.target / "report.txt").write_text("PASS", encoding="utf-8")

    def cleanup(self, *extra, target=None, ok=True):
        """Exercise the same CLI an agent uses, including private receipts."""
        return self.gate("cleanup-temp", "--path", str(target or self.target),
                         "--reason", "Owner explicitly requested these obsolete QA folders", *extra, ok=ok)

    def test_preview_then_remove_records_without_mutating_run(self):
        state = (self.project / ".factory/fast/run.json").read_bytes()
        before = json.loads(self.cleanup())
        self.assertTrue(self.target.is_dir())
        self.assertEqual(before["folders"][0]["entries"], 2)
        after = json.loads(self.cleanup("--expect", before["sha256"]))
        self.assertEqual(after["status"], "removed")
        self.assertFalse(self.target.exists())
        self.assertEqual(json.loads(Path(after["receipt"]).read_text())["status"], "removed")
        self.assertEqual(state, (self.project / ".factory/fast/run.json").read_bytes())

    def test_changed_inventory_and_wrong_digest_leave_everything(self):
        before = json.loads(self.cleanup())
        (self.target / "new.txt").write_text("new")
        self.assertIn("Inventory changed", self.cleanup("--expect", before["sha256"], ok=False))
        self.assertTrue((self.target / "report.txt").is_file())
        self.assertIn("Inventory changed", self.cleanup("--expect", "wrong", ok=False))

    def test_link_roots_children_and_ancestors_are_refused(self):
        sentinel = self.root / "sentinel"
        sentinel.mkdir()
        (sentinel / "keep.txt").write_text("keep")
        linked = self.temp / "linked"
        link(linked, sentinel)
        self.assertIn("Link or special", self.cleanup(target=linked, ok=False))
        link(self.target / "junction", sentinel)
        self.assertIn("Link or special", self.cleanup(ok=False))
        alias = self.root / "alias"
        link(alias, self.temp)
        with self.assertRaisesRegex(ValueError, "Link or special"):
            module("fast_cleanup").inventory([alias / self.target.name], alias, [])
        self.assertEqual((sentinel / "keep.txt").read_text(), "keep")

    def test_invalid_scope_and_duplicate_targets(self):
        for target in (self.temp, self.root, self.target / ".." / self.target.name, Path("relative")):
            with self.subTest(target=target):
                self.cleanup(target=target, ok=False)
        self.cleanup("--path", str(self.target), ok=False)
        self.assertTrue(self.target.is_dir())

    def test_protected_home_and_registered_project_overlap(self):
        cleanup = module("fast_cleanup")
        for protected in (self.target, self.target / "nested-project", self.temp):
            with self.subTest(protected=protected), self.assertRaisesRegex(ValueError, "Protected"):
                cleanup.inventory([self.target], self.temp, [protected])
        app = self.target / "active-app"
        app.mkdir()
        self.gate("start", "--key", "other", "--kind", "change", "--request", "Other app", project=app)
        self.assertIn("Protected", self.cleanup(ok=False))

    def test_inventory_is_bounded(self):
        cleanup = module("fast_cleanup")
        with patch.object(cleanup, "LIMIT", 1), self.assertRaisesRegex(ValueError, "exceeds"):
            cleanup.inventory([self.target], self.temp, [])

    @unittest.skipUnless(os.name == "nt", "Windows path aliases")
    def test_windows_trailing_dot_alias_is_not_an_exact_root(self):
        self.assertIn("canonical", self.cleanup(target=Path(str(self.target) + "."), ok=False))
        self.assertTrue(self.target.exists())

    def test_audit_failure_prevents_delete_and_partial_failure_is_reported(self):
        from types import SimpleNamespace
        cleanup = module("fast_cleanup")
        with patch.dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "test-home")):
            gate = module("fast_gate")
        args = SimpleNamespace(project=str(self.project), path=[str(self.target)], reason="Owner request", expect=None)
        with patch.object(gate, "open_run", return_value=(self.project, {"key": "test"})), \
                patch.object(gate, "active_runs", return_value=[]), \
                patch.object(cleanup.tempfile, "gettempdir", return_value=str(self.temp)):
            args.expect = cleanup.inventory(args.path, self.temp, [gate.HOME, self.project])["sha256"]
            with patch.object(gate, "save", side_effect=OSError("locked")), self.assertRaises(SystemExit):
                cleanup.run(args, gate)
            self.assertTrue(self.target.exists())
            setup = gate.sibling("fast_setup")
            with patch.object(setup, "remove", side_effect=lambda path, left: left.append("locked")), \
                    self.assertRaises(SystemExit):
                cleanup.run(args, gate)
            receipt = next((gate.HOME / "cleanup").glob("*.json"))
            self.assertEqual(json.loads(receipt.read_text())["status"], "partial")


if __name__ == "__main__":
    unittest.main()
