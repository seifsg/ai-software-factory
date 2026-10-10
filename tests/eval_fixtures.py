"""Shared helpers for the eval tests: fake-agent templates, a sleeper that records its PID, process liveness."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import fake_agent
from evals import agent

FAKE = Path(fake_agent.__file__).resolve()


def fake(delivering, action=""):
    """Template running the fake agent; the `delivering` arm gets the reference solution."""
    return (f"{agent.quote(sys.executable)} {agent.quote(FAKE)} {{arm}} {{sample}} {{workdir}} {{factory}} "
            f"{delivering} {action}").strip()


def sleeper(pids):
    """Template for an agent that records its PID in `pids` and sleeps 60 s: only a kill ends it early."""
    code = (f"import os, time, pathlib; pathlib.Path('{Path(pids).as_posix()}', str(os.getpid())).write_text('x'); "
            "time.sleep(60)")
    return f'{agent.quote(sys.executable)} -c "{code}"'


def alive(pid):
    """Whether process `pid` still runs."""
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    stat = Path(f"/proc/{pid}/stat")
    return not (stat.is_file() and stat.read_text().split(")")[-1].split()[0] == "Z")  # a zombie is dead


def dead_soon(pid, seconds=5):
    """Whether `pid` is gone within `seconds` (a killed tree needs a moment to unwind)."""
    deadline = time.monotonic() + seconds
    while alive(pid):
        if time.monotonic() > deadline:
            return False
        time.sleep(0.2)
    return True


class EvalCase(unittest.TestCase):
    """A private folder per test, with the system temp redirected into it so leftovers and escapes show."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="evals-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.scratch = self.tmp / "temp"
        self.scratch.mkdir()
        temp = patch.object(tempfile, "tempdir", str(self.scratch))
        temp.start()
        self.addCleanup(temp.stop)
