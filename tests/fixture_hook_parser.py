"""Bounded native-parser RPC fixture, not a TOML implementation or host acceptance test.

Accepts only the simple literals/tables emitted by the setup fixtures. Production
uses Codex's parser; actual installed-parser evidence is recorded separately.
"""
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch


def parse_fixture(raw):
    root, current = {}, None
    for line in raw.decode('utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            current = root
            for key in line[1:-1].split('.'):
                current = current.setdefault(key, {})
            continue
        key, value = (part.strip() for part in line.split('=', 1))
        target = current if current is not None else root
        if key in target:
            raise ValueError('duplicate fixture key')
        if value.startswith('{ SAFE_ENGINE_HOME = '):
            value = {'SAFE_ENGINE_HOME': json.loads(value[len('{ SAFE_ENGINE_HOME = '):-2])}
        else:
            value = json.loads(value)
        target[key] = value
    return root


@contextlib.contextmanager
def native_fixture(installer, cfg):
    """Exercise the real bounded RPC client without a machine-wide Codex prerequisite."""
    original_module, original_popen = installer.runtime_module, subprocess.Popen

    def spawn(command, **kwargs):
        if command[1:] != ['app-server', '--stdio']:
            return original_popen(command, **kwargs)
        return original_popen([sys.executable, str(Path(__file__).resolve()), '--rpc'], **kwargs)

    with patch.object(installer, 'runtime_module', side_effect=lambda name: cfg if name == 'fast_hook_config' else original_module(name)), \
            patch.object(cfg, 'executable', return_value=sys.executable), patch.object(cfg.subprocess, 'Popen', side_effect=spawn):
        yield


def rpc():
    root = Path.cwd().resolve()
    for key in ('USERPROFILE', 'HOME', 'CODEX_HOME', 'SAFE_ENGINE_HOME', 'GH_CONFIG_DIR'):
        path = Path(os.environ[key]).resolve()
        assert path.is_relative_to(root) and path.is_dir()
    raw = (Path(os.environ['CODEX_HOME']) / 'config.toml').read_bytes()
    assert len(raw) <= 1048576
    methods = []
    for line in sys.stdin.buffer:
        request = json.loads(line)
        method = request['method']; methods.append(method)
        assert method in ('initialize', 'initialized', 'config/read'), methods
        if 'id' not in request:
            continue
        response = {'id': request['id'], 'result': {}}
        if method == 'config/read':
            assert methods == ['initialize', 'initialized', 'config/read']
            try:
                if b'# fixture RPC error' in raw:
                    raise ValueError('private config never echoed')
                parsed = parse_fixture(raw)
                response['result'] = {'layers': [{'name': {'type': 'user', 'file': str(Path(os.environ['CODEX_HOME']) / 'config.toml')}, 'config': parsed}]}
                if b'# fixture unsupported response' in raw:
                    response['result'] = {'layers': None}
            except Exception:
                response = {'id': request['id'], 'error': {'code': -32603, 'message': 'private fixture parse error'}}
        print(json.dumps(response), flush=True)


if __name__ == '__main__':
    rpc()
