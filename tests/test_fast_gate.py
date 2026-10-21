"""Fast gate: real CLI and hook calls against disposable projects (fast-run.md#the-gate)."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
GATE = SCRIPTS / "fast_gate.py"
sys.path.insert(0, str(SCRIPTS))
import fast_proof  # noqa: E402  (the credit line every sample PR body ends with)
SAMPLE = Path(__file__).resolve().parents[1] / ".agents/skills/safe-engine/references/work-record-sample.md"
STEPS = ["research", "kickoff", "tickets", "analysis", "plan", "design", "schema", "build", "done-run", "handoff"]
ONLINE = ("tickets", "plan", "done-run", "handoff")  # steps that read the listed tickets through gh
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
**PR:** https://github.com/acme/site/pull/2 (body: .factory/fast/pr-body.md)
**Unverified:** none
**Follow-ups:** none
"""
PR_BODY = """## 🎬 Before & after

### 🦶 Footer: contact link reads "Contact us"

**Before:** "Contcat us" (base)
![before](https://github.com/acme/site/blob/0a1b2c3/footer-before.png?raw=true)
**After:** "Contact us" (head)
![after](https://github.com/acme/site/blob/0a1b2c3/footer-after.png?raw=true)

---
""" + fast_proof.CREDIT + "\n"


EVERYDAY = (  # commands an agent runs all day: never denied
    "npm test", "npm run build", "npm run dev", "git status", "git diff --stat", "git log --oneline -5", "git add -A",
    'git commit -m "fix: drop unused prod flag"', "git push", "git push -u origin feat/x", "git pull --rebase",
    "git checkout -b feat/x", "git rm --cached .env", "git rm -r --cached node_modules", "git stash list", "ls -la",
    "cat README.md", "rg \"DROP TABLE\" -n", "gh issue view 73", "python -m pytest -q", "node scripts/build.js",
    "npx prisma generate", "npx prisma migrate status", "rails db:migrate", "docker compose up -d",
    "docker compose logs web", "rm -rf node_modules dist", "rm -rf build/ .next/", "mkdir -p src/lib",
    "cp .env.example .env", "mv old.ts new.ts", 'find . -name "*.log" -not -path "./.git/*" -delete',
    "Remove-Item -Recurse -Force dist",
    "Get-ChildItem -Recurse src", 'Select-String -Pattern "dropdb" -Path *.md', 'psql -c "select count(*) from users"',
    'sqlite3 app.db ".tables"', "cd src && npm test", "export NODE_ENV=test && npm test",
    'echo "deploy to production later"', 'printf "%s\n" "rm -rf is denied"', "curl -s localhost:3000/health",
    "tsc --noEmit", "eslint . --fix", "go test ./...", 'git log --grep "migrate prod"', "wc -l src/*.ts",
)


WINDOWS_READING = (  # a backslash before a space is a path separator in PowerShell and cmd, not an escape
    "Remove-Item ..\\ -Recurse -Force", "ri ..\\other\\ -r -fo", "cd ..\\ ; Remove-Item -Recurse other",
    "cd ..\\ && rm -rf other", "Set-Location E:\\ ; Remove-Item -Recurse -Force x", 'cmd /c "cd /d E:\\ && rd /s /q x"',
)


def module(name):
    """A gate script loaded in-process."""
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def link(at, target):
    """A directory link the way agents make them: a junction on Windows, a symlink elsewhere."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(at))
    else:
        os.symlink(target, at)


class GateHarness:
    """A disposable project and gate home, with the real CLI and hook."""
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
        for log in self.root.glob("*/logs/gate.log"):  # every gate home a test used: the fail-open guard must never
            self.assertNotIn("hook.error", log.read_text(encoding="utf-8"))  # have swallowed an exception

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

    def pr_body(self):
        """The draft PR's body file the handoff's PR line names (read offline)."""
        (self.project / ".factory/fast").mkdir(parents=True, exist_ok=True)
        (self.project / ".factory/fast/pr-body.md").write_text(PR_BODY, encoding="utf-8")

    def finish_sample(self, text=None, until=None):
        """Record the sample (or `text`) and pass the steps before `until`, or all of them."""
        record = self.project / ".factory/fast/work-record.md"
        record.write_text(text or SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        shot = self.project / ".factory/fast/shots/schedule.png"
        shot.parent.mkdir(parents=True, exist_ok=True)
        shot.write_bytes(b"PNG")
        self.pr_body()
        for step in STEPS[:STEPS.index(until) if until else None]:
            self.gate("done", step, *(["--offline", "sample URLs"] if step in ONLINE else []))


class FastGateTests(GateHarness, unittest.TestCase):
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
        self.assertIn("added .factory/ to", output)
        self.assertIn(".factory/\n", (self.project / ".git/info/exclude").read_text(encoding="utf-8"))
        self.assertFalse((self.project / ".gitignore").exists())  # no project file changes
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

    def test_mvp_done_run_needs_the_three_scans_through_the_cli(self):
        self.start("--auth")
        scans = ("**Secrets:** `gitleaks dir .`: 0 findings\n**Dependencies:** `npm audit`: 0 vulnerabilities\n"
                 "**Static:** `eslint .`: 0 findings\n")
        bare = SAMPLE.read_text(encoding="utf-8").replace("**Size:** POC", "**Size:** MVP")
        self.finish_sample(bare, until="done-run")
        run = json.loads((self.project / ".factory/fast/run.json").read_text(encoding="utf-8"))
        self.assertEqual((run["size"][:3], run["size_at"]), ("MVP", "kickoff"))  # frozen when the kickoff passed
        for label in ("Secrets", "Dependencies", "Static"):
            self.assertIn(f"needs a '**{label}:**' line (Size MVP, frozen at kickoff)", self.gate("done", "done-run", "--offline", "sample URLs", ok=False))
        record = self.project / ".factory/fast/work-record.md"
        record.write_text(bare.replace("**Size:** MVP", "**Size:** POC"), encoding="utf-8")  # edited after the kickoff
        self.assertIn("'**Secrets:**' line (Size MVP, frozen at kickoff)", self.gate("done", "done-run", "--offline", "sample URLs", ok=False))
        record.write_text(bare.replace("no errors\n", "no errors\n" + scans, 1), encoding="utf-8")
        self.gate("done", "done-run", "--offline", "sample URLs")  # sample tickets are not readable

    def test_done_run_scans_apply_to_flagged_mvp_and_production_runs_only(self):
        record = module("fast_record")
        body, flagged = "- PASS x\n**Logs:** ok\n", {"scans": True}
        recorded = body + "**Secrets:** s scan\n**Dependencies:** d audit\n**Static:** t lint\n"
        needs = lambda cause: [f"needs a '**{label}:**' line ({cause})" for label in ("Secrets", "Dependencies", "Static")]
        sized = lambda size: {"kickoff": f"**Size:** {size}\n"}
        for size, word in (("MVP", "MVP"), ("`MVP` (it can go live)", "MVP"), ("Production slice", "PRODUCTION"),
                           ("POC→MVP", "MVP"), ("POC -> MVP (upgrade)", "MVP"), ("POC, production later", "PRODUCTION")):
            with self.subTest(size=size):  # a second size anywhere fails closed, and the refusal says why
                self.assertEqual(record.check_done_run(flagged, body, ".", all_sections=sized(size)),
                                 needs(f"Size {word}, in the record"))
                self.assertEqual(record.check_done_run(flagged, recorded, ".", all_sections=sized(size)), [])
        for size in ("POC (from the request)", "POC"):  # not scanned
            self.assertEqual(record.check_done_run(flagged, body, ".", all_sections=sized(size)), [])
        feature = {**flagged, "kind": "feature"}
        self.assertEqual(record.check_done_run(feature, body, ".", all_sections=sized("none (small feature)")), [])
        self.assertEqual(record.check_done_run(flagged, body, "."), [])  # a change run has no kickoff
        self.assertEqual(record.check_done_run({}, body, ".", all_sections=sized("MVP")), [])  # older methods unchanged
        lucky, in_tickets = {"scans": True, "mode": "lucky", "kind": "product"}, lambda size: {"tickets": f"**Size:** {size}\n"}
        self.assertEqual(record.check_done_run(lucky, body, ".", all_sections=in_tickets("MVP")),
                         needs("Size MVP, in the record"))  # no kickoff in Lucky
        self.assertEqual(record.check_done_run(lucky, recorded, ".", all_sections=in_tickets("MVP")), [])
        self.assertEqual(record.check_done_run(lucky, body, ".", all_sections=in_tickets("POC")), [])

    def test_the_size_frozen_in_the_ledger_outlives_the_record_line(self):
        record = module("fast_record")
        body = "- PASS x\n**Logs:** ok\n"
        needs = lambda cause: [f"needs a '**{label}:**' line ({cause})" for label in ("Secrets", "Dependencies", "Static")]
        for step in ("kickoff", "tickets", None):  # the refusal names where the size was frozen
            frozen = {"scans": True, "size": "MVP", **({"size_at": step} if step else {})}
            cause = f"Size MVP, frozen at {step}" if step else "Size MVP, frozen in the ledger"
            for edited in ({}, {"kickoff": "**Size:** POC\n"}, {"tickets": "**Backlog:** x\n"}):  # deleted or edited later
                self.assertEqual(record.check_done_run(frozen, body, ".", all_sections=edited), needs(cause))
        self.assertEqual(record.check_done_run({"scans": True, "size": "POC"}, body, ".", all_sections={}), [])
        self.assertEqual(record.check_done_run({"size": "MVP"}, body, ".", all_sections={}), [])  # older runs unchanged

    def test_scan_markers_name_a_real_result(self):
        record = module("fast_record")
        run, sections = {"scans": True}, {"kickoff": "**Size:** MVP\n"}
        ok = "**Dependencies:** npm audit: 0 vulnerabilities\n**Static:** eslint .: 0 findings\n"
        for value in ("skipped", "Skipped: no network", "n/a", "N/A", "na", "none", "todo", "TBD", "-", "**-**"):
            with self.subTest(value=value):
                problems = record.check_done_run(run, f"- PASS x\n**Logs:** ok\n**Secrets:** {value}\n{ok}", ".", all_sections=sections)
                self.assertEqual(len(problems), 1)
                self.assertIn("'**Secrets:**' needs the tool, the command and the result", problems[0])
        real = "none found by gitleaks (`gitleaks dir .`)"  # a result that starts with a placeholder word is still a result
        self.assertEqual(record.check_done_run(run, f"- PASS x\n**Logs:** ok\n**Secrets:** {real}\n{ok}", ".", all_sections=sections), [])

    def test_flagged_runs_refuse_a_size_the_scans_cannot_read(self):
        record = module("fast_record")
        flagged, older, body = {"scans": True, "kind": "product"}, {"kind": "product"}, "- PASS x\n**Logs:** ok\n"
        kickoff = "**Features:** a\n**Approach:** b\n**Answered by:** o\n**Stack:** s\n**Size:** {}\n"
        for size in ("An MVP (launch)", "small MVP", "Minimum viable product", "Prod slice", "production-ready POC",
                     "none (small feature)"):  # none (<why>) is a feature size
            with self.subTest(size=size):
                refused = record.check_kickoff(flagged, kickoff.format(size))
                self.assertIn("Size must start with POC, MVP, production, not", refused[0])
                done = record.check_done_run(flagged, body, ".", all_sections={"kickoff": kickoff.format(size)})
                self.assertTrue(any("Size must start with" in problem for problem in done))
                self.assertEqual(record.check_kickoff(older, kickoff.format(size)), [])  # older methods unchanged
        for size in ("POC", "MVP (launch)", "`Production` slice", "**MVP**"):
            self.assertEqual(record.check_kickoff(flagged, kickoff.format(size)), [], size)
        small = {"scans": True, "kind": "feature"}
        self.assertEqual(record.check_kickoff(small, kickoff.format("none (small feature)")), [])
        self.assertIn("or 'none (<why>)'", record.check_kickoff(small, kickoff.format("tiny"))[0])
        prose = "The **Size:** question was open.\n" + kickoff.format("MVP")  # the first value is the one parsed
        self.assertIn("Size must start with", record.check_kickoff(flagged, prose)[0])

    def test_lucky_runs_record_their_size_in_tickets(self):
        record = module("fast_record")
        tickets = ("**Epic:** https://github.com/acme/portal/issues/1\n**Backlog:** x\n"
                   "**Sub-issue:** https://github.com/acme/portal/issues/2\n")
        check = lambda run, extra="": record.check_tickets(run, tickets + extra, offline="no network")
        lucky = {"scans": True, "mode": "lucky", "kind": "product"}
        self.assertEqual(check(lucky), ["needs a '**Size:**' line"])
        self.assertIn("Size must start with", check(lucky, "**Size:** small MVP\n")[0])
        self.assertIn("Size must start with", check(lucky, "**Size:** none (small)\n")[0])  # a product needs a real size
        for size in ("MVP", "POC (default)"):
            self.assertEqual(check(lucky, f"**Size:** {size}\n"), [])
        self.assertEqual(check({**lucky, "kind": "feature"}, "**Size:** none (small feature)\n"), [])
        self.assertEqual(check({**lucky, "scans": False}), [])  # older methods unchanged
        self.assertEqual(check({**lucky, "mode": "fast"}), [])  # Fast runs size at the kickoff

    def test_offline_needs_unreadable_tickets_and_features_record_a_size(self):
        record = module("fast_record")
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
        record = module("fast_record")
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
            # redirects resolve where they run: after a cd, with ( ) restoring the folder
            f'cd "{self.root}" && echo x > out.txt': "allow", f'(cd "{self.root}"; echo x > out.txt)': "allow",
            f'(cd "{self.root}"); echo x > src/a.ts': "deny", "cd src && echo x > a.ts": "deny",
            f'cd "{self.root}" > src/log.txt': "deny", "cd - && echo x > a.ts": "deny",
        }
        for command, decision in cases.items():
            with self.subTest(command=command):
                self.assertEqual(self.pre("Bash", command=command), decision)
        into = f'cd "{self.project}" && echo x > src/a.ts'  # from outside the project, into it
        self.assertEqual(self.pre("Bash", cwd=self.root, command=into), "deny")

    def test_destructive_rules_decide_every_probe(self):
        gate = module("fast_gate")
        (self.project / "drop.sql").write_text("DROP TABLE users;", encoding="utf-8")
        (self.project / "safe.sql").write_text("select 1;", encoding="utf-8")
        encoded = base64.b64encode("Remove-Item -Recurse C:\\x".encode("utf-16-le")).decode()
        deny = (
            "rm -rf ~", "rm -rf /", "rm -r ..", f'rm -rf "{self.root}"', "rm -rf $HOME/x", "rd /s /q ..",
            "Remove-Item -Recurse -Force ..\\other", "rm -rf .", "rm -rf *", "rm -rf ./*", "rm -rfvi ..",
            "Remove-Item -Recurse:$true ..\\x", "find .. -delete", "find / -name x -exec rm {} +",
            "cd .. && rm -rf proj2", "cd /; rm -rf Users", "pushd .. && rm -rf x", "sl ..; rm -r x",
            "Set-Location ..; Remove-Item -Recurse x", "chdir .. && rm -rf x", "cd $UNSET_DIR_73 && rm -rf dist",
            "popd; rm -rf dist", "cd - && rm -rf dist", 'bash -c "rm -rf ~"', "sh -c 'rm -rf /'", 'eval "rm -rf ~"',
            "cmd /c rd /s /q C:\\Users", 'pwsh -Command "Remove-Item -Recurse -Force C:\\x"',
            'powershell -c "Remove-Item -Recurse C:\\x"', f"pwsh -EncodedCommand {encoded}", "pwsh -enc !!x",
            "timeout 10 rm -rf /", "time rm -rf /", "nice -n 5 rm -rf /", "doas rm -rf /", "sudo -u root rm -rf /",
            "env -i rm -rf /", 'bash -c "git push -f"', "git push --force", "git push -f origin x",
            "git push origin +x", "git push --force-with-lease origin main", "git push --force-with-lease",
            "git push --force-with-lease origin HEAD", "git push --mirror", "git push origin :main",
            "git push origin --delete main", 'psql -c "DROP TABLE users"', "mysql app -e 'truncate orders'",
            "sqlite3 app.db <<'EOF'\ndrop table x;\nEOF", 'mongosh --eval "db.users.drop()"', 'echo "DROP TABLE x"|psql',
            'psql<<<"DROP TABLE x"', "psql < drop.sql", "dropdb app", "rails db:drop", "npx prisma migrate reset",
            "npx prisma migrate reset --force", "RAILS_ENV=production rails db:migrate", "MIX_ENV=prod mix ecto.migrate",
            "npx prisma migrate deploy --env production", "flask db upgrade --env production",
            "DATABASE_URL=$PROD_DATABASE_URL npx prisma migrate deploy", "rake db:schema:load RAILS_ENV=production",
            # round 2: reserved words and groups, framework wipes, carried env, stdin-fed shells, cheap gaps
            "if [ -d ../proj2 ]; then rm -rf ../proj2; fi", "for d in a; do rm -rf ..; done", "{ rm -rf ..; }",
            "! rm -rf ..", "cd sub && { cd ../..; rm -rf proj2; }", "if true; then git push -f; fi", "{ git push -f; }",
            "if true; then dropdb app; fi", "if (Test-Path ..\\proj2) { Remove-Item -Recurse -Force ..\\proj2 }",
            "try { Remove-Item -Recurse -Force C:\\Users\\x } catch {}", "(cd .. && rm -rf proj2)",
            'powershell -command "& {Remove-Item -Recurse -Force ..}"', "docker exec db dropdb app",
            "php artisan migrate:fresh", "php artisan db:wipe", "mix ecto.reset", "mix ecto.drop",
            "python manage.py flush",
            "supabase db reset", "npx prisma db push --force-reset", "rails db:purge", "npx typeorm schema:drop",
            "export RAILS_ENV=production && rails db:migrate", "$env:RAILS_ENV='production'; rails db:migrate",
            "set RAILS_ENV=production && rails db:migrate", "bash <<'EOF'\nrm -rf ~\nEOF", "bash -s <<< 'rm -rf /'",
            "echo 'rm -rf ~' | bash", "echo 'git push -f' | sh", "echo 'Remove-Item -Recurse C:\\x' | pwsh",
            "cat <<'EOF' | zsh\nrm -rf ..\nEOF", "echo 'rm -rf ~' |& bash", "Remove-Item -Recurse -Path:..",
            "rd /s/q ..", "rimraf ..", "npx rimraf ../x", "Push-Location ..; Remove-Item -Recurse x",
            "builtin cd .. && rm -rf x", "su -c 'rm -rf /'", "start cmd /c rd /s /q C:\\Users",
            "powershell Remove-Item -Recurse -Force ..", "psql -f drop.sql", "eval " * 1200 + "ls", "rm -rf ../a\x00b",
            "rm -rf .factory", "rm -rf .factory/*",
            # round 3: substitutions and groups, remote and container strings, piped SQL files, attached options
            "git push origin $(git branch --show-current) -f", 'psql $(cat .dburl) -c "DROP TABLE x"',
            "DATABASE_URL=$(heroku config:get DATABASE_URL -a shop-production) npx prisma migrate deploy",
            "Remove-Item -Recurse -Force (Resolve-Path ..\\proj2)", "Remove-Item (Join-Path $PSScriptRoot '..\\proj2') -Recurse -Force",
            "Remove-Item -Recurse -Force -Path @('..\\proj2','dist')",
            """docker exec -it db sh -c "psql -U postgres -c 'DROP DATABASE app'\"""",
            """docker compose exec db bash -c 'psql -c "DROP SCHEMA public CASCADE"'""",
            """kubectl exec -it pg-0 -- sh -c "psql -c 'TRUNCATE users'\"""", """ssh db1 "psql -c 'DROP TABLE users'\"""",
            'ssh deploy@prod-1 "cd /app && bundle exec rails db:migrate RAILS_ENV=production"',
            'docker compose exec web sh -c "RAILS_ENV=production rails db:migrate"', "cat drop.sql | psql",
            "cat drop.sql | docker compose exec -T db psql -U postgres", "Get-Content drop.sql | psql",
            "type drop.sql | sqlcmd", 'mysql -e"DROP TABLE x"', "psql --file=drop.sql", "psql -fdrop.sql",
            'sqlite3 app.db ".read drop.sql"', "npx prisma db execute --file drop.sql",
            'npx wrangler d1 execute shop --command "DROP TABLE x"', 'mysqlsh -e "DROP TABLE x"',
            'iex "rm -rf ~"', 'Invoke-Expression "Remove-Item -Recurse -Force C:\\x"',
            'Start-Process pwsh -ArgumentList "-c","Remove-Item -Recurse C:\\x"', "rm -rf .factory/fast", "find . -delete",
            "find .factory -delete", "find -L .. -delete", "find . -exec rm -rf {} +", "pnpm dlx rimraf ..",
            "yarn dlx rimraf ..", "npm exec -- rimraf ..", "pnpm exec rimraf ..", "rm -rf ../my\\ dir", "rm -rf .git",
            "rm -rf `pwd`/../x", "echo 'ls' | bash -c 'rm -rf ~'",
            # round 4: piped or fed text, braces, PowerShell lists, git clean, ledger, find from the root
            'echo "DROP TABLE users;" | docker exec -i db psql -U postgres',
            "printf 'DROP TABLE x;' | npx prisma db execute --stdin",
            "docker compose exec -T db psql <<'EOF'\nDROP TABLE users;\nEOF",
            "kubectl exec -i pg-0 -- psql <<EOF\nDROP TABLE users;\nEOF",
            'echo "DROP TABLE x;" | python manage.py dbshell', 'echo "DROP TABLE x;" | rails dbconsole',
            "ssh prod-1 <<'EOF'\nrm -rf /srv/app\nEOF", "echo 'rm -rf /srv/app' | ssh prod-1 bash",
            "echo 'rm -rf ~' | docker exec -i web sh", "rm -rf build/{cjs,esm} ~", "rm -rf apps/{web,api}/dist /",
            "rm -rf node_modules/{.cache,.vite} ~/.npm", "rm -rf packages/{a,b}/dist ../shared/dist",
            "rm -rf dist{/../../other,}", "rm -rf x{a ~", "Remove-Item -Recurse -Force dist,..\\other",
            "Remove-Item -Recurse -Force node_modules,..\\other\\node_modules", "git clean -fdx", "git clean -fdX",
            "git clean -ffdx", "git clean -x -f", "rm -rf .factory/fast/run.json", "rm -f .factory/fast/run.json",
            "find . -type f -delete", "find . -name '*' -exec rm -rf {} +",
            "find .git -name '*.pack' -delete", "find . -name run.json -delete", "rm -rf .git/objects",
            *WINDOWS_READING,
            # round 5: wildcards reaching protected paths, moves, stash --all, unproven root finds, --prune, --file -
            "rm -rf .[!.]*", "rm -rf .??*", "rm -rf .git*", "rm -rf .fact*", "rm -rf .[gf]*", "rm -rf .*/",
            "rm -rf .factory/f*", "rm -rf .factory/fast/run*", "Remove-Item -Recurse -Force .\\.f*",
            "rm -f .factory/fast/*", "rm .factory/fast/*.json", "del /q .factory\\fast\\*",
            "Remove-Item .factory\\fast\\* -Force", "rm -rf */", "rm -rf .git/obj*", "mv .factory/fast/run.json /tmp/x",
            "Move-Item .factory .factory.old", "ren .factory old", "Rename-Item .git old", "mv .git* /tmp",
            "mv notes.md .factory/fast/run.json", "git stash --all", "git stash -a", "git stash push --all",
            "find . ! -name '*.md' -path '*/.git/*' -delete", "find . -not -name '*.md' -delete",
            "find . -name '*.pyc' -o -delete", "find . -name '*.pyc' -path './.git/*' -delete",
            "find . -name 'run*' -delete", "find . -iname 'FAST' -exec rm -rf {} +", "rm -rf .git/objects",
            "git push --prune origin main:main", "psql --file - <<'EOF'\nDROP TABLE x;\nEOF",
        )
        allow = (
            "rm -rf dist node_modules", "Remove-Item -Recurse dist", "rm -f ../x.txt", "rm -rf dist 2> /dev/null",
            "rm -rf dist > /tmp/log.txt", "rm -rf $PWD/dist", "rm -rf ${PWD}/dist", "rm -rf src/*", "rm -r -Force dist",
            "Remove-Item -Recurse:$false ..\\x", "find src -name '*.pyc' -delete", "cd src && rm -rf build",
            f'cd .. && cd "{self.project.name}" && rm -rf dist', 'bash -c "rm -rf dist"', "pwsh -File build.ps1",
            "git push", "git push origin feature", "git push --force-with-lease origin feature",
            "git push --force-with-lease origin HEAD:feature", "git push origin --delete feature",
            'grep "DROP TABLE" schema.sql', "echo truncate", 'gh issue create --body "psql DROP x"',
            'psql -c "select 1"; echo "we will drop the cache later"', "psql < safe.sql", "psql < missing.sql",
            "RAILS_ENV=test rails db:migrate", "npm run migrate -- --env local", "grep -rn migrate src/ | grep prod",
            "MIX_ENV=test mix ecto.migrate", 'rm -rf "unclosed',  # unparsable: fails open
            "if true; then rm -rf dist; fi", "{ cd src; rm -rf build; }", "(cd ..); rm -rf dist", 'echo "rm -rf ~"',
            "cat script.sh | bash", "export RAILS_ENV=test && rails db:migrate", "psql -f safe.sql",
            "Remove-Item -Recurse -Path:dist", "npx rimraf dist", "rm -rf $(pwd)/dist",
            'cd "$(git rev-parse --show-toplevel)" && rm -rf dist', "rm -rf .factory/fast/shots", "rm -rf \x007\x00",
            # round 3: message and search text, names holding prod, escaped spaces
            'grep -rn "dropdb" scripts/', 'git commit -m "Remove the db:reset task"', "rm -rf my\\ dir",
            'gh pr create --title "Drop prod flag" --body "Removes rm -rf ~ and DROP TABLE calls"',
            "npx prisma migrate dev --name add_prod_flag", "find .factory -name '*.tmp' -delete",
            """git commit -m "$(cat <<'EOF'\nfix: stop rm -rf ~ and git push -f\nEOF\n)\"""",
            "echo 'rm -rf ~' | tee notes.txt", 'echo "DROP TABLE x" > notes.txt',
            "cat > notes.md <<'EOF'\nrm -rf ~ and DROP TABLE x\nEOF",
            "gh issue create --title t --body-file - <<'EOF'\npsql -c 'DROP TABLE x'; rm -rf ~\nEOF",
            "rm -rf build/{cjs,esm}", "rm -rf apps/{web,api}/dist", "Remove-Item -Recurse -Force dist,build",
            "git clean -fd", "git clean -n", "git rm -r --cached .", 'git commit -am "drop table cleanup, rm -rf old"',
            'git commit -qm "git push -f fixed"', 'gh pr create -t "DROP TABLE x" -b "rm -rf ~"',
            'glab mr create --description "rm -rf ~ and DROP TABLE x"', "rm -f .git/index.lock",
            "find . -name '*.pyc' -not -path './.git/*' -delete", "find .factory -name '*.tmp' -delete",
            # round 5: routine finds, plain wildcards, moves, stashes, stale lock, git messages from stdin
            "find . -name '*.pyc' -delete", "find . -name __pycache__ -type d -exec rm -rf {} +",
            "find . -name node_modules -type d -prune -exec rm -rf '{}' +", "find . -name .DS_Store -delete",
            "find . -maxdepth 1 -name '*.tmp' -delete", "rm -f *.log", "rm -rf dist/*", "mv old.ts new.ts",
            "Move-Item src\\a.ts src\\b.ts", "git stash", "git stash -u", "git stash list", "rm -rf .git/index.lock",
            "git commit --file - <<'EOF'\nrm -rf ~\nEOF", "git commit --file=- <<'EOF'\nDROP TABLE x\nEOF",
            "git push --prune origin",
            # interpreter code is never a shell move: its "move" or 'mv' text is data
            "py -3 - <<'EOF'\n# move the line\nprint(open('.factory/fast/work-record.md').read())\nEOF",
            "python -c \"print(open('.factory/x').read().replace('mv', 'cp'))\"", 'node -e "// rename .git refs"',
        ) + EVERYDAY
        root = gate.norm(str(self.project))
        judge = gate.sibling("fast_guard").Judge(root, gate.norm, gate.inside)
        for command in deny + allow:
            with self.subTest(command=command[:80]):
                self.assertEqual(bool(judge.rule(command, root)), command in deny)
        self.assertIn("cannot be resolved after a directory change (dist)", judge.rule("popd; rm -rf dist", root))
        for command in WINDOWS_READING:  # a PowerShell or cmd reading denies; the Bash reading alone sees no delete
            with self.subTest(dialect=command):
                self.assertTrue(judge.rule(command, root, "windows"))
        self.assertIsNone(judge.rule("rm -rf my\\ dir", root, "bash"))
        other = self.root / "proj2"  # the cwd's own run judges, not the session's bound run
        runs = [(None, {"sessions": ["s1"]}, {"project": str(self.project)}), (None, {}, {"project": str(other)})]
        self.assertIsNone(gate.guard("rm -rf dist", runs, gate.norm(str(other)), "s1"))

    def scratch(self, out):
        """The scratch folder a start or scratch command printed (its path may hold spaces)."""
        line = next(line for line in out.splitlines() if line.startswith("Scratch: "))
        return Path(line[len("Scratch: "):line.index(" (the run's")])

    def shell(self, command, tool="Bash"):
        out = self.hook({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"command": command}})
        return (out or {}).get("hookSpecificOutput", {}).get("permissionDecision", "allow")

    def test_run_scratch_folder_takes_throwaway_deletes_and_goes_at_close(self):
        out = self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "fix the footer copy")
        scratch = self.scratch(out)
        self.assertTrue(scratch.is_dir())
        self.assertEqual(scratch.parent, self.root / "home" / "scratch")  # in the gate home, outside every project
        self.assertEqual(self.gate("scratch").strip(), str(scratch))
        (scratch / "profile" / "deep").mkdir(parents=True)
        (scratch / "profile" / "deep" / "lock").write_text("x", encoding="utf-8")
        os.chmod(scratch / "profile" / "deep" / "lock", 0o444)  # read-only, as browser and Git files often are
        other, beside = self.root / "home" / "scratch" / "other-0-20990101000000", self.root / "op-temp"
        for folder in (other, beside):
            folder.mkdir(parents=True)
        for command, tool in ((f'rm -rf "{scratch / "profile"}"', "Bash"), (f'rm -rf "{scratch}"/*', "Bash"),
                              (f'rm -rf "{scratch}"', "Bash"), (f'find "{scratch}" -name "*.db" -delete', "Bash"),
                              (f'rd /s /q "{scratch / "profile"}"', "PowerShell"),
                              (f'rimraf "{scratch / "profile"}"', "PowerShell")):
            with self.subTest(allow=command):
                self.assertEqual(self.shell(command, tool), "allow")
        for command, tool in ((f'rm -rf "{other}"', "Bash"), (f'rm -rf "{scratch}/../{other.name}"', "Bash"),
                              (f'rm -rf "{beside}"', "Bash"), (f'rm -rf "{self.root / "home" / "scratch"}"', "Bash"),
                              (f'rm -rf "{scratch}" "{beside}"', "Bash"),
                              (f'find -L "{scratch}" -name "*.db" -delete', "Bash"),  # follows links out
                              (f'Remove-Item -Recurse -Force "{scratch / "profile"}"', "PowerShell"),  # walks junctions
                              (f'rm -r -fo "{scratch / "profile"}"', "PowerShell"), (f'del /s /q "{scratch}"', "PowerShell"),
                              (f'rd "{scratch / "x"}" -Recurse -Exclude /s', "PowerShell"),  # Remove-Item in disguise
                              (f'rm -r "{scratch}"/*/', "Bash"), (f'rm -r "{scratch}"/*/data', "Bash"),  # via a link
                              (f'find "{scratch}" -type l -exec rm -rf "{{}}/" ";"', "Bash"),
                              (f'rm -r "{scratch / "a"}" && ln -s "{beside}" "{scratch / "a"}" && rm -r "{scratch / "a" / "b"}"', "Bash"),
                              (f'rd /s /q "{scratch}" & mklink /J "{scratch}" "{beside}" & rd /s /q "{scratch / "b"}"', "PowerShell"),
                              (f'ln --sym "{beside}" "{scratch / "a"}" && rm -rf "{scratch / "a" / "b"}"', "Bash"),
                              (f'New-Item -Type SymbolicLink -Path "{scratch / "a"}" -Target "{beside}"; rd /s /q "{scratch / "a" / "b"}"', "PowerShell"),
                              (f'New-Item -ItemType:HardLink -Path "{scratch / "a"}" -Target "{beside}"; rd /s /q "{scratch / "a" / "b"}"', "PowerShell"),
                              (f'mount -o bind "{beside}" "{scratch / "a"}" && rm -rf "{scratch / "a" / "b"}"', "Bash"),
                              (f'find "{scratch}" -name x -exec rm -rf {{}} "{beside}" ";"', "Bash"),  # a path beside {}
                              (f'rm -rf "$HOME/{scratch.name}"', "Bash"),
                              (f'find . -name x -exec rm -rf {{}} "{beside}" \\;', "Bash"),  # inside the project too
                              (f'New-Item -it j -Path "{scratch / "a"}" -Target "{beside}"; rd /s /q "{scratch / "a" / "b"}"', "PowerShell"),
                              (f'find "{scratch}" -exec rm -rf + "{beside}" ";"', "Bash")):  # + after no {} is an argument
            with self.subTest(deny=command):
                self.assertEqual(self.shell(command, tool), "deny")
        out = self.gate("close", "--abandon", "owner stopped it")
        self.assertFalse(scratch.exists())
        self.assertTrue(other.is_dir())  # another run's folder stays
        self.assertNotIn("left", out)
        self.assertNotEqual(self.scratch(self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "again")),
                            scratch)  # a new start never reuses an old run's folder

    def test_no_command_hides_behind_an_escaped_semicolon_or_a_find_wrapper(self):
        self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "fix the footer copy")
        for command, tool in (("echo x\\; rm -rf ~", "Bash"), ("printf x\\\\;rm -rf ~", "Bash"),
                              ("echo \\\\; git push --force origin main", "Bash"),
                              ("Write-Output x\\; Remove-Item -Recurse -Force C:\\victim", "PowerShell"),
                              ("find . -maxdepth 0 -exec sh -c 'rm -rf ~' \\;", "Bash"),
                              ("find . -exec env rm -rf ~ \\;", "Bash"), ("find . -exec sudo rm -rf {} /victim \\;", "Bash"),
                              ("find . -exec find /victim -delete \\;", "Bash")):
            with self.subTest(deny=command):
                self.assertEqual(self.shell(command, tool), "deny")
        for command in ("find . -name __pycache__ -type d -exec rm -rf {} +", "find . -name '*.pyc' -exec rm {} \\;"):
            with self.subTest(allow=command):  # routine cleanups still pass
                self.assertEqual(self.shell(command), "allow")

    def test_scratch_never_trusts_a_link_or_a_stored_path(self):
        victim = self.root / "victim"
        (victim / "keep").mkdir(parents=True)
        (victim / "keep" / "data.txt").write_text("x", encoding="utf-8")
        scratch = self.scratch(self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "fix it"))
        state = next((self.root / "home" / "runs").glob("*.json"))
        data = json.loads(state.read_text(encoding="utf-8"))
        state.write_text(json.dumps({**data, "scratch": str(victim)}), encoding="utf-8")  # a mirror's stored path
        self.assertEqual(self.shell(f'rm -rf "{victim}"'), "deny")
        scratch.rmdir()
        link(scratch, victim)  # the folder swapped for a link: the allowance must not follow it
        self.assertEqual(self.shell(f'rm -rf "{victim / "keep"}"'), "deny")
        self.assertEqual(self.shell(f'rm -rf "{scratch / "keep"}"'), "deny")
        self.gate("close", "--abandon", "owner stopped it")
        self.assertTrue((victim / "keep" / "data.txt").exists())  # close removed the link, not its target
        self.assertFalse(os.path.lexists(scratch))
        scratch = self.scratch(self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "again"))
        link(scratch / "inner", victim)  # a link inside goes as a link
        self.gate("close", "--abandon", "owner stopped it")
        self.assertTrue((victim / "keep" / "data.txt").exists())
        self.assertFalse(scratch.exists())

    def test_closing_a_lost_run_removes_its_scratch_folder(self):
        scratch = self.scratch(self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "fix it"))
        (scratch / "profile").mkdir()
        other = self.root / "proj2"
        other.mkdir()
        elsewhere = self.scratch(self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "same key",
                                           project=other))
        self.assertNotEqual(elsewhere.parent / elsewhere.name.rsplit("-", 1)[0], scratch.parent / scratch.name.rsplit("-", 1)[0])
        for state in (self.root / "home" / "runs").glob("*.json"):
            if json.loads(state.read_text(encoding="utf-8"))["project"] == str(self.project):
                state.unlink()  # the run's state is lost
        self.assertIn("without a readable run state", self.gate("close", "--abandon", "state lost"))
        self.assertFalse(scratch.exists())
        self.assertTrue(elsewhere.is_dir())  # the other project's run under the same key keeps its folder

    def test_destructive_denial_reaches_the_owner_in_every_step(self):
        self.assertEqual(self.pre("Bash", command="rm -rf ~"), "allow")  # no run: unchanged
        self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "fix the footer copy")
        out = self.hook({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm -rf ~"}})
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]  # gate closed: owner advice, not steps
        self.assertIn("recursive delete outside the project (~). Destructive commands are the owner's", reason)
        self.assertNotIn("Record these steps", reason)
        self.assertEqual(self.pre("Bash", command="git push"), "allow")
        crafted = "echo \x007\x00; " + "eval " * 1200 + "ls"  # stray placeholder, deep nesting: denied, no hook.error
        self.assertEqual(self.pre("Bash", command=crafted), "deny")
        log = (self.root / "home/logs/gate.log").read_text(encoding="utf-8")
        self.assertEqual(log.count('"hook.deny"'), 2)
        self.assertTrue(all(json.loads(line) for line in log.splitlines()))  # long fields cut, lines stay JSON

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

    def test_stop_passes_while_a_background_agent_runs(self):
        self.start()
        stop = {"hook_event_name": "Stop", "stop_hook_active": False, "session_crons": []}
        agent = {"id": "a", "type": "subagent", "status": "running", "agent_type": "general-purpose"}
        server = {"id": "b", "type": "shell", "status": "running", "command": "npm run dev"}
        waiting = self.hook({**stop, "background_tasks": [server, agent]}) or {}  # progress may ride along
        self.assertNotIn("decision", waiting)  # its result starts a new turn
        self.assertEqual(self.hook({**stop, "background_tasks": [server]})["decision"], "block")  # may never end
        self.assertEqual(self.hook({**stop, "background_tasks": []})["decision"], "block")  # the work ends here
        log = (self.root / "home/logs/gate.log").read_text(encoding="utf-8")
        self.assertEqual((log.count('"hook.wait_stop"'), log.count('"hook.block_stop"')), (1, 2))

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

    def test_hidden_checks_accept_only_strict_entries(self):
        record = module("fast_record")
        on = {"kind": "feature", "hidden_checks": True}
        check = lambda text, run=on: " ".join(record.check_done_run(
            run, "- PASS booked\n**Hidden checks:** " + text + "\n**Logs:** clean\n", project=".", all_sections={}))
        unreadable = ["#2 A1: PASS, #2 A2 did not pass", "#2 A1: PASS\n#2 A2 not passing (exit 1)",
                      "#2 A2 expected PASS, got FAIL", "\n- #2 A2 bad index passes to the error handler: FAIL",
                      "\n- #2 A2 passing an empty title is rejected: ❌", "#2 A2 FAILS", "#2 A2: ✗", "\n| FAIL | #2 A2 |",
                      "\n| #2 | A2 | PASS |", "A1: PASS, A2: PASS", "#2 A1: pass", "#2 A1: PASS (ok), note",
                      "#2 A1: PASS\n\nall good"]
        for text in unreadable:
            self.assertIn("unreadable hidden-check entry", check(text), text)
        self.assertIn("FAIL (#2 A2): back to build", check("#2 A1: PASS\n**Hidden checks:** #2 A2: FAIL"))
        self.assertIn("FAIL (#2 A2)", check("\n- #2 A1: PASS\n\n- #2 A2: FAIL (exit 1)"))
        self.assertIn("'**Hidden checks:**' block", check(""))
        for text in ("#2 A1: PASS, #2 A2: PASS", "\n- #2 A1: PASS (FAIL on first run, fixed)\n\n* #3 A1: PASS",
                     "#2 A1: PASS (#3 is unrelated)", "\n- [x] #2 A1: PASS\n1. #2 A2: PASS (check changed: wrong path)",
                     "#2 A1: PASS\n- **Notes:** a bulleted label ends the block"):
            self.assertEqual(check(text), "", text)
        only_hidden = record.check_done_run(on, "**Hidden checks:** #2 A1: PASS\n**Logs:** y\n", project=".",
                                            all_sections={})
        self.assertEqual(only_hidden, ["needs >=1 PASS result"])  # the builder's own done-run stays required
        for run in ({**on, "kind": "change"}, {"kind": "product"}):  # change runs and older methods: old rule
            self.assertEqual(" ".join(record.check_done_run(run, "- PASS x\n**Logs:** y\n", project=".")), "")

    def test_hidden_checks_cover_every_listed_criterion_online(self):
        record = module("fast_record")
        text = SAMPLE.read_text(encoding="utf-8")
        sections = record.sections(text)
        dod = "### Definition of done\n- **A1 (R1):** works\n- **A2:** fails safely\n"
        read = lambda url: {"url": url, "body": dod, "stopped": url.endswith("/9"), "backlog": False}
        run = {"kind": "product", "hidden_checks": True, "ticket_checks": True,
               "tickets": ["https://github.com/acme/studio-booking/issues/9"]}  # Blocked: needs no PASS
        check = lambda body, **kw: " ".join(record.check_done_run(run, body, project=".", all_sections=sections, **kw))
        done = sections["done-run"]
        with patch.object(record, "read_ticket", side_effect=read):
            self.assertEqual(check(done), "")
            no_epic = "\n".join(line for line in done.splitlines() if not line.startswith("- #1 "))
            self.assertIn("without a hidden-check PASS: #1 A1, #1 A2", check(no_epic))
            self.assertIn("#5 A2", check(done.replace(", #5 A2: PASS", "")))
        self.assertEqual(check(done.replace(", #5 A2: PASS", ""), offline="no network"), "")  # offline: >=1 entry

    def test_hidden_checks_gate_the_sample_done_run(self):
        self.start("--no-ui")
        text = SAMPLE.read_text(encoding="utf-8")
        record_file = self.project / ".factory/fast/work-record.md"
        self.assertIn("Hidden checks block", record_file.read_text(encoding="utf-8"))
        record_file.write_text(text.replace("#4 A2: PASS", "#4 A2: FAIL"), encoding="utf-8")
        for step in ("research", "kickoff", "tickets", "analysis", "plan", "schema", "build"):
            self.gate("done", step, *(["--offline", "sample URLs"] if step in ONLINE else []))
        self.assertIn("FAIL (#4 A2): back to build", self.gate("done", "done-run", "--offline", "sample", ok=False))
        record_file.write_text(text, encoding="utf-8")
        self.gate("done", "done-run", "--offline", "sample URLs")

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
        self.pr_body()
        for step in ("plan", "build", "done-run", "handoff"):
            self.gate("done", step, *(["--offline", "no network"] if step == "handoff" else []))
        self.assertIn("Next: close", self.gate("status"))

    def test_ticket_links_are_checked_against_the_epic(self):
        record = module("fast_record")
        epic = "https://github.com/acme/portal/issues/1"
        linked = "https://github.com/acme/portal/issues/2\n"
        with patch.object(record, "gh", side_effect=["1", linked]):
            self.assertEqual(record.verify_tickets(epic, ["https://github.com/acme/portal/issues/2"]), [])
        with patch.object(record, "gh", side_effect=["1", linked]):
            self.assertIn("not linked", record.verify_tickets(epic, ["https://github.com/acme/portal/issues/9"])[0])
        self.assertIn("--offline", record.verify_tickets("https://tracker.example/1", [])[0])

    def test_tickets_need_a_definition_checklist_and_ticks(self):
        record = module("fast_record")
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
        record = module("fast_record")
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
        layout, lane, ux, pr = Path(gate.LAYOUT), Path(gate.FAST_RUN), Path(gate.UX), Path(gate.PR)
        for name, texts in (("new", ("### ✅ Definition of done\nEvery criterion has an item.",
                                     "## Light lane\nT1 <title> → <what the owner can do once it is done>\n**Hidden checks:**\n**Secrets:**\n`**PR:**`",
                                     "| U10 | Performance |", "ends with the credit line in `references/credit.md`")),
                            ("old", ("### ✅ Done when", "## Hooks", "| Performance |", "No AI or tool attribution"))):
            for path, text in zip((layout, lane, ux, pr), texts):
                (self.root / name / path).parent.mkdir(parents=True, exist_ok=True)
                (self.root / name / path).write_text(text, encoding="utf-8")
        on = {"ticket_checks": True, "coverage": True, "light": True, "outcomes": True, "hidden_checks": True, "scans": True,
              "ux_rules": True, "pr_proof": True, "credit": True}
        off = dict.fromkeys(on, False)
        self.assertEqual(gate.method_flags({"root": str(self.root / "new")}, self.project), on)
        self.assertEqual(gate.method_flags({"root": str(self.root / "old")}, self.project), off)
        self.assertEqual(gate.method_flags({"root": str(self.root / "missing")}, self.project), off)
        self.assertEqual(gate.method_flags(None, self.project), on)
        self.assertEqual(gate.method_flags(None, SCRIPTS.parents[2]), on)  # this checkout's own methods define them
        (self.root / "new" / layout).write_bytes(b"\xff\xfe broken")
        self.assertEqual(gate.method_flags({"root": str(self.root / "new")}, self.project),
                         {**off, "light": True, "outcomes": True, "hidden_checks": True, "scans": True,
                          "ux_rules": True, "pr_proof": True, "credit": True})  # fast-run.md, ux-quality, PR still read
        lucky = {"mode": "lucky", "kind": "change"}
        self.assertNotIn("done-run", gate.steps_for(lucky))
        self.assertIn("done-run", gate.steps_for({**lucky, "ticket_checks": True}))
        self.assertIn("done-run", gate.steps_for({"mode": "fast", "kind": "change"}))
        self.assertIn("analysis", gate.steps_for({"mode": "fast", "kind": "change"}))  # older methods keep it
        self.assertNotIn("analysis", gate.steps_for({"mode": "fast", "kind": "change", "light": True}))
        self.assertIn("analysis", gate.steps_for({"mode": "fast", "kind": "feature", "light": True}))

    def test_ux_rules_need_brief_lines_and_one_verdict_per_rule(self):
        record = module("fast_record")
        skill = (SCRIPTS.parents[2] / ".agents/skills/ux-quality/SKILL.md").read_text(encoding="utf-8")
        table = re.findall(r"(?m)^\| (U\d+) \| ([^|]+?) \|", skill)
        self.assertEqual(table, list(zip(record.UX_RULES, record.UX_AREAS)))  # gate and method agree
        sections = record.sections(SAMPLE.read_text(encoding="utf-8"))
        design, done = sections["design"], sections["done-run"]
        on, old = {"ux_rules": True}, {}
        self.assertEqual(record.check_design(on, design), [])
        self.assertIn("needs a '**Map:**' line", record.check_design(on, design.replace("**Map:**", "Map:")))
        self.assertIn("primary action", " ".join(record.check_design(on, design.replace("primary", "main"))))
        bare = re.sub(r"(?m)^\*\*(?:Map|Hierarchy|Labels):\*\*.*\n", "", design)
        self.assertEqual(record.check_design(old, bare), [])  # older methods keep the old brief
        hierarchy = "**Hierarchy:** " + record.marker(design, "Hierarchy")
        for under in ("**Hierarchy:**\n- schedule: primary Book", "**Hierarchy:**\n| screen | primary |\n|---|---|\n| a | b |"):
            with self.subTest(under=under):  # "primary" may sit in the lines or table under the label
                self.assertEqual(record.check_design(on, design.replace(hierarchy, under)), [])
        for labels in ("- **Labels:** primary Book;", "2. **Labels:** primary Book;"):
            with self.subTest(labels=labels):  # the block ends at the next marker, bulleted or numbered
                unnamed = design.replace(hierarchy, "**Hierarchy:** schedule: Book first").replace("**Labels:**", labels)
                self.assertIn("primary action", " ".join(record.check_design(on, unnamed)))
        self.assertEqual(record.ux_audit(done), [])
        for layout in ("| **U1** | PASS |", "- **U1:** PASS", "| U1 | Map | PASS |", "- U1 Map: PASS"):
            with self.subTest(layout=layout):
                self.assertEqual(record.ux_audit(done.replace("- U1 PASS", layout)), [])
        self.assertIn("needs a 'U2 ", " ".join(record.ux_audit("- U1 to U10 PASS all fine\n**UX judge:** x\n")))
        for mixed, problem in (("- U3 FAIL schedule, PASS roster: two filled", "U3 FAIL is open"),
                               ("- U3 PASS schedule, FAIL roster: two filled", "U3 FAIL is open"),
                               ("- U3 N/A desktop, FAIL phone: no bar", "U3 FAIL is open"),
                               ("- U3 FAIL keyboard, N/A touch: focus lost", "U3 FAIL is open"),
                               ("- U3 partial PASS: some screens", "needs a 'U3 ")):
            with self.subTest(mixed=mixed):  # no other verdict word hides the line's FAIL or vague verdict
                self.assertIn(problem, " ".join(record.ux_audit(done.replace("- U3 PASS schedule", mixed))))
        u3 = re.search(r"(?m)^- U3 PASS .*$", done).group(0)
        def opened(text):
            return sorted({problem.split()[0] for problem in record.ux_audit(text) if " FAIL is open" in problem})
        for where in ("\n  - roster: FAIL two filled", "\nroster FAILED the blur test", "\n\n  roster FAILED the blur test",
                      "; roster FAILED", "; roster FAILS the blur test", "\n- U3 – FAIL roster", "\n> U3 FAIL roster",
                      "\n### U3 FAIL roster", " (recheck; was FAIL: two filled)", "\n  **Recheck:** roster FAILED",
                      "\n**Judge:** two filled, FAIL"):
            with self.subTest(where=where):  # an open FAIL never passes, wherever it is written, and touches no other rule
                self.assertEqual(opened(done.replace(u3, u3 + where)), ["U3"])
        message = " ".join(record.ux_audit(done.replace(u3, "- U3 FAIL roster: two filled")))
        self.assertIn("one final verdict line with no FAIL, FAILS or FAILED", message)
        contested = "- U3 UNKNOWN contested, builder: a popover"
        for reasons in (": judge FAIL on the modal", "\n  - judge: U3 FAIL on the modal", "\n  - U3 FAIL modal (judge)"):
            with self.subTest(reasons=reasons):  # a contested FAIL may quote its own rule's FAIL in or under its line
                self.assertEqual(record.ux_audit(done.replace(u3, contested + reasons)), [])
        self.assertEqual(opened(done.replace(u3, contested + "\n  - U4 FAIL roster")), ["U4"])  # not another rule's
        for sibling in ("  - U3 UNKNOWN no keyboard\n  - U3 FAIL roster", "\t- U3 UNKNOWN no keyboard\n    - U3 FAIL roster"):
            with self.subTest(sibling=sibling):  # a sibling FAIL is no reason, with tabs or spaces
                self.assertEqual(opened(done.replace(u3, sibling)), ["U3"])
        self.assertIn("U3 UNKNOWN needs its evidence or reason",  # a quote's own ID and verdict are no reason
                      record.ux_audit(done.replace(u3, "- U3 UNKNOWN\n  U3 PASS")))
        for kept in ("; a failed booking shows a retry", "\n  one filled button per view, checked twice",
                     "\n  **Logs:** 0 FAILED requests", "\n  - **Logs:** 0 FAILED requests",
                     "\n- FAIL then fixed: test user u2 could not join"):
            with self.subTest(kept=kept):  # lowercase and indented evidence, markers and test users stay accepted
                self.assertEqual(record.ux_audit(done.replace(u3, u3 + kept)), [])
        cases = {"- U4 PASS": ("- U4x PASS", "needs a 'U4 "), "- U3 PASS schedule": ("- U3 FAIL schedule", "U3 FAIL is open"),
                 "**UX judge:**": ("UX judge:", "'**UX judge:**' line")}
        for old_text, (new_text, problem) in cases.items():
            with self.subTest(problem=problem):
                self.assertIn(problem, " ".join(record.ux_audit(done.replace(old_text, new_text))))
        u10 = re.search(r"(?m)^- U10 .*$", done).group(0)
        self.assertIn("U10 N/A needs its evidence or reason", record.ux_audit(done.replace(u10, "- U10 N/A")))
        scanned = done.replace(u10, u10 + "\n**Static:** semgrep, 0 FAILED rules")  # the scan markers end a verdict too
        self.assertEqual(record.ux_audit(scanned), [])
        self.assertEqual(record.check_done_run(old, "- PASS app works\n**Logs:** clean\n", project=self.project), [])
        self.assertEqual(record.check_done_run(old, "- U1 PASS login works\n**Logs:** ok\n", project=self.project), [])
        rule_lines = record.HIDDEN.sub("", "\n".join(line for line in done.splitlines() if not line.startswith("- PASS")))
        for extra in ("- U3 recheck after fix: PASS roster", "- After the fix, U3 PASS roster",
                      "**UX judge:** U1 to U9 PASS, U10 UNKNOWN", "**UX judge:**\nfresh agent; all ten rules PASS",
                      "  -**UX judge:** all ten rules PASS", "- [x] **UX judge:** all ten rules PASS",
                      "- ***UX judge:*** all ten rules PASS", "- U1 PASS schedule\n  roster: PASS too",
                      "- U1 PASS schedule\n**Recheck:** PASS"):
            with self.subTest(extra=extra):  # on a UI run rule lines and the judge line never count as using it
                self.assertIn("needs >=1 PASS result", record.check_done_run(
                    {"ux_rules": True, "ui": True}, rule_lines + "\n" + extra + "\n", project=self.project))
        self.assertNotIn("needs >=1 PASS result", record.check_done_run(  # a test user is not a rule
            {"ux_rules": True, "ui": True}, rule_lines + "\n- PASS u1 books a class\n", project=self.project))
        self.assertEqual(record.check_done_run({"ux_rules": True}, "- U1 PASS login works\n**Logs:** ok\n",
                                               project=self.project), [])  # no UI owed: its lines count as before

    def test_ui_file_changes_need_the_ux_audit(self):
        repo, app = self.project, self.project / "app"  # the run's project is a folder inside the repository
        git = ["git", "-C", str(repo)]
        app.mkdir()
        subprocess.run(git + ["init", "-q"], check=True)
        for name, text in (("app/server.py", "x = 1\n"), ("style.css", "a {}\n"), ("app/view.vue", "<template/>\n")):
            (repo / name).write_text(text, encoding="utf-8")
        subprocess.run(git + ["add", "."], check=True)
        subprocess.run(git + ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"], check=True)
        (app / "notes.html").write_text("<p>draft</p>\n", encoding="utf-8")  # untracked before the run starts
        self.gate("start", "--key", "copy-fix", "--kind", "change", "--request", "fix the footer copy", project=app)
        run = json.loads((app / ".factory/fast/run.json").read_text(encoding="utf-8"))
        head = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual((run["base"], list(run["ui_seen"]), run["ui"]), (head, ["notes.html"], False))
        record = module("fast_record")
        done = record.sections(LIGHT)["done-run"]
        (app / "server.py").write_text("x = 2\n", encoding="utf-8")
        (repo / "style.css").write_text("a { color: red }\n", encoding="utf-8")  # outside the run's project
        (app / "Footer.test.tsx").write_text("test('x', () => {})\n", encoding="utf-8")
        self.assertEqual(record.check_done_run(run, done, project=app), [])  # no UI file of its own: no audit
        (app / "notes.html").unlink()  # a file that was already untracked, now deleted by this run
        problems = record.check_done_run(run, done, project=app)
        self.assertEqual(problems[0], "this run changed UI files (notes.html): record the UX audit")
        self.assertIn("needs a 'U1 ", " ".join(problems))
        (app / "Footer.tsx").write_text("export const Footer = () => null\n", encoding="utf-8")
        self.assertEqual(record.ui_files({**run, "ui_seen": {}}, app), ["Footer.tsx"])
        for base in ("123", 123, "-p", "0" * 40):  # unknown or tampered start commit: every tracked UI file counts
            with self.subTest(base=base):
                self.assertEqual(record.ui_files({"base": base}, app), ["view.vue"])
        self.assertEqual(record.ui_files({"base": head}, self.root / "not a repo"), [])
        for seen in ([], "x", 5):  # a damaged snapshot never crashes `done`
            with self.subTest(seen=seen):
                self.assertEqual(record.ui_files({"base": head, "ui_seen": seen}, self.root / "not a repo"), [])
        self.gate("close", "--abandon", "test", project=app)
        self.gate("start", "--key", "with-ui", "--kind", "change", "--ui", "--request", "restyle", project=app)
        ui_run = json.loads((app / ".factory/fast/run.json").read_text(encoding="utf-8"))
        self.assertNotIn("base", ui_run)  # --ui runs skip the start-time git calls


if __name__ == "__main__":
    unittest.main()
