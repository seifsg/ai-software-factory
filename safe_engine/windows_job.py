"""Windows job handles retain ownership after the command's original parent exits."""
import ctypes
from ctypes import wintypes as W


class Limits(ctypes.Structure):
    _fields_ = [("time", ctypes.c_longlong * 2), ("flags", W.DWORD),
                ("working_set", ctypes.c_size_t * 2), ("active", W.DWORD),
                ("affinity", ctypes.c_size_t), ("priority", W.DWORD), ("scheduling", W.DWORD)]


class Extended(ctypes.Structure):
    _fields_ = [("basic", Limits), ("io", ctypes.c_ulonglong * 6), ("memory", ctypes.c_size_t * 4)]


class Accounting(ctypes.Structure):
    _fields_ = [("times", ctypes.c_longlong * 4), ("faults", W.DWORD),
                ("total", W.DWORD), ("active", W.DWORD), ("terminated", W.DWORD)]


class Job:
    """A non-inherited, kill-on-close handle; children cannot break away."""
    def __init__(self):
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        for name, args, result in (
            ("CreateJobObjectW", [W.LPVOID, W.LPCWSTR], W.HANDLE),
            ("SetInformationJobObject", [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD], W.BOOL),
            ("AssignProcessToJobObject", [W.HANDLE, W.HANDLE], W.BOOL),
            ("QueryInformationJobObject", [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD, W.LPVOID], W.BOOL),
            ("TerminateJobObject", [W.HANDLE, W.UINT], W.BOOL),
            ("OpenProcess", [W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
            ("IsProcessInJob", [W.HANDLE, W.HANDLE, ctypes.POINTER(W.BOOL)], W.BOOL),
            ("WaitForSingleObject", [W.HANDLE, W.DWORD], W.DWORD),
            ("CloseHandle", [W.HANDLE], W.BOOL),
        ):
            function = getattr(self.api, name)
            function.argtypes, function.restype = args, result
        self.handle = self.api.CreateJobObjectW(None, None)
        self.waiting = {}
        self.check(self.handle)
        limit = Extended()
        limit.basic.flags = 0x2000
        try:
            self.check(self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limit), ctypes.sizeof(limit)))
        except BaseException:
            self.close()
            raise

    @staticmethod
    def check(result):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())

    def assign(self, process):
        self.check(self.api.AssignProcessToJobObject(self.handle, int(process._handle)))

    def pids(self):
        """Query the job, never an unrelated process-name or parent-PID snapshot."""
        capacity = 64
        while True:
            class Pids(ctypes.Structure):
                _fields_ = [("assigned", W.DWORD), ("count", W.DWORD),
                            ("ids", ctypes.c_size_t * capacity)]
            data = Pids()
            if self.api.QueryInformationJobObject(self.handle, 3, ctypes.byref(data), ctypes.sizeof(data), None):
                return list(data.ids[:data.count])
            if ctypes.get_last_error() != 234:
                self.check(False)
            capacity = max(capacity * 2, data.assigned)

    def terminate(self):
        self.check(self.api.TerminateJobObject(self.handle, 1))

    def active(self):
        """Read job accounting; actual exit also requires signaled process handles."""
        data = Accounting()
        self.check(self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(data), ctypes.sizeof(data), None))
        return data.active

    def begin_stop(self):
        """Seal descendant creation, then retain exact members through asynchronous exit."""
        limit = Extended()
        limit.basic.flags = 0x2000 | 0x8  # Keep kill-on-close; no new active members.
        self.check(self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limit), ctypes.sizeof(limit)))
        for pid in self.pids():
            if pid in self.waiting:
                continue
            handle = self.api.OpenProcess(0x100000 | 0x1000, False, pid)
            if not handle and ctypes.get_last_error() == 87:  # Already fully exited.
                continue
            self.check(handle)
            try:
                member = W.BOOL()
                self.check(self.api.IsProcessInJob(handle, self.handle, ctypes.byref(member)))
                if member.value:
                    self.waiting[pid] = handle
                    handle = None
            finally:
                if handle:
                    self.check(self.api.CloseHandle(handle))

    def drained(self):
        """Do not confuse job removal with a signaled process and completed I/O teardown."""
        for handle in self.waiting.values():
            result = self.api.WaitForSingleObject(handle, 0)
            if result == 258:
                return False
            self.check(result == 0)
        return self.active() == 0

    def close(self):
        if self.handle:
            self.check(self.api.CloseHandle(self.handle))
            self.handle = None
        for handle in self.waiting.values():
            self.check(self.api.CloseHandle(handle))
        self.waiting.clear()


def identity(pid):
    """Creation time distinguishes a reused PID without granting termination access."""
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.OpenProcess.argtypes, api.OpenProcess.restype = [W.DWORD, W.BOOL, W.DWORD], W.HANDLE
    api.GetProcessTimes.argtypes = [W.HANDLE] + [ctypes.POINTER(W.FILETIME)] * 4
    api.CloseHandle.argtypes = [W.HANDLE]
    handle = api.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        times = [W.FILETIME() for _ in range(4)]
        if not api.GetProcessTimes(handle, *[ctypes.byref(value) for value in times]):
            raise ctypes.WinError(ctypes.get_last_error())
        return str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
    finally:
        api.CloseHandle(handle)
