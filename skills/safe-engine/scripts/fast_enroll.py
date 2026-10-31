"""Enroll a Git worktree that inherited another worktree's tracked run, never touching the source run."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from uuid import uuid4

FILES = ('.factory/fast/run.json', '.factory/entry-bundle.json', '.factory/fast/work-record.md')
MARKER = '.factory/worktree-enrollment.json'
LOCAL = ('.factory/state.json', '.factory/history', '.factory/runs', MARKER)  # local lifecycle evidence refuses
ARCHIVE = '.factory/fast/archive'


def parser(sub, common):
    """Explicit source, factory and owner reason: enrollment is never implied."""
    command = sub.add_parser('enroll-worktree', parents=[common], help='Archive inherited run files for a new worktree run')
    for name in ('source', 'bundle', 'reason'):
        command.add_argument('--' + name, required=True)


def check(ok, message):
    if not ok:
        raise RuntimeError(message)


def plain(*paths):
    """No symlink or reparse point anywhere on these paths, so no evidence is an alias."""
    for path in paths:
        for node in (path, *path.parents):
            info = os.lstat(node) if os.path.lexists(node) else None
            check(not info or not (stat.S_ISLNK(info.st_mode)
                                   or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT),
                  'Enrollment evidence must not use symlinks or reparse points')


def git(root, *args):
    """Raw Git bytes: inherited evidence compares without newline conversion."""
    result = subprocess.run(['git', '-C', str(root), *map(str, args)], capture_output=True, timeout=120)
    check(not result.returncode, 'Enrollment Git check failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout.strip()


def where(root, option, gate):
    """A Git location, normalized for case and relative paths."""
    return gate.norm(Path(root, os.fsdecode(git(root, 'rev-parse', option))).resolve())


def open_run(run, gate):
    """The gate's open-run shape, with no falsey stand-ins for its containers."""
    return (isinstance(run, dict) and gate.well_formed(run) and run.get('closed') is False
            and isinstance(run.get('moves', []), list) and (run.get('paused') is None or isinstance(run['paused'], dict)))


def inherited(project, source, gate, release):
    """The inherited bytes, mirror and source run, once every check passes."""
    source_entry = gate.registry_path(source)
    state = gate.store.state_path(source_entry)
    plain(project, source, source_entry, state, project / ARCHIVE, *(project / name for name in (*LOCAL, *FILES)))
    top, common = ([where(root, option, gate) for root in (project, source)]
                   for option in ('--show-toplevel', '--git-common-dir'))
    check(top == [gate.norm(project), gate.norm(source)] and top[0] != top[1] and common[0] == common[1],
          'Enrollment requires distinct worktrees of the same Git repository')
    check(not gate.store.held(gate.ACTIVE, project) and not any(os.path.lexists(project / name) for name in LOCAL),
          'Local active, lost, closed or unknown run state cannot be enrolled')
    snapshot = {}
    for name in FILES:  # Git's canonical form: filters and autocrlf may change worktree bytes
        check(git(project, 'rev-parse', 'HEAD:' + name) == git(project, 'hash-object', '--path=' + name, project / name),
              'Enrollment requires unchanged tracked inherited evidence: ' + name)
        snapshot[name] = (project / name).read_bytes()
    mirror, run, registration = json.loads(snapshot[FILES[0]].decode('utf-8-sig')), gate.load(state), gate.load(source_entry)
    check(open_run(gate.store.current(run), gate) and not run.get('lost') and isinstance(registration, dict)
          and registration.get('key') == run['key']
          and gate.norm(registration.get('project', '')) == gate.norm(run['project']) == gate.norm(source),
          'Source must have an intact, registered open run')
    same = all(mirror.get(field) and mirror.get(field) == run.get(field) for field in ('key', 'created', 'request', 'bundle'))
    check(open_run(mirror, gate) and mirror.get('version') == 1 and same,
          'Inherited mirror does not identify the source run')
    lineage = [run['project'], *(move.get('from') for move in run.get('moves', []) if isinstance(move, dict))]
    check(gate.norm(mirror['project']) != gate.norm(project)
          and any(isinstance(root, str) and gate.norm(root) == gate.norm(mirror['project']) for root in lineage),
          'Inherited project path is not in the source run lineage')
    # A legacy receipt may name another bundle than the run, but must be the source's committed one.
    check(release.saved_selection(project / FILES[1])
          and git(source, 'rev-parse', 'HEAD:' + FILES[1]) == git(project, 'rev-parse', 'HEAD:' + FILES[1]),
          'Inherited receipt does not match the source repository snapshot')
    return snapshot, mirror, run


def inheritance(project, gate):
    """The verified archive a new run links as `inherited`; a changed or partial archive refuses."""
    try:
        lineage = gate.load(project / MARKER)
        folder = project / lineage['archive']
        check(lineage['version'] == 1 and gate.norm(lineage['project']) == gate.norm(project)
              and re.fullmatch(re.escape(ARCHIVE) + r'/inherited-[0-9a-f]{32}', lineage['archive'])
              and set(lineage['files']) == {Path(name).name for name in FILES}, 'identity')
        plain(project / MARKER, *(folder / name for name in lineage['files']))
        check(all(hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
                  for name, digest in lineage['files'].items()), 'bytes')
        return {'inherited': lineage}
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        raise RuntimeError('Enrollment lineage changed or is incomplete; preserve evidence and diagnose it') from error


def run(args, gate):
    """Check, archive every inherited byte, select the factory, and drop the mirror last so start stays closed."""
    import resolve_bundle as release
    check(args.project and args.reason.strip(), 'Enrollment needs --project and a nonempty owner authorization reason')
    project, source = (Path(gate.native(value)).absolute() for value in (args.project, args.source))
    selected = release.inspect_bundle(args.bundle, entrypoint='safe-engine')  # slow: inspect before checks, not between
    check((Path(selected['bundle_root']) / 'skills/safe-engine/scripts/fast_enroll.py').is_file(),
          'Selected factory does not support worktree enrollment; choose a reviewed current bundle')
    with release.selection_lock(project):
        try:
            snapshot, mirror, origin = inherited(project, source, gate, release)
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise RuntimeError('Invalid enrollment lineage; preserve evidence and diagnose it') from error
        archive = project / ARCHIVE / ('inherited-' + uuid4().hex)
        archive.mkdir(parents=True)
        for name, raw in snapshot.items():
            (archive / Path(name).name).write_bytes(raw)
        lineage = {'version': 1, 'project': str(project.resolve()), 'source': str(source.resolve()),
                   'source_run': {key: origin.get(key) for key in ('key', 'created', 'pr_instance')},
                   'inherited_project': mirror['project'], 'head': git(project, 'rev-parse', 'HEAD').decode(),
                   'at': gate.now(), 'reason': args.reason,
                   'files': {Path(name).name: hashlib.sha256(raw).hexdigest() for name, raw in snapshot.items()},
                   'bundle': {'root': selected['bundle_root'], 'revision': selected['revision']},
                   'archive': archive.relative_to(project).as_posix()}
        gate.save(project / MARKER, lineage, new=True)
        release.save_selection(project / FILES[1], selected, 'explicit')
        (project / FILES[2]).unlink()
        (project / FILES[0]).unlink()  # last: start stays closed until every inherited byte is archived
        gate.log('run.enroll_worktree', **lineage)
        print(f"Enrolled independent worktree: {project}\nInherited evidence: {archive}\n"
              f"Selected factory: {selected['revision']}\nNo run started; use start with a new key and request.")
