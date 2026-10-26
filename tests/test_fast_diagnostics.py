"""Markdown evidence and complete diagnostics regressions."""
import unittest
from unittest.mock import patch

from test_fast_gate import GateHarness, module


class FastDiagnosticsTests(GateHarness, unittest.TestCase):
    def test_direct_handoff_without_record_sections_reports_every_missing_field(self):
        record = module("fast_record")
        problems = record.check_handoff({"kind": "change", "coverage": True}, "", project=self.project)
        self.assertEqual(problems, [f"needs a '**{label}:** <value or evidence>' line"
                                    for label in ("Run", "Statuses", "Unverified", "Follow-ups")])
        modern = record.check_handoff({"kind": "change", "ticket_checks": True, "check_selection": True},
                                      "", project=self.project)
        self.assertEqual(modern[:4], problems)
        self.assertTrue(any("checks --plan" in problem for problem in modern))

    def test_audit_excludes_markdown_examples_but_keeps_live_nested_verdicts(self):
        record = module("fast_record")
        examples = (
            "- Example:\n\n      - U2 FAIL Home: code example only.\n\nU2 PASS Home: navigation works.",
            "- Example:\n\n    ```text\n    U2 FAIL Home: code example only.\n    ```\n\nU2 PASS Home: navigation works.",
            "- Example\n---\n    U2 FAIL Home: code example only.\n\nU2 PASS Home: navigation works.",
        )
        for body in examples:
            with self.subTest(body=body):
                verdicts, failed, _ = record.audit_lines(body)
                self.assertEqual([value for value, _ in verdicts["U2"]], ["PASS"])
                self.assertEqual(failed, set())
                self.assertFalse(any("U2 has duplicate" in item for item in record.ux_audit(body)))
        for body in ("- Group\n  - U2 FAIL Home: actual overlap found.",
                     "- Group\n  | U2 | Hierarchy | FAIL | actual overlap found. |"):
            with self.subTest(body=body):
                verdicts, failed, _ = record.audit_lines(body)
                self.assertEqual(verdicts["U2"][0][0], "FAIL")
                self.assertEqual(failed, {"U2"})

    def test_empty_sections_report_independent_required_fields(self):
        record = module("fast_record")
        gate = module("fast_gate")
        run = {"key": "empty-record", "kind": "change", "light": True, "briefs": True}
        plan = record.check_plan(run, "", project=self.project, all_sections={"plan": ""})
        self.assertTrue(any("### Todos" in item for item in plan))
        self.assertTrue(any("todo IDs" in item for item in plan))
        self.assertTrue(any("Ports" in item for item in plan))
        self.assertTrue(any("Success" in item for item in plan))
        done = record.check_done_run(run, "", project=self.project, all_sections={"done-run": ""})
        self.assertIn("needs >=1 PASS result", done)
        self.assertTrue(any("Logs" in item for item in done))
        path = self.project / "empty-record.md"
        path.write_text("", encoding="utf-8")
        args = type("Args", (), {"project": str(self.project), "step": "plan", "offline": None})()
        with patch.object(gate, "open_run", return_value=(self.project, {**run, "done": {}})), \
             patch.object(gate, "steps_for", return_value=["plan"]), \
             patch.object(gate, "record_path", return_value=path), \
             patch.object(gate, "sibling", return_value=record), \
             patch.object(gate, "log"), \
             patch.object(gate, "fail", side_effect=ValueError) as refusal:
            with self.assertRaises(ValueError):
                gate.cmd_done(args)
        message = refusal.call_args.args[0]
        for required in ("missing or empty", "### Todos", "todo IDs", "Ports", "Success"):
            self.assertIn(required, message)
