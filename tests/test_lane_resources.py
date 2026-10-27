"""Owned lane resources and cleanup failure regressions."""
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from safe_engine import lanes, posix_session, processes, resources
from safe_engine.storage import atomic_json, read_json
from test_fast_gate import module


shots = module("fast_shots")
entry = module("fast_entry")


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def listening(port):
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) == 0


class OwnedProcessTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "native Windows job ownership")
    def test_orphan_listener_stays_owned_until_stop(self):
        with tempfile.TemporaryDirectory() as root:
            port = free_port()
            child = [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"]
            parent = [sys.executable, "-c", "import subprocess,sys; subprocess.Popen(sys.argv[1:])", *child]
            tree = processes.ProcessTree(parent, root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                self.assertEqual(tree.wait(timeout=10), 0)
                deadline = time.monotonic() + 10
                while not listening(port) and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertTrue(listening(port), "the child must survive its command parent")
                self.assertTrue(tree.members())
            finally:
                tree.stop(grace=0)
            self.assertTrue(tree.closed)
            self.assertFalse(listening(port), "stop must wait for the orphan listener to release its port")

    def test_unconfirmed_job_drain_keeps_handle_for_retry(self):
        tree = processes.ProcessTree.__new__(processes.ProcessTree)
        class Job:
            confirmed = False
            closed = False
            def begin_stop(self): pass
            def active(self): return 0
            def drained(self): return self.confirmed
            def close(self): self.closed = True
        class Child:
            def wait(self, timeout): return 0
        tree.job, tree.process, tree.closed = Job(), Child(), False
        with patch.object(processes.time, "monotonic", side_effect=[0, 11]):
            with self.assertRaisesRegex(RuntimeError, "cleanup unconfirmed"):
                tree.stop(grace=0)
        self.assertFalse(tree.closed)
        self.assertFalse(tree.job.closed)
        tree.job.confirmed = True
        tree.stop(grace=0)
        self.assertTrue(tree.closed)
        self.assertTrue(tree.job.closed)

    @unittest.skipUnless(os.name == "nt", "native Windows supervisor")
    def test_lane_stop_releases_only_its_owned_orphan(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root)
            owned, foreign = free_port(), free_port()
            child = [sys.executable, "-m", "http.server", str(owned), "--bind", "127.0.0.1"]
            parent = [sys.executable, "-c", "import subprocess,sys; subprocess.Popen(sys.argv[1:])", *child]
            sentinel = subprocess.Popen([sys.executable, "-m", "http.server", str(foreign), "--bind", "127.0.0.1"],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            state = None
            try:
                deadline = time.monotonic() + 10
                while not listening(foreign) and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertTrue(listening(foreign))
                with self.assertRaisesRegex(RuntimeError, "occupied"):
                    lanes.start(project, "blocked", parent, [foreign])
                state = lanes.start(project, "owned", parent, [owned])
                self.assertEqual(state["status"], "running")
                deadline = time.monotonic() + 10
                while not listening(owned) and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertTrue(listening(owned))
                with self.assertRaisesRegex(RuntimeError, "generation changed"):
                    lanes.stop(project, "owned", "0" * 32)
                self.assertTrue(listening(owned))
                final = lanes.stop(project, "owned", state["generation"])
                self.assertEqual(final["status"], "stopped")
                self.assertEqual(final["processes"], [])
                self.assertFalse(listening(owned))
                self.assertTrue(listening(foreign))
            finally:
                if state and lanes.status(lanes.folder(project, "owned"))["status"] not in ("stopped", "stale"):
                    lanes.stop(project, "owned", state["generation"])
                sentinel.terminate()
                sentinel.wait(timeout=10)

    def test_resource_roots_and_supported_caches_are_isolated(self):
        with tempfile.TemporaryDirectory() as root:
            one = resources.resource_root(root + "/one")
            two = resources.resource_root(root + "/two")
            profile_root = resources.resource_root(root + "/deep")
            for path in (one, two, profile_root):
                self.addCleanup(shutil.rmtree, path, ignore_errors=True)
            self.assertNotEqual(one, two)
            left, right = resources.environment(one), resources.environment(two)
            for key in ("FACTORY_CACHE_DIR", "CARGO_TARGET_DIR", "npm_config_cache", "PYTHONPYCACHEPREFIX", "FACTORY_PROFILE_DIR"):
                self.assertNotEqual(left[key], right[key])
                self.assertTrue(Path(left[key]).is_dir())
                self.assertTrue(Path(right[key]).is_dir())
            self.assertTrue(str(resources.profile(root + "/deep")).startswith(str(profile_root)))

    def test_lane_cleanup_failure_keeps_state_until_retry(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            generation = "a" * 32
            state = {"generation": generation, "status": "running", "ports": [], "processes": [77]}
            class Owner:
                attempts = 0
                stop_note = None
                def stop(self):
                    self.attempts += 1
                    if self.attempts == 1:
                        raise RuntimeError("not drained")
            owner = Owner()
            worker = threading.Thread(target=lanes.finish, args=(directory, generation, state, owner), daemon=True)
            worker.start()
            deadline = time.monotonic() + 5
            while (not (directory / "state.json").exists() or read_json(directory / "state.json")["status"] != "cleanup_failed") and time.monotonic() < deadline:
                time.sleep(.02)
            failed = read_json(directory / "state.json")
            self.assertEqual(failed["status"], "cleanup_failed")
            self.assertEqual(failed["processes"], [77])
            atomic_json(directory / f"{generation}.stop", {"generation": generation, "attempt": "retry"})
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
            final = read_json(directory / "state.json")
            self.assertEqual(final["status"], "stopped")
            self.assertEqual(final["processes"], [])
            self.assertEqual(owner.attempts, 2)

    def test_posix_retry_observes_only_after_final_signal(self):
        session = posix_session.Session.__new__(posix_session.Session)
        session.closed = False
        session.signals_done = False
        session.returncode = None
        session.anchor = type("Anchor", (), {"wait": lambda self, timeout: 0})()
        session.control = type("Control", (), {"cleanup": lambda self: None})()
        session.pid = 991
        session.poll = lambda: 0
        sent = []
        present = [True, True, False]
        def group(pid, kind):
            sent.append(kind)
            if kind == 0 and present.pop(0):
                return
            if kind == 0:
                raise ProcessLookupError
        with patch.object(posix_session.Session, "check_reaper"), patch.object(posix_session.signal, "SIGKILL", 9, create=True), \
             patch.object(posix_session.os, "killpg", side_effect=group, create=True), \
             patch.object(posix_session.time, "sleep"), patch.object(posix_session.time, "monotonic", side_effect=[0, 11, 0, 11, 0]):
            with self.assertRaisesRegex(RuntimeError, "cleanup unconfirmed"):
                session.stop(0)
            self.assertTrue(session.signals_done)
            self.assertFalse(session.closed)
            with self.assertRaisesRegex(RuntimeError, "cleanup unconfirmed"):
                session.stop(0)
            session.stop(0)
        self.assertEqual(sent[:2], [signal.SIGTERM, 9])
        self.assertEqual(sent[2:], [0, 0, 0])
        self.assertTrue(session.closed)


class ConsumerTests(unittest.TestCase):
    def test_shots_attempt_all_stops_and_retry_retains_failed_owner(self):
        first, second = SimpleNamespace(pid=1), SimpleNamespace(pid=2)
        calls = []
        fail = True
        def stop(owner):
            calls.append(owner)
            if owner is first and fail:
                raise RuntimeError("not drained")
        with patch.object(shots, "stop", side_effect=stop):
            try:
                shots.cleanup([first, second])
            except shots.CleanupError as error:
                self.assertEqual([owner for owner, _ in error.failures], [first])
                self.assertEqual(calls, [first, second])
                fail = False
                error.retry()
                self.assertEqual(error.failures, [])
                self.assertEqual(calls, [first, second, first])
            else:
                self.fail("unconfirmed cleanup must propagate")

    def test_child_help_and_project_are_not_gate_routing_options(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root)
            forwarded = []
            class Gate:
                native = staticmethod(lambda value: value)
                find_project = staticmethod(lambda value: project)
            with patch.object(entry, "selected_command", return_value=project / "gate.py"), \
                 patch.object(entry.subprocess, "call", side_effect=lambda argv: forwarded.append(argv) or 0):
                for child in (["--help"], ["--project", "foreign"], ["--project=foreign"]):
                    args = ["lane", "start", "--project", str(project), "--name", "one", "--ports", "12345", "--", sys.executable, *child]
                    self.assertEqual(entry.route(args, Gate), 0)
                    self.assertEqual(forwarded[-1][2:], args)


if __name__ == "__main__":
    unittest.main()
