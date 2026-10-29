"""Current public startup, separate from deliberately historical run-state fixtures."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from bundle_fixtures import historical_gate
from safe_engine.project import bundle_input_paths

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/safe-engine/scripts'
ENTRY = '''import sys
from pathlib import Path
sys.path.insert(0,sys.argv.pop(1))
import fast_gate,resolve_bundle
source=Path(sys.argv.pop(1)); calls=Path(sys.argv.pop(1)); forbidden=sys.argv.pop(1)=='forbid'
def remote(*args,**kwargs):
 if forbidden: raise AssertionError('Unexpected remote discovery')
 calls.write_text(calls.read_text()+'x' if calls.exists() else 'x')
 return resolve_bundle.inspect_bundle(source,entrypoint='safe-engine')
resolve_bundle.resolve_bundle=remote
fast_gate.main()
'''


class StartSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory(prefix='selected factory ')
        cls.source = Path(cls.shared.name) / 'bundle'
        for name in bundle_input_paths(ROOT):
            target = cls.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        for args in [('init', '-q'), ('remote', 'add', 'origin', 'https://github.com/seifsg/ai-software-factory.git'),
                     ('add', '.'), ('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                                    '-c', 'commit.gpgsign=false', 'commit', '-qm', 'local snapshot')]:
            subprocess.run(['git', '-C', str(cls.source), *args], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='start selection ')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        self.calls = self.root / 'calls'
        self.env = dict(os.environ, SAFE_ENGINE_HOME=str(self.root / 'home'), PYTHONDONTWRITEBYTECODE='1')

    def cli(self, *args, forbidden=False, ok=True):
        result = subprocess.run([sys.executable, '-X', 'utf8', '-c', ENTRY, str(SCRIPTS), str(self.source),
                                 str(self.calls), 'forbid' if forbidden else 'allow', *args,
                                 '--project', str(self.project)], env=self.env, capture_output=True,
                                text=True, encoding='utf-8', timeout=60)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def start(self, **kwargs):
        return self.cli('start', '--key', 'fresh', '--kind', 'change', '--no-ui', '--no-data',
                        '--request', 'Fix this isolated fixture', **kwargs)

    def run_record(self):
        return json.loads((self.project / '.factory/fast/run.json').read_text(encoding='utf-8'))

    def test_receiptless_public_start_selects_once_before_activating_current_policy(self):
        self.start()
        receipt = json.loads((self.project / '.factory/entry-bundle.json').read_text(encoding='utf-8'))
        run = self.run_record()
        self.assertEqual(self.calls.read_text(), 'x')
        self.assertEqual(run['bundle'], {'root': receipt['bundle_root'], 'revision': receipt['revision']})
        self.assertTrue(run['check_selection'])
        self.assertTrue(run['suite_policy'])
        self.assertNotIn('legacy start', self.cli('status', forbidden=True))

    def test_explicit_public_start_inspects_pin_without_remote_discovery(self):
        self.start()
        receipt_path = self.project / '.factory/entry-bundle.json'
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        self.cli('close', '--abandon', 'fixture finished')
        receipt['policy'] = 'explicit'
        receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
        before = receipt_path.read_bytes()
        self.assertIn('latest factory not checked', self.start(forbidden=True))
        self.assertEqual(receipt_path.read_bytes(), before)
        self.assertEqual(self.calls.read_text(), 'x')

    def test_automatic_new_start_still_discovers_and_resume_does_not(self):
        self.start()
        self.cli('status', forbidden=True)
        self.assertEqual(self.calls.read_text(), 'x')
        self.cli('close', '--abandon', 'fixture finished', forbidden=True)
        self.start()
        self.assertEqual(self.calls.read_text(), 'xx')

    def test_corrupt_receipt_fails_without_state_or_replacement(self):
        receipt = self.project / '.factory/entry-bundle.json'
        receipt.parent.mkdir()
        receipt.write_text('{broken', encoding='utf-8')
        self.assertIn('Cannot read existing bundle selection', self.start(forbidden=True, ok=False))
        self.assertEqual(receipt.read_text(), '{broken')
        self.assertFalse((self.project / '.factory/fast/run.json').exists())

    def test_mismatched_revision_fails_without_silent_latest_substitution(self):
        receipt = self.project / '.factory/entry-bundle.json'
        receipt.parent.mkdir()
        receipt.write_text(json.dumps({'version': 2, 'policy': 'explicit', 'revision': 'a' * 40,
                                      'bundle_root': str(self.source)}), encoding='utf-8')
        self.assertIn('does not match the requested commit', self.start(forbidden=True, ok=False))
        self.assertFalse((self.project / '.factory/fast/run.json').exists())

    def test_historical_unresolved_run_resume_keeps_recorded_policy(self):
        result = subprocess.run([*historical_gate(), 'start', '--key', 'old', '--kind', 'change',
                                 '--no-ui', '--no-data', '--request', 'historical fixture', '--project',
                                 str(self.project)], env=self.env, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        before = self.run_record()
        self.cli('status', forbidden=True)
        after = self.run_record()
        self.assertEqual(after, before)
        self.assertFalse(after['check_selection'])
        self.assertFalse((self.project / '.factory/entry-bundle.json').exists())
