"""Fast gate run state lives in the gate home: no project write opens the gate or silences a guard (fast-run.md#the-gate)."""
import json
import shutil
import subprocess
import unittest

import test_fast_gate as harness

SOURCE, PUSH = "src/app.ts", "git push -f origin main"


class RunStateTests(harness.GateHarness, unittest.TestCase):
    def begin(self):
        self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "fix the footer copy")
        self.mirror = self.project / ".factory/fast/run.json"
        self.state = next((self.root / "home/runs").glob("*.json"))

    def assert_gated(self, lost=False):
        """A source write and a force push are both refused; lost runs say so."""
        out = self.hook({"hook_event_name": "PreToolUse", "tool_name": "Write",
                         "tool_input": {"file_path": str(self.project / SOURCE)}})
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertEqual("run state in the gate home is missing" in reason, lost, reason)
        self.assertEqual(self.pre("Bash", command=PUSH), "deny")

    def test_no_project_write_opens_the_gate(self):
        self.begin()
        mirror, closed = self.mirror, json.loads(self.mirror.read_text(encoding="utf-8"))
        closed.update(closed=True, done={step: {"at": "x"} for step in ("tickets", "plan", "build")})
        backup = self.root / "backup.json"
        backup.write_text(json.dumps(closed), encoding="utf-8")
        tampers = {  # each form found in the PR #78 reviews, as an agent's shell would leave the project
            "overwrite {}": lambda: mirror.write_text("{}", encoding="utf-8"),
            "truncate": lambda: mirror.write_bytes(b""),
            "BOM {} (Set-Content)": lambda: mirror.write_bytes("﻿{}".encode("utf-8")),
            "cp a closed backup": lambda: shutil.copy(backup, mirror),
            "steps written by hand (sed -i)": lambda: mirror.write_text(json.dumps({**closed, "closed": False})),
            "delete run.json": lambda: mirror.unlink(),
            "mv run.json away": lambda: mirror.replace(self.root / "moved.json"),
            "rm -rf .factory/fast": lambda: shutil.rmtree(mirror.parent),
            "a file where .factory/fast was": lambda: (shutil.rmtree(mirror.parent),
                                                      mirror.parent.write_text("x", encoding="utf-8")),
        }
        for name, tamper in tampers.items():
            with self.subTest(name):
                if mirror.parent.is_file():
                    mirror.parent.unlink()
                mirror.parent.mkdir(parents=True, exist_ok=True)
                mirror.write_text("{}", encoding="utf-8")
                tamper()
                self.assert_gated()
                self.assertIn("Gate: closed until tickets, plan", self.gate("status"))  # A2: steps only via `done`

    def test_a_lost_home_state_keeps_the_gate_closed_until_the_owner_closes(self):
        for broken in (None, b"not json {", b"", json.dumps({"version": 99}).encode("utf-8")):
            with self.subTest(broken=broken):
                self.begin()
                self.state.unlink() if broken is None else self.state.write_bytes(broken)
                self.mirror.write_text("{}", encoding="utf-8")  # an older run's mirror would migrate; this one cannot
                self.assert_gated(lost=True)
                self.assertIn("--abandon", self.gate("done", "tickets", ok=False))
                self.assertIn("--abandon", self.gate("close", ok=False))
                refused = self.gate("start", "--key", "next", "--kind", "change", "--request", "x", ok=False)
                self.assertIn("still open here", refused)
                self.assertNotIn("Traceback", refused)
                self.assertIn("without a readable run state", self.gate("close", "--abandon", "the owner dropped it"))
                self.assertEqual(list((self.root / "home/active").glob("*.json")), [])
                self.assertEqual(self.pre("Write", file_path=str(self.project / SOURCE)), "allow")

    def test_close_and_start_need_no_project_copy(self):
        self.begin()
        self.mirror.write_bytes(b"not json {")
        sub = self.project / "src"
        sub.mkdir()
        self.assertIn("abandoned", self.gate("close", "--abandon", "dropped", project=sub))  # found from a subfolder
        self.assertEqual(list((self.root / "home/active").glob("*.json")), [])
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        self.assertIn("nothing was closed", self.gate("close", "--abandon", "dropped", project=elsewhere, ok=False))
        self.mirror.unlink()
        self.gate("start", "--key", "next", "--kind", "change", "--request", "fix the header copy")
        self.assertEqual(json.loads(self.mirror.read_text(encoding="utf-8"))["key"], "next")
        archived = list((self.project / ".factory/fast/archive").glob("copy-fix-*/work-record.md"))
        self.assertEqual(len(archived), 1)  # named from the home state, not the mirror

    def test_an_older_run_moves_home_from_its_open_mirror(self):
        for mirror_change, lost in ((None, False), ({"closed": True}, True), ({"key": "other"}, True)):
            with self.subTest(mirror_change=mirror_change):
                self.begin()
                self.state.unlink()  # as an older gate left it: ledger in the project only
                if mirror_change:
                    run = json.loads(self.mirror.read_text(encoding="utf-8"))
                    self.mirror.write_text(json.dumps({**run, **mirror_change}), encoding="utf-8")
                self.assert_gated(lost=lost)
                self.assertEqual(self.state.exists(), not lost)
                if not lost:
                    self.mirror.write_text("{}", encoding="utf-8")  # moved home: the mirror no longer counts
                    self.assert_gated()
                    self.assertIn("run.migrate", (self.root / "home/logs/gate.log").read_text(encoding="utf-8"))
                self.gate("close", "--abandon", "next case")

    def test_a_parallel_move_home_never_replaces_the_state_that_landed_first(self):
        self.begin()
        newer = {**json.loads(self.state.read_text(encoding="utf-8")), "done": {"tickets": {"at": "x"}}}
        self.state.write_text(json.dumps(newer), encoding="utf-8")  # a gate command moved it home and ran `done`
        moved = harness.module("fast_ledger").migrate(self.state, {"project": str(self.project), "key": "copy-fix"},
                                                       lambda *args, **data: None)
        self.assertEqual(moved["done"], newer["done"])
        self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["done"], newer["done"])

    def test_the_ignore_line_comes_back_before_a_shell_command(self):
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        gitignore = self.project / ".gitignore"
        gitignore.write_text("node_modules/\n", encoding="utf-8")
        self.begin()
        gitignore.write_text("node_modules/\n", encoding="utf-8")  # git checkout .gitignore
        self.assertEqual(self.pre("Write", file_path=str(self.project / ".factory/note.md")), "allow")
        self.assertNotIn(".factory/", gitignore.read_text(encoding="utf-8"))  # only shell commands restore it
        self.assertEqual(self.pre("Bash", command="git clean -fd"), "allow")
        self.assertEqual(gitignore.read_text(encoding="utf-8"), "node_modules/\n.factory/\n")
        gitignore.unlink()
        self.pre("Bash", command="ls")
        self.assertEqual(gitignore.read_text(encoding="utf-8"), ".factory/\n")

    def test_no_ignore_line_is_added_where_the_run_had_none(self):
        self.begin()  # not a Git repository: start adds no line, so hooks add none
        self.pre("Bash", command="ls")
        self.assertFalse((self.project / ".gitignore").exists())


if __name__ == "__main__":
    unittest.main()
