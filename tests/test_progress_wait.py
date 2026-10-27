"""Current helper receipts in the owner view and status card."""
from datetime import datetime, timedelta, timezone
import json
import unittest

from test_fast_gate import GateHarness, module
from test_fast_report import item


wait, view, report = (module(name) for name in ("fast_wait", "fast_view", "fast_report"))
TICKET = "https://example.test/issues/11"


class ProgressWaitTests(GateHarness, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.start("--no-ui", "--no-data", kind="change")
        self.state_file = next((self.root / "home" / "runs").glob("*.json"))
        self.run = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.view_folder = self.root / "home" / "view"
        old = item(TICKET)
        old.update(next="Historical next action", waiting="Historical owner wait")
        self.run["owner_report"] = {**report.prepare({"version": 1, "items": [old]}, self.project, {TICKET}),
                                    "at": datetime.now(timezone.utc).isoformat()}
        self.save()

    def save(self):
        self.state_file.write_text(json.dumps(self.run), encoding="utf-8")

    def payload(self):
        now = datetime.now(timezone.utc)
        return {"version": 1, "coordinator": "s1", "job": "worker", "name": "Finite worker",
                "kind": "helper", "host": "codex", "wakeup": "native-subagent-result",
                "source": "spawn acknowledgement", "observed_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=1)).isoformat()}

    def projection(self):
        return view.write(self.view_folder, self.project, self.run,
                          ["tickets", "plan", "build", "done-run", "handoff"])

    def test_projection_tracks_pending_terminal_and_lifecycle(self):
        legacy = self.projection()
        self.assertIsNone(legacy["helperWait"])
        self.assertEqual((legacy["done"], legacy["total"]), (0, 0))
        identity = wait.add(self.root / "home", self.run, self.payload())
        pending = self.projection()["helperWait"]
        self.assertEqual(pending["pending"], ["Finite worker"])
        self.assertEqual((pending["finished"], pending["problems"]), ([], []))
        self.assertIn("Finite worker", pending["message"])
        wait.finish(self.root / "home", self.run,
                    {"version": 1, **identity, "status": "completed", "source": "native result"})
        terminal = self.projection()["helperWait"]
        self.assertEqual(terminal["pending"], [])
        self.assertEqual(terminal["finished"], ["Finite worker (completed)"])
        for change in ({"paused": {"reason": "Owner input", "at": datetime.now(timezone.utc).isoformat()}},
                       {"closed": True}):
            with self.subTest(change=change):
                self.assertIsNone(view.write(self.view_folder, self.project, {**self.run, **change},
                                             ["tickets", "plan", "build", "done-run", "handoff"])["helperWait"])

    def test_status_current_wait_hides_historical_report_fields(self):
        legacy = self.gate("status")
        self.assertIn("Historical next action", legacy)
        self.assertIn("Historical owner wait", legacy)
        wait.add(self.root / "home", self.run, self.payload())
        current = self.gate("status")
        self.assertIn("Waiting on helpers: Finite worker", current)
        self.assertNotIn("Historical next action", current)
        self.assertNotIn("Historical owner wait", current)
        self.assertIn("Next: tickets", current)
        self.assertNotIn("0/0", current)

    def test_completed_wait_restores_new_public_report(self):
        identity = wait.add(self.root / "home", self.run, self.payload())
        self.assertTrue(self.projection()["helperWait"]["suppressReport"])
        wait.finish(self.root / "home", self.run,
                    {"version": 1, **identity, "status": "completed", "source": "native result"})
        old = self.projection()["helperWait"]
        self.assertTrue(old["suppressReport"])
        self.assertIsNotNone(old["latest_completed_at"])
        self.assertNotIn("Historical next action", self.gate("status"))

        fresh = item(TICKET)
        fresh.update(next="Inspect the newly completed result", waiting="Owner feedback on the new result")
        payload = self.project / ".factory" / "new-report.json"
        payload.parent.mkdir(exist_ok=True)
        payload.write_text(json.dumps({"version": 1, "items": [fresh]}), encoding="utf-8")
        (self.project / ".factory" / "fast" / "work-record.md").write_text(
            "# Fixture\n\n## Tickets\n**Ticket:** " + TICKET + "\n", encoding="utf-8")
        self.assertIn(fresh["next"], self.gate("report", "--file", str(payload)))
        self.run = json.loads(self.state_file.read_text(encoding="utf-8"))
        current = self.projection()["helperWait"]
        self.assertFalse(current["suppressReport"])
        self.assertEqual(current["finished"], ["Finite worker (completed)"])
        status = self.gate("status")
        self.assertIn(fresh["next"], status)
        self.assertIn(fresh["waiting"], status)

    def test_invalid_report_time_keeps_terminal_directions_hidden(self):
        identity = wait.add(self.root / "home", self.run, self.payload())
        wait.finish(self.root / "home", self.run,
                    {"version": 1, **identity, "status": "completed", "source": "native result"})
        self.run["owner_report"]["at"] = "invalid"
        self.assertTrue(self.projection()["helperWait"]["suppressReport"])


if __name__ == "__main__":
    unittest.main()
