"""Reuse complete-suite evidence only for identical effective inputs and intact outputs."""
import json
import os
import time
import uuid
from pathlib import Path

from .project import EngineError, digest, executable_path, file_hash, git, inside, reject_path_aliases, rescan
from .storage import atomic_json, now
from .suite_queue import admission


def inputs(value):
    """An explicit declaration keeps unknown external inputs from borrowing a cached result."""
    if not isinstance(value, dict) or set(value) - {'files', 'environment', 'clock'}:
        raise EngineError('suite_inputs needs files, environment and optional clock')
    for name in ('files', 'environment'):
        names = value.get(name)
        if (not isinstance(names, list) or len(names) > 1000
                or any(not isinstance(n, str) or not n or '\0' in n for n in names)
                or len(set(names)) != len(names)):
            raise EngineError(f'suite_inputs.{name} needs unique explicit input names')
    clock = value.get('clock')
    if clock is not None and (not isinstance(clock, dict) or set(clock) != {'instant', 'timezoneId'}
                              or any(not isinstance(x, str) or not x for x in clock.values())):
        raise EngineError('suite_inputs.clock needs explicit instant and timezoneId strings')
    return value


def describe(project, commands, declared, context):
    """Resolve commands and hash input values; never put environment secrets in receipts."""
    from .project import project_files, factory_inputs
    if declared is None:
        return None  # Unknown external inputs still queue, but never borrow evidence.
    inputs(declared)
    try:
        commit = git(project, 'rev-parse', 'HEAD').strip()
    except EngineError:
        return None
    rescan()
    executables = {}
    for argv in commands:
        path = executable_path(argv[0], project)
        if path is None or not path.is_file():
            return None
        executables[argv[0]] = {'path': str(path), 'sha256': file_hash(path)}
    names = set(declared['environment']) | {'PATH', 'PYTHONPATH', 'NODE_PATH', 'TZ'}
    external = {}
    for name in declared['files']:
        path = Path(name) if Path(name).is_absolute() else inside(project, name)
        if not path.is_file():
            return None
        external[name] = file_hash(path)
    return {'commit': commit,
            'fingerprint': digest({'source': project_files(project), 'factory': factory_inputs(),
                'argv': commands, 'executables': executables, 'external': external,
                'environment': {name: digest(os.environ.get(name)) for name in sorted(names)},
                'clock': declared.get('clock'), 'context': context})}


def evidence(project, results):
    """Measure an actual proof check while preserving its Boolean contract."""
    try:
        from . import run_metrics
    except Exception:
        run_metrics = None
    op_id = f'evidence-{uuid.uuid4().hex}'
    if run_metrics:
        run_metrics.safe_call(run_metrics.emit_current, 'operation.start', name='evidence_validation', event_id=op_id)
    started = time.monotonic()
    passed = False
    try:
        passed = _evidence(project, results)
        return passed
    finally:
        if run_metrics:
            run_metrics.safe_call(run_metrics.emit_current, 'operation.finish', name='evidence_validation',
                                  event_id=op_id + '-end', parent_id=op_id,
                                  duration_seconds=round(time.monotonic() - started, 3), passed=passed)


def _evidence(project, results):
    """Verify every retained command result and its local outputs before any reuse."""
    if not isinstance(results, list) or not 0 < len(results) <= 1000:
        return False
    for result in results:
        if (not isinstance(result, dict) or not isinstance(result.get('artifacts', []), list)
                or type(result.get('passed')) is not bool or type(result.get('exit_code')) is not int
                or result.get('timed_out') or result.get('log_truncated')
                or result['passed'] != (result['exit_code'] == 0)):
            return False
        for item in [{'path': result.get('log'), 'sha256': result.get('log_sha256')}, *result.get('artifacts', [])]:
            try:
                path = Path(item['path']).absolute()
                if not path.is_relative_to(project):
                    return False
                reject_path_aliases(path, project)
                if file_hash(path) != item['sha256']:
                    return False
            except (OSError, ValueError, TypeError, KeyError, EngineError):
                return False
    return True


def cached(project, path, identity, validate):
    """Partial, interrupted or modified receipts are never accepted as completed proof."""
    try:
        if path.stat().st_size > 1_000_000:
            return None
        reject_path_aliases(path, project)
        row = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(row, dict):
            return None
        checksum = row.pop('checksum')
        if (checksum == digest(row) and row.get('identity') == identity and row.get('unchanged') is True
                and evidence(project, row['results']) and validate(row['results'])):
            return row
    except (OSError, ValueError, TypeError, KeyError, EngineError):
        pass
    return None


def execute(project, identity, run, *, cache=True, stop=None, validate=lambda results: True):
    """Reuse verified proof early; queue misses and preserve truthful terminal evidence."""
    project = Path(project).resolve(strict=True)
    before = identity()
    directory = inside(project, '.factory/suite-cache')
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (digest(before) + '.json')
    if cache and before is not None:
        prior = cached(project, path, before, validate)
        if prior:
            if identity() != before:
                raise EngineError('Suite inputs changed during cache reuse; request current proof')
            prior = cached(project, path, before, validate)
        if prior:
            if stop is not None and stop.is_set():
                raise EngineError('Suite reuse cancelled before return')
            print('Reused unchanged full-suite result: ' + before['commit'], flush=True)
            try:
                from . import run_metrics
                run_metrics.emit_current('reuse', name='full_suite', commit=before.get('commit'))
            except Exception:
                pass
            return {**prior, 'reused': True}
    with admission(stop=stop) as slot:
        current = identity()
        if current != before:
            try:
                from . import run_metrics
                run_metrics.emit_current('invalidate', reason='suite_inputs_changed_while_queued')
            except Exception:
                pass
            raise EngineError('Suite inputs changed while queued; request proof for the current candidate')
        prior = cached(project, path, before, validate) if cache and before is not None else None
        if prior:
            print('Reused unchanged full-suite result: ' + before['commit'], flush=True)
            try:
                from . import run_metrics
                run_metrics.emit_current('reuse', name='full_suite', commit=before.get('commit'), after_queue=True)
            except Exception:
                pass
            return {**prior, 'reused': True}
        op_id = f'suite-exec-{slot.generation}'
        try:
            from . import run_metrics
            # container=True: wraps per-command ops; excluded from summed/overlap aggregation
            run_metrics.emit_current('operation.start', name='full_suite', event_id=op_id, container=True)
        except Exception:
            pass
        results = run(slot)
        after = identity()
        for result in results:
            result['log_sha256'] = file_hash(Path(result['log']))
        unchanged = after == before
        row = {'version': 1, 'identity': before, 'execution': slot.generation,
               'completed_at': now(), 'unchanged': unchanged, 'results': results}
        if (before is not None and unchanged and evidence(project, results) and validate(results)
                and (path.exists() or sum(1 for _ in directory.glob('*.json')) < 256)):
            atomic_json(path, {**row, 'checksum': digest(row)})
        try:
            from . import run_metrics
            run_metrics.emit_current('operation.finish', name='full_suite', event_id=op_id + '-end',
                                     parent_id=op_id, reused=False,
                                     container=True)
            if not unchanged:
                run_metrics.emit_current('invalidate', reason='suite_inputs_changed_after_execution')
        except Exception:
            pass
        return {**row, 'reused': False}
