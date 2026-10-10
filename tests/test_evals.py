"""Eval runner with fake agents: no network, no model. Real agent runs never belong in this suite."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from unittest.mock import patch

from eval_fixtures import EvalCase, dead_soon, fake, sleeper
from evals import agent, catalog, isolation, report, runner
from evals.__main__ import main


class EvalRunTests(EvalCase):
    def test_rubrics_fail_on_fixture_and_pass_on_reference(self):
        sources = catalog.kit()
        for sample in catalog.load():
            with self.subTest(sample=sample.name):
                self.assertEqual(catalog.self_check(sample, sources), [])
        self.assertEqual({s.name for s in catalog.load()}, {"cli-tool", "web-feature", "bug-fix"})

    def test_fake_agent_runs_both_arms_isolated_on_an_export(self):
        before = isolation.digest(catalog.ROOT)
        base = runner.run_all(fake("none"), self.tmp / "base", jobs=6, factory_template=fake("factory"))
        self.assertEqual(isolation.digest(catalog.ROOT), before)
        self.assertEqual(list(self.scratch.iterdir()), [])  # run folders and exports removed
        self.assertFalse(base["interrupted"])
        keep = {sample.name: sample.keep for sample in catalog.load()}
        for run in base["runs"]:
            with self.subTest(sample=run["sample"], arm=run["arm"]):
                self.assertEqual((run["exit"], run["timed_out"], run["void"], run["possible_escapes"]),
                                 (0, False, None, []))
                expected = run["total"] if run["arm"] == "factory" else len(keep[run["sample"]])
                self.assertEqual(run["delivered"], expected)
        paths = report.write(base, self.tmp / "base")
        self.assertEqual(report.load(paths[0]), {"runs": json.loads(json.dumps(base["runs"]))})
        text = paths[1].read_text(encoding="utf-8")
        self.assertIn("| bug-fix | plain | 1/4 | R1: AssertionError", text)
        self.assertIn("| factory | 10/10 |", text)

    def test_reachable_tricks_do_not_raise_the_score(self):
        result = runner.run_all(fake("none", "cheat"), self.tmp / "out", names=["bug-fix"], jobs=1)
        for run in result["runs"]:
            with self.subTest(arm=run["arm"]):
                self.assertEqual((run["exit"], run["void"]), (0, None))
                self.assertEqual(sorted(run["failing"]), ["R1", "R2", "R3", "R4"])
                self.assertIn("not plain data: Any", run["failing"]["R1"])

    def test_the_parent_never_runs_rubric_code(self):
        samples = self.tmp / "samples"
        shutil.copytree(catalog.ROOT / "bug-fix", samples / "bug-fix")
        marker = self.tmp / "ran.txt"
        rubric = samples / "bug-fix/rubric.py"
        rubric.write_text(f"open(r'{marker}', 'w').close()\n" + rubric.read_text(encoding="utf-8"), encoding="utf-8")
        with patch.object(catalog, "ROOT", samples):
            self.assertEqual(catalog.load()[0].items, ("R1", "R2", "R3", "R4"))
        self.assertFalse(marker.exists())

    def test_checkout_edits_void_the_runs(self):
        samples = self.tmp / "samples"
        shutil.copytree(catalog.ROOT / "bug-fix", samples / "bug-fix")
        with patch.object(catalog, "ROOT", samples), patch.dict(os.environ, {"FAKE_SAMPLES": str(samples)}):
            result = runner.run_all(fake("none", "tamper"), self.tmp / "out", jobs=1)
        self.assertIn("lambda", (samples / "bug-fix/rubric.py").read_text(encoding="utf-8"))  # it did tamper
        for run in result["runs"]:
            self.assertEqual((run["delivered"], run["void"]), (0, "the checkout's eval files changed during the run"))

    def test_writes_into_the_system_temp_are_reported_as_possible(self):
        with patch.dict(os.environ, {"FAKE_ESCAPE": str(self.scratch)}):
            result = runner.run_all(fake("none", "escape"), self.tmp / "out", names=["bug-fix"], jobs=1)
        self.assertEqual({run["arm"]: run["possible_escapes"] for run in result["runs"]},
                         {"factory": ["escaped-factory.txt"], "plain": ["escaped-plain.txt"]})
        self.assertIn("possibly other programs", report.markdown(result))

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
        self.assertTrue(all(dead_soon(int(pid.name)) for pid in pids.iterdir()), "an agent survived the timeout")

    def test_leftovers_die_when_the_agent_exits_normally(self):
        pids = self.tmp / "pids"
        pids.mkdir()
        child = "import time; time.sleep(60)"
        code = (f"import subprocess, sys, pathlib; p = subprocess.Popen([sys.executable, '-c', '{child}']); "
                f"pathlib.Path('{pids.as_posix()}', str(p.pid)).write_text('x')")
        template = f'{agent.quote(sys.executable)} -c "{code}"'
        result = runner.run_all(template, self.tmp / "out", names=["bug-fix"], jobs=2)
        self.assertEqual([run["exit"] for run in result["runs"]], [0, 0])
        self.assertEqual(len(list(pids.iterdir())), 2)
        self.assertTrue(all(dead_soon(int(pid.name)) for pid in pids.iterdir()), "a leftover outlived its agent")

    def test_interrupt_stops_running_and_queued_runs_and_writes_a_partial_report(self):
        pids, out, real_wait = self.tmp / "pids", self.tmp / "int", runner.wait
        pids.mkdir()

        def interrupt_once_running(pending, timeout):
            deadline = time.monotonic() + 30
            while not any(pids.iterdir()) and time.monotonic() < deadline:
                real_wait(pending, timeout=0.2)
            raise KeyboardInterrupt
        args = ["run", "--agent", sleeper(pids), "--sample", "bug-fix", "--sample", "cli-tool", "--out", str(out)]
        with patch.object(runner, "wait", interrupt_once_running), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args), 130)
        saved = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertEqual((saved["interrupted"], saved["runs"]), (True, []))
        self.assertEqual(len(list((out / "logs").iterdir())), 1)  # the three queued runs never started
        self.assertTrue(all(dead_soon(int(pid.name)) for pid in pids.iterdir()))
        self.assertEqual(list(self.scratch.iterdir()), [])
        with self.assertRaisesRegex(ValueError, "interrupted"):
            report.load(out / "report.json")

    def test_an_interrupt_during_scoring_drops_the_row(self):
        scoring, real_wait, real_score = threading.Event(), runner.wait, catalog.score

        def slow_score(*args):
            scoring.set()
            time.sleep(2)  # the interrupt lands now
            return real_score(*args)

        def interrupt_while_scoring(pending, timeout):
            deadline = time.monotonic() + 30  # a regression fails the test instead of hanging it
            while not scoring.is_set() and time.monotonic() < deadline:
                real_wait(pending, timeout=0.2)
            raise KeyboardInterrupt
        with patch.object(catalog, "score", slow_score), patch.object(runner, "wait", interrupt_while_scoring):
            result = runner.run_all(fake("factory"), self.tmp / "out", names=["bug-fix"], jobs=1)
        self.assertEqual((result["interrupted"], result["runs"]), (True, []))  # not a false 0/4

    def test_a_broken_run_is_recorded_and_the_others_continue(self):
        with patch.object(isolation, "export_factory", side_effect=OSError("disk full")):
            result = runner.run_all(fake("plain"), self.tmp / "out", names=["bug-fix"], jobs=1)
        rows = {run["arm"]: run for run in result["runs"]}
        self.assertEqual((rows["factory"]["error"], rows["factory"]["delivered"]), ("OSError: disk full", 0))
        self.assertEqual((rows["plain"].get("error"), rows["plain"]["delivered"]), (None, 4))
        self.assertIn("ERROR: OSError: disk full", report.markdown(result))

    def test_report_folder_inside_evals_is_refused(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            runner.run_all(fake("none"), isolation.EVALS / "out")
        self.assertFalse((isolation.EVALS / "out").exists())

    def test_fixture_copy_starts_with_a_commit(self):
        work = catalog.write_fixture(catalog.load(["bug-fix"])[0], self.tmp / "work")
        runner.git_init(work)
        git = ["git", "-C", str(work)]
        self.assertEqual(subprocess.run([*git, "rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout,
                         "1\n")
        self.assertEqual(subprocess.run([*git, "status", "--porcelain"], capture_output=True, text=True).stdout, "")
