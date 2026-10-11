"""Persistent policy effects and recoverable setup, with portable bounded native RPC fixtures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_fast_gate as harness
import test_fast_hosts as hosts
from fixture_hook_parser import native_fixture


class ProjectConfigTests(harness.GateHarness, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.cfg = hosts.module('fast_hook_config')
        self.home = Path(self.env['SAFE_ENGINE_HOME'])
        self.scope = hosts.installer.ledger().registry_path(Path('active'), self.project).stem
        self.folder = self.project / '.codex'; self.folder.mkdir()
        self.hooks = self.folder / 'hooks.json'; self.toml = self.folder / 'config.toml'
        self.original = (b'{"owner": 1, "hooks": {}}\r\n', b'# owner bytes\r\nfixture_owner="keep"\r\n')
        self.hooks.write_bytes(self.original[0]); self.toml.write_bytes(self.original[1])
        self.receipt = self.home / 'installations' / ('codex-' + self.scope + '.json')
        self.events = []

    def setup_hooks(self, remove=False):
        with patch.dict(os.environ, self.env), native_fixture(hosts.installer, self.cfg):
            return self.cfg.configure(self.project, hosts.SCRIPTS, self.home, self.scope, remove,
                                      hosts.installer.codex_data, hosts.installer.without_factory,
                                      lambda _: None, lambda event, **fields: self.events.append((event, fields)))

    def pair(self):
        return self.hooks.read_bytes(), self.toml.read_bytes()

    def test_setup_update_remove_preserves_outside_bytes_and_unknown_handlers(self):
        self.setup_hooks(); first = self.pair(); self.setup_hooks()
        self.assertEqual(self.pair(), first)
        data = json.loads(self.hooks.read_bytes()); data['owner_new'] = True
        data['hooks']['Stop'][0]['hooks'].append({'type': 'command', 'command': 'echo keep'})
        self.hooks.write_text(json.dumps(data))
        self.setup_hooks(remove=True)
        self.assertEqual(self.toml.read_bytes(), self.original[1])
        data = json.loads(self.hooks.read_bytes())
        self.assertTrue(data['owner_new']); self.assertEqual(data['owner'], 1)
        self.assertEqual(data['hooks']['Stop'][0]['hooks'], [{'type': 'command', 'command': 'echo keep'}])
        self.assertEqual(json.loads(self.receipt.read_bytes())['status'], 'removed')
        self.assertEqual(list((self.home / 'tmp').iterdir()), [])

    def test_status_reports_configuration_without_claiming_loaded_or_spawning_parser(self):
        self.setup_hooks()
        setup = hosts.module('fast_setup')
        with patch.object(Path, 'home', return_value=self.root / 'unused-home'), \
                patch.object(subprocess, 'Popen', side_effect=AssertionError('status must not launch native parser')):
            status = setup.hook_status(self.project)
        self.assertIn('Codex project: configured', status)
        self.assertIn('loading/trust/connection/runtime version unverified', status)

    def test_native_rpc_error_despite_zero_exit_preserves_pair_and_private_content(self):
        self.toml.write_bytes(b'# fixture RPC error\n')
        before = self.pair()
        with self.assertRaisesRegex(SystemExit, 'Native Codex could not parse') as raised:
            self.setup_hooks()
        self.assertNotIn('private fixture', str(raised.exception))
        self.assertEqual(self.pair(), before); self.assertFalse(self.receipt.exists())
        self.assertEqual(list((self.home / 'tmp').iterdir()), [])

    def test_unsupported_native_response_is_actionable_and_preserves_pair(self):
        self.toml.write_bytes(b'# fixture unsupported response\n')
        before = self.pair()
        with self.assertRaisesRegex(SystemExit, 'Native Codex could not parse'): self.setup_hooks()
        self.assertEqual(self.pair(), before); self.assertFalse(self.receipt.exists())

    def test_recovery_receipt_read_is_bounded_on_failure_path_too(self):
        self.receipt.parent.mkdir(parents=True)
        self.receipt.write_bytes(b'x' * 1025)
        with patch.object(self.cfg, 'LIMIT', 256):
            with self.assertRaisesRegex(SystemExit, 'reconcile the paired backups'): self.cfg.read_receipt(self.receipt)
        self.assertEqual(self.pair(), self.original)
        self.receipt.unlink()
        with self.assertRaisesRegex(SystemExit, 'receipt disappeared'): self.cfg.read_receipt(self.receipt, required=True)

    def test_invalid_mcp_container_is_actionable_and_preserved(self):
        self.toml.write_bytes(b'mcp_servers=[]\n')
        before = self.pair()
        with self.assertRaisesRegex(SystemExit, 'mcp_servers configuration is invalid'): self.setup_hooks()
        self.assertEqual(self.pair(), before); self.assertFalse(self.receipt.exists())

    def test_same_name_and_modified_owned_block_refuse_without_writes(self):
        self.toml.write_bytes(('[mcp_servers.safe_engine_' + self.scope + ']\ncommand="mine"\n').encode())
        before = self.pair()
        with self.assertRaisesRegex(SystemExit, 'without verified ownership'): self.setup_hooks()
        self.assertEqual(self.pair(), before)
        self.toml.write_bytes(self.original[1]); self.setup_hooks()
        self.toml.write_bytes(self.toml.read_bytes().replace(b'required = true', b'required = false'))
        before = self.pair()
        with self.assertRaisesRegex(SystemExit, 'Owned MCP configuration changed'): self.setup_hooks(remove=True)
        self.assertEqual(self.pair(), before)

    def test_second_write_failure_rolls_back_exact_originals(self):
        original_replace = self.cfg.replace
        failed = False
        def replace(path, value):
            nonlocal failed
            if Path(path) == self.toml and not failed:
                failed = True
                raise PermissionError('private fixture')
            return original_replace(path, value)
        with patch.object(self.cfg, 'replace', side_effect=replace):
            with self.assertRaisesRegex(SystemExit, 'did not finish'): self.setup_hooks()
        self.assertEqual(self.pair(), self.original)
        self.assertIn(('hooks.recovery', {'status': 'recovered'}), self.events)
        self.assertNotIn('private fixture', repr(self.events))

    def test_interruption_refuses_owner_edit_then_recovers_exact_factory_bytes(self):
        original_replace = self.cfg.replace
        def replace(path, value):
            if Path(path) == self.toml: raise KeyboardInterrupt()
            return original_replace(path, value)
        with patch.object(self.cfg, 'replace', side_effect=replace):
            with self.assertRaises(KeyboardInterrupt): self.setup_hooks()
        self.assertEqual(json.loads(self.receipt.read_bytes())['status'], 'prepared')
        factory_bytes = self.hooks.read_bytes()
        self.hooks.write_bytes(b'{"owner_after_interrupt":true}')
        before = self.pair()
        with self.assertRaisesRegex(SystemExit, 'changed afterward'): self.setup_hooks()
        self.assertEqual(self.pair(), before)
        self.hooks.write_bytes(factory_bytes); self.setup_hooks()
        self.assertEqual(json.loads(self.receipt.read_bytes())['status'], 'configured')

    def test_editor_change_after_parse_is_preserved_without_receipt(self):
        parse = self.cfg.parse_toml
        count = 0
        def concurrent(*args, **kwargs):
            nonlocal count
            result = parse(*args, **kwargs); count += 1
            if count == 2: self.hooks.write_bytes(b'{"owner_edit":true}')
            return result
        with patch.object(self.cfg, 'parse_toml', side_effect=concurrent):
            with self.assertRaisesRegex(SystemExit, 'changed during setup'): self.setup_hooks()
        self.assertEqual(self.hooks.read_bytes(), b'{"owner_edit":true}')
        self.assertEqual(self.toml.read_bytes(), self.original[1]); self.assertFalse(self.receipt.exists())

    def test_bounded_hook_capture_is_reused_when_owner_edits_after_read(self):
        original_validator = hosts.installer.codex_data
        original_read = Path.read_text
        def no_hook_reread(path, *args, **kwargs):
            if path == self.hooks: raise AssertionError('hook JSON path reread')
            return original_read(path, *args, **kwargs)
        def owner_edit(path, **kwargs):
            self.assertEqual(kwargs['raw'], self.original[0])
            self.hooks.write_bytes(b'{"owner_edit":true,"hooks":{}}')
            return original_validator(path, **kwargs)
        with patch.object(Path, 'read_text', no_hook_reread), \
                patch.object(hosts.installer, 'codex_data', side_effect=owner_edit):
            with self.assertRaisesRegex(SystemExit, 'changed during setup'): self.setup_hooks()
        self.assertEqual(self.hooks.read_bytes(), b'{"owner_edit":true,"hooks":{}}')
        self.assertEqual(self.toml.read_bytes(), self.original[1]); self.assertFalse(self.receipt.exists())
        self.hooks.write_bytes(b'\xef\xbb\xbf' + self.original[0])
        with patch.object(Path, 'read_text', no_hook_reread): self.setup_hooks()
        self.assertEqual(json.loads(self.hooks.read_bytes())['owner'], 1)

    def test_generated_and_receipt_limits_refuse_before_persistence(self):
        self.hooks.write_text(json.dumps({'hooks': {'Stop': [{'hooks': [{'command': 'echo keep'} for _ in range(30)]}]}}))
        before = self.pair()
        with patch.object(self.cfg, 'LIMIT', 2048):
            with self.assertRaisesRegex(SystemExit, 'Generated project configuration exceeds'): self.setup_hooks()
        self.assertEqual(self.pair(), before); self.assertFalse(self.receipt.exists())
        with patch.object(self.cfg, 'LIMIT', 256):
            with self.assertRaisesRegex(SystemExit, 'receipt exceeds'): self.cfg.save_receipt(self.receipt, {'large': 'x' * 1024})
        self.assertFalse(self.receipt.exists())

    def test_invalid_receipt_has_actionable_reconciliation(self):
        self.receipt.parent.mkdir(parents=True)
        for saved in ([], {'version': 2}, {'version': 2, 'status': 'prepared', 'journal': [None]}):
            self.receipt.write_text(json.dumps(saved))
            with self.assertRaisesRegex(SystemExit, 'reconcile the paired backups'): self.setup_hooks()
            self.assertEqual(self.pair(), self.original)


class PersistentHookTests(harness.GateHarness, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.scope = hosts.installer.ledger().registry_path(Path('active'), self.project).stem
        self.process = subprocess.Popen([sys.executable, str(hosts.SCRIPTS / 'fast_hook_server.py'), self.scope],
                                        env=self.env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.number = 0

    def tearDown(self):
        self.process.stdin.close()
        self.process.wait(timeout=10)
        error = self.process.stderr.read()
        self.process.stdout.close(); self.process.stderr.close()
        self.assertEqual(self.process.returncode, 0); self.assertEqual(error, b'')
        super().tearDown()

    def rpc(self, method, params=None):
        self.number += 1
        self.process.stdin.write((json.dumps({'jsonrpc': '2.0', 'id': self.number, 'method': method, 'params': params or {}}) + '\n').encode())
        self.process.stdin.flush()
        result = json.loads(self.process.stdout.readline())
        self.assertEqual(result['id'], self.number)
        return result

    def event(self, kind='PreToolUse', session='other', cwd=None):
        result = self.rpc('tools/call', {'name': 'factory_hook', 'arguments': {'event': {
            'hook_event_name': kind, 'session_id': session, 'cwd': str(cwd or self.project),
            'tool_name': 'apply_patch', 'tool_input': {'command': '*** Begin Patch\n*** Add File: src/a.ts\n+x\n*** End Patch'}}}})['result']
        self.assertNotIn('structuredContent', result); self.assertFalse(result['isError'])
        self.assertEqual(len(result['content']), 1); self.assertEqual(result['content'][0]['type'], 'text')
        return json.loads(result['content'][0]['text'])

    def test_supported_protocol_negotiates_same_version(self):
        answer = self.rpc('initialize', {'protocolVersion': '2025-06-18'})['result']
        self.assertEqual(answer['protocolVersion'], '2025-06-18')
        self.assertEqual(answer['capabilities'], {'tools': {}})
        self.assertEqual(self.event(), {})

    def test_unknown_protocol_negotiates_supported_fallback(self):
        answer = self.rpc('initialize', {'protocolVersion': '2099-01-01'})['result']
        self.assertEqual(answer['protocolVersion'], '2025-06-18')
        self.process.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        self.process.stdin.flush()
        self.assertEqual([tool['name'] for tool in self.rpc('tools/list')['result']['tools']], ['factory_hook'])
        self.assertEqual(self.event(), {})

    def test_malformed_protocol_returns_actionable_error_and_can_retry(self):
        for version in (None, True, 'x' * 33):
            error = self.rpc('initialize', {'protocolVersion': version})['error']
            self.assertEqual(error['code'], -32602)
            self.assertIn('reconnect after repair', error['message'])
        self.assertEqual(self.rpc('initialize', {'protocolVersion': '2025-06-18'})['result']['protocolVersion'], '2025-06-18')
        self.assertEqual(self.rpc('ping')['result'], {})

    def test_same_connection_fresh_policy_participation_recovery_and_close(self):
        self.rpc('initialize', {'protocolVersion': '2024-11-05'})
        tools = self.rpc('tools/list')['result']['tools']
        self.assertEqual([tool['name'] for tool in tools], ['factory_hook'])
        self.assertEqual(tools[0]['_meta']['ui']['visibility'], [])
        self.assertEqual(self.event(), {})
        self.start('--session', 'joined', kind='change')
        self.assertEqual(self.event()['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.event('Stop'), {})
        self.assertEqual(self.event('Stop', 'joined')['decision'], 'block')
        other = self.root / 'other'; other.mkdir()
        self.assertEqual(self.event('Stop', 'joined', other), {})
        home = Path(self.env['SAFE_ENGINE_HOME'])
        (home / 'active' / (self.scope + '.json')).unlink()
        self.assertEqual(self.event()['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertTrue((home / 'active' / (self.scope + '.json')).exists())
        self.gate('close', '--abandon', 'fixture completion')
        self.assertEqual(self.event(), {})

    def test_invalid_and_oversized_requests_recover_on_same_connection(self):
        self.assertIn('error', self.rpc('tools/call', {'name': 'factory_hook', 'arguments': {'event': [], 'private': 'secret'}}))
        self.process.stdin.write(b'x' * 262145 + b'\n'); self.process.stdin.flush()
        error = json.loads(self.process.stdout.readline())
        self.assertIn('error', error); self.assertNotIn('secret', json.dumps(error))
        self.assertEqual(self.rpc('ping')['result'], {})
        self.assertEqual(self.event(), {})


if __name__ == '__main__':
    unittest.main()
