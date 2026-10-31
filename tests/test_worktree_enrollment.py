"""Independent worktree enrollment through real CLI/Git, with disposable lifecycle state."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from bundle_fixtures import legacy_bundle, offline_gate, SCRIPTS


class WorktreeEnrollmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source, self.target, self.home = (self.root / name for name in ('source', 'target', 'home'))
        self.env = {**os.environ, 'SAFE_ENGINE_HOME': str(self.home), 'PYTHONUTF8': '1'}
        self.old_bundle = legacy_bundle(self.root / 'old-bundle')
        self.new_bundle = legacy_bundle(self.root / 'new-bundle')
        self.source.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.source / 'seed').write_text('fixture\n')
        self.git('add', 'seed')
        self.git('commit', '-qm', 'initial fixture')
        (self.source / '.factory').mkdir()
        self.write(self.source / '.factory/entry-bundle.json', self.old_bundle)
        self.start(self.source, 'source-run')
        self.git('add', '-f', '.factory/entry-bundle.json', '.factory/fast/run.json', '.factory/fast/work-record.md')
        self.git('commit', '-qm', 'tracked legacy evidence')
        self.git('worktree', 'add', '-qb', 'new-work', str(self.target))

    def call(self, command, expected=0):
        result = subprocess.run(list(map(str, command)), cwd=self.source, env=self.env,
                                capture_output=True, encoding='utf-8', timeout=120)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def git(self, *args, project=None):
        return self.call(['git', '-C', project or self.source, *args]).strip()

    @staticmethod
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def start(self, project, key, expected=0):
        return self.call([*offline_gate(), 'start', '--project', project, '--key', key, '--kind', 'change',
                          '--request', 'Independent fixture work', '--no-ui', '--no-data'], expected)

    def enroll(self, expected=0, source=None, project=None):
        gate = os.environ.get('FACTORY_ENROLL_GATE') or str(SCRIPTS / 'fast_gate.py')
        return self.call([sys.executable, gate, 'enroll-worktree', '--project', project or self.target,
                          '--source', source or self.source, '--bundle', self.new_bundle['bundle_root'],
                          '--reason', 'Owner authorizes isolated worktree enrollment'], expected)

    def entry(self, project):
        key = hashlib.sha1(os.path.normcase(os.path.realpath(project)).encode()).hexdigest()[:16] + '.json'
        return self.home / 'active' / key

    @staticmethod
    def bytes_under(root):
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
                if p.is_file() and not p.name.endswith('.lock')}

    def unchanged(self, target=None, **enroll):
        """Enrollment refuses and writes nothing under the target's .factory."""
        target = target or self.target
        before = self.bytes_under(target / '.factory')
        self.enroll(project=target, expected=1, **enroll)
        self.assertEqual(self.bytes_under(target / '.factory'), before)

    def worktree(self, name):
        target = self.root / name
        self.git('worktree', 'add', '-qb', name, str(target))
        return target

    def test_enroll_preserves_source_bytes_and_starts_new_identity(self):
        original = self.bytes_under(self.source / '.factory')
        state = self.home / 'runs' / self.entry(self.source).name
        protected = {p: p.read_bytes() for p in (state, self.entry(self.source))}
        inherited = self.bytes_under(self.target / '.factory')
        self.assertIn('open or unknown', self.start(self.target, 'separate', expected=1))
        self.assertIn('No run started', self.enroll())
        lineage = json.loads((self.target / '.factory/worktree-enrollment.json').read_text())
        self.assertEqual(lineage['bundle']['root'], self.new_bundle['bundle_root'])
        archive = self.target / lineage['archive']
        for name in ('fast/run.json', 'entry-bundle.json', 'fast/work-record.md'):
            raw = (archive / Path(name).name).read_bytes()
            self.assertEqual(raw, inherited[name])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), lineage['files'][Path(name).name])
        self.write(self.target / '.factory/entry-bundle.json', self.old_bundle)  # a later selection keeps lineage
        self.start(self.target, 'separate')
        new = json.loads((self.target / '.factory/fast/run.json').read_text())
        self.assertNotEqual(json.loads(protected[state])['pr_instance'], new['pr_instance'])
        self.assertEqual(new['project'], str(self.target))
        self.assertEqual(new['inherited'], lineage)
        target_state = self.home / 'runs' / self.entry(self.target).name
        self.assertEqual(json.loads(target_state.read_text())['inherited'], lineage)
        self.assertFalse(new['done'].get('plan'))
        self.assertEqual(self.bytes_under(self.source / '.factory'), original)
        self.assertEqual({p: p.read_bytes() for p in protected}, protected)
        self.unchanged()

    def test_local_state_or_changed_inherited_files_refuse(self):
        for case in ('active', 'closed', 'safe', 'unknown', 'record'):
            with self.subTest(case=case):
                target = self.worktree(case)
                entry = self.entry(target)
                if case == 'active':
                    self.write(entry, {'project': str(target), 'key': 'local', 'home': True})
                if case == 'closed':
                    self.write(self.home / 'runs/closed' / entry.name,
                               {'version': 1, 'project': str(target), 'key': 'local', 'closed': True})
                if case == 'safe':
                    self.write(target / '.factory/state.json', {})
                if case == 'unknown':
                    self.write(target / '.factory/fast/run.json', {})
                if case == 'record':
                    (target / '.factory/fast/work-record.md').write_text('unrelated evidence')
                self.unchanged(target)
                self.assertFalse((target / '.factory/fast/archive').exists())

    def test_invalid_source_and_committed_unrelated_receipt_refuse(self):
        for source in (self.target, self.root):
            with self.subTest(source=source):
                self.unchanged(source=source)
        receipt = self.target / '.factory/entry-bundle.json'
        self.write(receipt, self.new_bundle)
        self.git('add', '-f', str(receipt), project=self.target)
        self.git('commit', '-qm', 'unrelated receipt', project=self.target)
        self.unchanged()

    def test_source_move_lineage_allows_legacy_path_and_normalizes_case(self):
        state = self.home / 'runs' / self.entry(self.source).name
        run = json.loads(state.read_text())
        old = json.loads((self.target / '.factory/fast/run.json').read_text())
        old['project'] = str(self.root / 'former-source')
        run['moves'] = [{'from': old['project']}]
        self.write(state, run)
        self.write(self.target / '.factory/fast/run.json', old)
        self.git('add', '-f', '.factory/fast/run.json', project=self.target)
        self.git('commit', '-qm', 'inherited legacy path', project=self.target)
        self.enroll(source=str(self.source).upper() if os.name == 'nt' else self.source)
        lineage = json.loads((self.target / '.factory/worktree-enrollment.json').read_text())
        self.assertEqual(lineage['inherited_project'], old['project'])

    def test_mismatched_or_malformed_runs_refuse(self):
        state = self.home / 'runs' / self.entry(self.source).name
        original = state.read_bytes()
        for changed in ({'key': 'another'}, {'closed': True}, {'moves': None}, {'bundle': None}, {'paused': []}):
            with self.subTest(changed=changed):
                self.write(state, {**json.loads(original), **changed})
                self.unchanged()
                self.assertEqual(state.read_bytes(), json.dumps({**json.loads(original), **changed}).encode())
        state.write_bytes(original)
        mirror = self.target / '.factory/fast/run.json'
        self.write(mirror, {**json.loads(mirror.read_bytes()), 'paused': []})
        self.git('add', '-f', str(mirror), project=self.target)
        self.git('commit', '-qm', 'malformed inherited fixture', project=self.target)
        self.unchanged()

    def test_tampered_archive_cannot_become_new_run_lineage(self):
        self.enroll()
        lineage = json.loads((self.target / '.factory/worktree-enrollment.json').read_text())
        (self.target / lineage['archive'] / 'run.json').write_bytes(b'changed archive bytes')
        before = self.bytes_under(self.target / '.factory')
        self.assertIn('Enrollment lineage changed', self.start(self.target, 'new-run', expected=1))
        self.assertEqual(self.bytes_under(self.target / '.factory'), before)
        self.assertFalse(self.entry(self.target).exists())


if __name__ == '__main__':
    unittest.main()
