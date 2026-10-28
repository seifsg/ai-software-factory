"""Selected hidden proof: public authority, real execution and current receipts."""
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_fast_gate as harness

sys.path.insert(0, str(harness.SCRIPTS))
import fast_checks as checks
import fast_checks_command as command
import fast_design as evidence
import fast_record as record
from safe_engine.runner import run_command

EPIC = "https://github.com/example/fixture/issues/1"
CHILD = "https://github.com/example/fixture/issues/2"
CHECK_SOURCE = ("import sys\nfrom pathlib import Path\n"
                "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
                "from app import add\nassert add(-2, 2) == 0\n")


def ticket(url, todo):
    return {"url": url, "body": "### Definition of done\n- **A1:** Addition handles signed values.\n"
            f"### Checklist\n- [ ] {todo} Addition proof (A1)\n"}


def selected(run, *rows):
    run["checks"] = {"plan": checks.selection({"version": 1, "tickets": list(rows)}, run)}
    return run


class OwnershipTests(unittest.TestCase):
    def test_selection_routes_visual_and_mixed_criteria_without_dropping_proof(self):
        run = {"kind": "feature", "tickets": [EPIC, CHILD], "design_port": True, "show_first": True}
        visual = {**ticket(EPIC, "T9"), "category": "visual-port", "reason": "Appearance port"}
        mixed = {**ticket(CHILD, "T1"), "category": "mixed", "reason": "Behavior and appearance"}
        selected(run, visual, mixed)
        checks.freeze_ownership(run)
        self.assertEqual(checks.wanted(run), {CHILD + "#A1"})
        self.assertTrue(checks.problems({**run, "check_selection": True}, ".", final=True))
        with self.assertRaisesRegex(ValueError, "keep hidden checks"):
            selected({**run, "checks": {}}, visual, {**mixed, "hidden": False})
        with self.assertRaisesRegex(ValueError, "owner request"):
            selected({**run, "checks": {}}, {**visual, "hidden": True}, mixed)

    def test_public_derived_fields_cannot_waive_child_and_live_owner_drifts(self):
        run = {"kind": "feature", "check_selection": True, "tickets": [EPIC, CHILD], "todos": ["T1"]}
        rows = [{**ticket(EPIC, "T9"), "category": "logic", "reason": "Other integration run"},
                {**ticket(CHILD, "T1"), "category": "logic", "reason": "This child run"}]
        for field, value in (("owed", False), ("criteria", []), ("contract", "forged"),
                             ("integration_todos", []), ("verified_integration_todos", ["T9"])):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "Unknown checks ticket fields"):
                selected(run.copy(), rows[0], {**rows[1], field: value})
        selected(run, *rows)
        self.assertIsNone(checks.verify_plan(run, rows[0]))
        checks.freeze_ownership(run)
        self.assertEqual(checks.wanted(run), {CHILD + "#A1"})
        run["checks"]["plan"]["tickets"][CHILD]["owed"] = False
        self.assertEqual(checks.wanted(run), {CHILD + "#A1"})
        self.assertTrue(checks.problems(run, ".", final=True))
        self.assertIn(CHILD + "#A1", " ".join(checks.verdict_problems(run, "", record)))
        self.assertIn("differs", checks.verify_plan(run, {**rows[0], "body": ticket(EPIC, "T1")["body"]}))
        self.assertIn("ownership differs", checks.refreshed(run, {**rows[0], "body": ticket(EPIC, "T1")["body"]}))
        self.assertIsNone(checks.refreshed(run, {**rows[0], "body": rows[0]["body"].replace("- [ ]", "- [x]")}))

    def test_offline_tracker_keeps_canonical_url_and_requires_its_verdict(self):
        url = "https://app.example.invalid/t/demo"
        row = {**ticket(url, "T1"), "category": "logic", "reason": "CLI behavior"}
        run = selected({"kind": "change", "check_selection": True, "tickets": [url]}, row)
        checks.freeze_ownership(run)
        self.assertEqual(checks.wanted(run), {url + "#A1"})
        self.assertIn(url + "#A1", " ".join(checks.verdict_problems(run, "", record)))
        self.assertEqual(checks.verdict_problems(run, f"**Hidden checks:** {url}#A1: PASS", record), [])
        self.assertIn("FAIL", " ".join(checks.verdict_problems(run, f"**Hidden checks:** {url}#A1: FAIL", record)))

    def test_observed_check_without_record_verdict_reports_all_independent_errors(self):
        row = {**ticket(CHILD, "T1"), "category": "logic", "reason": "CLI behavior"}
        run = selected({"kind": "change", "tickets": [CHILD]}, row)
        run["checks"]["observations"] = {CHILD + "#A1": {"verdict": "PASS"}}
        missing = checks.verdict_problems(run, "", record)
        self.assertTrue(any("Hidden criteria missing or failed" in item for item in missing))
        malformed = checks.verdict_problems(run, f"**Hidden checks:** {CHILD}#A1: MAYBE", record)
        self.assertTrue(any("unreadable hidden-check entry" in item for item in malformed))
        self.assertTrue(any("Hidden criteria missing or failed" in item for item in malformed))
        self.assertEqual(checks.verdict_problems(run, f"**Hidden checks:** {CHILD}#A1: PASS", record), [])
        disagree = checks.verdict_problems(run, f"**Hidden checks:** {CHILD}#A1: FAIL", record)
        self.assertTrue(any("Hidden checks contain FAIL" in item for item in disagree))
        self.assertTrue(any("Manual verdict differs" in item for item in disagree))

    def test_preparation_rejects_missing_criterion_and_unlisted_command_source(self):
        with tempfile.TemporaryDirectory(prefix="fast-check-prepare-") as folder:
            project = Path(folder)
            (project / "check.py").write_text("pass\n", encoding="utf-8")
            run = selected({"kind": "change", "tickets": [CHILD]},
                           {**ticket(CHILD, "T1"), "category": "logic", "reason": "Behavior"})
            checks.freeze_ownership(run)
            base = {"version": 1, "checker": "other author", "interface": "CLI", "ports": "none", "checks": []}
            with self.assertRaisesRegex(ValueError, "cover exactly"):
                checks.prepare(project, run, base)
            wrong = {"criterion": CHILD + "#A1", "files": ["check.py"],
                     "argv": [sys.executable, "other.py"], "timeout_seconds": 10}
            with self.assertRaisesRegex(ValueError, "first declared source"):
                checks.prepare(project, run, {**base, "checks": [wrong]})


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fast-checks-")
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        (self.project / ".gitignore").write_text(".factory/\n__pycache__/\n", encoding="utf-8")
        (self.project / "app.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")
        subprocess.run(["git", "add", ".gitignore", "app.py"], cwd=self.project, check=True)
        (self.project / ".factory").mkdir()
        self.path = self.project / ".factory/check.py"
        self.path.write_text(CHECK_SOURCE, encoding="utf-8")
        self.url = "https://app.example.invalid/t/check"
        row = {**ticket(self.url, "T1"), "category": "logic", "reason": "Signed input"}
        self.run = selected({"key": "checks-fixture", "kind": "change", "check_selection": True, "tickets": [self.url],
                             "done": {"build": "done"}, "ui": False}, row)
        checks.freeze_ownership(self.run)
        self.prepared = {"version": 1, "checker": "separate fixture checker", "interface": "add(a,b)",
                         "ports": "none", "checks": [{"criterion": self.url + "#A1", "files": [".factory/check.py"],
                           "argv": [sys.executable, ".factory/check.py"], "timeout_seconds": 10,
                           "environment": ["FACTORY_CHECK_INPUT"]}]}
        self.run["checks"]["prepared"] = checks.prepare(self.project, self.run, self.prepared)
        self.run["checks"]["runtime"] = {"candidate": evidence.candidate(self.project), "source": "CLI fixture",
                                                    "not_applicable": "No UI"}

    def execute(self, syntax_only=False):
        class Gate:
            def put(self, *_):
                pass
            def mutate(self, project, state, update):
                update(state)
                return state
            def log(self, *_ , **__):
                pass
        with patch.object(command, "runner", return_value=run_command):
            with redirect_stdout(StringIO()):
                command.execute(self.project, self.run, Gate(), syntax_only=syntax_only)

    def test_parse_before_build_and_execute_only_after_build(self):
        self.run["done"].clear()
        self.execute(syntax_only=True)
        self.assertEqual(checks.syntax_problems(self.run, self.project), [])
        with self.assertRaisesRegex(ValueError, "Finish build"):
            self.execute()
        self.run["done"]["build"] = "done"
        self.execute()
        self.assertEqual(checks.problems(self.run, self.project, final=True), [])
        self.assertIn(self.url + "#A1", " ".join(checks.verdict_problems(self.run, "", record)))
        self.assertEqual(checks.verdict_problems(
            self.run, f"**Hidden checks:** {self.url}#A1: PASS", record), [])

    def test_runtime_snapshot_is_candidate_bound_and_hashed(self):
        self.run["ui"] = True
        snapshot = self.project / ".factory/names.txt"
        snapshot.write_text("- button \"Export records\"\n", encoding="utf-8")
        captured = checks.runtime(self.project, self.run, {"candidate": evidence.candidate(self.project),
            "source": "Chrome desktop and phone after manual use", "path": ".factory/names.txt"})
        self.assertEqual(captured["sha256"], evidence.file_hash(snapshot))
        snapshot.write_text("- button \"Changed\"\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Runtime names changed"):
            checks.runtime(self.project, self.run, captured)
        with self.assertRaisesRegex(ValueError, "different candidate"):
            checks.runtime(self.project, self.run, {**captured, "candidate": "stale"})

    def test_failure_and_mutations_invalidate_real_receipts(self):
        self.execute()
        self.path.write_text("def broken(: pass\n", encoding="utf-8")
        self.assertIn("changed", " ".join(checks.problems(self.run, self.project, final=True)))
        with self.assertRaisesRegex(ValueError, "Checks did not pass"):
            self.execute(syntax_only=True)
        self.assertEqual(self.run["checks"]["syntax"]["status"], "harness-invalid")
        self.path.write_text(CHECK_SOURCE.replace("== 0", "== 9"), encoding="utf-8")
        self.execute(syntax_only=True)
        with self.assertRaisesRegex(ValueError, "Checks did not pass"):
            self.execute()
        self.assertEqual(self.run["checks"]["result"]["status"], "failed-unclassified")
        self.path.write_text(CHECK_SOURCE, encoding="utf-8")
        self.execute()
        self.assertEqual(checks.problems(self.run, self.project, final=True), [])
        with patch.dict(os.environ, {"FACTORY_CHECK_INPUT": "changed"}):
            self.assertIn("environment changed", " ".join(checks.problems(self.run, self.project, final=True)))
        (self.project / "app.py").write_text("def add(a, b): return a - b\n", encoding="utf-8")
        self.assertIn("Build changed", " ".join(checks.problems(self.run, self.project, final=True)))
        (self.project / "app.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")
        log = self.project / self.run["checks"]["result"]["logs"][0]["path"]
        log.write_text("tampered", encoding="utf-8")
        self.assertIn("log changed", " ".join(checks.problems(self.run, self.project, final=True)))


if __name__ == "__main__":
    unittest.main()
