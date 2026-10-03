"""Run explicitly configured checks without a shell; retain bounded output."""

import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

from .storage import now


def stop_process(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=20)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=20)


def run_command(argv, cwd, timeout, log_path, stdin=None):
    started = now()
    clock = time.monotonic()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile() as output:
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, **options)
        timed_out = False
        try:
            process.communicate(input=stdin.encode("utf-8") if stdin is not None else None, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            stop_process(process)
        except BaseException:
            stop_process(process)
            raise
        output.seek(0, os.SEEK_END)
        size = output.tell()
        output.seek(max(0, size - 1_000_000))
        log_path.write_bytes(output.read())
    return {"argv": argv, "started_at": started, "duration_seconds": round(time.monotonic() - clock, 3),
            "exit_code": process.returncode, "timed_out": timed_out,
            "passed": process.returncode == 0 and not timed_out,
            "log": str(log_path), "log_truncated": size > 1_000_000}
