"""Atomic checkpoints and process-scoped locks; no daemon or database."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

from .project import EngineError, reject_path_aliases


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
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
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


@contextmanager
def locked(run_dir):
    reject_path_aliases(run_dir, run_dir.parent)
    run_dir.mkdir(parents=True, exist_ok=True)
    for directory, folders, files in os.walk(run_dir, followlinks=False):
        for name in folders + files:
            reject_path_aliases(Path(directory) / name, run_dir.parent)
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
