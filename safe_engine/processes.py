"""One owned process tree for checks, screenshot commands and persistent lanes."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time


class ProcessTree:
    """Command PID, streams and poll/wait, with retained ownership and bounded stop."""
    def __init__(self, argv, cwd, *, shell=False, owned_lease=None, **options):
        cwd = Path(cwd).resolve(strict=True)
        if not cwd.is_dir() or not argv:
            raise ValueError("A command and existing working directory are required")
        self.job = None
        self.closed = False
        self.stop_note = None
        if os.name == "nt":
            from .windows_job import Job
            from .suite_lease import job_name
            self.job = Job(job_name(owned_lease) if owned_lease else None)
        try:
            if self.job:
                # No command can spawn until the waiting bootstrap belongs to our job.
                with tempfile.TemporaryDirectory(prefix="factory-start-") as barrier:
                    ready = Path(barrier) / "go"
                    command = [sys.executable, str(Path(__file__).resolve()), str(ready), json.dumps(argv), str(int(shell))]
                    self.process = subprocess.Popen(command, cwd=cwd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                                                    **options)
                    try:
                        self.job.assign(self.process)
                        ready.touch()
                        deadline = time.monotonic() + 10
                        while ready.exists() and self.process.poll() is None and time.monotonic() < deadline:
                            time.sleep(.01)
                        if ready.exists():
                            raise RuntimeError("Owned command startup did not acknowledge its barrier")
                    except BaseException:
                        self.process.kill()
                        self.process.wait(timeout=10)
                        raise
            else:
                from .posix_session import Session
                self.process = Session(argv, cwd, shell=shell, owned_lease=owned_lease, **options)
        except BaseException:
            if self.job:
                self.job.close()
            raise

    def __getattr__(self, name):
        return getattr(self.process, name)

    def members(self):
        if self.closed:
            return []
        return self.job.pids() if self.job else [self.pid]

    def stop(self, grace=1):
        """Try the owned console/session first, then force only the retained job/group."""
        if self.closed:
            return
        if self.job:
            self.job.begin_stop()
            if self.job.active():
                # A dead group leader may have had its PID reused. Never signal it.
                if self.poll() is None:
                    try:
                        self.send_signal(signal.CTRL_BREAK_EVENT)
                    except OSError as error:
                        self.stop_note = f"console grace unavailable: {error}"
                deadline = time.monotonic() + grace
                while self.job.active() and time.monotonic() < deadline:
                    time.sleep(.02)
                if self.job.active():
                    self.job.terminate()
            deadline = time.monotonic() + 10
            while not self.job.drained():
                if time.monotonic() >= deadline:
                    raise RuntimeError("Owned job cleanup unconfirmed; handle retained for retry")
                time.sleep(.02)
        else:
            self.process.stop(grace)
        self.wait(timeout=10)
        if self.job:
            self.job.close()
        self.closed = True


def bootstrap():
    """Wait for job assignment before running user code, preserving its standard streams."""
    ready = Path(sys.argv[1])
    deadline = time.monotonic() + 10
    while not ready.exists():
        if time.monotonic() > deadline:
            return 125
        time.sleep(.01)
    ready.unlink()
    return subprocess.call(json.loads(sys.argv[2]), shell=bool(int(sys.argv[3])))


if __name__ == "__main__":
    sys.exit(bootstrap())
