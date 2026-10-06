"""Atomic checkpoints and process-scoped locks; no daemon or database."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import time

from .project import EngineError, reject_alias, reject_path_aliases


def now():
    return datetime.now(timezone.utc).isoformat()


def windows_retry(action):
    """Windows briefly denies access while a lock-free reader or a replace holds the file."""
    for attempt in range(20):
        try:
            return action()
        except PermissionError:
            if os.name != "nt" or attempt == 19:
                raise
            time.sleep(0.05)


def read_json(path):
    try:
        return json.loads(windows_retry(lambda: Path(path).read_text(encoding="utf-8-sig")))
    except (OSError, ValueError) as exc:
        raise EngineError(f"Cannot read JSON at {path}: {exc}") from exc


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".writing-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        windows_retry(lambda: os.replace(temp, path))
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def reject_tree_aliases(folder):
    """Use cached DirEntry data; Windows needs no extra call per entry, POSIX lstats only links."""
    with os.scandir(folder) as entries:
        for entry in entries:
            if os.name == "nt" or entry.is_symlink():
                reject_alias(entry.path, entry.stat(follow_symlinks=False))
            if entry.is_dir(follow_symlinks=False):
                reject_tree_aliases(entry.path)


@contextmanager
def locked(run_dir):
    reject_path_aliases(run_dir, run_dir.parent)
    run_dir.mkdir(parents=True, exist_ok=True)
    reject_tree_aliases(run_dir)
    with (run_dir / "lock").open("a+b") as lock:
        lock.seek(0)
        if os.fstat(lock.fileno()).st_size == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise EngineError("Another Safe Engine operation is active for this project") from exc
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def save(run_dir, state, event):
    state["updated_at"] = now()
    state["sequence"] += 1
    state["history"].append({"sequence": state["sequence"], "at": state["updated_at"], "event": event, "phase": state["phase"]})
    atomic_json(run_dir / "history" / f"{state['sequence']:04d}.json", state)
    atomic_json(run_dir / "state.json", state)
