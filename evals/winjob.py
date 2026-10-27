"""Strict Windows ownership for suspended eval commands and their descendants."""
import ctypes
from ctypes import wintypes
from functools import lru_cache
import time

from safe_engine.windows_job import Job

CREATE_SUSPENDED = 0x4


@lru_cache(maxsize=None)
def _api():
    """Load the signed NTSTATUS resume operation once."""
    nt = ctypes.WinDLL("ntdll")
    nt.NtResumeProcess.argtypes = [wintypes.HANDLE]
    nt.NtResumeProcess.restype = ctypes.c_long
    return nt


def adopt(process):
    """Assign before running; failed setup kills and reaps the suspended command."""
    job = None
    try:
        job = Job()
        job.assign(process)
        status = _api().NtResumeProcess(int(process._handle))
        if status < 0:
            raise OSError(f"NtResumeProcess failed: {status:#x}")
        return job
    except BaseException:
        try:
            try:
                process.kill()
            finally:
                process.wait(timeout=10)
        finally:
            if job:
                job.close()
        raise


def close(job):
    """Stop exact owned members and confirm exit before releasing their handles."""
    if job.handle:
        job.begin_stop()
        job.terminate()
        deadline = time.monotonic() + 10
        while not job.drained():
            if time.monotonic() >= deadline:
                raise TimeoutError("eval job did not drain within 10 seconds")
            time.sleep(.01)
    for pid, handle in list(job.waiting.items()):
        job.check(job.api.CloseHandle(handle))
        del job.waiting[pid]  # a retry must never close an already released member
    job.close()
