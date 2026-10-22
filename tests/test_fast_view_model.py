"""Owner dashboard facts preserve evidence, scope and missing-information boundaries."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
spec = importlib.util.spec_from_file_location("dashboard_view", SCRIPTS / "fast_view.py")
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)
model, facts, card = view.model, view.facts, view.card
import fast_hosts as hosts  # noqa: E402 - fast_view installs the sibling module path


def report(label, value):
    """Write the documented record shape, including explicit JSON nulls."""
    return f"**{label}:** {json.dumps(value)}\n"


def child(**changes):
    """A small valid report for lifecycle and boundary cases."""
    return {"id": "worker", "title": "Preview", "task": "Check interactions", "status": "working",
            "updated": "2026-10-22T09:00:00Z", **changes}


class DashboardFactsTests(unittest.TestCase):
    def test_only_explicit_boolean_milestones_define_percentage(self):
        value = {"id": "preview", "title": "Test a useful dashboard", "milestones": [
            {"id": "visual", "title": "Clear overview", "done": True},
            {"id": "qa", "title": "Usable controls", "done": False}]}
        result = model.metadata({"plan": report("Goal", value)})
        self.assertEqual((result["goal"]["done"], result["goal"]["total"], result["goal"]["pct"]), (1, 2, 50))
        self.assertEqual(result["goal"]["basis"], "recorded-milestones")
        value["milestones"][0]["done"] = False
        self.assertEqual(model.metadata({"plan": report("Goal", value)})["goal"]["pct"], 0)

    def test_legacy_plain_and_empty_goals_never_invent_progress(self):
        legacy = model.metadata({"plan": "**Success:** Build the app", "build log": "**Now:** T1"})
        self.assertIsNone(legacy["goal"])
        self.assertIsNone(legacy["nextTest"])
        self.assertEqual(legacy["subsessions"], [])
        self.assertEqual(legacy["metadataErrors"], [])
        for line in ("**Goal:** A useful app", report("Goal", {"title": "A useful app"}),
                     report("Goal", {"title": "A useful app", "milestones": []})):
            with self.subTest(line=line):
                goal = model.metadata({"plan": line})["goal"]
                self.assertIsNone(goal["pct"])
                self.assertEqual(goal["total"], 0)
                self.assertEqual(goal["basis"], "title-only")

    def test_invalid_goal_evidence_is_rejected_with_safe_diagnostics(self):
        milestone = {"id": "a", "title": "Visible outcome", "done": True}
        invalid = [{"title": None}, {"title": ""}, {"title": "Goal", "milestones": None},
                   {"title": "Goal", "milestones": [{**milestone, "done": "false"}]},
                   {"title": "Goal", "milestones": [{**milestone, "done": 1}]},
                   {"title": "Goal", "milestones": [milestone, milestone]}]
        for value in invalid:
            with self.subTest(value=value):
                result = model.metadata({"plan": report("Goal", value)})
                self.assertIsNone(result["goal"])
                self.assertEqual(len(result["metadataErrors"]), 1)
        result = model.metadata({"plan": '**Goal:** {"private-test-payload": broken'})
        self.assertNotIn("private-test-payload", " ".join(result["metadataErrors"]))

    def test_next_test_uses_only_recorded_expectations_and_last_report(self):
        first = report("Next test", {"title": "Old preview", "estimate": "Tomorrow"})
        last = report("Next test", {"title": "Current preview", "when": "After controls pass",
                                    "feedback": "Can you find the goal?"})
        result = model.metadata({"plan": first + last})["nextTest"]
        self.assertEqual(result, {"title": "Current preview", "when": "After controls pass",
                                  "feedback": "Can you find the goal?", "estimate": ""})
        for value in (None, [], {}, {"title": ""}, {"title": "Preview", "estimate": None}):
            with self.subTest(value=value):
                invalid = model.metadata({"plan": report("Next test", value)})
                self.assertIsNone(invalid["nextTest"])
                self.assertEqual(len(invalid["metadataErrors"]), 1)

    def test_child_lifecycle_keeps_last_report_and_explicit_parent(self):
        log = report("Session", child()) + report("Session", child(status="blocked", parent="coordinator"))
        log += report("Session", child(status="finished", parent="coordinator", updated="2026-10-22T09:01:00Z"))
        rows = model.metadata({"build log": log})["subsessions"]
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["status"], rows[0]["parent"], rows[0]["source"]),
                         ("finished", "coordinator", "record"))
        self.assertEqual(rows[0]["updated"], 1792659660000)

    def test_invalid_child_status_time_and_null_are_safe(self):
        invalid = (None, {}, child(status="live"), child(updated=None),
                   child(updated="2026-10-22T09:00:00"), child(parent="worker"))
        result = model.metadata({"build log": "".join(report("Session", value) for value in invalid)})
        self.assertEqual(result["subsessions"], [])
        self.assertEqual(len(result["metadataErrors"]), 1)

    def test_all_host_children_remain_and_unknown_status_is_not_finished(self):
        tasks = [{"id": f"w{i}", "type": "subagent", "description": "Check", "status": "running"}
                 for i in range(12)]
        tasks += [{"id": "unknown", "type": "workflow", "status": []},
                  {"id": "shell", "type": "shell", "status": "running"}]
        rows = model.subsessions([], hosts.agents(tasks), 123)
        self.assertEqual(len(rows), 13)
        self.assertTrue(all(row["updated"] == 123 for row in rows))
        self.assertEqual(rows[-1]["status"], "unknown")
        self.assertEqual(model.subsessions([], [{"id": "old", "run": True}], None)[0]["status"], "unknown")
        recorded = model.metadata({"build log": report("Session", child(id="w0", status="finished"))})
        merged = model.subsessions(recorded["subsessions"], hosts.agents(tasks), 123)
        self.assertEqual(len(merged), 13)
        self.assertEqual((merged[0]["status"], merged[0]["source"]), ("finished", "record"))

    def ticket_rows(self, ticket_lines, todo_lines, build=""):
        """Exercise the shared parser and card ownership contract together."""
        sections = facts.sections(f"## Tickets\n{ticket_lines}\n## Plan\n### Todos\n{todo_lines}\n## Build log\n{build}")
        return model.tickets(sections, card.view({"coverage": True}, sections))

    def test_all_tickets_use_card_ownership_and_local_states(self):
        tickets = "\n".join(f"**Sub-issue:** https://tracker.test/issues/{i} Ticket {i}" for i in (11, 12, 13))
        rows = self.ticket_rows(tickets, "T1 First → result (#11, A1)\nT2 Second → result (#12, A1)",
                                "T1 pre: read do: build post: use\n**Now:** T2")
        self.assertEqual([row["state"] for row in rows], ["finished", "working", "unknown"])
        self.assertEqual([row["tasks"] for row in rows], [["T1"], ["T2"], []])
        self.assertTrue(all(row["basis"] == "local-tasks" for row in rows))
        sole = self.ticket_rows("**Ticket:** https://tracker.test/issues/11 Only ticket", "T1 Untagged → result")
        self.assertEqual(sole[0]["tasks"], ["T1"])
        self.assertEqual(sole[0]["state"], "next")

    def test_tracker_number_collision_never_assigns_a_task_to_both(self):
        rows = self.ticket_rows("**Ticket:** https://one.test/issues/1 One\n"
                                "**Sub-issue:** https://two.test/issues/1 Two\n"
                                "**Sub-issue:** https://one.test/issues/1 Duplicate\n"
                                "**Sub-issue:** http://[broken/2 Invalid", "T1 Work → result (#1, A1)", "**Now:** T1")
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(rows[0]["id"], rows[1]["id"])
        self.assertTrue(all(row["state"] == "unknown" and row["pct"] is None and not row["tasks"] for row in rows))

    def test_writer_preserves_report_age_and_embeds_full_snapshot_tasks(self):
        with tempfile.TemporaryDirectory(prefix="dashboard facts ") as temp:
            root = Path(temp)
            project = root / "project"
            record = project / ".factory/fast/work-record.md"
            record.parent.mkdir(parents=True)
            record.write_text("## Plan\n### Todos\nT1 Build → useful result\n## Build log\n**Now:** T1", encoding="utf-8")
            run = {"key": "preview", "kind": "change", "mode": "fast", "coverage": True,
                   "created": "2026-10-22T08:00:00+00:00", "done": {}}
            folder = root / "view"
            original = view.write(folder, project, run, ["plan", "build"],
                                  agents=hosts.agents([{"id": "w", "type": "subagent", "status": "running"}]),
                                  now_ms=1792659600000)
            later = view.write(folder, project, run, ["plan", "build"], now_ms=1792663200000)
            self.assertEqual(later["agentsObservedAt"], original["agentsObservedAt"])
            self.assertEqual(later["subsessions"][0]["updated"], original["subsessions"][0]["updated"])
            self.assertEqual((later["done"], later["total"], later["pct"]), (0, 1, 0))
            self.assertIsNone(later["goal"])
            output = root / "snapshot.html"
            view.snapshot(folder, output)
            html = output.read_text(encoding="utf-8")
            embedded = html.split('<script id="snapshot" type="application/json">', 1)[1].split("</script>", 1)[0]
            self.assertEqual(json.loads(embedded)["runs"][0]["tasks"], later["tasks"])
            cleared = view.write(folder, project, run, ["plan", "build"], agents=[], now_ms=1792663260000)
            self.assertEqual(cleared["subsessions"], [])


if __name__ == "__main__":
    unittest.main()
