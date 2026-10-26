"""Full-suite identity and Safe item feedback regressions."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from safe_engine.project import EngineError
from safe_engine.runner import run_command
from safe_engine.suites import describe, execute
from safe_engine.workflow import Workflow


class SuitePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.queue = self.root / '.factory' / 'queue'
        self.queue.mkdir(parents=True)
        self.queue_patch = patch('safe_engine.suite_queue.machine_directory', return_value=self.queue)
        self.queue_patch.start()
        self.addCleanup(self.queue_patch.stop)
        (self.root / '.gitignore').write_text('.factory/\nbin/\n')
        (self.root / 'README.md').write_text('Contact opens help.\n')
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'add', '.gitignore', 'README.md'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture',
                        '-c', 'user.email=fixture@invalid', 'commit', '-qm', 'fixture'], check=True)

    def test_relative_executable_change_invalidate_cache(self):
        self.check_executable_change(r'bin\probe.cmd')

    def test_relative_path_change_invalidate_cache(self):
        self.check_executable_change('probe.cmd')

    def check_executable_change(self, name):
        if os.name != 'nt':
            self.skipTest('Windows command fixture')
        folder = self.root / 'bin'
        folder.mkdir()
        tool = folder / 'probe.cmd'
        with patch.dict(os.environ, {'PATH': 'bin' + os.pathsep + os.environ['PATH']}):
            tool.write_text('@echo FIRST\n@exit /b 0\n')
            calls = []
            argv = [name]
            def identity():
                return describe(self.root, [argv], {'files': [], 'environment': []}, {'case': name})
            def run(slot):
                log = self.root / '.factory' / f'run-{len(calls)}.log'
                calls.append(log)
                return [run_command(argv, self.root, 8, log, owned_lease=slot.lease())]
            first = execute(self.root, identity, run)
            same = execute(self.root, identity, run)
            tool.write_text('@echo CHANGED\n@exit /b 7\n')
            changed = execute(self.root, identity, run)
            self.assertEqual((first['results'][0]['exit_code'], same['reused'],
                              changed['reused'], changed['results'][0]['exit_code'], len(calls)),
                             (0, True, False, 7, 2))

    def test_tampered_evidence_and_unknown_inputs_never_reuse(self):
        argv = [sys.executable, '-c', 'print("ok")']
        calls = []
        def run(slot):
            log = self.root / '.factory' / f'log-{len(calls)}.txt'
            calls.append(log)
            return [run_command(argv, self.root, 8, log, owned_lease=slot.lease())]
        known = lambda: describe(self.root, [argv], {'files': [], 'environment': []}, {})
        first = execute(self.root, known, run)
        self.assertTrue(execute(self.root, known, run)['reused'])
        calls[0].write_text('tampered')
        self.assertFalse(execute(self.root, known, run)['reused'])
        unknown = lambda: describe(self.root, [argv], None, {})
        self.assertFalse(execute(self.root, unknown, run)['reused'])
        self.assertFalse(execute(self.root, unknown, run)['reused'])
        self.assertEqual(len(calls), 4)
        self.assertEqual(first['results'][0]['exit_code'], 0)

    def test_safe_completed_item_feedback_keeps_final_barriers_and_legacy_rule(self):
        profile = {'version': 2, 'interface': 'library', 'checks': [
            {'id': name, 'kind': 'unit', 'argv': ['{python}', '-c', 'print("ok")'], 'timeout_seconds': 8}
            for name in ('readme', 'license')], 'protected_paths': [], 'environment_inputs': [],
            'input_files': [], 'test_paths': [], 'review_scopes': [], 'exposure': 'local'}
        task = {'request': 'Read both files', 'acceptance': [
            {'id': name, 'text': name, 'mode': 'manual', 'checks': []} for name in ('A1', 'A2')]}
        flow = Workflow(self.root)
        flow.initialize(task, profile)
        for kind in ('analysis', 'plan'):
            path = self.root / '.factory' / f'{kind}.md'
            path.write_text('Fixture evidence for controller transition.\n')
            flow.record(kind, path)
        evidence = self.root / '.factory' / 'observed.txt'
        evidence.write_text((self.root / 'README.md').read_text())
        receipt = {'version': 1, 'item': 'T1', 'completed': True, 'mapping': 'README to readme',
                   'candidate': flow.status()['feature_candidate'], 'observations': [{
                       'criterion': 'A1', 'device': 'filesystem', 'action': 'Read README',
                       'result': evidence.read_text().strip(), 'status': 'PASS',
                       'evidence': ['.factory/observed.txt']}]}
        source = self.root / '.factory' / 'item.json'
        source.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(EngineError, 'fewer than all'):
            flow.feature_check(['readme', 'license'], source)
        self.assertTrue(flow.feature_check(['readme'], source)['feature_checks_passed'])
        state = flow.load()
        self.assertIsNone(state['manual'])
        self.assertIsNone(state['checks'])
        self.assertFalse(state['contract_sealed'])
        with self.assertRaises(EngineError):
            flow.require_manual(state)
        implementation = self.root / '.factory' / 'implementation.md'
        implementation.write_text('The completed contact sentence was read from the fixture file and the selected check passed. The license item still needs final manual observation and the full suite.\n')
        flow.record('implementation', implementation)
        receipt['candidate'] = flow.status()['manual_candidate']
        source.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(EngineError, 'A2'):
            flow.record('manual', source)
        legacy = flow.load()
        legacy.pop('suite_policy')
        with patch.object(flow, 'load', return_value=legacy):
            with self.assertRaisesRegex(EngineError, 'All testing waits'):
                flow.feature_check(['readme'], source)
