"""Audited stale baseline recovery through real Git history and the gate CLI."""
import json
import subprocess
import unittest

from test_fast_gate import GateHarness, LIGHT, module


class BaselineTests(GateHarness, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.env.update(GIT_AUTHOR_DATE="2020-01-01T00:00:00Z", GIT_COMMITTER_DATE="2020-01-01T00:00:00Z")
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.old = self.commit("README.md", "old")
        self.base = self.commit("page.html", "upstream")
        self.git("update-ref", "refs/remotes/origin/main", self.base)
        self.git("checkout", "--detach", self.old)
        self.start("--no-ui", "--no-data", kind="change")
        self.git("checkout", "-b", "assets", self.base)
        self.commit("README.md", "assets")
        self.gate("pause", "--reason", "Owner requested audited baseline recovery")

    def git(self, *args):
        """Use actual Git ancestry, not mocked path lists."""
        return subprocess.check_output(["git", "-C", str(self.project), *args], env=self.env,
                                       text=True, encoding="utf-8", stderr=subprocess.DEVNULL).strip()

    def commit(self, name, contents):
        """Create a deterministic historical change before the fixture's run."""
        (self.project / name).write_text(contents, encoding="utf-8")
        self.git("add", name)
        self.git("commit", "-qm", contents)
        return self.git("rev-parse", "HEAD")

    def state(self):
        """Read the public mirror; never change gate-owned state."""
        return json.loads((self.project / ".factory/fast/run.json").read_text(encoding="utf-8"))

    def recover(self, *args, base=None, ok=True):
        """Run the supported preview/apply command."""
        return self.gate("recover-baseline", "--base", base or self.base,
                         "--upstream", "refs/remotes/origin/main", "--reason", "Owner requested repair", *args, ok=ok)

    def test_apply_preserves_state_and_real_ui_proof(self):
        before = self.state()
        record = module("fast_record")
        self.assertIn("page.html", record.ui_files(before, self.project))
        preview = json.loads(self.recover())
        self.assertEqual(self.state(), before)
        self.recover("--expect", preview["sha256"])
        after = self.state()
        receipt = after.pop("baseline_recovery")
        self.assertEqual(after, before)
        self.assertEqual(receipt["original_base"], self.old)
        self.assertEqual(record.ui_files(self.state(), self.project), [])
        (self.project / "page.html").write_text("owned")
        self.assertIn("page.html", record.ui_files(self.state(), self.project))
        (self.project / "page.html").unlink()
        self.assertIn("page.html", record.ui_files(self.state(), self.project))
        self.assertIn("no previous recovery", self.recover(ok=False))

    def test_preview_rejects_changed_inputs(self):
        for mutate in (lambda: (self.project / "README.md").write_text("dirty"),
                       lambda: (self.project / "new.tsx").write_text("owned"),
                       lambda: self.gate("pause", "--reason", "new reason"),
                       lambda: self.git("update-ref", "refs/remotes/origin/main", "HEAD")):
            preview = json.loads(self.recover())
            mutate()
            self.assertIn("Preview changed", self.recover("--expect", preview["sha256"], ok=False))
            self.assertNotIn("baseline_recovery", self.state())

    def test_invalid_and_foreign_baseline(self):
        for base in (self.old, "HEAD", "0" * 40):
            self.recover(base=base, ok=False)
        self.git("checkout", "--orphan", "foreign")
        foreign = self.commit("README.md", "foreign")
        self.git("checkout", "assets")
        self.assertIn("Cannot verify Git", self.recover(base=foreign, ok=False))

    def test_staged_only_change_invalidates_preview(self):
        preview = json.loads(self.recover())
        path = self.project / "README.md"
        path.write_text("staged", encoding="utf-8")
        self.git("add", "README.md")
        path.write_text("assets", encoding="utf-8")
        self.assertEqual(self.git("diff", "HEAD"), "")
        self.assertIn("Preview changed", self.recover("--expect", preview["sha256"], ok=False))

    def test_post_start_commit_cannot_be_excluded(self):
        self.env.update(GIT_AUTHOR_DATE="2099-01-01T00:00:00Z", GIT_COMMITTER_DATE="2099-01-01T00:00:00Z")
        owned = self.commit("page.html", "owned")
        self.git("update-ref", "refs/remotes/origin/main", owned)
        self.assertIn("predate run start", self.recover(base=owned, ok=False))

    def test_unpaused_and_completed_run_refused(self):
        self.gate("resume")
        self.assertIn("paused open run", self.recover(ok=False))
        self.gate("pause", "--reason", "review")
        preview = json.loads(self.recover())
        self.recover("--expect", preview["sha256"])
        (self.project / ".factory/fast/work-record.md").write_text(LIGHT, encoding="utf-8")
        for step in ("tickets", "plan", "build", "done-run"):
            self.gate("done", step)
        self.gate("pause", "--reason", "late")
        self.assertIn("before done-run", self.recover(ok=False))

    def test_changed_initial_snapshot_rejected(self):
        recovery = module("fast_baseline")
        from types import SimpleNamespace
        run = {**self.state(), "ui_seen": {"page.html": "old digest"}}
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            recovery.preview(self.project, run, SimpleNamespace(base=self.base, upstream="refs/remotes/origin/main", reason="owner"))


if __name__ == "__main__":
    unittest.main()
