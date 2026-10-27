"""Time-limited process trees: everything a command starts dies with it, after a timeout and after a normal exit.

Windows keeps the tree in a kill-on-close job object; elsewhere the command leads its own process group. A live
registry lets an interrupt stop every running tree. Children get only the handles passed to them (close_fds).
"""
import os
import signal
import subprocess
import threading

WINDOWS = os.name == "nt"
if WINDOWS:
    from evals import winjob  # ctypes.wintypes loads only on Windows
STOPPING = threading.Event()  # set on interrupt or taint: running trees are killed, new ones refused
_LIVE = set()
_LOCK = threading.Lock()


class Tree:
    """A started command and every process it spawns; stop() kills them all, once."""

    def __init__(self, command, cwd, env, shell, stdin, output, errors=subprocess.STDOUT, **extra):
        """Start `command` suspended in its job (Windows) or session; `extra` adds Popen options (pass_fds,
        startupinfo) for one deliberately inherited handle."""
        self.process = subprocess.Popen(command, shell=shell, cwd=cwd, env=env, stdin=stdin, stdout=output,
                                        stderr=errors, close_fds=True, start_new_session=not WINDOWS,
                                        creationflags=winjob.CREATE_SUSPENDED if WINDOWS else 0, **extra)
        self.job = winjob.adopt(self.process) if WINDOWS else None
        self._lock, self._stopped = threading.Lock(), False

    def stop(self):
        """Kill the whole tree (a no-op for processes already gone) and reap the command."""
        with self._lock:
            if self._stopped:
                return
            if WINDOWS:
                winjob.close(self.job)
            else:
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except OSError:
                    pass  # the group is already gone
            if self.process.poll() is None:
                self.process.kill()
            self.process.wait(timeout=10)
            self._stopped = True


def _feed(pipe, data):
    """Write `data` to a child's stdin and close it; a child that exits early just stops reading."""
    try:
        with pipe:
            pipe.write(data)
    except OSError:
        pass


def _drain(pipe, into):
    """Read a child's output pipe to the end."""
    with pipe:
        into.append(pipe.read())


def _supervise(tree, seconds, stdin_data):
    """Feed stdin, wait up to `seconds`, then stop the tree either way: (exit code, timed out, captured bytes)."""
    if stdin_data is not None:
        threading.Thread(target=_feed, args=(tree.process.stdin, stdin_data), daemon=True).start()
    captured, reader = [], None
    if tree.process.stdout:
        reader = threading.Thread(target=_drain, args=(tree.process.stdout, captured), daemon=True)
        reader.start()
    try:
        code, timed_out = tree.process.wait(timeout=seconds), False
    except subprocess.TimeoutExpired:
        code, timed_out = None, True
    finally:
        tree.stop()  # leftovers die after a normal exit too
        if reader:
            reader.join(10)
    return code, timed_out, b"".join(captured)


def run_limited(command, cwd, seconds, env=None, shell=False, stdin_path=None, stdin_data=None, log=None):
    """Run `command` as a tree with a time limit. Stdin from `stdin_path`, or `stdin_data` bytes, else nothing.

    Output goes to the `log` file, or else through a pipe only this process holds and comes back as text.
    Returns (exit code, timed out, text or None); (None, False, None) when an interrupt stopped or refused it.
    """
    stdin = open(stdin_path, "rb") if stdin_path else subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL
    output = open(log, "wb") if log else subprocess.PIPE
    try:
        with _LOCK:
            if STOPPING.is_set():
                return None, False, None
            tree = Tree(command, cwd, env, shell, stdin, output)
            _LIVE.add(tree)
        try:
            code, timed_out, captured = _supervise(tree, seconds, stdin_data)
        finally:
            with _LOCK:
                _LIVE.discard(tree)
    finally:
        for handle in (stdin if stdin_path else None, output if log else None):
            if handle:
                handle.close()
    if STOPPING.is_set() and not timed_out:
        return None, False, None
    return code, timed_out, None if log else captured.decode("utf-8", "replace")


def stop_all():
    """Refuse new processes and kill every running tree: an interrupt must leave no paid agent running."""
    STOPPING.set()
    with _LOCK:
        live = list(_LIVE)
    for tree in live:
        tree.stop()
