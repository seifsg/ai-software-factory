"""New-run lifecycle and hook regression checks; all ticket/host metadata is synthetic."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from safe_engine.distribution import active_selection
from test_fast_gate import module
import test_tickets as ticket_fixtures


class SafeSelectionTests(unittest.TestCase):
    def test_cancelled_ticket_releases_selection_but_unknown_or_active_evidence_does_not(self):
        fixture = ticket_fixtures.TicketTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.start()
        self.assertIn("named Safe", active_selection(fixture.root))
        fixture.flow.cancel("Synthetic lifecycle cancellation")
        self.assertIsNone(active_selection(fixture.root))
        state = fixture.flow.load()
        # A released claim alone cannot prove a completed handoff.
        state["phase"] = "ready"
        fixture.flow.persist(state, "Synthetic ready but not handed off")
        self.assertIn("named Safe", active_selection(fixture.root))
        fixture.flow.persist(state, "Prepared checked local handoff")
        self.assertIn("named Safe", active_selection(fixture.root))
        (fixture.flow.directory / "handoff.md").write_text(f"Run: {state['run_id']}\n")
        self.assertIsNone(active_selection(fixture.root))
        fixture.store.claim("alpha", state["run_id"], fixture.flow.directory)
        self.assertIn("named Safe", active_selection(fixture.root))
        fixture.store.release("alpha", state["run_id"])
        state["pending_operation"] = {"operation": "checks"}
        fixture.flow.persist(state, "Prepared checked local handoff")
        self.assertIn("named Safe", active_selection(fixture.root))
        state["pending_operation"] = None
        fixture.flow.persist(state, "Prepared checked local handoff")
        (fixture.flow.directory / "state.json").write_text("{broken")
        self.assertIn("named Safe", active_selection(fixture.root))


class HookSelectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.entry, self.gate = module("fast_entry"), module("fast_gate")
        self.project = self.root / "project"
        self.target = self.root / "bundle/skills/safe-engine/scripts/fast_gate.py"
        self.target.parent.mkdir(parents=True)
        self.target.write_text("# pinned gate fixture")
        self.run = (self.root / "registration", {"sessions": ["bound"]},
                    {"project": str(self.project), "bundle": {"root": str(self.root / "bundle"), "revision": "a" * 40}})

    def event(self, name="PreToolUse", session="unbound", **args):
        raw = {"cwd": str(self.root), "session_id": session, "hook_event_name": name, **args}
        return raw, self.gate.sibling("fast_hosts").read("codex", raw)

    def test_absolute_edit_and_bound_stop_execute_the_pinned_gate(self):
        cases = [self.event(tool_name="Write", tool_input={"file_path": str(self.project / "a.py")}),
                 self.event("Stop", "bound"),
                 self.event(tool_name="Bash", tool_input={"command": f'echo value > "{self.project / "a.py"}"'})]
        for raw, event in cases:
            with self.subTest(event=raw), patch.object(self.entry.subprocess, "run") as call:
                call.return_value.returncode = 0
                self.assertEqual(self.entry.hook("codex", raw, event, [self.run], self.gate), 0)
                self.assertEqual(call.call_args.args[0][1], str(self.target.resolve()))
                self.assertEqual(json.loads(call.call_args.kwargs["input"]), raw)

    def test_mixed_factories_deny_once_without_recursive_dispatch(self):
        other = (self.root / "other-registration", {}, {"project": str(self.root / "other"), "bundle": None})
        raw, event = self.event(tool_name="apply_patch", tool_input={"input":
            f'*** Update File: {self.project / "a.py"}\n*** Update File: {self.root / "other/b.py"}'})
        output = StringIO()
        with redirect_stdout(output), patch.object(self.entry.subprocess, "run") as call:
            self.assertEqual(self.entry.hook("codex", raw, event, [self.run, other], self.gate), 0)
        call.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")
