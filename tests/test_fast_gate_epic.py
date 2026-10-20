"""Fast gate: who owes an epic at the done-run and handoff (fast-run.md#work-record, "Another run owes an epic")."""
import json
import unittest
from unittest.mock import patch

import test_fast_gate as harness

DOD = "### Definition of done\n- **A1 (R1):** works\n- **A2:** fails safely\n"


class EpicOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.record = harness.module("fast_record")

    def test_done_run_owes_the_epic_only_from_the_integration_todo_holder(self):
        record = self.record
        sections = record.sections(harness.SAMPLE.read_text(encoding="utf-8"))
        epic = record.ticket_urls(sections["tickets"])[0][0]
        done = sections["done-run"]
        no_epic = "\n".join(line for line in done.splitlines() if not line.startswith("- #1 "))
        run = {"kind": "feature", "hidden_checks": True, "ticket_checks": True}
        check = lambda body, r=run: " ".join(record.check_done_run(r, body, project=".", all_sections=sections))

        def holding(todo):  # the epic's checklist gives its integration todo to `todo`
            items = f"\n### Checklist\n- [ ] #2 Booking: every item ticked\n- [ ] {todo} Integration proof (A1, A2)\n"
            return lambda url: {"url": url, "body": DOD + (items if url == epic else ""), "stopped": False, "backlog": False}
        with patch.object(record, "read_ticket", side_effect=holding("T99")):  # another run holds it
            self.assertEqual(check(no_epic), "")  # the epic's criteria wait for that run
            self.assertEqual(check(no_epic, {**run, "kind": "product"}), "")  # product runs too (owner, 2026-10-20)
            self.assertIn("#5 A2", check(no_epic.replace(", #5 A2: PASS", "")))  # owned tickets still need every PASS
            self.assertIn("FAIL", check(done.replace("#1 A1: PASS", "#1 A1: FAIL")))  # any FAIL still refuses
            self.assertIn("#1 A1", check(no_epic, {**run, "todos": ["T99"]}))  # pinned at `done plan`: still owed
        with patch.object(record, "read_ticket", side_effect=holding("T8")):  # this run holds it: owed whole
            self.assertIn("without a hidden-check PASS: #1 A1, #1 A2", check(no_epic))
        with patch.object(record, "read_ticket", side_effect=holding("🤝 **T8**")):  # the method's own example
            self.assertIn("without a hidden-check PASS: #1 A1, #1 A2", check(no_epic))
        odd = lambda url: {**holding("T99")(url), "body": holding("T99")(url)["body"] + "- [ ] Soak sign-off for A2\n"}
        with patch.object(record, "read_ticket", side_effect=odd):  # off the layout: owed whole, with the form
            self.assertIn("off the ticket layout", check(no_epic))
            self.assertIn("#1 A1, #1 A2", check(no_epic))

    def test_ownership_is_read_from_the_layout_only(self):
        record, epic = self.record, "https://github.com/acme/studio-booking/issues/1"
        read = lambda text: record.integration({"url": epic, "body": DOD + "\n### Checklist\n" + text})
        for text, holders in [("- [ ] T63 Proof → it works (A1, A2)\n", {"T63"}),
                              ("- [ ] T63 Proof (#1, A1)\n", {"T63"}), ("- [ ] T63 Proof (#1 A1, A2)\n", {"T63"}),
                              ("- [ ] T63 Proof (A1; A2)\n", {"T63"}), ("- [ ] T63 Proof ( A1 )\n", {"T63"}),
                              ("- [ ] **T63** Proof (A1)\n", {"T63"}), ("- [ ] [T63] Proof (A1)\n", {"T63"}),
                              ("- [ ] 🤝 **T63** Proof (A1)\n", {"T63"}), ("- [ ] ✅ [T63] Proof (A1)\n", {"T63"}),
                              ("- [ ]T63 Proof (A1)\n", {"T63"}), ("- [ ] T62 / T63 Proof (A1)\n", {"T62", "T63"}),
                              ("- [ ] T61 to T63 Proof (A1)\n", {"T61", "T62", "T63"}),
                              ("- [ ] T63 and T64 Proof (A1)\n", {"T63", "T64"}), ("- [ ] T63-T64 Proof (A1)\n", {"T63", "T64"}),
                              ("- [ ] T63 Proof (A1). needs #2 T29, needs #3 T18\n", {"T63"}),  # needs markers: not read
                              ("- [x] T63 Proof (A1). Proof: A2 passed on the fleet\n", {"T63"}),  # the proof tail: not read
                              ("- [x] T80 Checks synced (#4 A1 to A8, #5 A1, A2)\n", set()),  # other tickets' criteria
                              ("- [ ] T75 Docs, as T63 says (#2, A1)\n", set()),  # later IDs never claim
                              ("- [ ] #2 Booking: every item ticked\n", set())]:
            with self.subTest(text=text):
                self.assertEqual(read(text), (holders, None))
        for text in ["- [ ] T63 Proof (**A1**, A2)\n", "- [ ] T63 Proof (needs #2 T29, A1)\n", "- [ ] Soak sign-off for A2\n",
                     "- [ ] Integration proof (A1)\n", "- [ ] #2 Booking, then T63 (A1)\n", "- [ ] T7 Collector, needs #2 A1\n",
                     "- [ ] T63 Proof, after #2 T29 (A1)\n- [ ] Owner soak (A2)\n"]:
            with self.subTest(text=text):  # names the epic's criteria off the layout: owed whole, the item named
                self.assertIsNotNone(read(text)[1])
        self.assertEqual(record.lead_todos("- [x] 🤝 T76, T77 Docs. needs #1 T75"), {"T76", "T77"})

    def test_a_later_epic_owes_only_this_runs_items(self):
        record = self.record
        ticket = "### ✅ Definition of done\n- **A1:** x\n\n### ☑️ Checklist\n- [x] T1 a\n- [ ] T2 b\n"
        later = lambda own, body=ticket: {"stopped": False, "backlog": False, "later": own, "body": body}
        self.assertIsNone(record.needs_ticks(later({"T1", "T3"})))  # T2 belongs to another run
        self.assertIn("1 unticked", record.needs_ticks(later({"T2"})))  # this run's own todo stays owed
        for own in ["- [ ] **T2** b", "- [ ] 🤝 **T2** b", "- [ ] T9 / T2 b"]:
            self.assertIn("1 unticked", record.needs_ticks(later({"T2"}, ticket.replace("- [ ] T2 b", own))), own)
        for other in ["T2 b. needs #2 T29", "T2 b, after #1 T29", "T2 b, as T29 says"]:  # only the leading IDs claim
            self.assertIsNone(record.needs_ticks(later({"T29"}, ticket.replace("T2 b", other))), other)
        whole = {"stopped": False, "backlog": False, "body": ticket, "layout": "- [ ] Soak sign-off for A1"}
        self.assertIn("off the ticket layout", record.needs_ticks(whole))
        self.assertIn("1 unticked", record.needs_ticks(whole))

    def test_a_planning_run_on_an_epic_owes_only_its_own_todos(self):
        record = self.record
        epic = "https://github.com/acme/portal/issues/1"
        body = ("### ✅ Definition of done\n- **A1:** x\n\n### ☑️ Checklist\n- [ ] #2 Collector: every item ticked\n"
                "- [ ] T63 Integration proof (A1)\n- [x] T75 Gap audit\n- [ ] T77 Tickets tightened\n")
        issue = lambda text: json.dumps({"body": text, "state": "OPEN", "labels": [{"name": "status: in progress"}]})
        run = {"kind": "change", "ticket_checks": True, "coverage": True, "light": True}
        handoff = "**Run:** x\n**Statuses:** x\n**Unverified:** x\n**Follow-ups:** x\n"

        def check(todos, text=body):
            plan = "**Success:** x\n\n### Todos\n\n" + "".join(f"- {t} → x (#1)\n" for t in todos)
            sections = {"tickets": f"**Ticket:** {epic}\n**Backlog:** owned #1\n", "plan": plan}
            with patch.object(record, "gh", return_value=issue(text)):
                return " ".join(record.check_handoff(run, handoff, offline=None, all_sections=sections))
        self.assertEqual(check(["T75"]), "")  # #109: a planning run owes only its own items on the epic
        self.assertIn("1 unticked", check(["T75", "T77"]))  # its own unticked todo stays owed
        self.assertIn("3 unticked", check(["T63"]))  # the run holding the integration todo owes the epic whole
        self.assertIn("3 unticked", check(["T75"], body.replace(" (A1)", "")))  # no integration todo: owed whole


class PlanPinTests(harness.GateHarness, unittest.TestCase):
    def test_done_plan_pins_the_plan_todos(self):
        self.start("--auth")
        self.finish_sample()
        run = json.loads((self.project / ".factory/fast/run.json").read_text(encoding="utf-8"))
        self.assertEqual(run["todos"], [f"T{n}" for n in range(1, 9)])  # read later even if the plan drops one


if __name__ == "__main__":
    unittest.main()
