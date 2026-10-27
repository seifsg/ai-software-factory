"""Small OS locks and a machine-stable queue directory, independent of factory homes."""
from contextlib import contextmanager
import os
from pathlib import Path
import time

from .project import EngineError, reject_path_aliases


class FileLock:
    """Keep an exclusive byte/flock lock until its handle closes, including process exit."""
    def __init__(self, path):
        reject_path_aliases(path, path.parent)
        self.stream = path.open('a+b')
        if os.fstat(self.stream.fileno()).st_size == 0:
            self.stream.write(b'0')
            self.stream.flush()
        self.held = False

    def acquire(self):
        self.stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.held = True
            return True
        except (BlockingIOError, PermissionError):
            return False
        except OSError as error:
            if error.errno in (11, 13, 36):
                return False
            raise

    def close(self):
        self.stream.close()
        self.held = False


@contextmanager
def locked(path, timeout=10):
    """Bound metadata waits; a held execution lease uses its own separate lock."""
    lock = FileLock(path)
    try:
        end = time.monotonic() + timeout
        while not lock.acquire():
            if time.monotonic() >= end:
                raise EngineError(f'Suite queue metadata is busy: {path}')
            time.sleep(.05)
        yield
    finally:
        lock.close()


def machine_directory():
    """Use the OS common data location, never a caller-supplied home or temporary path."""
    if os.name == 'nt':
        import ctypes
        buffer = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 35, None, 0, buffer):
            raise EngineError('Cannot locate common machine data for the suite queue')
        parent = Path(buffer.value)
    else:
        parent = Path('/tmp')
    root = parent / 'ai-software-factory-suite-v1'
    reject_path_aliases(root, parent)
    root.mkdir(mode=0o700, exist_ok=True)
    if os.name != 'nt' and (root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077):
        raise EngineError('Machine suite queue belongs to another account or has unsafe permissions; no suite started')
    return root
