"""Project-scoped Codex setup, explicit consent, and actual native command effects."""
import json
import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_fast_gate as harness
import test_fast_hosts as hosts
from fixture_hook_parser import native_fixture


class ScopedCodexTests(harness.GateHarness, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.home = self.root / 'user é ! %'
        self.home.mkdir()
        self.env.update(USERPROFILE=str(self.home), HOME=str(self.home),
                        CODEX_HOME=str(self.home / '.codex'), CODEX_THREAD_ID='')
        self.scope = hosts.installer.ledger().registry_path(Path('active'), self.project).stem
        self.command = [sys.executable, str(harness.GATE), 'hook', '--host', 'codex', '--scope', self.scope]

    def codex(self, kind='PreToolUse', session='other', cwd=None, **extra):
        return self.hook({'hook_event_name': kind, 'session_id': session, 'cwd': str(cwd or self.project),
                          'tool_name': 'apply_patch', 'tool_input': {'command':
                          '*** Begin Patch\n*** Add File: src/a.ts\n+x\n*** End Patch'}, **extra}, self.command)

    def begin(self):
        self.start('--session', 'joined', kind='change')

    def test_other_chats_share_protection_but_only_joined_current_project_gets_messages(self):
        self.begin()
        self.assertEqual(self.codex()['hookSpecificOutput']['permissionDecision'], 'deny')
        for event in ('Stop', 'SessionStart', 'UserPromptSubmit'):
            self.assertIsNone(self.codex(event))
        self.assertEqual(self.codex('Stop', session='joined')['decision'], 'block')
        other = self.root / 'other'; other.mkdir()
        self.assertIsNone(self.codex('Stop', session='joined', cwd=other))
        self.assertIsNone(self.codex(session='joined', cwd=other, tool_name='Bash',
                                     tool_input={'command': 'rm -rf dist'}))
        absolute = '*** Begin Patch\n*** Add File: '+str(self.project/'src/b.ts')+'\n+x\n*** End Patch'
        self.assertEqual(self.codex(cwd=other, tool_input={'command': absolute})['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_explicit_join_normalizes_optional_data_and_legacy_sessions_are_not_consent(self):
        self.begin()
        entry = next((self.root/'home/active').glob('*.json'))
        state = self.root/'home/runs'/entry.name
        data = json.loads(state.read_text()); data['participants'] = [None, {}, 'good', 'bad space', 'good']
        state.write_text(json.dumps(data))
        reg = json.loads(entry.read_text()); reg['sessions'] = ['other']; entry.write_text(json.dumps(reg))
        self.assertIsNone(self.codex('Stop'))
        self.gate('join', '--session', 'other')
        self.assertEqual(json.loads(state.read_text())['participants'], ['good', 'other'])
        self.assertEqual(self.codex('Stop')['decision'], 'block')

    def test_two_home_files_and_closed_retirement_preserve_recovery(self):
        self.begin()
        entry = next((self.root/'home/active').glob('*.json')); state = self.root/'home/runs'/entry.name
        entry.unlink()
        self.assertEqual(self.codex()['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertTrue(entry.exists())
        state.unlink()
        self.assertIn('missing', self.codex()['hookSpecificOutput']['permissionDecisionReason'])
        self.gate('close', '--abandon', 'fixture ended')
        self.begin()
        self.gate('close', '--abandon', 'readable fixture ended')
        closed = state.parent/'closed'/state.name
        closed.replace(state)  # an interrupted retirement leaves authoritative closed data
        self.assertIsNone(self.codex())
        self.assertFalse(state.exists()); self.assertFalse(entry.exists()); self.assertTrue(closed.exists())

    def test_nested_child_build_is_not_denied_by_parent_plan_hook(self):
        self.begin()
        child = self.project/'child'; child.mkdir()
        self.gate('start', '--key', 'child', '--kind', 'change', '--request', 'harmless child', project=child)
        (child/'.factory/fast/work-record.md').write_text(
            '# fixture\n## Tickets\n**Ticket:** none (isolated fixture)\n**Backlog:** none\n'
            '## Plan\n**Success:** harmless change\n### Todos\n- T1 Write harmless fixture -> observe it (#100, A4)\n')
        self.gate('done', 'tickets', project=child); self.gate('done', 'plan', project=child)
        self.assertIsNone(self.codex(cwd=child))
        self.assertEqual(self.codex()['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_failed_participation_write_has_actionable_recovery_and_no_success_log(self):
        gate = harness.module('fast_gate')
        run = {'project': str(self.project), 'key': 'fixture', 'participants': []}
        error = io.StringIO()
        with patch.object(gate, 'open_run', return_value=(self.project, run)), \
                patch.object(gate, 'put', side_effect=PermissionError('unsafe private path')), \
                patch.object(gate, 'log') as log, contextlib.redirect_stderr(error):
            with self.assertRaises(SystemExit):
                gate.cmd_join(SimpleNamespace(project=str(self.project), session='joined'))
        log.assert_called_once_with('run.join_failed', key='fixture', error_class='PermissionError')
        self.assertIn('Participation was not saved', error.getvalue())
        self.assertNotIn('unsafe private path', error.getvalue())

    def configure(self, **kw):
        with patch.dict(os.environ, self.env), native_fixture(hosts.installer, hosts.module('fast_hook_config')):
            return hosts.installer.configure('codex', self.project, self.home, log=lambda _: None, **kw)

    def test_hooks_only_preserve_canonical_skills_mixed_handlers_and_unknown_commands(self):
        canonical = self.project/'.agents/skills/safe-engine/SKILL.md'
        canonical.parent.mkdir(parents=True); canonical.write_text('canonical')
        config = self.project/'.codex/hooks.json'; config.parent.mkdir()
        owned = hosts.installer.scoped_commands(hosts.SCRIPTS, self.project)[0]
        unrelated = 'sh "C:/tools/run-gate.sh" codex '+self.scope
        unknown_override = {'command': owned, 'commandWindows': 'echo custom Windows handler'}
        config.write_text(json.dumps({'custom': 7, 'hooks': {'PreToolUse': [
            {'matcher': 'Bash', 'metadata': 'preserved', 'hooks': [{'command': owned}, {'command': 'echo mine'}, {'command': unrelated}, unknown_override]}]}}))
        self.configure()
        self.configure(remove=True)
        data = json.loads(config.read_text())
        self.assertEqual(data['custom'], 7)
        group = data['hooks']['PreToolUse'][0]
        self.assertEqual(group['metadata'], 'preserved')
        self.assertEqual(group['hooks'], [{'command': 'echo mine'}, {'command': unrelated}, unknown_override])
        self.assertEqual(canonical.read_text(), 'canonical')

    def test_invalid_config_is_preserved_and_active_removal_refuses(self):
        config = self.project/'.codex/hooks.json'; config.parent.mkdir()
        for hooks in (None, [], {'PreToolUse': None}, {'Stop': [{'hooks': [None]}]}):
            raw = json.dumps({'hooks': hooks}); config.write_text(raw)
            with self.assertRaises(SystemExit): self.configure()
            self.assertEqual(config.read_text(), raw)
        config.write_text('{}'); self.configure(); self.begin()
        before = config.read_bytes()
        with self.assertRaisesRegex(SystemExit, 'Unfinished runs'): self.configure(remove=True)
        self.assertEqual(config.read_bytes(), before)

    def test_user_update_retains_legacy_hook_bytes_and_clean_install_has_no_hooks(self):
        with patch.dict(os.environ, self.env):
            hosts.installer.install('codex', home=self.home, log=lambda _: None)
            config = self.home/'.codex/hooks.json'
            self.assertFalse(config.exists())
            gate = self.home/'.agents/skills/safe-engine/scripts'
            hosts.installer.merge_codex(config, gate)
            before = config.read_bytes()
            hosts.installer.install('codex', home=self.home, log=lambda _: None)
            self.assertEqual(config.read_bytes(), before)

    def test_cli_session_flag_is_only_on_joining_commands(self):
        for name in ('start', 'resume', 'join', 'status', 'done', 'pause', 'close'):
            result = subprocess.run([sys.executable, str(harness.GATE), name, '--help'], capture_output=True, env=self.env)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(b'--session' in result.stdout, name in ('start', 'resume', 'join'), name)

    @unittest.skipUnless(os.name == 'nt' and shutil.which('pwsh'), 'actual Windows PowerShell command')
    def test_native_idle_unrelated_and_closed_never_launch_dispatcher(self):
        runtime = self.root/'safe-engine/scripts'; runtime.mkdir(parents=True)
        (runtime/'fast_gate.py').write_text('def main(): print("DISPATCHED")\n')
        windows = hosts.installer.scoped_commands(runtime, self.project)[1]
        def call():
            return subprocess.run([shutil.which('pwsh'), '-NoLogo', '-NoProfile', '-Command', windows],
                                  input=b'{}', capture_output=True, env=self.env)
        # The fake interpreter records dispatch attempts, distinct from the real-runtime latency benchmark.
        fake = self.root/'bin'; fake.mkdir()
        (fake/'py.cmd').write_text('@echo DISPATCHED\n')
        (fake/'python.cmd').write_text('@echo DISPATCHED\n')
        self.env['PATH'] = str(fake)+';'+self.env['PATH']
        self.assertEqual(call().stdout, b'')
        other = self.root/'home/active/0123456789abcdef.json'; other.parent.mkdir(parents=True)
        other.write_text('{}'); self.assertEqual(call().stdout, b'')
        state = self.root/'home/runs'/f'{self.scope}.json'; state.parent.mkdir(parents=True)
        state.write_text('{}'); self.assertIn(b'DISPATCHED', call().stdout)
        state.unlink(); reg = other.with_name(f'{self.scope}.json'); reg.write_text('{}')
        self.assertIn(b'DISPATCHED', call().stdout)
        reg.unlink(); self.assertEqual(call().stdout, b'')


if __name__ == '__main__':
    unittest.main()
