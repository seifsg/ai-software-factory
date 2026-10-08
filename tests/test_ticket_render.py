"""Ticket body rendering and parsing: pure functions, no Git, tracker or workflow.

Owner and reviewer assertions are synthetic test doubles; no live acceptance is claimed.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import unittest

from safe_engine.project import EngineError
from safe_engine.tickets import binding, parse_body, render_ticket, scope_digest
from ticket_fixtures import SYNTHETIC, base_contract, visual_contract


class TicketRenderTests(unittest.TestCase):
    def setUp(self):
        self.initial_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        self.contract = base_contract(self.initial_at)

    def visual_contract(self):
        return visual_contract(self.contract, self.initial_at)

    def test_canonical_projection_accepts_crlf_but_rejects_ignored_owner_edits(self):
        for folded in (True, False):
            body = render_ticket(self.contract, fold_contract=folded)
            with self.subTest(folded=folded):
                self.assertEqual(parse_body(body), self.contract)
                self.assertEqual(parse_body(body.replace("\n", "\r\n")), self.contract)
            for edited in (body.replace("Synthetic outcome", "Owner changed outcome", 1),
                           body + "Owner adds a new requirement\n", body + body):
                with self.subTest(folded=folded, edited=edited[:60]), self.assertRaises(EngineError):
                    parse_body(edited)

    def test_legacy_body_from_original_format_keeps_complete_history(self):
        contract = deepcopy(self.contract)
        contract["scope_history"] = [{"revision": 1, "owner_words": "Keep this reminder. Keep it."}]
        contract["scope"]["purpose"] = {"older_custom_metadata": True}
        scope = contract["scope"]
        legacy = (f"## Before\n\n{scope['before']}\n\n## After\n\n{scope['after']}\n\n"
                  "## Acceptance\n\n" + "\n".join(f"- {c['id']}: {c['text']}" for c in scope["acceptance"])
                  + "\n\n<!-- safe-engine-ticket:v1 -->\n```json\n"
                  + json.dumps(contract, indent=2, ensure_ascii=False)
                  + "\n```\n<!-- /safe-engine-ticket -->\n")
        folded = render_ticket(parse_body(legacy))
        self.assertEqual(parse_body(folded), contract)
        self.assertEqual(scope_digest(parse_body(legacy)), scope_digest(parse_body(folded)))
        self.assertIn('<details>', folded)
        self.assertIn('Keep this reminder. Keep it.', folded)
        for edited in (folded.replace('<details>', '<details open>'),
                       folded.replace('Full contract: owner input, journeys and history', 'Changed expectation'),
                       folded.replace('</details>', 'New owner requirement\n</details>')):
            with self.subTest(edited=edited[:60]), self.assertRaises(EngineError):
                parse_body(edited)

    def test_scope_must_have_a_journey_sourced_owner_input_and_unique_criteria(self):
        for field, value in (("journeys", []), ("owner_input", [{"text": SYNTHETIC}]),
                             ("dependencies", ["beta", "beta"]),
                             ("acceptance", self.contract["scope"]["acceptance"] * 2)):
            with self.subTest(field=field):
                changed = deepcopy(self.contract)
                changed["scope"][field] = value
                with self.assertRaises(EngineError):
                    render_ticket(changed)

    def test_visual_prose_edits_cannot_change_or_hide_the_bound_record(self):
        contract = self.visual_contract()
        for folded in (True, False):
            body = render_ticket(contract, fold_contract=folded)
            for field in ("purpose", "goal", "context", "approach", "flow"):
                with self.subTest(folded=folded, field=field), self.assertRaises(EngineError):
                    parse_body(body.replace(contract["scope"][field], "Changed owner expectation", 1))
            for edited in (body.replace(contract["progress"], "Claimed merged", 1),
                           body.replace("Synthetic inspection", "Claimed review", 1),
                           body + "New requirement outside contract\n"):
                with self.subTest(folded=folded, edited=edited[:50]), self.assertRaises(EngineError):
                    parse_body(edited)

    def test_new_visual_scope_fields_require_exact_confirmation(self):
        contract = self.visual_contract()
        for field in ("purpose", "goal", "context", "approach", "flow", "optional"):
            changed = deepcopy(contract)
            changed["scope"][field] = ["Changed optional scope"] if field == "optional" else "Changed scope"
            with self.subTest(field=field):
                self.assertNotEqual(scope_digest(changed), scope_digest(contract))
                with self.assertRaises(EngineError):
                    binding({"contract": parse_body(render_ticket(changed)), "observed_at": self.initial_at})

    def test_checklist_ticks_render_outside_scope_and_older_headings_still_parse(self):
        contract = self.visual_contract()
        original = scope_digest(contract)
        contract["checklist"] = [{"id": "T1", "text": "Synthetic sentence kept", "done": True,
                                  "proof": "Synthetic read-back"},
                                 {"id": "T2", "text": "Synthetic second item", "done": False}]
        self.assertEqual(scope_digest(contract), original)
        for layout in ("auto", "legacy"):
            for folded in (True, False):
                with self.subTest(layout=layout, folded=folded):
                    body = render_ticket(contract, layout=layout, fold_contract=folded)
                    self.assertIn("- [x] T1 Synthetic sentence kept Proof: Synthetic read-back", body)
                    self.assertIn("- [ ] T2 Synthetic second item", body)
                    self.assertEqual(parse_body(body), contract)
                    with self.assertRaises(EngineError):
                        parse_body(body.replace("- [ ] T2", "- [x] T2", 1))
        visual = render_ticket(contract)
        self.assertIn("## ✅ Definition of done", visual)
        older = render_ticket(contract, done_heading="Done when")
        self.assertIn("## ✅ Done when", older)
        self.assertEqual(parse_body(older), contract)
        for bad in ([{"id": "T1", "text": "x", "done": True}],
                    [{"id": "T1", "text": "x", "done": "yes"}],
                    [{"id": "T1", "text": "x", "done": False}, {"id": "T1", "text": "y", "done": False}],
                    {"id": "T1"}):
            with self.subTest(bad=bad), self.assertRaises(EngineError):
                render_ticket({**contract, "checklist": bad})

    def test_partial_or_invalid_visual_fields_do_not_silently_fall_back(self):
        contract = self.visual_contract()
        for field in ("purpose", "goal", "context", "approach"):
            changed = deepcopy(contract)
            del changed["scope"][field]
            with self.subTest(field=field), self.assertRaises(EngineError):
                render_ticket(changed, layout="legacy")
        for field, value in (("flow", []), ("optional", "not an array"), ("optional", [""])):
            changed = deepcopy(contract)
            changed["scope"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(EngineError):
                render_ticket(changed)
        for field, value in (("progress", ""), ("activity", {}), ("activity", [{}])):
            changed = deepcopy(contract)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(EngineError):
                render_ticket(changed)
        with self.assertRaises(EngineError):
            render_ticket(contract, layout="unknown")


if __name__ == "__main__":
    unittest.main()
