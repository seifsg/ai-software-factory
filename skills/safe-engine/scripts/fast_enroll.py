"""Enroll inherited Git worktree evidence without transferring its source run."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from uuid import uuid4

FILES = ('.factory/fast/run.json', '.factory/entry-bundle.json', '.factory/fast/work-record.md')


def parser(sub, common):
    """Require explicit source, factory and authority for this lifecycle transition."""
    command = sub.add_parser('enroll-worktree', parents=[common], help='Archive inherited evidence for an independent new worktree run')
    for name in ('source', 'bundle', 'reason'):
        command.add_argument('--' + name, required=True)


def plain(path):
    """Reject evidence aliases before reads, archival or removal."""
    for node in (path, *path.parents):
        if os.path.lexists(node):
            info = node.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise RuntimeError('Enrollment evidence must not use symlinks or reparse points')


def git(project, *args):
    """Read raw Git bytes so inherited evidence is compared without newline conversion."""
    result = subprocess.run(['git', '-C', str(project), *args], capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError('Enrollment Git validation failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout


def location(project, option):
    """Resolve Git metadata relative to its worktree, including Windows casing."""
    return Path(project, os.fsdecode(git(project, 'rev-parse', option)).strip()).resolve()


def validate(project, source, gate, release):
    """Malformed lineage is a refusal, never a partially applied transition."""
    try:
        return inherited_snapshot(project, source, gate, release)
    except (ValueError, TypeError, KeyError) as error:
        raise RuntimeError('Invalid enrollment lineage; preserve evidence and diagnose it') from error


def supported(run, gate):
    """Use the gate's supported shape and reject falsey malformed lifecycle containers."""
    return (isinstance(run, dict) and gate.well_formed(run) and run.get('closed') is False
            and isinstance(run.get('moves', []), list)
            and (run.get('paused') is None or isinstance(run['paused'], dict)))


def inherited_snapshot(project, source, gate, release):
    """Prove an unregistered sibling worktree inherited exactly this source run."""
    for root in (project, source):
        plain(root)
        if not root.is_dir() or gate.norm(location(root, '--show-toplevel')) != gate.norm(root):
            raise RuntimeError('Enrollment requires exact Git worktree roots')
    if (gate.norm(project) == gate.norm(source)
            or gate.norm(location(project, '--git-common-dir')) != gate.norm(location(source, '--git-common-dir'))
            or gate.norm(location(project, '--git-dir')) == gate.norm(location(source, '--git-dir'))):
        raise RuntimeError('Enrollment requires distinct worktrees of the same Git repository')
    entry = gate.registry_path(project)
    held = (entry, gate.store.state_path(entry), gate.store.closed_path(entry))
    for path in held:
        plain(path)
    if gate.store.held(gate.ACTIVE, project) or any(map(os.path.lexists, held)):
        raise RuntimeError('Local active, lost or closed run state cannot be enrolled')
    for name in ('.factory/state.json', '.factory/history', '.factory/runs', '.factory/worktree-enrollment.json'):
        plain(project / name)
        if os.path.lexists(project / name):
            raise RuntimeError('Existing or unknown local lifecycle evidence cannot be enrolled')
    snapshot = {}
    for name in FILES:
        path = project / name
        plain(path)
        raw = path.read_bytes()
        # clean/smudge filters and core.autocrlf may change worktree bytes; compare Git's canonical form.
        blob = git(project, 'rev-parse', 'HEAD:' + name).strip()
        actual = git(project, 'hash-object', '--path=' + name, str(path)).strip()
        if blob != actual:
            raise RuntimeError('Enrollment requires unchanged tracked inherited evidence: ' + name)
        snapshot[name] = raw
    inherited = json.loads(snapshot[FILES[0]].decode('utf-8-sig'))
    receipt = release.saved_selection(project / FILES[1])
    source_entry = gate.registry_path(source)
    for path in (source_entry, gate.store.state_path(source_entry), source / FILES[0]):
        plain(path)
    canonical = gate.store.current(gate.load(gate.store.state_path(source_entry)))
    registration = gate.load(source_entry)
    if (not supported(canonical, gate) or canonical.get('lost')
            or not isinstance(canonical.get('created'), str) or not canonical['created']
            or not isinstance(canonical.get('request'), str) or not canonical['request'].strip()
            or not isinstance(registration, dict) or registration.get('key') != canonical.get('key')
            or gate.norm(registration.get('project', '')) != gate.norm(source)
            or gate.norm(canonical.get('project', '')) != gate.norm(source)):
        raise RuntimeError('Source must have an intact, registered open run')
    if (not supported(inherited, gate) or inherited.get('version') != 1
            or (inherited.get('pr_instance') and inherited['pr_instance'] != canonical.get('pr_instance'))
            or not all(inherited.get(field) and inherited.get(field) == canonical.get(field)
                       for field in ('key', 'created', 'request', 'bundle'))):
        raise RuntimeError('Inherited mirror does not identify the source run')
    lineage = [canonical['project'], *(move.get('from') for move in canonical.get('moves', []) if isinstance(move, dict))]
    if (not isinstance(inherited.get('project'), str) or gate.norm(inherited['project']) == gate.norm(project)
            or not any(isinstance(root, str) and gate.norm(inherited['project']) == gate.norm(root) for root in lineage)):
        raise RuntimeError('Inherited project path is not in the source run lineage')
    # A copied legacy receipt can differ from the run bundle, but must come from the same committed snapshot.
    if not receipt or git(source, 'rev-parse', 'HEAD:' + FILES[1]).strip() != git(project, 'rev-parse', 'HEAD:' + FILES[1]).strip():
        raise RuntimeError('Inherited receipt does not match the source repository snapshot')
    return snapshot, inherited, canonical


def inheritance(project, gate):
    """Bind a new run to complete archived enrollment evidence, never inherited acceptance."""
    marker = project / '.factory/worktree-enrollment.json'
    plain(marker)
    try:
        lineage = gate.load(marker)
        archive = lineage['archive']
        # The selection may change after enrollment; only the archive identity binds later runs.
        if (lineage['version'] != 1 or gate.norm(lineage['project']) != gate.norm(project)
                or not re.fullmatch(r'\.factory/fast/archive/inherited-[0-9a-f]{32}', archive)
                or set(lineage['files']) != {Path(name).name for name in FILES}):
            raise ValueError('enrollment identity mismatch')
        folder = project / archive
        plain(folder / 'lineage.json')
        if gate.load(folder / 'lineage.json') != lineage:
            raise ValueError('archive lineage changed')
        for name, digest in lineage['files'].items():
            plain(folder / name)
            if hashlib.sha256((folder / name).read_bytes()).hexdigest() != digest:
                raise ValueError('archive bytes changed')
        return {'inherited': lineage}
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise RuntimeError('Enrollment lineage changed or is incomplete; preserve evidence and diagnose it') from error


def run(args, gate):
    """Archive all bytes before publishing the new selection; never write the source or its state."""
    import resolve_bundle as release
    if not args.project or not args.reason.strip():
        raise RuntimeError('Enrollment needs --project and a nonempty owner authorization reason')
    project, source = (Path(gate.native(value)).absolute() for value in (args.project, args.source))
    plain(project)
    plain(source)
    with release.selection_lock(project):
        snapshot, inherited, canonical = validate(project, source, gate, release)
        selected = release.inspect_bundle(args.bundle, entrypoint='safe-engine')
        if not (Path(selected['bundle_root']) / 'skills/safe-engine/scripts/fast_enroll.py').is_file():
            raise RuntimeError('Selected factory does not support worktree enrollment; choose a reviewed current bundle')
        archive = project / '.factory/fast/archive' / ('inherited-' + uuid4().hex)
        plain(archive)
        archive.mkdir(parents=True)
        files = {}
        for name, raw in snapshot.items():
            target = archive / Path(name).name
            target.write_bytes(raw)
            files[target.name] = hashlib.sha256(raw).hexdigest()
        lineage = {'version': 1, 'project': str(project.resolve()), 'source': str(source.resolve()),
                   'source_run': {key: canonical.get(key) for key in ('key', 'created', 'pr_instance')},
                   'inherited_project': inherited['project'], 'head': git(project, 'rev-parse', 'HEAD').decode().strip(),
                   'at': gate.now(), 'reason': args.reason, 'files': files,
                   'bundle': {'root': selected['bundle_root'], 'revision': selected['revision']},
                   'archive': archive.relative_to(project).as_posix()}
        gate.save(archive / 'lineage.json', lineage, new=True)
        # Revalidate after bundle inspection: a concurrent source or target write cannot be hidden by the archive.
        latest, _, current = validate(project, source, gate, release)
        if latest != snapshot or current != canonical:
            raise RuntimeError('Enrollment inputs changed; preserved archive, no lifecycle transition')
        gate.save(project / '.factory/worktree-enrollment.json', lineage, new=True)
        release.save_selection(project / FILES[1], selected, 'explicit')
        # Mirror last: ordinary start remains closed until every inherited byte has an archived copy.
        (project / FILES[2]).unlink()
        (project / FILES[0]).unlink()
        gate.log('run.enroll_worktree', **lineage)
        print(f"Enrolled independent worktree: {project}\nInherited evidence: {archive}\n"
              f"Selected factory: {selected['revision']}\nNo run started; use start with a new key and request.")
