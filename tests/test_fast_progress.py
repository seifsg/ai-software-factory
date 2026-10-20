"""Owner progress: record facts, the mini dashboard, once-only hook messages and the no-read hot path (fast-run.md#progress)."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
GATE = SCRIPTS / "fast_gate.py"
STEPS = ["tickets", "plan", "build", "done-run", "handoff"]
RECORD = """# copy-fix
## Tickets
**Ticket:** https://github.com/o/r/issues/7 Footer copy
**Backlog:** searched "footer": nothing open
## Plan
**Success:** the footer reads "Contact us".
### Todos
- T1 fix the footer word → the footer reads Contact us
- T2 link the footer to the contact page → click Contact and the form opens
## Build log
"""
PORTAL = """## Tickets
**Sub-issue:** https://x/issues/11 Landing page
**Sub-issue:** https://x/issues/12 (Download & SEO)
## Plan
### Todos
- T1 (standard) Landing page loads fast → open the site and it shows in under a second (#11, A1)
- T2 Download button → click it and the PDF saves (#12, A2)
- [ ] **T3** SEO tags → search shows the title and description (#12, A3)
- T4 Download counter -> see how many people downloaded (#12, A4)
## Build log
- T1 pre: a do: b post: c
- T3 pre: a do: b post: c
**Now:** T2
"""


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


facts, cards = module("fast_progress"), module("fast_card")


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.run = {"mode": "fast", "kind": "feature", "key": "portal-poc", "created": "2026-10-10T10:00:00+00:00",
                    "coverage": True, "paused": None,
                    "done": {"tickets": {"at": "2026-10-10T10:05:00+00:00"}, "plan": {"at": "2026-10-10T10:20:00+00:00"}}}
        self.sections = facts.sections(PORTAL)
        self.at = "2026-10-10T11:02:00+00:00"

    def test_dashboard_shows_ticket_done_now_and_next(self):
        self.assertEqual(cards.card(self.run, STEPS, self.sections, self.at).splitlines(), [
            "🏭 portal-poc · 🔨 build · step 3/5 · ⏱️ 1h02m total, 42m in step",
            "🎫 #12 Download & SEO   ▰▱▱ 1/3 · run 2/4",
            "✅ SEO tags",
            "🔨 NOW  Download button",
            "     → click it and the PDF saves",
            "⏭️ NEXT Download counter"])

    def test_paused_card_asks_first_and_holds_the_work(self):
        lines = cards.card({**self.run, "paused": {"reason": "PDF or ZIP?"}}, STEPS, self.sections, self.at).splitlines()
        self.assertEqual(lines[0], "⏸️ WAITING ON YOU: PDF or ZIP?")
        self.assertIn("🔨 ON HOLD until you answer: Download button", lines)

    def test_before_and_after_the_build_the_card_shows_steps(self):
        early = {**self.run, "done": {"tickets": {"at": "2026-10-10T10:05:00+00:00"}}}
        self.assertEqual(cards.card(early, STEPS, self.sections, "2026-10-10T10:07:00+00:00").splitlines()[1],
                         "✅ tickets   🗺️ plan   ⬜ build · done-run · handoff")
        done = {step: {"at": f"2026-10-10T1{i}:00:00+00:00"} for i, step in enumerate(STEPS, 1)}
        finished = cards.card({**self.run, "done": done, "closed": True}, STEPS, self.sections, "2026-10-10T16:30:00+00:00")
        self.assertEqual(finished.splitlines(), [
            "🏭 portal-poc · ⏱️ 6h30m total · 🏁 closed",
            "⏱️ tickets 1h00m · plan 1h00m · build 1h00m · done-run 1h00m · handoff 1h00m"])

    def test_record_facts(self):
        self.assertEqual(facts.todo_items(self.sections), {
            "1": ("Landing page loads fast", "open the site and it shows in under a second", "11"),
            "2": ("Download button", "click it and the PDF saves", "12"),
            "3": ("SEO tags", "search shows the title and description", "12"),
            "4": ("Download counter", "see how many people downloaded", "12")})
        self.assertEqual(facts.ticket_titles(self.sections), {"11": "Landing page", "12": "Download & SEO"})
        self.assertEqual((facts.now_ids(self.sections), facts.without_result(self.sections)), (["2"], []))
        bare = facts.sections("## Plan\n### Todos\n- T1 add store_true option\n- Wave 2: T2, T3\n- T3 x → y\n")
        self.assertEqual(facts.without_result(bare), ["1", "2"])  # no result; no line of its own
        long = facts.sections('## Plan\n### Todos\n- T1 (light) fix the typo in `greeting`: "Helo" to "Hello" now → ok\n')
        self.assertEqual(facts.todo_items(long)["1"][0], 'fix the typo in `greeting`: "Helo" to "Hello"…')
        layouts = facts.sections("## Plan\n### Todos\nT1 and T2 run first.\n- T1 Schema → the app opens seeded (#2, A1, deep)\n"
                                 "#### T2 Logger → every error lands in one log (#2, a1)\n")
        self.assertEqual(facts.todo_items(layouts), {"1": ("Schema", "the app opens seeded", "2"),
                                                     "2": ("Logger", "every error lands in one log", "2")})
        self.assertEqual(facts.without_result(layouts), [])  # the line with a result wins over the earlier mention
        older = facts.sections("## Plan\n### Todos\n- T1 Schema (#2)\nT1 and T2 share one migration.\n")
        self.assertEqual(facts.todo_items(older)["1"], ("Schema", "", "2"))  # without results, the first line wins
        started = time.perf_counter()
        facts.todo_items(facts.sections("## Plan\n### Todos\n#" + " " * 20000 + "x\n"))
        self.assertLess(time.perf_counter() - started, 0.5)  # no quadratic backtracking on odd input

    def test_a_long_now_list_never_breaks_the_hook(self):
        many = " ".join(f"T{n}" for n in range(2, 302))
        plan = "\n".join(f"- T{n} item {n} → result {n}" for n in range(1, 302))
        with tempfile.TemporaryDirectory() as folder:
            record = Path(folder) / "work-record.md"
            record.write_text(f"## Plan\n### Todos\n{plan}\n## Build log\n- T1 pre: a do: b post: c\n**Now:** {many}\n",
                              encoding="utf-8")
            lines = cards.news(self.run, STEPS, record, Path(folder) / "shown", 1, self.at)
        self.assertEqual(lines[0], "✅ item 1 done → result 1")
        self.assertIn("+299 in parallel", "\n".join(lines))

    def test_a_claim_fault_is_raised_for_a_retry_never_hidden(self):
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(cards.os, "open", side_effect=PermissionError("claims folder not writable")):
            record = Path(folder) / "work-record.md"
            record.write_text(PORTAL, encoding="utf-8")
            with self.assertRaises(PermissionError):  # fast_gate logs it and leaves `seen` alone: the next hook retries
                cards.news(self.run, STEPS, record, Path(folder) / "shown", 1, self.at)

    def test_parsers_and_formats(self):
        line = "- T2 pre: a do: b post: see T5\n- T1 pre: a do: b post: c"
        self.assertEqual(list(facts.built_ids(line, strict=True)), ["2", "1"])  # log order
        self.assertEqual(set(facts.built_ids(line, strict=False)), {"1", "2", "5"})  # older runs: any mention counts
        self.assertEqual(facts.built_ids("- T4 pre: a do: b", strict=False), {})
        self.assertEqual([cards.bar(1, 3), cards.bar(5, 20), cards.bar(0, 0)], ["▰▱▱", "▰▰▰▱▱▱▱▱▱▱", ""])
        times = ("2026-10-10T10:00:40+00:00", "2026-10-10T10:14:00+00:00", "2026-10-10T11:02:00+00:00",
                 "2026-10-12T13:00:00+00:00", None)
        self.assertEqual([cards.span("2026-10-10T10:00:00+00:00", end) for end in times], ["40s", "14m", "1h02m", "2d3h", ""])


class ProgressHookTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="fast progress ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.project = self.root / "app ü"
        self.project.mkdir()
        self.env = dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "home"), GH_CONFIG_DIR=str(self.root / "gh"))
        for name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"):
            self.env.pop(name, None)  # gh logged out: --offline stays honest
        self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "fix the footer")
        self.record = self.project / ".factory/fast/work-record.md"
        self.shown = self.project / ".factory/fast/shown"
        (self.project / ".factory/fast/prompts").write_text("1", encoding="utf-8")  # the live view's link reminder
        # (first and every sixth prompt, test_fast_view.py) stays out of these exact message checks

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
        self.assertTrue(status.startswith("🏭 copy-fix · 🎫 tickets · step 1/5"), status)
        self.assertIn("[ ] tickets", status)
        self.assertIn("Next: tickets", status)

    def test_each_change_is_shown_once(self):
        self.assertIn("step 1/5", self.hook()["systemMessage"])
        self.assertIsNone(self.hook())
        self.plan()
        card = self.hook(name="Stop", stop_hook_active=True)["systemMessage"].splitlines()
        self.assertIn("🔨 build · step 3/5", card[0])
        self.assertEqual(card[1:], ["🎫 #7 Footer copy   ▱▱ 0/2", "⏭️ NEXT fix the footer word"])
        self.record.write_text(RECORD + "**Now:** T1\n", encoding="utf-8")
        self.assertEqual(self.hook(name="UserPromptSubmit", prompt="go")["systemMessage"].splitlines(), [
            "🔨 NOW  fix the footer word", "     → the footer reads Contact us", "🎫 #7 Footer copy   ▱▱ 0/2"])
        self.record.write_text(RECORD + "- T1 pre: typo do: fixed post: reads right\n**Now:** T2\n", encoding="utf-8")
        self.assertEqual(self.hook(name="UserPromptSubmit", prompt="go")["systemMessage"].splitlines(), [
            "✅ fix the footer word done → the footer reads Contact us",
            "🔨 NOW  link the footer to the contact page", "     → click Contact and the form opens",
            "🎫 #7 Footer copy   ▰▱ 1/2"])
        self.assertNotIn("systemMessage", self.hook(name="UserPromptSubmit", prompt="go"))

    def test_work_finished_while_paused_shows_on_hold_never_now(self):
        self.plan()
        self.hook()
        self.gate("pause", "--reason", "which contact page?")
        self.hook()  # the paused card
        self.record.write_text(RECORD + "- T1 pre: typo do: fixed post: reads right\n**Now:** T2\n", encoding="utf-8")
        self.assertEqual(self.hook()["systemMessage"].splitlines()[:2], [
            "✅ fix the footer word done → the footer reads Contact us",
            "🔨 ON HOLD until you answer: link the footer to the contact page"])

    def test_a_plan_without_results_is_refused(self):
        self.record.write_text(RECORD.replace(" → the footer reads Contact us", ""), encoding="utf-8")
        self.gate("done", "tickets", "--offline", "test")
        result = subprocess.run([sys.executable, str(GATE), "done", "plan", "--offline", "test", "--project",
                                 str(self.project)], capture_output=True, text=True, encoding="utf-8", env=self.env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("T1 needs its own line with its result", result.stderr)

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
        self.assertTrue(shown[0].startswith("⏸️ WAITING ON YOU: pick the link target"))

    def test_a_deny_carries_progress_and_each_host_answers_in_its_format(self):
        answer = self.hook(tool_name="Write", tool_input={"file_path": str(self.project / "src/a.ts")})
        self.assertEqual(answer["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("step 1/5", answer["systemMessage"])
        self.gate("pause", "--reason", "x")
        self.assertIn("WAITING ON YOU: x", self.hook(host="codex")["systemMessage"])
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

    def test_sibling_modules_cache_their_bytecode_in_the_gate_home_only(self):
        scripts = self.root / "plugin" / "scripts"  # stands in for an install inside a product repository
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        probe = ("import sys; sys.path.insert(0, sys.argv[1]); import fast_gate\n"
                 "try:\n    fast_gate.sibling('no_such_module')\nexcept ImportError:\n    pass\n"
                 "fast_gate.sibling('fast_card'); print(sys.dont_write_bytecode, sys.pycache_prefix)")
        env = {**self.env, "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("PYTHONPYCACHEPREFIX", None)
        out = subprocess.run([sys.executable, "-c", probe, str(scripts)], capture_output=True, text=True, env=env)
        self.assertEqual(out.stdout.strip(), "True None", out.stderr)  # the host's settings come back, failed import too
        cached = {path.name.split(".")[0] for path in (self.root / "home" / "pycache").rglob("*.pyc")}
        self.assertTrue({"fast_card", "fast_progress"} <= cached, cached)  # later hooks load these, never compile
        self.assertEqual(list(scripts.rglob("*.pyc")), [])  # nothing lands beside the scripts or in a project

    def test_a_gate_command_during_a_hook_never_shows_a_stale_card(self):
        self.hook()
        with patch.dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "home")):
            gate = module("fast_gate")
        runs, cwd = gate.active_runs(), gate.norm(self.project)  # read before the command lands
        self.record.write_text(RECORD, encoding="utf-8")
        self.gate("done", "tickets", "--offline", "test")
        with patch.object(gate, "load_stamped", side_effect=PermissionError("mid-replace")):
            self.assertIsNone(gate.news(runs, cwd, "s1"))  # cannot re-read: show nothing rather than stale
        self.assertIn("🗺️ plan · step 2/5", gate.news(runs, cwd, "s1"))
        self.assertIsNone(self.hook())

    def test_delegate_calls_leave_messages_for_the_main_thread(self):
        self.assertIsNone(self.hook(agent_id="agent-1"))
        self.assertIn("step 1/5", self.hook()["systemMessage"])

    def test_claims_another_run_left_never_hide_a_finished_todo(self):
        self.hook()
        for stale in (self.shown / "19990101000000", self.shown):  # an older gate copy's claims
            stale.mkdir(parents=True, exist_ok=True)
            (stale / "todo-1").touch()
        self.plan()
        self.record.write_text(RECORD + "- T1 pre: a do: b post: c\n", encoding="utf-8")
        self.assertIn("✅ fix the footer word done", self.hook()["systemMessage"])

    def test_a_broken_registration_never_drops_a_deny(self):
        entry = next((self.root / "home/active").glob("*.json"))
        registration = json.loads(entry.read_text(encoding="utf-8"))
        for broken in (None, 5, "s1"):
            entry.write_text(json.dumps({**registration, "sessions": broken}), encoding="utf-8")
            answer = self.hook(tool_name="Write", tool_input={"file_path": str(self.project / "src/a.ts")})
            self.assertEqual(answer["hookSpecificOutput"]["permissionDecision"], "deny", broken)

    def test_start_and_close_clear_the_claims(self):
        self.hook()
        self.assertTrue((self.shown.parent / "seen").exists())
        self.gate("close", "--abandon", "owner stopped it")
        self.assertFalse(self.shown.exists() or (self.shown.parent / "seen").exists())
