"""Recover only a named owned job or a cooperative session after its queue owner exits."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from .project import EngineError
from .storage import atomic_json, read_json
from .suite_lock import locked


def job_name(lease):
    """The queue creates the random directory before any command may spawn."""
    import hashlib
    return 'Global\\FactorySuite-' + hashlib.sha256(str(Path(lease).resolve()).encode()).hexdigest()


def recover(lease):
    """Drain the exact owned resource before a replacement suite is admitted."""
    lease = Path(lease)
    if os.name == 'nt':
        from .windows_job import Job
        try:
            job = Job(job_name(lease), reopen=True)
        except OSError as error:
            if error.winerror == 2:
                return
            raise
        try:
            job.begin_stop()
            job.terminate()
            end = time.monotonic() + 10
            while not job.drained():
                if time.monotonic() >= end:
                    raise EngineError('Abandoned suite job cleanup remains unconfirmed')
                time.sleep(.02)
        finally:
            job.close()
        return
    with locked(lease / 'startup.lock'):
        (lease / 'cancel').touch()
        owner = read_json(lease / 'owner.json') if (lease / 'owner.json').exists() else None
    if owner is None:
        return  # A future guardian must acquire the same lock and see cancel before spawning.
    group = owner['group']
    if type(group) is not int or group <= 1:
        raise EngineError('Invalid suite guardian identity; no process was signalled')
    end = time.monotonic() + 10
    while True:
        try:
            os.killpg(group, 0)  # Observation only: recovery never signals a numeric PID/group.
        except ProcessLookupError:
            return
        if time.monotonic() >= end:
            raise EngineError('Abandoned suite session cleanup remains unconfirmed')
        time.sleep(.05)


def guardian(result, argv, shell, lease):
    """A generation-scoped cancel file asks this still-owned guardian to stop its own group."""
    lease = Path(lease)
    signal.signal(signal.SIGTERM, lambda *_: None)
    signal.signal(signal.SIGINT, lambda *_: None)
    with locked(lease / 'startup.lock'):
        if (lease / 'cancel').exists():
            result.write_text('125')
            return
        atomic_json(lease / 'owner.json', {'group': os.getpgrp()})
        try:
            process = subprocess.Popen(argv, shell=shell)
        except OSError as error:
            print(f'Owned command failed to start: {error}', file=sys.stderr, flush=True)
            process = None
    while process is not None and process.poll() is None and not (lease / 'cancel').exists():
        time.sleep(.02)
    if process is None or process.poll() is not None:
        pending = result.with_suffix('.pending')
        pending.write_text(str(process.returncode if process is not None else 125))
        pending.replace(result)
    while not (lease / 'cancel').exists():
        time.sleep(.05)
    os.killpg(os.getpgrp(), signal.SIGTERM)
    time.sleep(1)
    os.killpg(os.getpgrp(), signal.SIGKILL)
