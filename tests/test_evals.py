"""Eval runner with a fake agent: no network, no model. Real agent runs never belong in this suite."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from evals import agent, catalog, report, runner
from evals.__main__ import main
import fake_agent

FAKE = Path(fake_agent.__file__).resolve()


def digest(folder):
    """One hash over every file under `folder`, to prove the runner never writes the samples."""
    files = sorted(p for p in Path(folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return hashlib.sha1(b"".join(p.as_posix().encode() + p.read_bytes() for p in files)).hexdigest()


def fake(delivering):
    """Agent command template running the fake agent; `delivering` arm gets the reference solution."""
    return f"{agent.quote(sys.executable)} {agent.quote(FAKE)} {{arm}} {{sample}} {{workdir}} {delivering}"


class EvalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="evals-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        scratch = self.tmp / "temp"
        scratch.mkdir()
        self.scratch = scratch  # the runner's temp copies land here, so leftovers are visible
        temp = patch.object(tempfile, "tempdir", str(scratch))
        temp.start()
        self.addCleanup(temp.stop)

    def test_rubrics_fail_on_fixture_and_pass_on_reference(self):
        for sample in catalog.find():
            with self.subTest(sample=sample.name):
                self.assertEqual(catalog.self_check(sample), [])
        self.assertEqual({s.name for s in catalog.find()}, {"cli-tool", "web-feature", "bug-fix"})

    def test_fake_agent_runs_both_arms_isolated_and_compare_flags_drops(self):
        before = digest(catalog.ROOT)
        base = runner.run_all(fake("none"), self.tmp / "base", jobs=6, factory_template=fake("factory"))
        self.assertEqual(digest(catalog.ROOT), before)
        self.assertEqual(list(self.scratch.iterdir()), [])  # every temp copy removed
        self.assertEqual(len(base["runs"]), 2 * len(catalog.find()))
        for run in base["runs"]:
            with self.subTest(sample=run["sample"], arm=run["arm"]):
                self.assertEqual((run["exit"], run["timed_out"]), (0, False))  # fake saw its arm's prompt
                delivered = run["arm"] == "factory"
                self.assertEqual(run["delivered"], run["total"] if delivered else 0)
                self.assertEqual(sorted(run["failing"]), [] if delivered else ["R1", "R2", "R3"])
                self.assertTrue((self.tmp / "base/logs" / f"{run['sample']}-{run['arm']}.log").is_file())
        paths = report.write(base, self.tmp / "base")
        self.assertEqual(report.load(paths[0]), json.loads(json.dumps(base)))
        self.assertIn("| bug-fix | plain | 0/3 | R1: AssertionError", paths[1].read_text(encoding="utf-8"))
        self.assertIn("| factory | 9/9 |", paths[1].read_text(encoding="utf-8"))
        dropped = copy.deepcopy(base)
        dropped["runs"] = [dict(r, delivered=r["delivered"] - 1) if r["sample"] == "cli-tool" and r["arm"] == "factory"
                           else r for r in dropped["runs"] if (r["sample"], r["arm"]) != ("bug-fix", "factory")]
        report.write(dropped, self.tmp / "now")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["compare", str(paths[0]), str(self.tmp / "now/report.json")]), 1)
            self.assertEqual(main(["compare", str(paths[0]), str(paths[0])]), 0)
        self.assertIn("DROP bug-fix/factory: 3 -> missing", out.getvalue())
        self.assertIn("DROP cli-tool/factory: 3 -> 2", out.getvalue())
        self.assertNotIn("plain", out.getvalue())

    def test_timeout_kills_the_agent_tree_and_fails_every_item(self):
        marker = self.tmp / "survived.txt"
        code = f"import time, pathlib; time.sleep(3); pathlib.Path('{marker.as_posix()}').write_text('x')"
        started = time.monotonic()
        result = runner.run_all(f'{agent.quote(sys.executable)} -c "{code}"', self.tmp / "slow",
                                names=["bug-fix"], minutes=0.01, jobs=2)
        self.assertLess(time.monotonic() - started, 3)
        for run in result["runs"]:
            self.assertEqual((run["timed_out"], run["exit"], run["delivered"]), (True, None, 0))
            self.assertEqual(set(run["failing"].values()), {"agent timed out"})
        time.sleep(max(0.0, started + 4 - time.monotonic()))
        self.assertFalse(marker.exists(), "a child of the timed-out agent kept running")
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_bad_inputs_are_refused(self):
        values = dict.fromkeys(agent.PLACEHOLDERS, "a b")
        self.assertEqual(agent.fill("x {workdir} {other}", values),
                         'x "a b" {other}' if os.name == "nt" else "x 'a b' {other}")
        for template, names, minutes in (("  ", None, 1), (fake("x"), ["nope"], 1), (fake("x"), None, 0)):
            with self.subTest(template=template, names=names, minutes=minutes), self.assertRaises(ValueError):
                runner.run_all(template, self.tmp / "bad", names=names, minutes=minutes)
        (self.tmp / "broken.json").write_text('{"runs": [{"sample": "x"}]}', encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(main(["compare", str(self.tmp / "broken.json"), str(self.tmp / "missing.json")]), 2)
        self.assertIn("not an eval report", err.getvalue())


if __name__ == "__main__":
    unittest.main()
