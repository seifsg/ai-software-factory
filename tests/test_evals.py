"""Eval runner with fake agents: no network, no model. Real agent runs never belong in this suite."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import time
from unittest.mock import patch

from eval_fixtures import EvalCase, dead_soon, fake, sleeper
from evals import catalog, isolation, report, runner
from evals.__main__ import main
from evals.check import load_rubric


class EvalRunTests(EvalCase):
    def test_rubrics_fail_on_fixture_and_pass_on_reference(self):
        for sample in catalog.find():
            with self.subTest(sample=sample.name):
                self.assertEqual(catalog.self_check(sample), [])
        self.assertEqual({s.name for s in catalog.find()}, {"cli-tool", "web-feature", "bug-fix"})

    def test_fake_agent_runs_both_arms_isolated_on_an_export(self):
        before = isolation.digest(catalog.ROOT)
        base = runner.run_all(fake("none"), self.tmp / "base", jobs=6, factory_template=fake("factory"))
        self.assertEqual(isolation.digest(catalog.ROOT), before)
        self.assertEqual(list(self.scratch.iterdir()), [])  # temp copies, private rubrics and exports removed
        self.assertFalse(base["interrupted"])
        for run in base["runs"]:
            with self.subTest(sample=run["sample"], arm=run["arm"]):
                self.assertEqual((run["exit"], run["timed_out"], run["void"], run["escapes"]), (0, False, None, []))
                keep = getattr(load_rubric(catalog.ROOT / run["sample"]), "KEEP", set())
                self.assertEqual(run["delivered"], run["total"] if run["arm"] == "factory" else len(keep))
                self.assertEqual(set(run["failing"]) & keep, set())
        paths = report.write(base, self.tmp / "base")
        self.assertEqual(report.load(paths[0]), {"runs": json.loads(json.dumps(base["runs"]))})
        text = paths[1].read_text(encoding="utf-8")
        self.assertIn("| bug-fix | plain | 1/4 | R1: AssertionError", text)
        self.assertIn("| factory | 10/10 |", text)

    def test_checkout_edits_void_the_runs(self):
        samples = self.tmp / "samples"
        shutil.copytree(catalog.ROOT / "bug-fix", samples / "bug-fix")
        with patch.object(catalog, "ROOT", samples), patch.dict(os.environ, {"FAKE_SAMPLES": str(samples)}):
            result = runner.run_all(fake("none", "tamper"), self.tmp / "out", jobs=1)
        self.assertIn("lambda", (samples / "bug-fix/rubric.py").read_text(encoding="utf-8"))  # it did tamper
        for run in result["runs"]:
            self.assertEqual(run["delivered"], 0)
            self.assertEqual(run["void"], "the checkout's eval files changed during the run")
        self.assertIn("VOID: the checkout's eval files changed", report.markdown(result))

    def test_writes_outside_the_run_folder_are_reported(self):
        with patch.dict(os.environ, {"FAKE_ESCAPE": str(self.scratch)}):
            result = runner.run_all(fake("none", "escape"), self.tmp / "out", names=["bug-fix"], jobs=1)
        self.assertEqual({run["arm"]: run["escapes"] for run in result["runs"]},
                         {"factory": ["escaped-factory.txt"], "plain": ["escaped-plain.txt"]})
        self.assertIn("escaped to temp: escaped-plain.txt", report.markdown(result))

    def test_timeout_kills_the_whole_agent_tree_and_fails_every_item(self):
        pids = self.tmp / "pids"
        pids.mkdir()
        started = time.monotonic()
        result = runner.run_all(sleeper(pids), self.tmp / "slow", names=["bug-fix"], minutes=0.1, jobs=2)
        self.assertLess(time.monotonic() - started, 40)  # the agents sleep 60 s; only the kill ends them sooner
        for run in result["runs"]:
            self.assertEqual((run["timed_out"], run["exit"], run["delivered"]), (True, None, 0))
            self.assertEqual(set(run["failing"].values()), {"agent timed out"})
        self.assertEqual(len(list(pids.iterdir())), 2)
        for pid in pids.iterdir():
            self.assertTrue(dead_soon(int(pid.name)), f"agent process {pid.name} survived the timeout")

    def test_interrupt_stops_running_and_queued_runs_and_writes_a_partial_report(self):
        pids, out, real_wait = self.tmp / "pids", self.tmp / "int", runner.wait
        pids.mkdir()

        def interrupt_once_running(pending, timeout):
            deadline = time.monotonic() + 30
            while not any(pids.iterdir()) and time.monotonic() < deadline:
                real_wait(pending, timeout=0.2)
            raise KeyboardInterrupt
        args = ["run", "--agent", sleeper(pids), "--sample", "bug-fix", "--sample", "cli-tool", "--out", str(out)]
        started = time.monotonic()
        with patch.object(runner, "wait", interrupt_once_running), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args), 130)
        self.assertLess(time.monotonic() - started, 40)
        saved = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertEqual((saved["interrupted"], saved["runs"]), (True, []))
        self.assertIn("Interrupted", (out / "report.md").read_text(encoding="utf-8"))
        self.assertEqual(len(list((out / "logs").iterdir())), 1)  # the three queued runs never started
        self.assertTrue(all(dead_soon(int(pid.name)) for pid in pids.iterdir()))
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_fixture_copy_starts_with_a_commit(self):
        work = catalog.copy_fixture(catalog.find(["bug-fix"])[0], self.tmp)
        runner.git_init(work)
        git = ["git", "-C", str(work)]
        self.assertEqual(subprocess.run([*git, "rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout,
                         "1\n")
        self.assertEqual(subprocess.run([*git, "status", "--porcelain"], capture_output=True, text=True).stdout, "")
