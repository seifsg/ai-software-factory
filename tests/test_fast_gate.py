"""Fast gate: real CLI and hook calls against disposable projects (fast-run.md#the-gate)."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
GATE = SCRIPTS / "fast_gate.py"
SAMPLE = Path(__file__).resolve().parents[1] / ".agents/skills/safe-engine/references/work-record-sample.md"
STEPS = ["research", "kickoff", "tickets", "analysis", "plan", "design", "schema", "build", "done-run", "handoff"]


class FastGateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="fast gate ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.project = self.root / "app projekt ü"  # spaces and non-ASCII: hosts send raw UTF-8
        self.project.mkdir()
        self.env = dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "home"))

    def tearDown(self):
        log = self.root / "home" / "logs" / "gate.log"
        if log.exists():  # the fail-open guard must never have swallowed an exception
            self.assertNotIn("hook.error", log.read_text(encoding="utf-8"))

    def gate(self, *args, ok=True, project=None):
        result = subprocess.run([sys.executable, str(GATE), *args, "--project", str(project or self.project)],
                                capture_output=True, text=True, errors="replace", env=self.env)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def hook(self, event, command=None):
        event = {"session_id": "s1", "cwd": str(self.project), **event}
        result = subprocess.run(command or [sys.executable, str(GATE), "hook"],
                                input=json.dumps(event, ensure_ascii=False).encode("utf-8"),
                                capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        out = result.stdout.decode("utf-8").strip()
        return json.loads(out) if out else None

    def pre(self, tool, cwd=None, session="s1", **tool_input):
        out = self.hook({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input,
                         "session_id": session, "cwd": str(cwd or self.project)})
        return out["hookSpecificOutput"]["permissionDecision"] if out else "allow"

    def start(self, *flags, kind="product"):
        self.gate("start", "--key", "portal-poc", "--kind", kind, "--request", "Build a client portal", *flags)

    def finish_sample(self):
        record = self.project / ".factory/fast/work-record.md"
        shutil.copyfile(SAMPLE, record)
        shot = self.project / ".factory/fast/shots/schedule.png"
        shot.parent.mkdir(parents=True)
        shot.write_bytes(b"PNG")
        for step in STEPS:
            self.gate("done", step, *(["--offline", "sample URLs"] if step == "tickets" else []))

    def test_start_records_run_and_enforces_step_order(self):
        self.start("--auth")
        run = json.loads((self.project / ".factory/fast/run.json").read_text(encoding="utf-8"))
        self.assertEqual((run["ui"], run["data"], run["auth"]), (True, True, True))
        self.assertEqual(len(list((self.root / "home/active").glob("*.json"))), 1)
        self.assertIn("Finish first: research, kickoff", self.gate("done", "tickets", ok=False))
        self.assertIn("missing or empty", self.gate("done", "research", ok=False))
        self.assertIn("still open", self.gate("start", "--key", "again", "--kind", "change", "--request", "x", ok=False))

    def test_start_keeps_factory_out_of_git_and_notes_the_bundle(self):
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        (self.project / ".factory").mkdir()
        receipt = {"version": 1, "bundle_root": str(self.root / "bundle"), "revision": "a" * 40}
        (self.project / ".factory/entry-bundle.json").write_text(json.dumps(receipt), encoding="utf-8")
        output = self.gate("start", "--key", "portal-poc", "--kind", "change", "--request", "fix copy")
        self.assertIn("added .factory/ to .gitignore", output)
        self.assertIn(".factory/", (self.project / ".gitignore").read_text(encoding="utf-8"))
        run = json.loads((self.project / ".factory/fast/run.json").read_text(encoding="utf-8"))
        self.assertEqual(run["bundle"]["revision"], "a" * 40)
        self.assertIn("Hooks:", output)

    def test_research_needs_cited_competitors(self):
        self.start()
        record = self.project / ".factory/fast/work-record.md"
        record.write_text(SAMPLE.read_text(encoding="utf-8").replace("https://", "see "), encoding="utf-8")
        self.assertIn("each citing a source URL", self.gate("done", "research", ok=False))

    def test_sample_record_passes_every_step_and_close_unregisters(self):
        self.start("--auth")
        self.finish_sample()
        self.assertIn("Next: close", self.gate("status"))
        self.gate("close")
        self.assertEqual(list((self.root / "home/active").glob("*.json")), [])
        self.assertIsNone(self.hook({"hook_event_name": "Stop", "stop_hook_active": False}))

    def test_checks_refuse_missing_markers(self):
        self.start("--auth")
        self.finish_sample()
        record = self.project / ".factory/fast/work-record.md"
        text = SAMPLE.read_text(encoding="utf-8")
        record.write_text(text.replace("**Theme:** light mode default", "**Theme:** dark by default")
                              .replace("- T7 pre:", "- T7 skipped:"), encoding="utf-8")
        self.assertIn("light mode", self.gate("done", "design", ok=False))
        self.assertIn("T7 needs", self.gate("done", "build", ok=False))
        record.write_text(text.replace("**Dev sign-in:**", "Sign-in:"), encoding="utf-8")
        self.assertIn("Dev sign-in", self.gate("done", "handoff", ok=False))

    def test_hooks_deny_source_writes_until_the_gate_opens(self):
        self.start()
        source, factory = str(self.project / "src/app.ts"), str(self.project / ".factory/fast/notes.md")
        self.assertEqual(self.pre("Write", file_path=source), "deny")
        self.assertEqual(self.pre("Edit", file_path=factory), "allow")
        self.assertEqual(self.pre("Write", file_path=str(self.root / "elsewhere.ts")), "allow")
        self.assertEqual(self.pre("apply_patch", command="*** Begin Patch\n*** Add File: src/x.ts\n+x\n*** End Patch"), "deny")
        self.finish_sample()
        self.assertEqual(self.pre("Write", file_path=source), "allow")
        ledger = str(self.project / ".factory/fast/run.json")
        self.assertEqual(self.pre("Edit", file_path=ledger), "deny")  # only the gate writes its ledger

    def test_shell_commands_count_code_not_quoted_text(self):
        self.start()
        cases = {
            "npm install next": "deny", "pnpm dlx shadcn@latest init": "deny", "git status 2>/dev/null": "allow",
            "cat > src/a.ts <<'EOF'\nx -> y\nEOF": "deny", "cat <<'EOF' > src/a.ts\nx\nEOF": "deny",
            "cat <<'EOF' | tee src/b.ts\nx\nEOF": "deny", "printf x | tee -a src/b.ts": "deny",
            "node x.js &> src/c.ts": "deny", "echo x >| src/e.ts": "deny",
            'gh issue create --title "A -> B" --body "## Flow\nlogin -> home\nnpm install next"': "allow",
            "gh issue create --body @'\nlogin -> home\n'@": "allow",
            "cat > .factory/fast/work-record.md <<'EOF'\npip install -e .\nEOF": "allow",
            'python -c "\nprint(len([1]) > 3)\n"': "allow", "if (( $# > 2 )); then echo ok; fi": "allow",
            "grep -rn tee src/": "allow", "ls > /dev/null 2>&1": "allow", "echo {} > .factory/fast/run.json": "deny",
        }
        for command, decision in cases.items():
            with self.subTest(command=command):
                self.assertEqual(self.pre("Bash", command=command), decision)

    def test_stop_blocks_once_and_respects_pause(self):
        self.start()
        self.pre("Write", file_path=str(self.project / "src/app.ts"))  # binds session s1
        elsewhere = {"hook_event_name": "Stop", "cwd": str(self.root), "stop_hook_active": False}
        self.assertEqual(self.hook(elsewhere)["decision"], "block")
        self.assertIsNone(self.hook({**elsewhere, "stop_hook_active": True}))
        self.assertIsNone(self.hook({**elsewhere, "session_id": "other"}))
        self.gate("pause", "--reason", "waiting on the owner")
        self.assertIsNone(self.hook(elsewhere))
        context = self.hook({"hook_event_name": "UserPromptSubmit", "prompt": "go"})
        self.assertIn("paused: waiting on the owner", context["hookSpecificOutput"]["additionalContext"])

    def test_reading_a_project_does_not_bind_a_session(self):
        self.start()
        self.assertEqual(self.pre("Bash", cwd=self.root, session="reader", command=f'ls "{self.project}"'), "allow")
        self.assertIsNone(self.hook({"hook_event_name": "Stop", "session_id": "reader", "cwd": str(self.root),
                                     "stop_hook_active": False}))

    def test_linked_paths_resolve_to_the_real_project(self):
        self.start()
        link = self.root / "link"
        try:
            os.symlink(self.project, link, target_is_directory=True)
        except OSError:
            made = os.name == "nt" and subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.project)],
                                                      capture_output=True).returncode == 0
            if not made:
                self.skipTest("cannot create a directory link here")
        self.addCleanup(lambda: os.rmdir(link) if link.exists() else None)
        self.assertEqual(self.pre("Write", cwd=link, file_path=str(link / "src/x.ts")), "deny")

    def test_bad_registry_entry_and_unreachable_drive_keep_gating(self):
        self.start()
        active = self.root / "home/active"
        (active / "bad.json").write_text("[1, 2]", encoding="utf-8")
        ghost = active / "ghost.json"
        ghost.write_text(json.dumps({"project": str(self.root / "unmounted/drive/app"), "key": "ghost"}), encoding="utf-8")
        self.assertEqual(self.pre("Write", file_path=str(self.project / "src/y.ts")), "deny")
        self.assertTrue(ghost.exists())

    def test_launcher_is_silent_without_runs_and_gates_with_one(self):
        launcher = shutil.which("sh")
        if not launcher:
            self.skipTest("no POSIX sh")
        command = [launcher, (SCRIPTS / "run-gate.sh").as_posix()]
        event = {"hook_event_name": "PreToolUse", "tool_name": "Write",
                 "tool_input": {"file_path": str(self.project / "src/a.ts")}}
        self.assertIsNone(self.hook(event, command))
        self.assertFalse((self.root / "home/hook-python").exists())  # no run: Python never started
        self.start()
        self.assertEqual(self.hook(event, command)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertTrue((self.root / "home/hook-python").exists())
        self.assertEqual(self.hook(event, command)["hookSpecificOutput"]["permissionDecision"], "deny")  # cached

    def test_git_bash_project_paths_work(self):
        if os.name != "nt":
            self.skipTest("Windows path forms")
        self.start()
        posix = "/" + str(self.project)[0].lower() + str(self.project)[2:].replace("\\", "/")
        self.assertIn("Next: research", self.gate("status", project=posix))

    def test_ticket_links_are_checked_against_the_epic(self):
        spec = importlib.util.spec_from_file_location("fast_record", SCRIPTS / "fast_record.py")
        record = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(record)
        epic = "https://github.com/acme/portal/issues/1"
        linked = "https://github.com/acme/portal/issues/2\n"
        with patch.object(record, "gh", side_effect=["1", linked]):
            self.assertEqual(record.verify_tickets(epic, ["https://github.com/acme/portal/issues/2"]), [])
        with patch.object(record, "gh", side_effect=["1", linked]):
            self.assertIn("not linked", record.verify_tickets(epic, ["https://github.com/acme/portal/issues/9"])[0])
        self.assertIn("--offline", record.verify_tickets("https://tracker.example/1", [])[0])


if __name__ == "__main__":
    unittest.main()
