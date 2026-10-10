"""Time-limited processes that stop with their whole tree; a live registry lets an interrupt stop them all."""
import os
import signal
import subprocess
import threading

STOPPING = threading.Event()  # set on interrupt: running processes are killed, new ones refused
_LIVE = set()
_LOCK = threading.Lock()


def kill_tree(process):
    """Stop a process and every process it started, so nothing keeps running or holds files."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, timeout=60)
        else:
            os.killpg(process.pid, signal.SIGKILL)  # the process leads its own session (start_new_session)
    except (OSError, subprocess.SubprocessError):
        pass  # already gone, or the tree kill failed: fall back to the direct child
    if process.poll() is None:
        process.kill()
    process.wait()


def run_limited(command, cwd, stdin_path, log, seconds, env=None, shell=False):
    """Run `command` with stdin from a file and output to `log` (never a pipe a child could hold open).

    Returns (exit code, timed out); (None, False) when an interrupt stopped it or refused to start it.
    """
    with open(stdin_path, "rb") as stdin, open(log, "wb") as output:
        with _LOCK:
            if STOPPING.is_set():
                return None, False
            process = subprocess.Popen(command, shell=shell, cwd=cwd, env=env, stdin=stdin, stdout=output,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            _LIVE.add(process)
        try:
            code = process.wait(timeout=seconds)
            return (None, False) if STOPPING.is_set() else (code, False)
        except subprocess.TimeoutExpired:
            kill_tree(process)
            return None, True
        finally:
            with _LOCK:
                _LIVE.discard(process)


def stop_all():
    """Refuse new processes and kill every running tree: an interrupt must leave no paid agent running."""
    STOPPING.set()
    with _LOCK:
        live = list(_LIVE)
    for process in live:
        kill_tree(process)
