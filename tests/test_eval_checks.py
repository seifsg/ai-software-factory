"""Eval rubric checks, command quoting and the baseline compare: candidate tricks fail, bad reports are refused."""
import contextlib
import io
import json
import os
import shutil
import time

from eval_fixtures import EvalCase, fake
from evals import agent, catalog, isolation, report
from evals.__main__ import main

EARLY_EXIT = "import os\nos._exit(0)\n"
HOLD_PIPE = "import subprocess, sys\nsubprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'])\n"


class EvalCheckTests(EvalCase):
    def workspace(self, name, files, reference=False):
        """A scored workspace for sample `name`: the fixture, optionally the reference, then `files` on top."""
        sample, root = catalog.find([name])[0], self.tmp / name
        work = catalog.copy_fixture(sample, root)
        if reference:
            shutil.copytree(sample / "reference", work, dirs_exist_ok=True)
        for file, text in files.items():
            (work / file).write_text(text, encoding="utf-8")
        return catalog.score(sample, work, root, isolation.run_env(root))

    def test_early_exit_and_stdlib_shadowing_fail(self):
        invoice = (catalog.ROOT / "bug-fix/reference/invoice.py").read_text(encoding="utf-8")
        failing = self.workspace("bug-fix", {"invoice.py": EARLY_EXIT + invoice})
        self.assertLessEqual({"R1", "R2", "R3"}, set(failing))
        self.assertIn("pass marker", failing["R1"])
        failing = self.workspace("cli-tool", {"tempfile.py": EARLY_EXIT}, reference=True)
        self.assertEqual(failing, {})  # the rubric's own tempfile loaded first; the shadow changes nothing

    def test_a_child_holding_the_output_does_not_hang_the_check(self):
        invoice = (catalog.ROOT / "bug-fix/reference/invoice.py").read_text(encoding="utf-8")
        started = time.monotonic()
        failing = self.workspace("bug-fix", {"invoice.py": HOLD_PIPE + invoice})
        self.assertLess(time.monotonic() - started, 15)  # the held child sleeps 20 s
        self.assertEqual(failing, {})

    def test_cmd_quoting_refuses_what_it_would_expand(self):
        values = dict.fromkeys(agent.PLACEHOLDERS, "a b")
        self.assertEqual(agent.fill("x {workdir} {other}", values),
                         'x "a b" {other}' if os.name == "nt" else "x 'a b' {other}")
        if os.name == "nt":
            with self.assertRaisesRegex(ValueError, "cmd"):
                agent.quote(r"C:\x%PATH%y")
        else:
            self.assertEqual(agent.quote("x%PATH%y"), "x%PATH%y")

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
        self.assertIn("not an eval report", err.getvalue())
        self.assertFalse(out.exists())  # refused before any agent ran
