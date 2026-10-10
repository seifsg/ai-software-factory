"""Owner progress: the run card, once-only hook messages and the no-read hot path (fast-run.md#progress)."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
GATE = SCRIPTS / "fast_gate.py"
STEPS = ["tickets", "plan", "build", "done-run", "handoff"]
RECORD = """# copy-fix
## Tickets
**Ticket:** https://github.com/o/r/issues/7
**Backlog:** searched "footer": nothing open
## Plan
**Success:** the footer reads "Contact us".
### Todos
- T1 fix the footer word
- T2 link the footer to the contact page
## Build log
"""


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


progress = module("fast_progress")


class CardTests(unittest.TestCase):
    def setUp(self):
        self.run = {"mode": "fast", "kind": "change", "key": "k", "created": "2026-10-10T10:00:00+00:00",
                    "done": {"tickets": {"at": "2026-10-10T10:05:00+00:00"}}, "paused": None, "coverage": True,
                    "tickets": ["https://x/1", "https://x/2"]}
        self.sections = progress.sections("## Plan\n### Todos\n- T1 fix footer (A1)\n- [ ] **T2** add link\n"
                                          "## Build log\n- T1 pre: a do: b post: c\n- T3 pre: x do: y post: z\n")

    def test_card_shows_step_time_todos_and_tickets(self):
        lines = progress.card(self.run, STEPS, self.sections, "2026-10-10T11:07:00+00:00").splitlines()
        self.assertEqual(lines, ["🏭 fast change 'k' · step 2/5 plan · 1h02m in step · 1h07m total",
                                 "✅ tickets   ▶️ plan   ⬜ build · done-run · handoff",
                                 "☑️ todos 1/2 · open: T2 · https://x/1 +1"])  # T3 is not a plan todo

    def test_paused_card_leads_with_the_question_and_a_finished_one_lists_durations(self):
        paused = progress.card({**self.run, "paused": {"reason": "pick a link"}}, STEPS, self.sections, "2026-10-10T11:07:00+00:00")
        self.assertTrue(paused.startswith("⏸️ waiting on you: pick a link\n🏭"))
        done = {step: {"at": f"2026-10-10T1{i}:00:00+00:00"} for i, step in enumerate(STEPS, 1)}
        finished = progress.card({**self.run, "done": done, "closed": True}, STEPS, {}, "2026-10-10T16:30:00+00:00")
        self.assertEqual(finished.splitlines(), ["🏭 fast change 'k' · 6h30m total · closed",
                                                 "⏱️ tickets 1h00m · plan 1h00m · build 1h00m · done-run 1h00m · handoff 1h00m",
                                                 "🎫 https://x/1 +1"])

    def test_parsers(self):
        self.assertEqual(progress.titles(self.sections), {"1": "fix footer (A1)", "2": "add link"})
        tagged = progress.sections('## Plan\n### Todos\n- T1 (light) fix the typo in `greeting`: "Helo" to "Hello" now\n')
        self.assertEqual(progress.titles(tagged), {"1": 'fix the typo in `greeting`: "Helo" to "Hello"…'})  # at a word
        line = "- T2 pre: a do: b post: see T5"
        self.assertEqual(progress.built_ids(line, strict=True), {"2"})
        self.assertEqual(progress.built_ids(line, strict=False), {"2", "5"})  # older runs: any mention counts
        self.assertEqual(progress.built_ids("- T4 pre: a do: b", strict=False), set())
        times = ("2026-10-10T10:00:40+00:00", "2026-10-10T10:14:00+00:00", "2026-10-10T11:02:00+00:00",
                 "2026-10-12T13:00:00+00:00", None)
        self.assertEqual([progress.span("2026-10-10T10:00:00+00:00", end) for end in times], ["40s", "14m", "1h02m", "2d3h", ""])


class ProgressHookTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="fast progress ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.project = self.root / "app ü"
        self.project.mkdir()
        self.env = dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "home"), GH_CONFIG_DIR=str(self.root / "gh"))
        self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "fix the footer")
        self.record = self.project / ".factory/fast/work-record.md"
        self.shown = self.project / ".factory/fast/shown"

    def tearDown(self):
        log = self.root / "home" / "logs" / "gate.log"
        if log.exists():  # progress failures are logged as hook errors; none may happen
            self.assertNotIn("hook.error", log.read_text(encoding="utf-8"))

    def gate(self, *args):
        result = subprocess.run([sys.executable, str(GATE), *args, "--project", str(self.project)],
                                capture_output=True, text=True, encoding="utf-8", env=self.env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def hook(self, name="PreToolUse", host="claude", **extra):
        event = {"hook_event_name": name, "session_id": "s1", "cwd": str(self.project), "tool_name": "Bash",
                 "tool_input": {"command": "ls"}, **extra}
        result = subprocess.run([sys.executable, str(GATE), "hook", "--host", host], input=json.dumps(event).encode(),
                                capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        out = result.stdout.decode("utf-8").strip()
        return json.loads(out) if out else None

    def plan(self):
        self.record.write_text(RECORD, encoding="utf-8")
        self.gate("done", "tickets", "--offline", "test")
        self.gate("done", "plan", "--offline", "test")

    def test_commands_print_the_card_first_and_keep_the_plain_status(self):
        status = self.gate("status")
        self.assertTrue(status.startswith("🏭 fast change 'copy-fix' · step 1/5 tickets"), status)
        self.assertIn("[ ] tickets", status)
        self.assertIn("Next: tickets", status)

    def test_each_change_is_shown_once(self):
        self.assertIn("step 1/5 tickets", self.hook()["systemMessage"])
        self.assertIsNone(self.hook())
        self.plan()
        card = self.hook(name="Stop", stop_hook_active=True)["systemMessage"]
        self.assertIn("step 3/5 build", card)
        self.assertIn("todos 0/2 · open: T1 T2 · https://github.com/o/r/issues/7", card)
        self.record.write_text(RECORD + "- T1 pre: typo do: fixed post: reads right\n", encoding="utf-8")
        self.assertEqual(self.hook(name="UserPromptSubmit", prompt="go")["systemMessage"],
                         "☑️ T1 fix the footer word · todos 1/2 · open: T2")
        self.assertNotIn("systemMessage", self.hook(name="UserPromptSubmit", prompt="go"))

    def test_parallel_hooks_show_a_change_once(self):
        self.hook()
        self.gate("pause", "--reason", "pick the link target")
        answers = []
        threads = [threading.Thread(target=lambda: answers.append(self.hook())) for _ in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        shown = [answer["systemMessage"] for answer in answers if answer]
        self.assertEqual(len(shown), 1, answers)
        self.assertTrue(shown[0].startswith("⏸️ waiting on you: pick the link target"))

    def test_a_deny_carries_progress_and_each_host_answers_in_its_format(self):
        answer = self.hook(tool_name="Write", tool_input={"file_path": str(self.project / "src/a.ts")})
        self.assertEqual(answer["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("step 1/5 tickets", answer["systemMessage"])
        self.gate("pause", "--reason", "x")
        self.assertIn("waiting on you: x", self.hook(host="codex")["systemMessage"])
        self.gate("resume")
        cursor = self.hook(name="stop", host="cursor", conversation_id="s1", loop_count=0,
                           workspace_roots=[str(self.project)])
        self.assertEqual(set(cursor), {"followup_message"})  # cursor shows no hook messages: the agent relays

    def test_nothing_changed_reads_no_file(self):
        self.hook()
        with patch.dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "home")):
            gate = module("fast_gate")
        runs, cwd = gate.active_runs(), gate.norm(self.project)
        failing = AssertionError("read on the no-change path")
        with patch("builtins.open", side_effect=failing), patch.object(Path, "read_text", side_effect=failing), \
                patch.object(Path, "read_bytes", side_effect=failing):
            self.assertIsNone(gate.news(runs, cwd, "s1"))  # a read would log hook.error; tearDown fails then

    def test_a_gate_command_during_a_hook_never_shows_a_stale_card(self):
        self.hook()
        with patch.dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "home")):
            gate = module("fast_gate")
        runs, cwd = gate.active_runs(), gate.norm(self.project)  # read before the command lands
        self.record.write_text(RECORD, encoding="utf-8")
        self.gate("done", "tickets", "--offline", "test")
        self.assertIn("step 2/5 plan", gate.news(runs, cwd, "s1"))
        self.assertIsNone(self.hook())

    def test_delegate_calls_leave_messages_for_the_main_thread(self):
        self.assertIsNone(self.hook(agent_id="agent-1"))
        self.assertIn("step 1/5 tickets", self.hook()["systemMessage"])

    def test_claims_another_run_left_never_hide_a_tick(self):
        self.hook()
        for stale in (self.shown / "19990101000000", self.shown):  # an older gate copy's claims
            stale.mkdir(parents=True, exist_ok=True)
            (stale / "todo-1").touch()
        self.plan()
        self.record.write_text(RECORD + "- T1 pre: a do: b post: c\n", encoding="utf-8")
        self.assertIn("☑️ T1 fix the footer word", self.hook()["systemMessage"])

    def test_a_broken_registration_never_drops_a_deny(self):
        entry = next((self.root / "home/active").glob("*.json"))
        entry.write_text(json.dumps({**json.loads(entry.read_text(encoding="utf-8")), "sessions": None}), encoding="utf-8")
        answer = self.hook(tool_name="Write", tool_input={"file_path": str(self.project / "src/a.ts")})
        self.assertEqual(answer["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_start_and_close_clear_the_claims(self):
        self.hook()
        self.assertTrue((self.shown.parent / "seen").exists())
        self.gate("close", "--abandon", "owner stopped it")
        self.assertFalse(self.shown.exists() or (self.shown.parent / "seen").exists())
