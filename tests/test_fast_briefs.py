"""Briefs (fast-run.md#briefs): plan Interface, Ports and UX rules lines, ports no other open lane holds, DEFERRED
owner or hardware items, and the before/after `shots` command."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
GATE = SCRIPTS / "fast_gate.py"
PLAN = """## Tickets
**Ticket:** none (lane test)
**Backlog:** searched "lane": nothing open
## Plan
**Success:** the lane serves.
**Ports:** {ports}
### Todos
- T1 Serve the lane → open it and see it
## Build log
"""


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


record, briefs, shots = module("fast_record"), module("fast_briefs"), module("fast_shots")


class BriefsTests(unittest.TestCase):
    def plan(self, body, **run):
        return briefs.plan_problems({"briefs": True, **run}, body, record.marker, record.subsection)

    def test_plan_names_interface_ports_and_ux_rules(self):
        full = "### Interface\n`book(id)`; route `/schedule`\n**Ports:** app 5281\n**UX rules:** U1 to U10, docs/RULES.md\n"
        self.assertEqual(self.plan(full, ui=True), [])
        self.assertEqual(briefs.plan_problems({}, "", record.marker, record.subsection), [])  # older methods: none
        missing = " ".join(self.plan("", ui=True))
        for label in ("### Interface", "**Ports:**", "**UX rules:**"):
            self.assertIn(label, missing)
        self.assertIn("U1 to U10", " ".join(self.plan(full.replace("U1 to U10", "U3"), ui=True)))
        self.assertEqual(self.plan(full.replace("**UX rules:** U1 to U10, docs/RULES.md\n", "")), [])  # no UI
        self.assertEqual(briefs.plan_problems({"briefs": True}, "**Ports:** none (cli)", record.marker,
                                              record.subsection, light=True), [])  # light lane: Ports only

    def test_ports_are_read_from_the_line(self):
        self.assertEqual(briefs.ports("app http://localhost:5281, hub 8791; spare 8792, app again 5281"), [5281, 8791, 8792])
        for line, wanted in (("none (no server)", []), ("none; existing preview 8877", []),
                             ("none (no server); references: 8877", []), ("app 5281.", [5281]),
                             ("app 5281.5", [])):
            with self.subTest(line=line):
                self.assertEqual(briefs.ports(line), wanted)
        for tail in ("app 5281", "existing preview 8877; app 5180", "existing preview 8877, app 5180"):
            self.assertIn("contradicts", " ".join(self.plan("**Ports:** none; " + tail, light=True)))
        self.assertEqual(briefs.ports("v1.2.3000 and 80 and 70000"), [])

    def test_compact_journey_still_requires_a_minimum(self):
        body = "\n".join(f"**{key}:** {value}" for key, value in {
            "UI kit": "existing #112233 #223344 #334455 #445566", "Font": "existing", "Logo": "existing",
            "Icons": "existing", "Layout": "existing", "Theme": "light", "Journeys": "Inspect:2actions,0loads,min2"}.items())
        self.assertEqual(record.check_design({}, body), [])
        self.assertIn("counts and a minimum", " ".join(record.check_design({}, body.replace("min2", "unknown"))))

    def test_another_lanes_ports_are_refused(self):
        run = {"project": "/w/lane-b"}
        others = [(None, None, {"key": "lane-a", "project": "/w/lane-a", "ports": [5281, 8791]}),
                  (None, None, {"key": "lane-b", "project": "/w/lane-b", "ports": [5281]})]  # itself
        found = briefs.clashes(run, briefs.ports("app 5281. spare 8891."), others)
        self.assertEqual(len(found), 1)
        self.assertIn("5281", found[0])
        self.assertIn("lane-a", found[0])
        self.assertEqual(briefs.clashes(run, [5381], others), [])

    def test_deferred_hidden_checks_read_only_on_briefs_runs_with_a_reason(self):
        body = "**Hidden checks:**\n- #2 A1: PASS, #2 A2: DEFERRED (hardware: needs a second OS)\n**Logs:** x"
        entries, unreadable = record.verdicts(body, deferred=True)
        self.assertEqual((entries, unreadable), ([("2", "A1", True), ("2", "A2", True)], []))
        self.assertEqual(record.verdicts(body)[1], ["- #2 A1: PASS, #2 A2: DEFERRED (hardware: needs a second OS)"])
        for note in ("DEFERRED", "DEFERRED (later)", "DEFERRED (owner: )"):
            self.assertTrue(record.verdicts(f"**Hidden checks:**\n#2 A2: {note}\n", deferred=True)[1], note)
        self.assertEqual(record.verdicts("**Hidden checks:**\n#2 A2: FAIL (x)\n", deferred=True)[0], [("2", "A2", False)])

    def test_handoff_lists_every_deferred_item_once(self):
        done = "**Hidden checks:**\n#2 A2: DEFERRED (hardware: needs a device), #3 A1: PASS\n"
        problems = lambda body: briefs.handoff_problems({"briefs": True}, body, record.marker, done)
        self.assertIn("'**Deferred:**' line", problems("**Run:** x")[0])
        self.assertIn("#2 A2", problems("**Deferred:** none")[0])
        self.assertEqual(problems("**Deferred:** #2 A2 device run (hardware)"), [])
        self.assertEqual(briefs.handoff_problems({}, "", record.marker, done), [])
        handoff = "**Run:** x\n**Statuses:** x\n**Unverified:** x\n**Follow-ups:** x\n**Deferred:** none\n"
        prose = "- PASS the demo printed `#2 A2: DEFERRED (hardware: x)`\n**Hidden checks:**\n#2 A1: PASS\n"
        self.assertEqual(record.check_handoff({"briefs": True}, handoff, all_sections={"done-run": prose}), [])
        self.assertIn("#2 A2", record.check_handoff({"briefs": True}, handoff, all_sections={"done-run": done})[0])

    def test_a_deferred_checklist_item_does_not_hold_the_ticket(self):
        body = ("### ✅ Definition of done\n- **A1:** x\n\n### ☑️ Checklist\n- [x] T1 a\n"
                "- [ ] T2 run it on the second OS (A1) DEFERRED (hardware: needs a second OS)\n")
        ticket = {"url": "https://github.com/o/r/issues/2", "body": body, "stopped": False, "backlog": False}
        self.assertIsNone(record.needs_ticks(ticket, deferred=True))
        self.assertIn("1 unticked", record.needs_ticks(ticket))
        undeferred = {**ticket, "body": body.replace("DEFERRED (hardware: needs a second OS)", "")}
        self.assertIn("1 unticked", record.needs_ticks(undeferred, deferred=True))


class LaneTests(unittest.TestCase):
    """Two worktree lanes through the real gate: the second may not take the first one's ports."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="lanes ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.env = dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "home"), GH_CONFIG_DIR=str(self.root / "gh"))

    def gate(self, project, *args, ok=True):
        result = subprocess.run([sys.executable, str(GATE), *args, "--project", str(project)], capture_output=True,
                                text=True, encoding="utf-8", env=self.env)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def lane(self, name, ports):
        project = self.root / name
        project.mkdir()
        self.gate(project, "start", "--key", name, "--kind", "change", "--no-ui", "--no-data", "--request", "serve")
        (project / ".factory/fast/work-record.md").write_text(PLAN.format(ports=ports), encoding="utf-8")
        self.gate(project, "done", "tickets", "--offline", "test")
        return project

    def test_parallel_lanes_get_their_own_ports(self):
        self.gate(self.lane("lane-a", "app 5281, hub 8791"), "done", "plan", "--offline", "test")
        second = self.lane("lane-b", "app 5281, hub 8891")
        self.assertIn("5281 belong to open run 'lane-a'", self.gate(second, "done", "plan", "--offline", "test", ok=False))
        (second / ".factory/fast/work-record.md").write_text(PLAN.format(ports="app 5381, hub 8891"), encoding="utf-8")
        self.gate(second, "done", "plan", "--offline", "test")


class ShotsTests(unittest.TestCase):
    def test_names_ports_and_browser(self):
        self.assertEqual([shots.slug(p) for p in ("/", "/settings/Team", "?tab=2")], ["home", "settings-team", "tab-2"])
        self.assertEqual(shots.parse_ports("5281,5282"), [5281, 5282])
        for bad in ("5281,5281", "5281", "80,81"):
            self.assertIsNone(shots.parse_ports(bad))
        self.assertEqual(len(set(shots.parse_ports(None))), 2)
        self.assertEqual(shots.find_browser(sys.executable), sys.executable)

    def test_phase_keeps_early_baseline_and_rejects_drift(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        import json
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            args = SimpleNamespace(phase="after", path=["/"], size="640x240", serve="serve", setup=None)
            with self.assertRaises(FileNotFoundError):
                shots.phased(args, root, "browser", None, root, root, [5281, 5282])
            args.phase = "before"
            image = root / "home-before.png"
            image.write_bytes(b"early")
            with patch.object(shots, "capture", return_value=[("/", str(image))]):
                shots.phased(args, root, "browser", None, root, root, [5281, 5282])
                with self.assertRaisesRegex(ValueError, "already exists"):
                    shots.phased(args, root, "browser", None, root, root, [5281, 5282])
                args.phase = "after"
                shots.phased(args, root, "browser", None, root, root, [5281, 5282])
                args.size = "800x600"
                with self.assertRaisesRegex(ValueError, "conditions changed"):
                    shots.phased(args, root, "browser", None, root, root, [5281, 5282])
                args.size = "640x240"
                image.write_bytes(b"replacement")
                with self.assertRaisesRegex(ValueError, "Before image changed"):
                    shots.phased(args, root, "browser", None, root, root, [5281, 5282])

    @unittest.skipUnless(shots.find_browser(None), "no Chromium-family browser on this machine")
    def test_base_and_head_are_shot_on_their_own_ports(self):
        temp = tempfile.TemporaryDirectory(prefix="shots ")
        self.addCleanup(temp.cleanup)
        project, home = Path(temp.name) / "site", Path(temp.name) / "home"
        project.mkdir()
        git = lambda *args: subprocess.run(["git", "-C", str(project), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                                           check=True, capture_output=True)
        (project / "index.html").write_text("<h1>before</h1>", encoding="utf-8")
        git("init", "-q")
        git("add", "index.html")
        git("commit", "-qm", "base")
        (project / "index.html").write_text("<h1 style='color:#070'>after, longer</h1>", encoding="utf-8")
        serve = f'"{sys.executable}" -m http.server {{port}} --bind 127.0.0.1'
        result = subprocess.run([sys.executable, str(GATE), "shots", "--project", str(project), "--base", "HEAD",
                                 "--serve", serve, "--path=/", "--size", "640x240"], capture_output=True, text=True,
                                env=dict(os.environ, SAFE_ENGINE_HOME=str(home)), timeout=300)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        before, after = (project / ".factory/fast/shots" / f"home-{side}.png" for side in ("before", "after"))
        self.assertNotEqual(before.read_bytes(), after.read_bytes())
        self.assertNotIn("detached", subprocess.run(["git", "-C", str(project), "worktree", "list"], capture_output=True,
                                                    text=True).stdout)  # the base checkout is gone


if __name__ == "__main__":
    unittest.main()
