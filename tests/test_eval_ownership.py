"""Eval ownership refuses unowned work and confirms exact descendants have exited."""
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import Mock, patch

from eval_fixtures import EvalCase
from evals import catalog, isolation, proc, report, runner

if os.name == "nt":
    from evals import winjob


@unittest.skipUnless(os.name == "nt", "Windows job ownership")
class EvalOwnershipTests(EvalCase):
    def test_native_assignment_refusal_never_runs_and_reaps_command(self):
        marker = self.tmp / "ran"
        original, popen = ctypes.WinDLL, subprocess.Popen
        started = []

        class Refuse:
            def __call__(self, *args):
                ctypes.set_last_error(5)
                return 0

        class Library:
            def __init__(self, library):
                self.library = library
                self.AssignProcessToJobObject = Refuse()

            def __getattr__(self, name):
                return getattr(self.library, name)

        def loader(name, *args, **kwargs):
            library = original(name, *args, **kwargs)
            return Library(library) if name.lower() == "kernel32" else library

        def spawn(*args, **kwargs):
            process = popen(*args, **kwargs)
            started.append(process)
            return process

        tree = None
        try:
            with patch.object(ctypes, "WinDLL", side_effect=loader), patch.object(proc.subprocess, "Popen", spawn):
                with self.assertRaises(OSError):
                    tree = proc.Tree([sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"],
                                     self.tmp, None, False, subprocess.DEVNULL, subprocess.DEVNULL)
            self.assertEqual(len(started), 1)
            self.assertIsNotNone(started[0].returncode, "refused command was not reaped")
            self.assertFalse(marker.exists(), "unowned command executed")
        finally:
            if tree:
                tree.stop()
            for process in started:
                if process.poll() is None:
                    process.kill()
                process.wait()

    def test_constructor_and_resume_failure_reap_without_execution(self):
        for stage in ("constructor", "resume"):
            with self.subTest(stage=stage):
                marker = self.tmp / stage
                process = subprocess.Popen(
                    [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"],
                    creationflags=winjob.CREATE_SUSPENDED)
                job = winjob.Job() if stage == "resume" else None
                api = Mock()
                api.NtResumeProcess.return_value = -1
                try:
                    with patch.object(winjob, "_api", return_value=api), patch.object(
                            winjob, "Job", side_effect=OSError("constructor refused") if job is None else None,
                            return_value=job):
                        with self.assertRaises(OSError):
                            winjob.adopt(process)
                    self.assertIsNotNone(process.returncode)
                    self.assertFalse(marker.exists())
                    if job:
                        self.assertIsNone(job.handle)
                finally:
                    if process.poll() is None:
                        process.kill()
                    process.wait()
                    if job:
                        job.close()

    def test_stop_confirms_exact_descendant_after_normal_exit_and_timeout(self):
        for normal in (True, False):
            with self.subTest(normal=normal):
                marker, release = self.tmp / f"{normal}.pid", self.tmp / f"{normal}.release"
                code = ("import subprocess,sys,time\nfrom pathlib import Path\n"
                        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])\n"
                        f"Path({str(marker)!r}).write_text(str(p.pid))\n"
                        f"while not Path({str(release)!r}).exists(): time.sleep(.01)\n")
                tree = proc.Tree([sys.executable, "-c", code], self.tmp, None, False,
                                 subprocess.DEVNULL, subprocess.DEVNULL)
                try:
                    deadline = time.monotonic() + 5
                    while not marker.exists():
                        self.assertLess(time.monotonic(), deadline)
                        time.sleep(.01)
                    handle = tree.job.api.OpenProcess(0x100000, False, int(marker.read_text()))
                    tree.job.check(handle)
                    try:
                        if normal:
                            release.touch()
                            self.assertEqual(tree.process.wait(timeout=5), 0)
                        else:
                            with self.assertRaises(subprocess.TimeoutExpired):
                                tree.process.wait(timeout=.05)
                        tree.stop()
                        self.assertEqual(tree.job.api.WaitForSingleObject(handle, 0), 0,
                                         "owned descendant survived confirmed cleanup")
                        self.assertTrue(tree._stopped)
                        tree.stop()
                    finally:
                        tree.job.api.CloseHandle(handle)
                finally:
                    tree.stop()

    def test_close_waits_for_drain_and_preserves_native_failures(self):
        job = Mock()
        job.waiting = {}
        job.drained.side_effect = [False, True]
        with patch.object(winjob.time, "sleep"):
            winjob.close(job)
        self.assertEqual([call[0] for call in job.mock_calls],
                         ["begin_stop", "terminate", "drained", "drained", "close"])
        for operation in ("begin_stop", "terminate", "drained", "close"):
            with self.subTest(operation=operation):
                job = Mock()
                job.waiting = {}
                getattr(job, operation).side_effect = OSError("native cleanup refused")
                with self.assertRaisesRegex(OSError, "native cleanup refused"):
                    winjob.close(job)
                self.assertEqual(job.close.call_count, int(operation == "close"))
        job = Mock()
        job.waiting = {}
        job.drained.return_value = False
        with patch.object(winjob.time, "monotonic", side_effect=[0, 11]):
            with self.assertRaisesRegex(TimeoutError, "did not drain"):
                winjob.close(job)
        job.close.assert_not_called()

    def test_tree_does_not_hide_cleanup_failure_or_mark_stopped(self):
        tree = proc.Tree([sys.executable, "-c", "import time; time.sleep(60)"], self.tmp, None, False,
                         subprocess.DEVNULL, subprocess.DEVNULL)
        try:
            for operation in ("terminate", "drained"):
                with self.subTest(operation=operation), patch.object(
                        tree.job, operation, side_effect=OSError("cleanup refused")), patch.object(
                        proc.subprocess, "run", side_effect=AssertionError("PID fallback used")):
                    with self.assertRaisesRegex(OSError, "cleanup refused"):
                        tree.stop()
                    self.assertFalse(tree._stopped)
                    self.assertIsNotNone(tree.process.returncode, "root was not reaped after a job error")
                    self.assertIsNotNone(tree.job.handle, "unconfirmed ownership was released")
            tree.stop()
            self.assertTrue(tree._stopped)
        finally:
            tree.stop()

    def test_limited_failure_stays_registered_until_global_retry(self):
        with patch.object(proc, "_LIVE", set()), patch.object(proc, "STOPPING", proc.threading.Event()):
            try:
                with patch.object(winjob.Job, "terminate", side_effect=OSError("controlled stop refusal")):
                    with self.assertRaisesRegex(OSError, "controlled stop refusal"):
                        proc.run_limited([sys.executable, "-c", "pass"], self.tmp, 5, log=self.tmp / "run.log")
                self.assertEqual(len(proc._LIVE), 1)
                tree = next(iter(proc._LIVE))
                self.assertIsNotNone(tree.process.returncode)
                self.assertIsNotNone(tree.job.handle)
                self.assertEqual(proc.stop_all(), [])
                self.assertTrue(tree._stopped)
                self.assertFalse(proc._LIVE)
            finally:
                proc.stop_all()

    def test_member_release_failure_never_recloses_released_handles(self):
        job = Mock()
        job.waiting = {1: 101, 2: 102}
        job.check = winjob.Job.check
        job.api.CloseHandle.side_effect = [True, False]
        with self.assertRaises(OSError):
            winjob.close(job)
        self.assertEqual(job.waiting, {2: 102})
        job.close.assert_not_called()
        job.api.CloseHandle.side_effect = None
        job.api.CloseHandle.return_value = True
        winjob.close(job)
        self.assertEqual([call.args[0] for call in job.api.CloseHandle.call_args_list], [101, 102, 102])
        self.assertEqual(job.waiting, {})
        job.close.assert_called_once()


class EvalCleanupConsumerTests(EvalCase):
    def setUp(self):
        super().setUp()
        stopping = patch.object(proc, "STOPPING", proc.threading.Event())
        stopping.start()
        self.addCleanup(stopping.stop)

    def test_stop_all_attempts_every_tree_and_aggregates_failures(self):
        trees = [Mock() for _ in range(3)]
        for index, tree in enumerate(trees):
            tree.process.pid = index + 1
        trees[0].stop.side_effect = OSError("first refused")
        trees[1].stop.side_effect = TimeoutError("second refused")
        with patch.object(proc, "_LIVE", set(trees)):
            failure, errors = None, []
            try:
                errors = proc.stop_all()
            except Exception as error:
                failure = error
            for tree in trees:
                self.assertEqual(tree.stop.call_count, 1, f"process {tree.process.pid} was skipped")
            self.assertIsNone(failure, "cleanup must aggregate errors after attempting every tree")
            self.assertEqual(len(errors), 2)
            self.assertTrue(any("first refused" in error for error in errors))
            self.assertTrue(any("second refused" in error for error in errors))
            self.assertEqual(proc._LIVE, set(trees[:2]))
            for tree in trees:
                tree.stop.side_effect = None
            self.assertEqual(proc.stop_all(), [])
            self.assertFalse(proc._LIVE)

    def test_interrupt_preserves_rows_and_cleanup_diagnostic(self):
        completed, failures = {"sample": "finished"}, []
        real_wait = runner.wait

        def interrupt(pending, timeout):
            real_wait(pending, timeout=5)
            raise KeyboardInterrupt

        with patch.object(runner, "wait", interrupt), patch.object(
                proc, "stop_all", return_value=["controlled stop refusal"]):
            rows, interrupted = runner.execute([lambda: completed], 1, failures)
        self.assertEqual((rows, interrupted), ([completed], True))
        self.assertEqual(failures, ["controlled stop refusal"])

    def test_interrupt_bounds_wait_for_an_unfinished_worker(self):
        started, release, failures = proc.threading.Event(), proc.threading.Event(), []

        def task():
            started.set()
            release.wait(5)

        def interrupt(pending, timeout):
            self.assertTrue(started.wait(5))
            raise KeyboardInterrupt

        try:
            with patch.object(runner, "wait", interrupt), patch.object(proc, "stop_all", return_value=[]), patch.object(
                    runner.time, "monotonic", side_effect=[0, 11]):
                self.assertEqual(runner.execute([task], 1, failures), ([], True))
            self.assertEqual(failures, ["eval workers did not finish within 10 seconds"])
        finally:
            release.set()

    def test_taint_preserves_reason_and_cleanup_diagnostic(self):
        with patch.object(catalog, "loaded_modules", return_value=()), patch.object(
                runner.interpreter, "state", return_value={}), patch.object(runner.Watch, "digests", return_value=[]):
            watch = runner.Watch([], {})
        with patch.object(proc, "stop_all", return_value=["controlled taint cleanup refusal"]):
            self.assertEqual(watch.taint("interpreter tainted"), "interpreter tainted")
        self.assertEqual(watch.tainted, "interpreter tainted")
        self.assertEqual(watch.cleanup, ["controlled taint cleanup refusal"])

    def test_final_cleanup_failure_keeps_partial_report_unusable_as_baseline(self):
        sample = catalog.load(["bug-fix"])[0]
        completed = runner.row(sample, "factory", {}, exit=0)
        base = self.tmp / "retained"
        base.mkdir()
        proc.STOPPING.set()
        with patch.object(runner, "execute", return_value=([completed], False)), patch.object(
                runner.tempfile, "mkdtemp", return_value=str(base)), patch.object(
                proc, "stop_all", return_value=["controlled final stop refusal"]), patch.object(
                runner, "Watch", return_value=Mock(tainted=None, cleanup=[])):
            result = runner.run_all("local-unused", self.tmp / "out", names=["bug-fix"])
        self.assertEqual(result["runs"], [completed])
        self.assertIn("unconfirmed", result["tainted"])
        self.assertIn("controlled final stop refusal", result["cleanup"])
        self.assertTrue(base.exists())
        self.assertTrue(proc.STOPPING.is_set())
        paths = report.write(result, self.tmp / "out")
        with self.assertRaisesRegex(ValueError, "partial"):
            report.load(paths[0], baseline=True)


class EvalSnapshotTests(EvalCase):
    def test_isolated_check_uses_snapshot_and_inherited_result_pipe(self):
        sources = catalog.kit()
        self.assertEqual(sources["windows_job"],
                         (catalog.CODE.parent / "safe_engine/windows_job.py").read_text(encoding="utf-8"))
        sources["windows_job"] += "\nSNAPSHOT = 'sent-before-agent'\n"
        rubric = '''import os,sys
from evals.rubric_tools import call, op, expect

def verify(work):
    assert sys.flags.isolated and sys.flags.no_site
    assert not any('site-packages' in path for path in sys.path)
    if os.name == 'nt':
        import safe_engine
        from safe_engine import windows_job
        assert safe_engine.__path__ == []
        assert windows_job.SNAPSHOT == 'sent-before-agent'
        assert not getattr(windows_job, '__file__', None)
    expect(call(work, 'answer', [op('value')])[0], 42, 'inherited result pipe')
CHECKS = {'ownership': verify}
'''
        sample = catalog.Sample("snapshot", "", {"answer.py": b"def value(): return 42\n"}, rubric,
                                ("ownership",), frozenset(), {})
        work = catalog.write_fixture(sample, self.tmp / "work")
        self.assertIsNone(catalog.check_item(sample, sources, work, "ownership", self.tmp,
                                             isolation.run_env(self.tmp)))
