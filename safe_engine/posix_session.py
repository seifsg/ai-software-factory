"""Retain a session leader independently of the command's exit and descendants."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time


class Session:
    """Only stop reaps the guardian, so its PID and PGID cannot be reused first."""
    def __init__(self, argv, cwd, *, shell=False, **options):
        self.check_reaper()
        self.control = tempfile.TemporaryDirectory(prefix="factory-session-")
        self.result = Path(self.control.name) / "exit"
        self.returncode = None
        self.closed = False
        self.signals_done = False
        try:
            self.anchor = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), str(self.result),
                                            json.dumps(argv), str(int(shell))],
                                           cwd=cwd, start_new_session=True, **options)
        except BaseException:
            self.control.cleanup()
            raise

    def __getattr__(self, name):
        if name not in {"pid", "args", "stdin", "stdout", "stderr"}:
            raise AttributeError(name)  # Do not expose Popen methods that could reap the guardian.
        return getattr(self.anchor, name)

    @staticmethod
    def check_reaper():
        """Automatic or external SIGCHLD reaping would release the ownership anchor."""
        if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
            raise RuntimeError("Owned sessions require default SIGCHLD handling and exclusive child reaping")

    def poll(self):
        if self.returncode is None and self.result.exists():
            self.returncode = int(self.result.read_text())
        return self.returncode

    def wait(self, timeout=None):
        deadline = None if timeout is None else time.monotonic() + timeout
        while self.poll() is None:
            if deadline is not None and time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(self.args, timeout)
            time.sleep(.01)
        return self.returncode

    def stop(self, grace):
        """Signal while the live or unreaped guardian reserves the group identity."""
        if self.closed:
            return
        if not self.signals_done:
            self.check_reaper()
            os.killpg(self.pid, signal.SIGTERM)
            time.sleep(grace)
            os.killpg(self.pid, signal.SIGKILL)
            self.signals_done = True
        code = self.anchor.wait(timeout=10)  # No group signals are permitted after this reap.
        self.wait_drained()
        self.closed = True
        if self.poll() is None:
            self.returncode = code
        self.control.cleanup()

    def wait_drained(self):
        """Observe only after reaping: a reused group fails closed, never gets killed."""
        deadline = time.monotonic() + 10
        while True:
            try:
                os.killpg(self.pid, 0)
            except ProcessLookupError:
                return
            except PermissionError:
                pass  # Existence without permission is not confirmed cleanup.
            if time.monotonic() >= deadline:
                raise RuntimeError("Owned group cleanup unconfirmed; retry is observation-only after final signal")
            time.sleep(.02)


def guardian():
    """Stay alive after command exit; caught handlers reset to default on child exec."""
    signal.signal(signal.SIGTERM, lambda *_: None)
    signal.signal(signal.SIGINT, lambda *_: None)
    result = Path(sys.argv[1])
    try:
        code = subprocess.call(json.loads(sys.argv[2]), shell=bool(int(sys.argv[3])))
    except OSError as error:
        print(f"Owned command failed to start: {error}", file=sys.stderr, flush=True)
        code = 125
    pending = result.with_suffix(".pending")
    pending.write_text(str(code))
    pending.replace(result)
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    guardian()
