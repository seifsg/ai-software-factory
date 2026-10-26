"""Approved suite declarations remain plans, scoped to current non-UI methods."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/safe-engine/scripts"))
import fast_plan_reuse as reuse
import fast_show as show


class PlanSuiteContractTests(unittest.TestCase):
    def setUp(self):
        self.run = {"suite_policy": True, "ui": False, "tickets": []}
        self.plan = {"version": 1, "full_suite": ["python", "tests/run.py"],
                     "suite_inputs": {"files": [], "environment": []}}
        self.data = {"suite_plan": self.plan, "proof_selection": {
            "version": 1, "tickets": [], "none_reason": "Pure obligation fixture"}}

    def test_current_plan_normalizes_without_importing_proof(self):
        self.plan.update(proof={"passed": True}, reply={"action": "approve"})
        reuse.obligations(ROOT, self.run, self.data)
        self.assertEqual(self.run["suite"], {"plan": show.suite_plan(self.plan)})
        self.assertEqual(set(self.run["suite"]["plan"]), {"full_suite", "timeout_seconds", "suite_inputs"})
        self.assertEqual(show.problems(self.run, ROOT), [])
        self.assertTrue(show.completion_problems(self.run, ROOT))

    def test_missing_or_invalid_current_plan_refuses(self):
        for plan in (None, [], {}, {**self.plan, "full_suite": []},
                     {**self.plan, "version": True}, {**self.plan, "timeout_seconds": True},
                     {**self.plan, "suite_inputs": {"files": []}}):
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                reuse.obligations(ROOT, copy.deepcopy(self.run), {**self.data, "suite_plan": plan})
        del self.data["suite_plan"]
        with self.assertRaises(ValueError):
            reuse.obligations(ROOT, self.run, self.data)
        self.assertNotIn("suite", self.run)

    def test_plan_is_rejected_outside_current_non_ui_scope(self):
        for flags in ({"suite_policy": False}, {"ui": True}):
            with self.subTest(flags=flags), self.assertRaisesRegex(ValueError, "outside this run's scope"):
                reuse.obligations(ROOT, {**self.run, **flags}, self.data)

    def test_legacy_non_ui_needs_no_suite_plan(self):
        self.run["suite_policy"] = False
        del self.data["suite_plan"]
        reuse.obligations(ROOT, self.run, self.data)
        self.assertNotIn("suite", self.run)

    def test_ui_retains_show_plan_without_reply_or_proof(self):
        self.run.update(ui=True, show_first=True)
        show_plan = {**self.plan, "surfaces": [{"id": "home", "name": "Home"}]}
        del self.data["suite_plan"]
        self.data["show_plan"] = show_plan
        reuse.obligations(ROOT, self.run, self.data)
        self.assertEqual(self.run["show"], {"plan": show.plan(show_plan)})
        self.assertNotIn("suite", self.run)

    def test_ui_rejects_malformed_suite_inputs_as_start_errors(self):
        self.run.update(ui=True, show_first=True)
        for value in ({"files": []}, []):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "suite_inputs"):
                reuse.obligations(ROOT, copy.deepcopy(self.run), {
                    **self.data, "show_plan": {**self.plan, "surfaces": [{"id": "home", "name": "Home"}],
                                               "suite_inputs": value},
                })

    def test_schema_allows_plan_but_not_execution_or_identity(self):
        source = "https://tracker.example/plan"
        snapshot = {**self.data, "version": 1, "source": source,
                    "scope": {key: self.run.get(key, False) for key in reuse.SCOPE},
                    "record": {"path": "plan.md", "sha256": "a" * 64},
                    "approval": {"actor": "owner", "source": source, "quote": "Approved",
                                 "plan_sha256": "a" * 64}, "inputs": {"source.py": "b" * 64}}
        self.assertEqual(reuse.shape(snapshot, source, self.run), [])
        for field in ("proof", "execution", "identity", "reply"):
            with self.subTest(field=field):
                self.assertTrue(reuse.shape({**snapshot, field: {}}, source, self.run))


if __name__ == "__main__":
    unittest.main()
