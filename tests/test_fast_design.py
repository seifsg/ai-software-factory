"""Design evidence cannot shrink scope or survive a changed candidate/capture."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from png_fixtures import png

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
sys.path.insert(0, str(SCRIPTS))
import fast_design as design


class DesignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        cache_home = patch.dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "cache-home"))
        cache_home.start()
        self.addCleanup(cache_home.stop)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / ".gitignore").write_text(".factory/\n")
        (self.root / "source.txt").write_text("original\n")
        (self.root / ".factory").mkdir()
        png(self.root / ".factory/ref.png")
        png(self.root / ".factory/current.png")
        self.data = {"version": 1, "builder": "builder", "screens": [
            {"id": "home", "reference": ".factory/ref.png", "viewport": [64, 32], "theme": "light", "state": "ready"}],
            "elements": [{"id": "title", "screen": "home", "name": "Title", "status": "done"},
                         {"id": "panel", "screen": "home", "name": "Panel", "status": "missing"}]}
        self.run = {"design_port": True, "project": str(self.root), "design": {
            "path": ".factory/coverage.json", "inventory": design.inventory(self.root, self.data)}}
        self.save()

    def save(self):
        (self.root / ".factory/coverage.json").write_text(json.dumps(self.data), encoding="utf-8")

    def review(self):
        """A controlled fixture identity is evidence data, not a real independent verdict."""
        return {"version": 1, "reviewer": "judge", "independent": True,
                "candidate": design.candidate(self.root), "screens": [
                    {"id": "home", "capture": ".factory/current.png", "viewport": [64, 32],
                     "theme": "light", "state": "ready"}],
                "elements": [{"id": e["id"], "status": e["status"], "evidence": "Observed fixture",
                              "differences": [] if e["status"] == "done" else ["Panel absent"]}
                             for e in self.data["elements"]]}

    def accept(self):
        self.data["elements"][1]["status"] = "done"
        self.save()
        review = self.review()
        path = self.root / ".factory/review.json"
        path.write_text(json.dumps(review), encoding="utf-8")
        self.run["design"]["review"] = {"path": ".factory/review.json", "sha256": design.file_hash(path),
            "evidence": design.review_evidence(self.root, self.run, self.data, review)}
        self.assertEqual(design.problems(self.run, self.root, final=True), [])

    def test_cuts_need_recorded_answer_and_keep_original_denominator(self):
        row = self.data["elements"][1]
        row["status"] = "cut"
        self.save()
        self.assertIn("owner", " ".join(design.problems(self.run, self.root)))
        row["approval"] = {"actor": "owner", "source": "ticket comment", "quote": "Cut the panel"}
        self.save()
        self.assertEqual(design.problems(self.run, self.root), [])
        report = design.summary(self.data)
        self.assertEqual((report["done"], report["cut"], report["total"]), (1, 1, 2))
        self.assertIn("1 of 2 design elements", design.report(self.run))
        self.assertIn("independent likeness", " ".join(design.problems(self.run, self.root, final=True)))

    def test_original_inventory_and_reference_bytes_cannot_change(self):
        for mutation in (lambda: self.data["elements"].pop(),
                         lambda: self.data["elements"][0].update(name="Different"),
                         lambda: png(self.root / ".factory/ref.png", color=1)):
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.data)
                mutation()
                self.save()
                self.assertIn("inventory or reference changed", " ".join(design.problems(self.run, self.root)))
                self.data = original
                png(self.root / ".factory/ref.png")
                self.save()

    def test_review_requires_independence_matched_state_and_all_observations(self):
        for mutation in (lambda r: r.update(reviewer="builder"), lambda r: r.update(independent=False),
                         lambda r: r["screens"][0].update(theme="dark"),
                         lambda r: r["screens"][0].update(state="empty"),
                         lambda r: r["elements"].pop(),
                         lambda r: r["elements"][0].update(differences=["Wrong density"]),
                         lambda r: r["elements"][1].update(differences=[])):
            with self.subTest(mutation=mutation):
                review = self.review()
                mutation(review)
                with self.assertRaises(ValueError):
                    design.review_evidence(self.root, self.run, self.data, review)

    def test_partial_and_missing_block_final_but_approved_cut_can_finish(self):
        for status in ("partial", "missing"):
            self.data["elements"][1]["status"] = status
            self.save()
            self.assertIn("Unresolved design elements: panel", " ".join(design.final_problems(self.root, self.run)))
        self.accept()
        self.data["elements"][1].update(status="cut", approval={"actor": "owner", "source": "comment", "quote": "Cut"})
        self.save()
        review = self.review()
        path = self.root / ".factory/review.json"
        path.write_text(json.dumps(review))
        self.run["design"]["review"].update(sha256=design.file_hash(path),
            evidence=design.review_evidence(self.root, self.run, self.data, review))
        self.assertEqual(design.final_problems(self.root, self.run), [])

    def test_done_proof_expires_on_source_capture_report_or_review_change(self):
        mutations = [lambda: (self.root / "source.txt").write_text("changed"),
                     lambda: png(self.root / ".factory/current.png", color=2),
                     lambda: (self.root / ".factory/review.json").write_text("{}"),
                     lambda: self.data.update(note="new coverage observation")]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.accept()
                mutation()
                self.save()
                self.assertTrue(design.final_problems(self.root, self.run))

    def test_candidate_sees_tracked_dirty_untracked_deleted_but_not_ignored_evidence(self):
        subprocess.run(["git", "-C", str(self.root), "add", "source.txt", ".gitignore"], check=True)
        initial = design.candidate(self.root)
        (self.root / ".factory/log.txt").write_text("runtime")
        self.assertEqual(initial, design.candidate(self.root))
        source = self.root / "source.txt"
        source.write_text("dirty")
        self.assertNotEqual(initial, design.candidate(self.root))
        source.write_text("original\n")
        self.assertEqual(initial, design.candidate(self.root))
        new = self.root / "new.txt"
        new.write_text("new")
        self.assertNotEqual(initial, design.candidate(self.root))
        new.unlink()
        source.unlink()
        self.assertNotEqual(initial, design.candidate(self.root))

    def test_bad_inputs_fail_closed_and_old_runs_are_unaffected(self):
        self.assertEqual(design.problems({}, self.root, final=True), [])
        self.assertIsNone(design.report({}))
        for mutation in (lambda: self.data.update(version=True),
                         lambda: self.data["screens"][0].update(viewport=[2, 1]),
                         lambda: self.data["elements"].append(self.data["elements"][0]),
                         lambda: self.data["screens"][0].update(reference="../outside.png")):
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.data)
                mutation()
                self.save()
                self.assertTrue(design.problems(self.run, self.root))
                self.data = original


if __name__ == "__main__":
    unittest.main()
