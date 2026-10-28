"""Scored repair boundaries; reviewer/owner claims are explicit fixture doubles, never acceptance proof."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

from safe_engine import worth
from safe_engine.project import EngineError
from safe_engine.review import ReviewMixin
from safe_engine.storage import atomic_json
from speed_fixtures import Base, report
from test_fast_gate import GateHarness, LIGHT

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"))
import fast_round
import fast_record


def finding(required=False, disposition=None):
    """A bounded fixture finding, with explicit synthetic deferral authority for optional polish."""
    return {"location": "README.md:1", "description": "Required sentence" if required else "Optional spacing",
            "severity": "LOW", "disposition": disposition or ("blocking" if required else "accepted-deferral"),
            "layer": "product", "evidence": "Synthetic fixture observation", "action": "Synthetic fixture action",
            "evidence_status": "valid", "exception": None if required else {
                "owner": "fixture owner", "authority": "Synthetic owner instruction in fixture",
                "reason": "Optional spacing can wait", "scope": "spacing", "revisit": "polish batch",
                "destination": "synthetic:existing-followups"},
            "worth": {"notice": 0, "harm": 0, "minutes": 120, "required": required, "reason": "Fixture estimate"}}


class WorthTests(unittest.TestCase):
    def test_boundaries_unknown_and_invalid_values(self):
        item = finding()
        for minutes, cost in ((0, 2), (14, 2), (15, 1), (59, 1), (60, 0), (120, 0), (None, None)):
            with self.subTest(minutes=minutes):
                item["worth"]["minutes"] = minutes
                self.assertEqual(worth.assess(item)["cost"], cost)
        for field, value in (("minutes", True), ("minutes", -1), ("notice", 3), ("harm", 4),
                             ("required", 1), ("reason", ""), ("reason", "injected\nline")):
            changed = finding()
            changed["worth"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                worth.assess(changed)

    def test_selection_preserves_required_quality_and_authority(self):
        body = {"findings": [finding(), finding(True)]}
        for chosen in (["F1"], ["F1", "F2"], ["F1", "F1"], ["F9"], []):
            with self.subTest(chosen=chosen), self.assertRaises(ValueError):
                worth.select(body, chosen)
        self.assertEqual(worth.select(body, ["F2"])["selected"], ["F2"])
        self.assertEqual(worth.select(body, ["F1"], "Synthetic owner starts batch")["selected"], ["F1"])
        for value in ("", "instruction\nwithout source"):
            with self.assertRaises(ValueError):
                worth.select(body, ["F1"], value)
        body["findings"][0]["worth"]["minutes"] = None
        with self.assertRaisesRegex(ValueError, "estimate"):
            worth.select(body, ["F1"], "Synthetic owner starts batch")

    def test_required_low_and_high_severity_cannot_be_parked(self):
        for field, value in (("required", True), ("harm", 3)):
            item = finding()
            item["worth"][field] = value
            with self.assertRaisesRegex(ValueError, "cannot be parked"):
                worth.rows({"findings": [item]})
        for severity in ("HIGH", "CRITICAL"):
            item = {**finding(), "severity": severity}
            with self.assertRaises(ValueError):
                worth.rows({"findings": [item]})
        self.assertTrue(ReviewMixin.finding_blocks(finding(True, "before-exposure"), {"worth": True}))

    def test_one_followups_destination_and_plain_output(self):
        body = {"findings": [finding(), finding()]}
        self.assertIn("Optional spacing (worth it 0/7). Optional spacing can wait", worth.parked_lines(body)[0])
        body["findings"][1]["exception"]["destination"] = "synthetic:duplicate-ticket"
        with self.assertRaisesRegex(ValueError, "one existing"):
            worth.rows(body)

    def test_all_prior_findings_need_one_unchanged_retention_resolution_or_cancellation(self):
        original = {"findings": [finding(), finding(True), finding(False, "before-exposure")]}
        rounds = [{"sha256": "receipt", "report": original, "selected": ["F2"]}]
        final = {"findings": [], "resolved": [{"report_sha256": "receipt", "finding": "F2", "evidence": "Fixture observed"}]}
        with self.assertRaisesRegex(ValueError, "F1.*F3"):
            worth.reconcile(final, rounds)
        final.update(findings=[original["findings"][0]],
                     retained=[{"report_sha256": "receipt", "finding": "F1", "current_finding": "F1"}],
                     cancelled=[{"report_sha256": "receipt", "finding": "F3", "owner": "fixture owner",
                                 "authority": "Synthetic scope withdrawal instruction and source", "reason": "Fixture only"}])
        worth.reconcile(final, rounds)
        for mode in ("missing", "duplicate", "foreign", "changed", "authority"):
            changed = deepcopy(final)
            if mode == "missing":
                changed.pop("cancelled")
            elif mode == "duplicate":
                changed["resolved"].append({"report_sha256": "receipt", "finding": "F1", "evidence": "Contradiction"})
            elif mode == "foreign":
                changed["retained"][0]["report_sha256"] = "foreign"
            elif mode == "changed":
                changed["findings"][0]["description"] = "Replacement"
            else:
                changed["cancelled"][0].pop("authority")
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                worth.reconcile(changed, rounds)

    def test_any_receipt_selection_requires_settlement_only_at_completion(self):
        original = {"findings": [finding(), {**finding(), "description": "Other optional polish"}]}
        rounds = [{"sha256": "receipt", "report": original, "selected": [number]} for number in ("F1", "F2")]
        final = {**original, "retained": [{"report_sha256": "receipt", "finding": number,
                                          "current_finding": number} for number in ("F1", "F2")]}
        for receipts in (rounds, rounds[::-1], rounds + rounds):
            with self.subTest(receipts=receipts), self.assertRaisesRegex(ValueError, "Selected findings"):
                worth.reconcile(final, receipts)
            worth.reconcile(final, receipts, completed=False)
        with self.assertRaisesRegex(ValueError, "Reconcile every"):
            worth.reconcile({"findings": []}, rounds, completed=False)
        final = {"findings": [], "resolved": [{"report_sha256": "receipt", "finding": "F1", "evidence": "Synthetic observation"}],
                 "cancelled": [{"report_sha256": "receipt", "finding": "F2", "owner": "fixture owner",
                                "authority": "Synthetic cancellation; fixture source", "reason": "Fixture only"}]}
        worth.reconcile(final, rounds)
        for group, field in (("resolved", "evidence"), ("cancelled", "authority")):
            changed = deepcopy(final)
            changed[group][0].pop(field)
            with self.subTest(group=group), self.assertRaises(ValueError):
                worth.reconcile(changed, rounds)


class FastWorthTests(GateHarness, unittest.TestCase):
    def test_finishing_completion_refuses_retained_selection_from_any_receipt(self):
        self.start("--no-ui", "--no-data", kind="change")
        self.pr_body()
        (self.project / ".factory/fast/work-record.md").write_text(
            LIGHT.replace("**Findings:** none", "**Findings:** .factory/final.json"), encoding="utf-8")
        for step in ("tickets", "plan"):
            self.gate("done", step)
        source = self.project / ".factory/findings.json"
        original = [finding(), {**finding(), "description": "Second optional item"},
                    {**finding(), "description": "Unselected optional item"}]
        atomic_json(source, {"findings": original})
        for number in ("F1", "F2"):
            self.gate("fix-round", "--file", str(source), "--finding", number,
                      "--finishing-authority", "Synthetic owner requests batch; fixture source")
        state = json.loads((self.project / ".factory/fast/run.json").read_text(encoding="utf-8"))
        self.assertEqual(state["fix_rounds"][0]["sha256"], state["fix_rounds"][1]["sha256"])
        digest = state["fix_rounds"][0]["sha256"]
        path = self.project / ".factory/final.json"
        final = {"findings": [original[0], original[2]], "retained": [
            {"report_sha256": digest, "finding": number, "current_finding": f"F{index}"}
            for index, number in enumerate(("F1", "F3"), 1)],
            "resolved": [{"report_sha256": digest, "finding": "F2", "evidence": "Synthetic observation"}]}
        atomic_json(path, final)
        self.gate("done", "build")
        self.assertIn("Selected findings", self.gate("done", "done-run", ok=False))
        final["findings"] = [original[2]]
        final["retained"] = [{"report_sha256": digest, "finding": "F3", "current_finding": "F1"}]
        final["resolved"].append({"report_sha256": digest, "finding": "F1", "evidence": "Synthetic observation"})
        atomic_json(path, final)
        self.gate("done", "done-run")

    def test_real_repair_receipt_reopens_done_and_blocks_unselected_finding_loss(self):
        self.start("--no-ui", "--no-data", kind="change")
        self.pr_body()
        work = self.project / ".factory/fast/work-record.md"
        work.write_text(LIGHT + "\n", encoding="utf-8")
        for step in ("tickets", "plan"):
            self.gate("done", step)
        path = self.project / ".factory/findings.json"
        atomic_json(path, {"findings": [finding(), finding(True)]})
        self.assertIn("optional score", self.gate("fix-round", "--file", str(path), "--finding", "F1", ok=False))
        accepted = self.gate("fix-round", "--file", str(path), "--finding", "F2")
        decision, _ = json.JSONDecoder().raw_decode(accepted)
        state = json.loads((self.project / ".factory/fast/run.json").read_text(encoding="utf-8"))
        canonical = hashlib.sha256(json.dumps(json.loads(path.read_text(encoding="utf-8")), sort_keys=True).encode()).hexdigest()
        self.assertEqual(decision["report_sha256"], state["fix_rounds"][0]["sha256"])
        self.assertEqual(decision["report_sha256"], canonical)
        self.assertNotEqual(decision["report_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertNotIn("done-run", state["done"])
        self.assertTrue(fast_round.findings("**Findings:** none", self.project, fast_record.marker, state))
        final = {"findings": [], "resolved": [{"report_sha256": state["fix_rounds"][0]["sha256"],
                                               "finding": "F2", "evidence": "Synthetic fixture evidence"}]}
        atomic_json(path, final)
        self.assertIn("F1", " ".join(fast_round.findings("**Findings:** .factory/findings.json", self.project, fast_record.marker, state)))


class SafeWorthTests(Base):
    def test_selected_deferral_cannot_pass_but_truthful_failed_review_is_recorded(self):
        f = self.fixture()
        f.start_build()
        f.artifact("implementation")
        path = f.flow.directory / "findings.json"
        original = finding()
        atomic_json(path, {"findings": [original]})
        f.flow.repair("Fixture finishing batch", findings=path, selected=["F1"],
                      finishing_authority="Synthetic owner requests batch; fixture source")
        receipt = f.flow.load()["fix_rounds"][0]
        f.finish_manual()
        self.seal_with(f)
        f.flow.check()
        f.flow.review_packet(f.flow.directory / "packet.md")
        final = report(findings=[original])
        final.update(retained=[{"report_sha256": receipt["sha256"], "finding": "F1", "current_finding": "F1"}])
        final["summary"] = f.flow.load()["review_packet"]["nonce"] + " Synthetic reviewer double"
        external = f.flow.directory / "external.json"
        atomic_json(external, final)
        before = f.flow.load()
        with self.assertRaisesRegex(EngineError, "Selected findings"):
            f.flow.review(report=external, reviewer="Synthetic reviewer")
        self.assertEqual(f.flow.load(), before)
        final["verdict"] = "FAIL"
        atomic_json(external, final)
        result = f.flow.review(report=external, reviewer="Synthetic reviewer")
        self.assertEqual((result["phase"], result["failed_reviews"]), ("review", 1))
        with self.assertRaises(EngineError):
            f.flow.handoff()

    def test_repair_review_and_handoff_preserve_unselected_polish(self):
        f = self.fixture()
        f.start_build()
        f.artifact("implementation")
        path = f.flow.directory / "failure.json"
        body = {"findings": [finding(), finding(True)]}
        atomic_json(path, body)
        before = f.flow.load()
        with self.assertRaisesRegex(EngineError, "optional score"):
            f.flow.repair("Fixture repair", findings=path, selected=["F1"])
        self.assertEqual(f.flow.load(), before)
        f.flow.repair("Fixture repair", findings=path, selected=["F2"])
        receipt = f.flow.load()["fix_rounds"][0]
        f.finish_manual()
        self.seal_with(f)
        f.flow.check()
        final = report(findings=[body["findings"][0]])
        final.update(retained=[{"report_sha256": receipt["sha256"], "finding": "F1", "current_finding": "F1"}],
                     resolved=[{"report_sha256": receipt["sha256"], "finding": "F2", "evidence": "Explicit regression double"}])
        with self.assertRaisesRegex(EngineError, "Reconcile every"):
            ReviewMixin.validate_review(report(), f.flow.load())
        f.flow.review_packet(f.flow.directory / "packet.md")
        final["summary"] = f.flow.load()["review_packet"]["nonce"] + " Synthetic reviewer double"
        atomic_json(f.flow.directory / "external.json", final)
        self.assertEqual(f.flow.review(report=f.flow.directory / "external.json", reviewer="Synthetic regression reviewer")["phase"], "ready")
        handoff = Path(f.flow.handoff()["handoff"]).read_text(encoding="utf-8")
        self.assertIn("Parked: Optional spacing", handoff)

    def test_saved_pre_worth_run_retains_old_repair_contract(self):
        f = self.fixture()
        f.start_build()
        f.artifact("implementation")
        self.set_state(f, worth=False)
        self.assertEqual(f.flow.repair("Legacy correction")["phase"], "build")


if __name__ == "__main__":
    unittest.main()
