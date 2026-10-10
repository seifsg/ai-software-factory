"""Eval rubric checks, command quoting, cleanup and the baseline compare: candidate tricks fail, bad reports fail."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

from eval_fixtures import EvalCase, fake
from evals import agent, catalog, isolation, report
from evals.__main__ import main
from evals.rubric_tools import same

EARLY_EXIT = "import os\nos._exit(0)\n"
HOLD_PIPE = "import subprocess, sys\nsubprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'])\n"
BROKEN_TAX = "\n\ndef total(lines, discount_percent=0, tax_percent=0):\n    return subtotal(lines)\n"
MATCHING_TEST = ("import unittest\nfrom invoice import total\n\n\nclass T(unittest.TestCase):\n"
                 "    def test_tax(self):\n        self.assertEqual(total([{'qty': 1, 'price': 1000}], tax_percent=20),"
                 " 1000)\n")


class EvalCheckTests(EvalCase):
    def workspace(self, name, files, reference=False, remove=()):
        """Score sample `name`: its fixture, optionally the reference, `files` on top, `remove` deleted."""
        sample, root = catalog.load([name])[0], Path(tempfile.mkdtemp(prefix=name, dir=self.tmp))
        work = catalog.write_fixture(sample, root / "work")
        if reference:
            catalog.write_files(sample.solution, work)
        for file, text in files.items():
            (work / file).write_text(text, encoding="utf-8")
        for file in remove:
            (work / file).unlink()
        return catalog.score(sample, catalog.kit(), work, root, isolation.run_env(root)), root

    def reference(self, name):
        return (catalog.ROOT / "bug-fix/reference" / name).read_text(encoding="utf-8")

    def test_early_exit_and_stdlib_shadowing_fail(self):
        failing, root = self.workspace("bug-fix", {"invoice.py": EARLY_EXIT + self.reference("invoice.py")})
        self.assertEqual(sorted(failing), ["R1", "R2", "R3", "R4"])
        self.assertIn("0 result records", failing["R1"])
        self.assertEqual([p.name for p in root.iterdir() if p.is_file()], [])  # verdicts come over a pipe
        self.assertFalse((root / "checks").exists())
        failing, _ = self.workspace("cli-tool", {"tempfile.py": EARLY_EXIT, "json.py": EARLY_EXIT}, reference=True)
        self.assertEqual(failing, {})  # rubric and tools never import from the workspace

    def test_a_child_holding_the_output_does_not_hang_the_check(self):
        started = time.monotonic()
        failing, _ = self.workspace("bug-fix", {"invoice.py": HOLD_PIPE + self.reference("invoice.py")})
        self.assertLess(time.monotonic() - started, 15)  # the held child sleeps 20 s
        self.assertEqual(failing, {})

    def test_edited_tests_do_not_hide_a_regression(self):
        failing, _ = self.workspace("bug-fix", {"invoice.py": self.reference("invoice.py") + BROKEN_TAX,
                                                "test_invoice.py": MATCHING_TEST})
        self.assertIn("R4", failing)  # the original tests ran, not the edited ones
        failing, _ = self.workspace("bug-fix", {}, reference=True, remove=("test_invoice.py",))
        self.assertEqual(failing, {})  # deleting them hides nothing either

    def test_same_is_type_strict(self):
        self.assertTrue(same([1, {"a": "x"}], [1, {"a": "x"}]))
        for actual, expected in ((True, 1), (1.0, 1), ([1], (1,)), ({"a": 1}, {"a": 1, "b": 2}), ([1, 2], [1])):
            with self.subTest(actual=actual, expected=expected):
                self.assertFalse(same(actual, expected))

    def test_cmd_quoting_always_quotes_and_refuses_what_it_would_expand(self):
        values = dict.fromkeys(agent.PLACEHOLDERS, r"C:\R&D\w")
        self.assertEqual(agent.fill("x {workdir} {other}", values),
                         'x "C:\\R&D\\w" {other}' if os.name == "nt" else "x 'C:\\R&D\\w' {other}")
        if os.name == "nt":
            self.assertEqual(agent.quote("C:\\x\\"), '"C:\\x\\\\"')
            with self.assertRaisesRegex(ValueError, "cmd"):
                agent.quote(r"C:\x%PATH%y")
        else:
            self.assertEqual(agent.quote("x%PATH%y"), "x%PATH%y")

    def test_cleanup_failures_are_reported(self):
        folder = self.tmp / "stuck"
        folder.mkdir()
        def stuck(path, ignore_errors=False, **_):
            if not ignore_errors:
                raise OSError("locked")
        with patch.object(isolation.shutil, "rmtree", stuck), patch.object(isolation.time, "sleep"):
            self.assertIn("could not delete", isolation.remove(folder))

    def test_compare_flags_totals_new_and_missing_pairs(self):
        def runs(*rows):
            return {"runs": [dict(zip(("sample", "arm", "delivered", "total"), row)) for row in rows]}
        baseline = runs(("a", "factory", 3, 3), ("b", "factory", 2, 3), ("c", "plain", 1, 3))
        current = runs(("a", "factory", 3, 4), ("b", "factory", 1, 3), ("d", "plain", 0, 3))
        problems, notes = report.compare(baseline, current)
        self.assertEqual(problems, ["CHANGED a/factory: total 3 -> 4, not comparable", "DROP b/factory: 2 -> 1",
                                    "DROP c/plain: 1 -> missing"])
        self.assertEqual(notes, ["NEW d/plain: not in the baseline"])
        self.assertEqual(report.compare(baseline, baseline), ([], []))

    def test_a_baseline_must_be_clean_and_compare_labels_broken_rows(self):
        clean = {"sample": "a", "arm": "x", "delivered": 3, "total": 3}
        for flaw in ({"error": "OSError: disk full"}, {"void": "edited"}, {"timed_out": True}):
            path = self.tmp / "flawed.json"
            path.write_text(json.dumps({"runs": [{**clean, **flaw}]}), encoding="utf-8")
            with self.subTest(flaw=flaw):
                self.assertEqual(report.load(path)["runs"][0]["delivered"], 3)  # fine as a current report
                with self.assertRaisesRegex(ValueError, "clean runs"):
                    report.load(path, baseline=True)
        broken = {**clean, "delivered": 0, "error": "OSError: disk full"}
        self.assertEqual(report.compare({"runs": [clean]}, {"runs": [broken]})[0],
                         ["DROP a/x: 3 -> 0 (error: OSError: disk full)"])

    def test_malformed_reports_are_refused_before_any_run(self):
        bad = {"bool": [{"sample": "a", "arm": "x", "delivered": True, "total": 3}],
               "over": [{"sample": "a", "arm": "x", "delivered": 4, "total": 3}],
               "twice": [{"sample": "a", "arm": "x", "delivered": 1, "total": 3}] * 2,
               "short": [{"sample": "a", "arm": "x", "delivered": 1}]}
        for name, rows in bad.items():
            path = self.tmp / f"{name}.json"
            path.write_text(json.dumps({"runs": rows}), encoding="utf-8")
            with self.subTest(name=name), self.assertRaises(ValueError):
                report.load(path)
        out = self.tmp / "never"
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(main(["run", "--agent", fake("factory"), "--baseline", str(self.tmp / "bool.json"),
                                   "--out", str(out)]), 2)
        self.assertIn("not a usable eval report", err.getvalue())
        self.assertFalse(out.exists())  # refused before any agent ran
