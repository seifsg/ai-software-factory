"""Windows job objects: every process a command starts stays in one job that dies as a whole. Stdlib ctypes only."""
import ctypes
from ctypes import wintypes
from functools import lru_cache

CREATE_SUSPENDED = 0x4
KILL_ON_JOB_CLOSE = 0x2000
EXTENDED_LIMIT_INFORMATION = 9


class _Basic(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]


class _Extended(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _Basic), ("IoInfo", ctypes.c_uint64 * 6),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


@lru_cache(maxsize=None)
def _api():
    """kernel32 and ntdll with 64-bit-safe signatures, set up once."""
    kernel, nt = ctypes.WinDLL("kernel32", use_last_error=True), ctypes.WinDLL("ntdll")
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    nt.NtResumeProcess.argtypes = [wintypes.HANDLE]
    return kernel, nt


def adopt(process):
    """Put a process started with CREATE_SUSPENDED into a new kill-on-close job, then resume it.

    Returns the job handle, or None when the job could not be set up; the process resumes either way.
    """
    kernel, nt = _api()
    handle, job = int(process._handle), None  # Popen keeps the Windows process handle here
    try:
        job = kernel.CreateJobObjectW(None, None)
        info = _Extended()
        info.BasicLimitInformation.LimitFlags = KILL_ON_JOB_CLOSE
        if not (job and kernel.SetInformationJobObject(job, EXTENDED_LIMIT_INFORMATION, ctypes.byref(info),
                                                       ctypes.sizeof(info))
                and kernel.AssignProcessToJobObject(job, handle)):
            raise OSError(ctypes.get_last_error(), "job object setup failed")
    except OSError:
        if job:
            kernel.CloseHandle(job)
        job = None
    finally:
        nt.NtResumeProcess(handle)  # a failed job must never leave the command frozen
    return job


def close(job):
    """Kill every process left in the job and release it."""
    kernel, _ = _api()
    kernel.TerminateJobObject(job, 1)
    kernel.CloseHandle(job)
