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
ONLINE = ("tickets", "plan", "handoff")  # steps that read the listed tickets through gh
LIGHT = """# copy-fix
## Tickets
**Ticket:** none (one-word copy fix, no outcome change)
**Backlog:** searched "footer": nothing open
## Plan
**Success:** the footer reads "Contact us".
### Todos
- T1 fix the footer word → the footer reads "Contact us"
## Build log
- T1 pre: footer says "Contcat us" do: fixed the word post: footer reads "Contact us"
## Done-run
- PASS: home page footer reads "Contact us"
**Logs:** dev server log clean
## Handoff
**Run:** npm run dev
**Statuses:** no ticket (trivial)
**Unverified:** none
**Follow-ups:** none
"""


def record_module():
    spec = importlib.util.spec_from_file_location("fast_record", SCRIPTS / "fast_record.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FastGateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="fast gate ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.project = self.root / "app projekt ü"  # spaces and non-ASCII: hosts send raw UTF-8
        self.project.mkdir()
        self.env = dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "home"), GH_CONFIG_DIR=str(self.root / "gh"))
        for name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"):
            self.env.pop(name, None)  # gh logged out: it fails at once, never reaching the network

    def tearDown(self):
        log = self.root / "home" / "logs" / "gate.log"
        if log.exists():  # the fail-open guard must never have swallowed an exception
            self.assertNotIn("hook.error", log.read_text(encoding="utf-8"))

    def gate(self, *args, ok=True, project=None):
        result = subprocess.run([sys.executable, str(GATE), *args, "--project", str(project or self.project)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", env=self.env)
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
        return (out or {}).get("hookSpecificOutput", {}).get("permissionDecision", "allow")  # may carry progress only

    def start(self, *flags, kind="product"):
        self.gate("start", "--key", "portal-poc", "--kind", kind, "--request", "Build a client portal", *flags)

    def finish_sample(self):
        record = self.project / ".factory/fast/work-record.md"
        shutil.copyfile(SAMPLE, record)
        shot = self.project / ".factory/fast/shots/schedule.png"
        shot.parent.mkdir(parents=True)
        shot.write_bytes(b"PNG")
        for step in STEPS:
            self.gate("done", step, *(["--offline", "sample URLs"] if step in ONLINE else []))

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
        record = (self.project / ".factory/fast/work-record.md").read_text(encoding="utf-8")
        self.assertIn("## Analysis", record)  # methods without the light lane keep it, with their own hints
        self.assertNotIn("Ticket line", record)

    def test_research_needs_cited_competitors(self):
        self.start()
        record = self.project / ".factory/fast/work-record.md"
        record.write_text(SAMPLE.read_text(encoding="utf-8").replace("https://", "see "), encoding="utf-8")
        self.assertIn("each citing a source URL", self.gate("done", "research", ok=False))

    def test_sample_record_passes_every_step_and_close_unregisters(self):
        self.start("--auth")
        self.finish_sample()
        self.assertIn("Next: close", self.gate("status"))
        run = json.loads((self.project / ".factory/fast/run.json").read_text(encoding="utf-8"))
        self.assertEqual(len(run["tickets"]), 5)  # the epic and four sub-issues, pinned at `done tickets`
        self.gate("close")
        self.assertEqual(list((self.root / "home/active").glob("*.json")), [])
        self.assertIsNone(self.hook({"hook_event_name": "Stop", "stop_hook_active": False}))

    def test_offline_needs_unreadable_tickets_and_features_record_a_size(self):
        record = record_module()
        url = "https://github.com/acme/portal/issues/2"
        sections = {"tickets": f"**Ticket:** {url}\n**Backlog:** none\n"}
        on, older = {"coverage": True, "ticket_checks": True, "kind": "change"}, {"ticket_checks": True, "kind": "change"}
        readable = json.dumps({"body": "### Definition of done\n", "stateReason": None, "labels": [], "projectItems": []})
        with patch.object(record, "gh", return_value=readable):
            self.assertIn("drop --offline", record.online(on, {"offline": "no network", "all_sections": sections},
                                                          record.needs_ticks)[0].replace("without --offline", "drop --offline"))
        with patch.object(record, "gh", side_effect=RuntimeError("no network")):  # truly offline: allowed
            self.assertEqual(record.online(on, {"offline": "no network", "all_sections": sections}, record.needs_ticks), [])
        with patch.object(record, "gh", side_effect=AssertionError("older runs never read tickets offline")):
            self.assertEqual(record.online(older, {"offline": "x", "all_sections": sections}, record.needs_ticks), [])
        kickoff = "**Features:** a\n**Approach:** b\n**Answered by:** owner\n"
        self.assertIn("'**Size:**' line", record.check_kickoff({"kind": "feature", "coverage": True}, kickoff)[0])
        self.assertEqual(record.check_kickoff({"kind": "feature", "coverage": True},
                                              kickoff + "**Size:** none (small feature: one screen)\n"), [])
        self.assertEqual(record.check_kickoff({"kind": "feature"}, kickoff), [])  # older methods unchanged

    def test_empty_markers_and_borrowed_build_lines_are_refused(self):
        record = record_module()
        self.assertIsNone(record.marker("**Backlog:**\n**Sub-issue:** https://x/2\n", "Backlog"))  # no borrowing
        self.assertEqual(record.marker("**Backlog:**\nsearched x: none\n", "Backlog"), "searched x: none")
        self.assertEqual(record.marker("**Backlog:** none\n**Sub-issue:** u\n", "Backlog"), "none")
        self.assertEqual(record.marker("**Logs:** **Run 1:** PASS\n", "Logs"), "**Run 1:** PASS")  # bold value, same line
        for line in ("1. T34 pre: a do: b post: c", "- [x] T34 pre: a do: b post: c", "- **T34** pre: a do: b post: c",
                     "- `T34` pre: a do: b post: c", "| T34 | pre: a do: b post: c |"):
            with self.subTest(line=line):
                self.assertEqual(record.check_build({"coverage": True}, line, all_sections={"plan": "### Todos\n- T34 b\n"}), [])
        sections = {"plan": "### Todos\n- T33 a\n- T34 b\n"}
        borrowed = "- T33 pre: a do: b post: T23..T34 held\n"
        self.assertEqual(record.check_build({"coverage": True}, borrowed, all_sections=sections),
                         ["T34 needs its own 'T34 pre: ... do: ... post: ...' line"])
        self.assertEqual(record.check_build({}, borrowed, all_sections=sections), [])  # older methods keep the old rule
        own = borrowed + "T34 pre: c do: d post: e\n"
        self.assertEqual(record.check_build({"coverage": True}, own, all_sections=sections), [])

    def test_checks_refuse_missing_markers(self):
        self.start("--auth")
        self.finish_sample()
        record = self.project / ".factory/fast/work-record.md"
        text = SAMPLE.read_text(encoding="utf-8")
        record.write_text(text.replace("**Theme:** light mode default", "**Theme:** dark by default")
                              .replace("- T7 pre:", "- T7 skipped:"), encoding="utf-8")
        self.assertIn("light mode", self.gate("done", "design", ok=False))
        self.assertIn("T7 needs", self.gate("done", "build", ok=False))
        journeys = next(line for line in text.splitlines() if line.startswith("**Journeys:**"))
        record.write_text(text.replace(journeys, "**Journeys:** book a class, cancel a booking"), encoding="utf-8")
        self.assertIn("counts and a minimum", self.gate("done", "design", ok=False))
        record.write_text(text.replace(journeys + "\n", ""), encoding="utf-8")
        self.assertIn("'**Journeys:**' line", self.gate("done", "design", ok=False))
        record.write_text(text.replace("**Dev sign-in:**", "Sign-in:"), encoding="utf-8")
        self.assertIn("Dev sign-in", self.gate("done", "handoff", ok=False))
        record.write_text(text.replace("**Backlog:**", "Backlog:").replace("**Statuses:**", "Statuses:"), encoding="utf-8")
        self.assertIn("'**Backlog:**' line", self.gate("done", "tickets", "--offline", "sample", ok=False))
        self.assertIn("'**Statuses:**' line", self.gate("done", "handoff", ok=False))

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
        paused = self.hook(elsewhere)  # no block; the owner sees the ask first
        self.assertNotIn("decision", paused)
        self.assertTrue(paused["systemMessage"].startswith("⏸️ WAITING ON YOU: waiting on the owner"))
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

    def test_lucky_runs_the_done_run(self):
        self.gate("start", "--key", "quick-try", "--mode", "lucky", "--kind", "change", "--request", "fix copy")
        self.assertIn("done-run", self.gate("status"))

    def test_light_change_records_five_steps(self):
        self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "fix the footer copy")
        self.assertNotIn("analysis", self.gate("status"))
        run = json.loads((self.project / ".factory/fast/run.json").read_text(encoding="utf-8"))
        self.assertEqual(run["done"]["analysis"]["skipped"], "light lane")  # older hook copies still require it
        self.assertIn("Ticket line", (self.project / ".factory/fast/work-record.md").read_text(encoding="utf-8"))
        self.assertIn("'analysis' does not apply", self.gate("done", "analysis", ok=False))
        record = self.project / ".factory/fast/work-record.md"
        record.write_text(LIGHT.replace("**Ticket:**", "Ticket:"), encoding="utf-8")
        self.assertIn("'**Ticket:** <url, or none (why)>'", self.gate("done", "tickets", ok=False))
        record.write_text(LIGHT.replace("**Success:**", "Success:"), encoding="utf-8")
        self.gate("done", "tickets")
        self.assertIn("'**Success:**' line", self.gate("done", "plan", ok=False))
        record.write_text(LIGHT, encoding="utf-8")
        for step in ("plan", "build", "done-run", "handoff"):
            self.gate("done", step)
        self.assertIn("Next: close", self.gate("status"))

    def test_ticket_links_are_checked_against_the_epic(self):
        record = record_module()
        epic = "https://github.com/acme/portal/issues/1"
        linked = "https://github.com/acme/portal/issues/2\n"
        with patch.object(record, "gh", side_effect=["1", linked]):
            self.assertEqual(record.verify_tickets(epic, ["https://github.com/acme/portal/issues/2"]), [])
        with patch.object(record, "gh", side_effect=["1", linked]):
            self.assertIn("not linked", record.verify_tickets(epic, ["https://github.com/acme/portal/issues/9"])[0])
        self.assertIn("--offline", record.verify_tickets("https://tracker.example/1", [])[0])

    def test_tickets_need_a_definition_checklist_and_ticks(self):
        record = record_module()
        url = "https://github.com/acme/portal/issues/2"

        def issue(body, state="OPEN", labels=("status: in progress",), board=None, reason=None):
            return json.dumps({"body": body, "state": state, "stateReason": reason,
                               "labels": [{"name": name} for name in labels],
                               "projectItems": [{"status": {"name": board}}] if board else []})
        ticket = "### ✅ Definition of done\n- **A1:** x\n\n### ☑️ Checklist\n- [x] T1 a\n- [ ] T2 b\n"
        cases = [(record.needs_definition, issue("### 🎯 Purpose"), "Definition of done"),
                 (record.needs_definition, issue(ticket), None),
                 (record.needs_definition, issue("## ✅ Done when\n- A1: x"), None),
                 (record.needs_ticks, issue("### ✅ Definition of done"), "Checklist section"),
                 (record.needs_ticks, issue(ticket, state="CLOSED", reason="COMPLETED"), "1 unticked"),
                 (record.needs_checklist, issue("### ✅ Definition of done"), "Checklist section"),
                 (record.needs_ticks, issue("### 📥 Request\n- [ ] owner's own list\n\n### ☑️ Checklist\n- [x] T1 a\n"), None),
                 (record.needs_checklist, issue(ticket), None),
                 (record.needs_ticks, issue(ticket), "1 unticked"),
                 (record.needs_ticks, issue(ticket, labels=["status: blocked"]), None),
                 (record.needs_ticks, issue(ticket, board="Blocked"), None),
                 (record.needs_ticks, issue(ticket, state="CLOSED", reason="NOT_PLANNED"), None),
                 (record.needs_ticks, issue(ticket.replace("[ ]", "[x]")), None),
                 (record.needs_ticks, issue(ticket, labels=["status: backlog"]), None),
                 (record.needs_checklist, issue("### ✅ Definition of done", labels=["status: backlog"]), "Checklist section"),
                 (record.needs_checklist, issue("### ✅ Definition of done", labels=["status: blocked"]), None),
                 (record.needs_ticks, issue("## Checklist\n+ [x] T1 a\n1. [ ] T2 b\n2) [ ] T3 c\n## Next\n- [ ] x"), "2 unticked"),
                 (record.needs_checklist, issue("### Checklist\n```text\n- [ ] T1 example only\n```\n"), "Checklist section"),
                 (record.needs_ticks, issue(ticket, labels=()), "1 unticked"),  # a run ticket must carry its status
                 (record.needs_ticks, issue(ticket, labels=(), board="In progress"), "1 unticked"),
                 (record.needs_ticks, json.dumps({"body": "### Checklist\n- [ ] T1", "state": "OPEN",
                                                  "labels": ["oops", None, {"name": "status: in progress"}],
                                                  "projectItems": [None, "x", {"status": "Blocked"}]}), "1 unticked"),
                 (record.needs_ticks, json.dumps(["not", "an", "issue"]), "--offline")]
        for check, raw, expected in cases:
            with self.subTest(check=check.__name__, expected=expected), patch.object(record, "gh", return_value=raw):
                problems = record.ticket_problems([url, url], check)
                if expected:
                    self.assertEqual(len(problems), 1)
                    self.assertIn(expected, problems[0])
                    self.assertIn(url, problems[0])
                else:
                    self.assertEqual(problems, [])
        with patch.object(record, "gh", side_effect=RuntimeError("no network")):
            self.assertIn("--offline", record.ticket_problems([url], record.needs_ticks)[0])
        self.assertIn("--offline", record.ticket_problems(["https://tracker.example/1"], record.needs_ticks)[0])
        sections = {"tickets": f"**Epic:** {url}\n**Backlog:** none\n"}
        current, older = {"ticket_checks": True}, {}
        with patch.object(record, "gh", side_effect=AssertionError("offline steps and older runs never call gh")):
            self.assertEqual(record.online(current, {"offline": "no network", "all_sections": sections}, record.needs_ticks), [])
            self.assertEqual(record.online(older, {"offline": None, "all_sections": sections}, record.needs_ticks), [])
        with patch.object(record, "gh", return_value=issue(ticket)):
            self.assertIn("1 unticked", record.online(current, {"offline": None, "all_sections": sections}, record.needs_ticks)[0])
            handoff = "**Run:** x\n**Statuses:** x\n**Unverified:** x\n**Follow-ups:** x\n"
            self.assertIn("1 unticked", record.check_handoff(current, handoff, offline=None, all_sections=sections)[0])
            dropped = "https://github.com/acme/portal/issues/3"  # pinned at `done tickets`, later removed from the record
            self.assertEqual(len(record.online({**current, "tickets": [dropped]},
                                               {"offline": None, "all_sections": sections}, record.needs_ticks)), 2)
        with patch.object(record, "gh", return_value=issue("### ✅ Definition of done")):
            plan = "### Files\n### Critique\n### Phases\n### Todos\n### Whole plan\n**Logging:** x\n**Efficiency:** x\n"
            self.assertIn("Checklist section", record.check_plan(current, plan, offline=None,
                                                               all_sections={**sections, "plan": "### Todos\n- T1 a\n"})[0])
        epic = "https://github.com/acme/portal/issues/1"

        def tracker(*args):
            if args[0] == "api":
                return url + "\n" if args[1].endswith("sub_issues") else "1"
            return issue(ticket if args[2] == epic else "### 🎯 Purpose")
        with patch.object(record, "gh", side_effect=tracker):
            problems = record.check_tickets({**current, "kind": "feature"},
                                            f"**Epic:** {epic}\n**Sub-issue:** {url}\n**Backlog:** none\n")
            self.assertEqual(len(problems), 1)
            self.assertIn(url, problems[0])
            self.assertIn("Definition of done", problems[0])

    def test_coverage_names_every_requested_item_and_criterion(self):
        record = record_module()
        epic, url = "https://github.com/acme/portal/issues/1", "https://github.com/acme/portal/issues/2"

        def issue(body, labels=("status: in progress",)):
            return json.dumps({"body": body, "stateReason": None, "labels": [{"name": name} for name in labels],
                               "projectItems": []})
        ticket = ("### ✅ Definition of done\n- **A1 (R1):** booked\n- **A2:** full class refused\n\n"
                  "### ☑️ Checklist\nA2 comes later.\n- [x] T1 book (A1). Proof: booked\n")
        self.assertEqual(record.uncovered(ticket), ["A2"])  # prose outside task items names nothing
        self.assertEqual(record.uncovered(ticket + "- [ ] T2 refuse (A2)\n"), [])
        self.assertEqual(record.uncovered("## Done when\n- **D1:** x\n- **D2:** y\n## Checklist\n- [ ] T1 (D1, D2)"), [])
        self.assertEqual(record.uncovered("## Definition of done\n1. **A1:** x\n## Checklist\n- [ ] T1 (A2)"), ["A1"])
        wrapped = "## Definition of done\n- **A1:** x\n## Checklist\n- [ ] T1 build the form\n  and its API (A1)\n"
        self.assertEqual(record.uncovered(wrapped), [])
        self.assertNotIn("T1", record.items("## Checklist\n- [ ] T4 list (A1) needs #11 T1\n"))
        self.assertEqual(record.requested("**Requested:**\n**R1:** book\n**R2:** cancel\n**Backlog:** x"), ["R1", "R2"])
        on, older = {"coverage": True, "ticket_checks": True}, {"ticket_checks": True}
        with patch.object(record, "gh", return_value=issue(ticket)):
            self.assertIn("criteria no checklist item names: A2",
                          record.ticket_problems([url], record.covered(on, record.needs_ticks))[0])
            self.assertEqual(record.ticket_problems([url], record.covered(older, record.needs_ticks)), [])
        with patch.object(record, "gh", return_value=issue(ticket, labels=("status: blocked",))):
            self.assertEqual(record.ticket_problems([url], record.covered(on, record.needs_ticks)), [])
        listed = f"**Epic:** {epic}\n**Sub-issue:** {url}\n**Requested:**\n- R1 book\n- R2 waitlist\n**Backlog:** none\n"
        self.assertEqual(record.requested(listed), ["R1", "R2"])

        def tracker(*args):
            if args[0] == "api":
                return url + "\n" if args[1].endswith("sub_issues") else "1"
            return issue(ticket)
        with patch.object(record, "gh", side_effect=tracker):
            self.assertEqual(record.check_tickets({**on, "kind": "feature"}, listed),
                             ["requested items no listed ticket's criteria name: R2"])
        legacy = ticket.replace("- **A2:**", "- **R2:**")  # an old criterion ID is no requested-item label
        with patch.object(record, "gh", side_effect=lambda *args: tracker(*args) if args[0] == "api" else issue(legacy)):
            self.assertEqual(record.check_tickets({**on, "kind": "feature"}, listed),
                             ["requested items no listed ticket's criteria name: R2"])
        unnumbered = listed.replace("**Requested:**\n- R1 book\n- R2 waitlist\n", "")
        self.assertIn("'**Requested:**' line", record.check_tickets({**on, "kind": "feature"}, unnumbered, offline="x")[0])
        self.assertEqual(record.check_tickets({**older, "kind": "feature"}, unnumbered, offline="x"), [])
        light = {**on, "light": True, "kind": "change"}
        trivial = "**Ticket:** none (typo)\n**Backlog:** none\n"
        with patch.object(record, "gh", side_effect=AssertionError("a trivial change reads no tickets")):
            self.assertEqual(record.check_tickets(light, trivial), [])
        self.assertIn("'**Epic:** <url>'", record.check_tickets({**on, "kind": "change"}, trivial)[0])  # older methods
        both = f"**Epic:** {epic}\n**Ticket:** {url}\n**Backlog:** none\n"
        self.assertIn("keep only the '**Ticket:**' line", record.check_tickets(light, both, offline="x")[0])
        follow_up = {"tickets": f"**Ticket:** {url}\n**Backlog:** none\n", "plan": "### Todos\n- T3 refuse a full class\n"}

        def ticket_api(state):
            return lambda *args: "1" if args[0] == "api" else json.dumps({**json.loads(issue(ticket)), "state": state})
        with patch.object(record, "gh", side_effect=ticket_api("CLOSED")):
            self.assertIn("is closed: reopen", record.check_tickets(light, follow_up["tickets"])[0])
        with patch.object(record, "gh", side_effect=ticket_api("OPEN")):
            self.assertEqual(record.check_tickets(light, follow_up["tickets"]), [])
        plan = "**Success:** x\n### Todos\n- T3 refuse a full class\n"
        with patch.object(record, "gh", return_value=issue(ticket + "- [ ] T2 refuse (A2)\n")):
            self.assertEqual(record.check_plan(light, plan, offline=None, all_sections=follow_up),
                             ["plan todos no listed ticket's checklist holds: T3"])
        with patch.object(record, "gh", return_value=issue(ticket + "- [ ] T3 refuse (A2)\n")):
            self.assertEqual(record.check_plan(light, plan, offline=None, all_sections=follow_up), [])
        handoff = "**Run:** x\n**Statuses:** x\n**Unverified:** x\n**Follow-ups:** x\n"
        with patch.object(record, "gh", return_value=issue(ticket + "- [x] T2 refuse (A2). Proof: refused\n")):
            self.assertEqual(record.check_handoff(light, handoff, offline=None, all_sections=follow_up),
                             ["plan todos no listed ticket's checklist holds: T3"])  # drift during build
        finished = ticket + "- [x] T2 refuse (A2). Proof: refused\n"
        sections = {"tickets": listed, "plan": "### Todos\n- T1 book\n- T2 refuse\n"}
        with patch.object(record, "gh", return_value=issue(finished)):  # R2 lost its criterion label after tickets
            self.assertEqual(record.check_handoff({**on, "kind": "feature"}, handoff, offline=None, all_sections=sections),
                             ["requested items no listed ticket's criteria name: R2"])
        with patch.object(record, "gh", return_value=issue(finished.replace("**A2:**", "**A2 (R2):**"))):
            self.assertEqual(record.check_handoff({**on, "kind": "feature"}, handoff, offline=None, all_sections=sections), [])
        deferred = listed.replace("- R2 waitlist", "- R2 waitlist (owner-deferred: https://github.com/acme/portal/issues/3)")
        self.assertEqual((record.requested(deferred), record.requested(deferred, deferred=True)), (["R1"], ["R1", "R2"]))
        mark = "(owner-deferred: https://x.test/3)"
        for line, open_ids in ((f"R1 book, R2 pay {mark}, R3 cancel", ["R1", "R3"]),  # one line, middle item
                               (f"\n**R1:** book\n**R2:** pay {mark}", ["R1"]),  # label lines
                               (f"R1 book, R2 pay {mark}; see R2 again", ["R1"]),  # a later mention stays deferred
                               ("R1 book, R2 pay. Payments were owner-deferred to #6.", ["R1", "R2"]),  # prose is no mark
                               ("R3 packs (#4, mock checkout; real payments owner-deferred: https://x.test/6)", ["R3"]),
                               ("R2 pay (owner-deferred)", ["R2"]),  # the mark needs its decision link
                               ("R1 a, R2 pay (owner-deferred: [R2 call](https://x.test/3))", ["R1"])):  # markdown link
            with self.subTest(line=line):
                self.assertEqual(record.requested(f"**Requested:** {line}\n**Backlog:** x\n"), open_ids)
        self.assertEqual(record.requested(f"- **Requested:** R1 a, R2 b\n- **Backlog:** R3 {mark}\n"), ["R1", "R2"])
        with patch.object(record, "gh", return_value=issue(finished)):  # the owner's deferral needs no criterion
            self.assertEqual(record.check_handoff({**on, "kind": "feature"}, handoff, offline=None,
                                                  all_sections={**sections, "tickets": deferred}), [])
        only_deferred = "**Requested:** R1 book (owner-deferred: x)\n**Sub-issue:** u\n"
        self.assertNotIn("'**Requested:**' line", " ".join(record.check_tickets({**on, "kind": "feature"},
                                                                              only_deferred, offline="x")))

    def test_run_flags_follow_the_methods_the_run_reads(self):
        spec = importlib.util.spec_from_file_location("fast_gate_module", GATE)
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        layout, lane = Path(gate.LAYOUT), Path(gate.FAST_RUN)
        for name, texts in (("new", ("### ✅ Definition of done\nEvery criterion has an item.",
                                     "## Light lane\nT1 <title> → <what the owner can do once it is done>")),
                            ("old", ("### ✅ Done when", "## Hooks"))):
            for path, text in zip((layout, lane), texts):
                (self.root / name / path).parent.mkdir(parents=True, exist_ok=True)
                (self.root / name / path).write_text(text, encoding="utf-8")
        on = {"ticket_checks": True, "coverage": True, "light": True, "outcomes": True}
        off = dict.fromkeys(on, False)
        self.assertEqual(gate.method_flags({"root": str(self.root / "new")}, self.project), on)
        self.assertEqual(gate.method_flags({"root": str(self.root / "old")}, self.project), off)
        self.assertEqual(gate.method_flags({"root": str(self.root / "missing")}, self.project), off)
        self.assertEqual(gate.method_flags(None, self.project), on)
        self.assertEqual(gate.method_flags(None, SCRIPTS.parents[2]), on)  # this checkout's own methods define them
        (self.root / "new" / layout).write_bytes(b"\xff\xfe broken")
        self.assertEqual(gate.method_flags({"root": str(self.root / "new")}, self.project),
                         {**off, "light": True, "outcomes": True})  # fast-run.md still reads
        lucky = {"mode": "lucky", "kind": "change"}
        self.assertNotIn("done-run", gate.steps_for(lucky))
        self.assertIn("done-run", gate.steps_for({**lucky, "ticket_checks": True}))
        self.assertIn("done-run", gate.steps_for({"mode": "fast", "kind": "change"}))
        self.assertIn("analysis", gate.steps_for({"mode": "fast", "kind": "change"}))  # older methods keep it
        self.assertNotIn("analysis", gate.steps_for({"mode": "fast", "kind": "change", "light": True}))
        self.assertIn("analysis", gate.steps_for({"mode": "fast", "kind": "feature", "light": True}))


if __name__ == "__main__":
    unittest.main()
