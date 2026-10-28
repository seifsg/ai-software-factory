"""Run explicitly configured checks without a shell; retain bounded output."""

import os
import hashlib
import json
import subprocess
import tempfile
import time

from . import run_metrics
from .storage import now
from .processes import ProcessTree
from .project import executable_path


LOG_LIMIT = 1_000_000
READ_SIZE = 65_536


def _read_available(pipe):
    """Read without waiting for a child (or inherited pipe holder) to write."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        import msvcrt

        available = wintypes.DWORD()
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        peek = kernel.PeekNamedPipe
        peek.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                         wintypes.LPVOID, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
        peek.restype = wintypes.BOOL
        if not peek(msvcrt.get_osfhandle(pipe.fileno()), None, 0, None, ctypes.byref(available), None):
            error = ctypes.get_last_error()
            if error in (109, 232):  # Broken/closing pipe: no remaining output.
                return b""
            raise ctypes.WinError(error)
        size = min(available.value, READ_SIZE)
    else:
        import select

        size = READ_SIZE if select.select([pipe], [], [], 0)[0] else 0
    return os.read(pipe.fileno(), size) if size else b""


def stop_process(process):
    process.stop()


def run_command(argv, cwd, timeout, log_path, stdin=None, stop=None, owned_lease=None):
    """stop: optional threading.Event; when set, the process tree is stopped like a timeout."""
    started = now()
    clock = time.monotonic()
    op_id = None
    if run_metrics.current():
        op_id = f"cmd-{int(clock * 1e9)}"
        command_id = hashlib.sha256(json.dumps({"argv": argv, "stdin": stdin}, default=str).encode()).hexdigest()[:24]
        run_metrics.emit_current("operation.start", name=str(argv[0]), event_id=op_id,
                                 argv0=str(argv[0]), command_id=command_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # A file avoids Windows' blocking communicate(input=...) pipe write.
    with tempfile.TemporaryFile() as input_file:
        if stdin is not None:
            input_file.write(stdin.encode("utf-8"))
            input_file.seek(0)
        executable = executable_path(argv[0], cwd)
        command = [str(executable), *argv[1:]] if executable else argv
        process = ProcessTree(command, cwd=cwd, stdin=input_file if stdin is not None else subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, owned_lease=owned_lease)
        timed_out = False
        output = bytearray()
        size = 0
        try:
            while True:
                chunk = _read_available(process.stdout)
                size += len(chunk)
                output.extend(chunk)
                del output[:-LOG_LIMIT]
                if process.poll() is not None:
                    # Drain the final pipe contents, but do not follow an orphan
                    # writer indefinitely after the configured command exits.
                    drained = 0
                    while drained < LOG_LIMIT:
                        chunk = _read_available(process.stdout)
                        if not chunk:
                            break
                        drained += len(chunk)
                        size += len(chunk)
                        output.extend(chunk)
                        del output[:-LOG_LIMIT]
                    break
                if time.monotonic() - clock >= timeout or (stop is not None and stop.is_set()):
                    timed_out = True
                    stop_process(process)
                elif not chunk:
                    time.sleep(0.01)
        except BaseException:
            stop_process(process)
            raise
        finally:
            process.stop()
            process.stdout.close()
        log_path.write_bytes(output)
    duration = round(time.monotonic() - clock, 3)
    result = {"argv": argv, "started_at": started, "duration_seconds": duration,
              "exit_code": process.returncode, "timed_out": timed_out,
              "passed": process.returncode == 0 and not timed_out,
              "log": str(log_path), "log_truncated": size > LOG_LIMIT}
    if op_id:
        run_metrics.emit_current("operation.finish", name=str(argv[0]), event_id=op_id + "-end",
                                 parent_id=op_id, duration_seconds=duration,
                                 passed=result["passed"], timed_out=timed_out, command_id=command_id)
    return result
