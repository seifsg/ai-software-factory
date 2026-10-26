"""V2 delivery regressions. All review/manual receipts are explicit test doubles."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from safe_engine.acceptance import validate_manual_receipt
from safe_engine.project import EngineError, production_fingerprint, validate_profile, validate_task
from safe_engine.review_packet import method_paths, preflight, prompt_for
from safe_engine.storage import atomic_json
from safe_engine.workflow import Workflow
from suite_fixture import isolate_suite_queue


class DeliveryV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        isolate_suite_queue(self)
        self.git("init", "-q")
        (self.root / ".gitignore").write_text(".factory/\n.env\n", encoding="utf-8")
        (self.root / "README.md").write_text("Fixture document: preserve this sentence.\n", encoding="utf-8")
        self.git("add", ".")
        self.git("-c", "user.name=Factory Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "Text fixture baseline")
        self.profile = {"version": 2, "interface": "library", "checks": [],
                        "environment_inputs": [], "input_files": [], "protected_paths": [],
                        "test_paths": ["tests"], "review_scopes": [], "exposure": "local"}
        self.task = {"request": "Preserve the fixture document", "acceptance": [
            {"id": "A1", "text": "The fixture sentence remains readable", "mode": "manual", "checks": []}]}
        self.flow = Workflow(self.root)

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def artifact(self, kind):
        path = self.root / ".factory" / f"input-{kind}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"# {kind}\nSynthetic regression artifact, not proof of actual agent method adherence.\n",
                        encoding="utf-8")
        return self.flow.record(kind, path)

    def start_build(self):
        self.flow.initialize(self.task, self.profile)
        self.artifact("analysis")
        self.artifact("plan")

    def repair(self, reason):
        """Supply explicit scored test-double findings to the new repair contract."""
        from speed_fixtures import finding
        state = self.flow.load()
        review = state.get("review")
        if review and json.loads(Path(review["report"]).read_text(encoding="utf-8"))["findings"]:
            return self.flow.repair(reason, selected=["F1"])
        path = self.root / ".factory/failure-double.json"
        atomic_json(path, {"findings": [finding()]})
        return self.flow.repair(reason, findings=path, selected=["F1"])

    def receipt(self):
        evidence = self.root / ".factory" / "manual-evidence.txt"
        evidence.write_text("Synthetic observation of the fixture document. No product QA claimed.\n", encoding="utf-8")
        return {"candidate": self.flow.status()["manual_candidate"], "observations": [
            {"criterion": criterion["id"], "device": "text fixture",
             "action": "Synthetic manual-review receipt for regression only",
             "result": "The fixture sentence is readable", "status": "PASS",
             "evidence": [".factory/manual-evidence.txt"]}
            for criterion in self.task["acceptance"]]}

    def finish_manual(self):
        self.artifact("implementation")
        receipt = self.receipt()
        path = self.root / ".factory" / "input-manual.json"
        atomic_json(path, receipt)
        self.flow.record("manual", path)
        return receipt

    def review_double(self, task=None, profile=None):
        proposal = self.flow.contract_proposal(task or self.task, profile or self.profile)
        return {"verdict": "PASS", "independent": True,
                "reviewer": "Explicit synthetic independent-review test double",
                "reason": "Exercise contract binding, not real review quality",
                "authority": "Fixture-only authority; no external action",
                "old_digest": proposal["old_digest"], "new_digest": proposal["new_digest"]}

    def configured_check(self):
        folder = self.root / "tests"
        folder.mkdir(exist_ok=True)
        (folder / "acceptance.py").write_text(
            "from pathlib import Path\n"
            "assert 'preserve this sentence' in Path('README.md').read_text()\n"
            "p = Path('.factory/check-count')\n"
            "p.write_text(str(int(p.read_text()) + 1) if p.exists() else '1')\n",
            encoding="utf-8")
        profile = deepcopy(self.profile)
        profile["checks"] = [{"id": "document", "kind": "unit",
                              "argv": ["{python}", "tests/acceptance.py"], "timeout_seconds": 10}]
        profile["protected_paths"] = ["tests/acceptance.py"]
        task = deepcopy(self.task)
        task["acceptance"][0].update(mode="mixed", checks=["document"])
        return task, profile

    def test_new_project_starts_without_tests_and_rejects_early_testing(self):
        self.start_build()
        self.assertFalse((self.root / "tests").exists())
        self.assertFalse(self.flow.status()["contract_sealed"])
        for action in (self.flow.check, lambda: self.artifact("batch"),
                       lambda: self.flow.feature_check(["anything"], self.root / "README.md")):
            with self.assertRaises(EngineError):
                action()
        self.assertEqual(self.flow.status()["phase"], "build")

    def test_final_test_creation_preserves_manual_evidence_and_runs_single_gate(self):
        self.start_build()
        self.finish_manual()
        manual_candidate = self.flow.status()["manual_candidate"]
        task, profile = self.configured_check()
        self.assertEqual(production_fingerprint(self.root, profile), manual_candidate)
        self.flow.seal(task, profile, self.review_double(task, profile))
        self.artifact("batch")
        result = self.flow.check()
        self.assertTrue(result["checks_passed"])
        self.assertEqual(result["phase"], "review")
        self.assertEqual((self.root / ".factory/check-count").read_text(), "1")
        with self.assertRaises(EngineError):
            self.flow.check()
        self.assertEqual((self.root / ".factory/check-count").read_text(), "1")

    def test_manual_only_contract_needs_no_dummy_command(self):
        self.start_build()
        self.finish_manual()
        self.flow.seal(self.task, self.profile, self.review_double())
        self.artifact("batch")
        result = self.flow.check()
        self.assertTrue(result["checks_passed"])
        self.assertEqual(result["results"], [])
        self.assertEqual(result["phase"], "review")

    def test_candidate_or_evidence_changes_invalidate_final_manual_qa(self):
        self.start_build()
        self.finish_manual()
        state = self.flow.load()
        self.flow.require_manual(state)
        evidence = self.root / ".factory/manual-evidence.txt"
        original = evidence.read_bytes()
        evidence.write_text("Replaced evidence", encoding="utf-8")
        with self.assertRaisesRegex(EngineError, "Manual evidence changed"):
            self.flow.require_manual(state)
        evidence.write_bytes(original)
        (self.root / "README.md").write_text("Changed production document", encoding="utf-8")
        with self.assertRaisesRegex(EngineError, "Current final manual"):
            self.flow.require_manual(state)
        self.repair("Correct changed implementation")
        self.assertIsNone(self.flow.load()["manual"])
        self.assertEqual(self.flow.status()["phase"], "build")

    def test_production_fingerprint_excludes_only_literal_test_paths(self):
        before = production_fingerprint(self.root, self.profile)
        (self.root / "tests").mkdir()
        (self.root / "tests/new.py").write_text("# final test\n")
        self.assertEqual(before, production_fingerprint(self.root, self.profile))
        (self.root / "tests-production.txt").write_text("not beneath the exclusion\n")
        self.assertNotEqual(before, production_fingerprint(self.root, self.profile))
        (self.root / "tests-production.txt").unlink()
        self.profile["input_files"] = ["tests/new.py"]
        declared_before = production_fingerprint(self.root, self.profile)
        (self.root / "tests/new.py").write_text("# explicitly declared changed input\n")
        self.assertNotEqual(declared_before, production_fingerprint(self.root, self.profile))
        self.profile["environment_inputs"] = ["FACTORY_V2_TEST_ENV"]
        with patch.dict(os.environ, {"FACTORY_V2_TEST_ENV": "one"}):
            environment_before = production_fingerprint(self.root, self.profile)
        with patch.dict(os.environ, {"FACTORY_V2_TEST_ENV": "two"}):
            self.assertNotEqual(environment_before, production_fingerprint(self.root, self.profile))

    def test_manual_and_mixed_criteria_require_real_declared_coverage(self):
        self.task["acceptance"].append({"id": "A2", "text": "Second required observation",
                                        "mode": "mixed", "checks": []})
        self.start_build()
        self.artifact("implementation")
        receipt = self.receipt()
        candidate = receipt["candidate"]
        self.assertEqual(len(validate_manual_receipt(receipt, candidate, self.task, self.root)["observations"]), 2)
        invalid = deepcopy(receipt)
        invalid["observations"].pop()
        with self.assertRaisesRegex(EngineError, "missing criteria"):
            validate_manual_receipt(invalid, candidate, self.task, self.root)
        for field, value in (("status", "FAIL"), ("status", "UNKNOWN"), ("criterion", "foreign"),
                             ("device", ""), ("action", ""), ("result", ""),
                             ("evidence", []), ("evidence", ["../outside.txt"]),
                             ("evidence", [".factory/missing.txt"])):
            with self.subTest(field=field, value=value):
                invalid = deepcopy(receipt)
                invalid["observations"][0][field] = value
                with self.assertRaises(EngineError):
                    validate_manual_receipt(invalid, candidate, self.task, self.root)
        with self.assertRaises(EngineError):
            validate_manual_receipt(receipt, "stale", self.task, self.root)

    @unittest.skipUnless(os.name == "nt", "Windows path casing regression")
    def test_windows_test_exclusion_matches_git_path_casing(self):
        self.profile["test_paths"] = ["Tests"]
        before = production_fingerprint(self.root, self.profile)
        (self.root / "tests").mkdir()
        (self.root / "tests/final.py").write_text("# final test content\n")
        self.assertEqual(before, production_fingerprint(self.root, self.profile))

    def test_all_automated_criteria_still_require_a_manual_action(self):
        self.task["acceptance"][0]["mode"] = "automated"
        self.start_build()
        self.artifact("implementation")
        receipt = self.receipt()
        receipt["observations"] = []
        with self.assertRaisesRegex(EngineError, "at least one"):
            validate_manual_receipt(receipt, receipt["candidate"], self.task, self.root)

    def test_profile_and_criterion_validation_rejects_unsafe_exclusions(self):
        for path in (".", "../src", ".factory", ".factory/private", "tests/*", "/absolute", "C:/tests", ".git/config"):
            with self.subTest(path=path):
                profile = deepcopy(self.profile)
                profile["test_paths"] = [path]
                with self.assertRaises(EngineError):
                    validate_profile(profile, draft=True)
        for scopes in (["unknown"], ["ui", "ui"]):
            profile = deepcopy(self.profile)
            profile["review_scopes"] = scopes
            with self.assertRaises(EngineError):
                validate_profile(profile)
        automated = deepcopy(self.task)
        automated["acceptance"][0]["mode"] = "automated"
        validate_task(automated, self.profile, draft=True)
        with self.assertRaises(EngineError):
            validate_task(automated, self.profile)
        task, profile = self.configured_check()
        task["acceptance"][0]["mode"] = "manual"
        with self.assertRaises(EngineError):
            validate_task(task, profile)

    def test_seal_rejects_stale_review_changed_exclusions_and_weakened_requirement(self):
        self.start_build()
        self.finish_manual()
        task, profile = self.configured_check()
        review = self.review_double(task, profile)
        (self.root / "tests/acceptance.py").write_text("# changed after review\n")
        with self.assertRaisesRegex(EngineError, "new_digest"):
            self.flow.seal(task, profile, review)
        changed_paths = deepcopy(profile)
        changed_paths["test_paths"].append("README.md")
        with self.assertRaisesRegex(EngineError, "test_paths"):
            self.flow.seal(task, changed_paths, self.review_double(task, changed_paths))
        changed_task = deepcopy(task)
        changed_task["acceptance"][0]["text"] = "Weakened requirement"
        with self.assertRaisesRegex(EngineError, "Preserve acceptance"):
            self.flow.seal(changed_task, profile, self.review_double(changed_task, profile))
        self.assertFalse(self.flow.status()["contract_sealed"])

    def test_draft_amendment_preserves_history_and_stays_unsealed(self):
        self.start_build()
        previous = self.flow.load()
        changed = deepcopy(self.profile)
        changed["review_scopes"] = ["research"]
        self.flow.amend(self.task, changed, self.review_double(profile=changed), "Record applicable research")
        current = self.flow.load()
        self.assertFalse(current["contract_sealed"])
        self.assertEqual(current["phase"], "build")
        self.assertEqual(current["history"][:-1], previous["history"])
        self.assertEqual(current["contract_history"][0]["profile"], previous["profile"])
        self.assertEqual(current["original_task"], previous["task"])
        self.assertEqual(current["repairs_used"], previous["repairs_used"] + 1)

    def test_changed_acceptance_needs_explicit_authority_and_cannot_replace_request(self):
        self.start_build()
        changed = deepcopy(self.task)
        changed["acceptance"][0]["text"] = "Owner revised the fixture criterion"
        review = self.review_double(task=changed)
        with self.assertRaisesRegex(EngineError, "acceptance_change_authority"):
            self.flow.amend(changed, self.profile, review, "Fixture owner correction")
        review["acceptance_change_authority"] = "Explicit fixture-only owner instruction"
        self.flow.amend(changed, self.profile, review, "Fixture owner correction")
        replacement = deepcopy(changed)
        replacement["request"] = "An unrelated product"
        with self.assertRaisesRegex(EngineError, "original request"):
            self.flow.amend(replacement, self.profile, self.review_double(task=replacement), "Not allowed")

    def test_sealed_amendment_invalidates_acceptance_and_retains_old_protected_hashes(self):
        self.start_build()
        self.finish_manual()
        task, profile = self.configured_check()
        self.flow.seal(task, profile, self.review_double(task, profile))
        self.artifact("batch")
        self.flow.check()
        previous = self.flow.load()
        with (self.root / "tests/acceptance.py").open("a") as stream:
            stream.write("# reviewed fixture check correction\n")
        self.flow.amend(task, profile, self.review_double(task, profile), "Correct final check")
        current = self.flow.load()
        self.assertTrue(current["contract_sealed"])
        self.assertEqual(current["phase"], "build")
        self.assertIsNone(current["checks"])
        self.assertIsNone(current["manual"])
        self.assertEqual(current["contract_history"][-1]["protected"], previous["protected"])
        self.assertNotEqual(current["protected"], previous["protected"])

    def test_pending_operations_and_cancelled_runs_cannot_amend_or_seal(self):
        self.start_build()
        self.finish_manual()
        review = self.review_double()
        state = self.flow.load()
        state["pending_operation"] = "interrupted-operation"
        atomic_json(self.flow.directory / "state.json", state)
        with self.assertRaisesRegex(EngineError, "pending"):
            self.flow.seal(self.task, self.profile, review)
        with self.assertRaisesRegex(EngineError, "pending"):
            self.flow.amend(self.task, self.profile, review, "Cannot skip reconciliation")
        self.flow.cancel("Fixture owner stop")
        with self.assertRaises(EngineError):
            self.flow.amend(self.task, self.profile, review, "Cannot revive stopped work")
        with self.assertRaises(EngineError):
            self.flow.seal(self.task, self.profile, review)

    def test_contract_reviews_require_independence_identity_authority_and_exact_old_digest(self):
        self.start_build()
        self.finish_manual()
        valid = self.review_double()
        for field, value in (("independent", False), ("reviewer", ""), ("authority", ""),
                             ("reason", ""), ("old_digest", "stale"), ("verdict", "FAIL")):
            with self.subTest(field=field):
                review = {**valid, field: value}
                with self.assertRaises(EngineError):
                    self.flow.seal(self.task, self.profile, review)
        self.assertEqual(self.flow.status()["contract_revision"], 0)

    def test_finding_disposition_cannot_hide_high_severity_or_exposure_blockers(self):
        state = {"delivery_version": 2, "profile": self.profile, "task": self.task}
        exception = {key: "Explicit fixture-only authority" for key in
                     ("owner", "reason", "scope", "revisit", "authority")}
        finding = {"severity": "MEDIUM", "location": "README.md:1", "description": "Fixture finding",
                   "disposition": "before-exposure", "exception": exception}
        report = {"verdict": "PASS", "summary": "Synthetic report", "method_followed": True,
                  "criteria": [{"id": "A1", "status": "PASS", "evidence": "Fixture receipt"}],
                  "findings": [finding]}
        self.flow.validate_review(report, state)
        self.assertFalse(self.flow.finding_blocks(finding, state))
        for exposure in ("public", "production"):
            state["profile"] = {**self.profile, "exposure": exposure}
            self.assertTrue(self.flow.finding_blocks(finding, state))
        state["profile"] = {**self.profile, "review_scopes": ["release"]}
        self.assertTrue(self.flow.finding_blocks(finding, state))
        finding["disposition"] = "accepted-deferral"
        finding["severity"] = "HIGH"
        with self.assertRaisesRegex(EngineError, "high severity"):
            self.flow.validate_review(report, state)
        self.assertTrue(self.flow.finding_blocks(finding, state))
        finding["severity"] = "MEDIUM"
        del exception["authority"]
        with self.assertRaises(EngineError):
            self.flow.validate_review(report, state)

    def test_conditional_review_packet_and_read_only_preflight(self):
        bundle = Path(__file__).resolve().parents[1]
        core = {path.relative_to(bundle).as_posix() for path in method_paths(bundle, self.profile)}
        self.assertNotIn(".agents/skills/database-schema/SKILL.md", core)
        self.assertNotIn(".agents/skills/ux-quality/SKILL.md", core)
        self.assertNotIn(".agents/skills/safe-engine/references/fast-run.md", core)
        public = {**self.profile, "interface": "web", "review_scopes": ["assets", "seo", "persistence"]}
        listed = method_paths(bundle, public)
        paths = {path.relative_to(bundle).as_posix() for path in listed}
        self.assertEqual(len(listed), len(paths))  # routed skills are listed once
        for required in ("analyze-start/SKILL.md", "ticketing/SKILL.md", "deep-review/references/security.md",
                         "ux-quality/SKILL.md", "ux-quality/references/assets.md",
                         "ux-quality/references/web-seo.md", "database-schema/SKILL.md",
                         "safe-engine/SKILL.md", "safe-engine/references/product-bar.md",
                         "safe-engine/references/controller.md"):
            self.assertIn(".agents/skills/" + required, paths)
        self.assertTrue(all(path.is_file() for path in listed))
        missing = {**self.profile, "checks": [{"id": "absent", "argv": ["missing-factory-test-tool"]}]}
        with patch("safe_engine.review_packet.shutil.which", return_value=None):
            result = preflight(self.root, missing)
        self.assertFalse(result["executed_tests"])
        self.assertFalse(result["local_reviewer"]["available"])
        self.assertEqual(result["local_reviewer"]["authentication"], "UNKNOWN")
        self.assertFalse(result["cloud_pr_review"]["local_substitute_allowed"])
        self.assertFalse((self.root / ".factory/state.json").exists())
        state = {"profile": self.profile, "task": self.task, "base_commit": "fixture-base"}
        prompt = prompt_for(state, self.root / ".factory", bundle)
        self.assertIn("not PR review", prompt)
        self.assertIn("Test-only exclusions must not", prompt)


if __name__ == "__main__":
    unittest.main()
