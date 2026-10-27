"""FIFO full-suite admission with crash recovery before releasing owned resources."""
from contextlib import contextmanager
import os
import threading
import time
import uuid

from .project import EngineError, reject_path_aliases
from .storage import atomic_json, read_json
from .suite_lease import recover
from .suite_lock import FileLock, locked, machine_directory

LIMIT = 256


def read(path):
    """Queue records are bounded and never executable instructions."""
    if path.stat().st_size > 65536:
        raise EngineError('Oversized suite queue record')
    return read_json(path)


def dead(root, name):
    """A released OS lock proves this registration has no living owner, without PID guesses."""
    lock = FileLock(root / (name + '.lock'))
    try:
        return lock.acquire()
    finally:
        lock.close()


def clean(root, generation):
    """Remove only this generation's known empty control files after proven drainage."""
    folder = root / generation
    if folder.exists():
        for lease in folder.glob('lease-*'):
            reject_path_aliases(lease, root)
            for name in ('startup.lock', 'owner.json', 'cancel'):
                path = lease / name
                reject_path_aliases(path, root)
                path.unlink(missing_ok=True)
            lease.rmdir()
        folder.rmdir()


def sweep(root):
    """Called under the metadata lock; drain old execution before removing its request."""
    pending = []
    for path in root.glob('*.lock'):
        name = path.stem
        if (len(name) == 32 and all(c in '0123456789abcdef' for c in name)
                and not (root / (name + '.request.json')).exists() and dead(root, name)):
            path.unlink()  # Registration and this sweep share the metadata lock.
    for path in root.glob('*.request.json'):
        name = path.name.removesuffix('.request.json')
        if len(name) != 32 or any(c not in '0123456789abcdef' for c in name):
            raise EngineError('Invalid suite queue registration name')
        reject_path_aliases(path, root)
        row = read(path)
        if row.get('generation') != name or type(row.get('sequence')) is not int:
            raise EngineError('Invalid suite queue registration')
        if dead(root, name):
            for lease in (root / name).glob('lease-*') if (root / name).exists() else []:
                reject_path_aliases(lease, root)
                recover(lease)
            clean(root, name)
            path.unlink()
            (root / (name + '.lock')).unlink()
        else:
            pending.append(row)
    return sorted(pending, key=lambda row: row['sequence'])


class Admission:
    """A suite can allocate several owned commands while holding one queue place."""
    def __init__(self, root, generation):
        self.folder = root / generation
        self.folder.mkdir(exist_ok=True)
        self.generation = generation
        self.mutex = threading.Lock()
        self.count = 0

    def lease(self):
        with self.mutex:
            self.count += 1
            path = self.folder / f'lease-{self.count}'
            path.mkdir()
            return path


@contextmanager
def admission(stop=None, timeout=86400):
    """Wait in the OS process, not a model loop; cancellation owns only this registration."""
    root = machine_directory()
    generation = uuid.uuid4().hex
    owner = None
    request = root / (generation + '.request.json')
    acquired = registered = owns_lock = False
    try:
        with locked(root / 'queue.lock'):
            pending = sweep(root)
            if len(pending) >= LIMIT:
                raise EngineError('Machine suite queue is full; no suite started')
            owner = FileLock(root / (generation + '.lock'))
            if not owner.acquire():
                raise EngineError('New suite ownership lock is unexpectedly occupied')
            owns_lock = True
            sequence = max([r['sequence'] for r in pending] + [0]) + 1
            atomic_json(request, {'generation': generation, 'sequence': sequence, 'pid': os.getpid()})
            registered = True
        deadline = time.monotonic() + timeout
        announced = False
        while True:
            if stop is not None and stop.is_set():
                raise EngineError('Queued suite cancelled before execution')
            with locked(root / 'queue.lock'):
                pending = sweep(root)
                if pending and pending[0]['generation'] == generation:
                    acquired = True
                    break
                if not announced:
                    position = next(i for i, row in enumerate(pending) if row['generation'] == generation)
                    print(f'Full suite queued: {position} request(s) ahead; waiting without model polling.', flush=True)
                    announced = True
            if time.monotonic() >= deadline:
                raise EngineError('Suite queue wait expired; no suite started')
            time.sleep(.1)
        yield Admission(root, generation)
    finally:
        # Normal and cancelled commands are drained before deleting admission.
        # A cleanup failure keeps the record so the next owner must recover it.
        try:
            if acquired:
                for lease in (root / generation).glob('lease-*'):
                    recover(lease)
                clean(root, generation)
            if registered:
                with locked(root / 'queue.lock'):
                    request.unlink(missing_ok=True)
        finally:
            if owner is not None:
                owner.close()
        if owns_lock:
            (root / (generation + '.lock')).unlink(missing_ok=True)
