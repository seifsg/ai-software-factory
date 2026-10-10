"""Time-limited process trees: everything a command starts dies with it, after a timeout and after a normal exit.

Windows keeps the tree in a kill-on-close job object; elsewhere the command leads its own process group. A live
registry lets an interrupt stop every running tree.
"""
import os
import signal
import subprocess
import threading

WINDOWS = os.name == "nt"
if WINDOWS:
    from evals import winjob  # ctypes.wintypes loads only on Windows
STOPPING = threading.Event()  # set on interrupt: running trees are killed, new ones refused
_LIVE = set()
_LOCK = threading.Lock()


class Tree:
    """A started command and every process it spawns; stop() kills them all, once."""

    def __init__(self, command, cwd, env, shell, stdin, output):
        self.process = subprocess.Popen(command, shell=shell, cwd=cwd, env=env, stdin=stdin, stdout=output,
                                        stderr=subprocess.STDOUT, start_new_session=not WINDOWS,
                                        creationflags=winjob.CREATE_SUSPENDED if WINDOWS else 0)
        self.job = winjob.adopt(self.process) if WINDOWS else None
        self._lock, self._stopped = threading.Lock(), False

    def stop(self):
        """Kill the whole tree (a no-op for processes already gone) and reap the command."""
        with self._lock:
            if self._stopped:
                return
            self._stopped = True
            try:
                if self.job:
                    winjob.close(self.job)
                elif WINDOWS:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], capture_output=True,
                                   timeout=60)
                else:
                    os.killpg(self.process.pid, signal.SIGKILL)
            except (OSError, subprocess.SubprocessError):
                pass  # the group is already gone
            if self.process.poll() is None:
                self.process.kill()
        self.process.wait()


def _feed(pipe, data):
    """Write `data` to a child's stdin and close it; a child that exits early just stops reading."""
    try:
        with pipe:
            pipe.write(data)
    except OSError:
        pass


def run_limited(command, cwd, log, seconds, env=None, shell=False, stdin_path=None, stdin_data=None):
    """Run `command` with output to `log` (a file, never a pipe a child could hold open).

    Stdin comes from `stdin_path`, or `stdin_data` bytes through a pipe, else nothing. Returns (exit code, timed
    out); (None, False) when an interrupt stopped the run or refused to start it.
    """
    stdin = open(stdin_path, "rb") if stdin_path else subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL
    try:
        with open(log, "wb") as output:
            with _LOCK:
                if STOPPING.is_set():
                    return None, False
                tree = Tree(command, cwd, env, shell, stdin, output)
                _LIVE.add(tree)
            if stdin_data is not None:
                threading.Thread(target=_feed, args=(tree.process.stdin, stdin_data), daemon=True).start()
            try:
                code, timed_out = tree.process.wait(timeout=seconds), False
            except subprocess.TimeoutExpired:
                code, timed_out = None, True
            finally:
                tree.stop()  # leftovers die after a normal exit too
                with _LOCK:
                    _LIVE.discard(tree)
    finally:
        if stdin_path:
            stdin.close()
    return (None, False) if STOPPING.is_set() and not timed_out else (code, timed_out)


def stop_all():
    """Refuse new processes and kill every running tree: an interrupt must leave no paid agent running."""
    STOPPING.set()
    with _LOCK:
        live = list(_LIVE)
    for tree in live:
        tree.stop()
