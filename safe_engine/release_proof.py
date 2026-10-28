"""Release-specific identity around the shared, validated full-suite cache."""
import os
from pathlib import Path
import platform
import shutil
import sys
import uuid

from . import distribution
from .project import EngineError
from .runner import run_command
from .storage import locked
from .suites import cached, describe, evidence, execute

RECEIPT = '.factory/release-proof/suite.json'  # One replaceable slot, independent of shared cache capacity.


def session(root):
    """Refuse overlapping release operations without leaving a stale PID lock."""
    return locked(Path(root, '.factory/release-proof'))


def identity(root, tag):
    """Bind the standard suite to clean source, tools and hashed environment values."""
    if distribution.git('status', '--porcelain', cwd=root):
        raise EngineError('Release proof requires a clean checkout')
    distribution.check_release(root, tag)
    git = shutil.which('git')
    if not git:
        raise EngineError('Release proof needs Git')
    return describe(root, [[sys.executable, str(Path(root, 'tests/run.py'))]],
                    {'files': [str(Path(git).resolve())], 'environment': sorted(os.environ)},
                    {'release': tag, 'python': sys.version, 'platform': platform.platform()})


def current(root, tag, proof):
    """Reject drift or altered output immediately before release publication."""
    root = Path(root).resolve()
    receipt = cached(root, root / RECEIPT,
                     proof['identity'], lambda rows: all(row['passed'] for row in rows))
    if (proof['identity'] != identity(root, tag) or not proof['unchanged']
            or receipt is None or receipt['execution'] != proof['execution']
            or receipt['results'] != proof['results'] or not evidence(root, proof['results'])
            or not all(row['passed'] for row in proof['results'])):
        raise EngineError('Release suite proof is no longer current; nothing published')


def run(root, tag):
    """Run or reuse the complete suite; logs belong to one execution forever."""
    command = [sys.executable, str(Path(root, 'tests/run.py'))]
    log = Path(root, '.factory/release-proof/logs', uuid.uuid4().hex + '.log')
    proof = execute(root, lambda: identity(root, tag),
                    lambda slot: [run_command(command, root, 1800, log, owned_lease=slot.lease())],
                    validate=lambda rows: all(row['passed'] for row in rows), cache_path=RECEIPT)
    for result in proof['results']:
        print(Path(result['log']).read_text(encoding='utf-8', errors='replace'))
    current(root, tag, proof)
    print('Release suite: ' + ('reused' if proof['reused'] else 'executed'))
    return proof


def tag_target(root, tag):
    """The published remote tag must identify the source whose proof we checked."""
    tags = distribution.releases(distribution.git('ls-remote', '--tags', 'origin',
                                                  'refs/tags/' + tag, 'refs/tags/' + tag + '^{}', cwd=root))
    head = distribution.git('rev-parse', 'HEAD', cwd=root)
    if tags != [(tag, head)]:
        raise EngineError('Remote release tag does not point to the checked commit; nothing published')
