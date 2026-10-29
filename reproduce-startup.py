import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
frozen = Path('<baseline-checkout>')
scripts = root / 'skills/safe-engine/scripts'
with tempfile.TemporaryDirectory(prefix='selection-manual-') as tmp:
    tmp = Path(tmp)
    project = tmp / 'project'
    project.mkdir()
    env = dict(os.environ, SAFE_ENGINE_HOME=str(tmp / 'home'))
    code = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv.pop(1))
import fast_gate,resolve_bundle
frozen=Path(sys.argv.pop(1)); calls=Path(sys.argv.pop(1))
def resolve(*args,**kwargs):
 calls.write_text('called')
 return resolve_bundle.inspect_bundle(frozen,entrypoint='safe-engine')
resolve_bundle.resolve_bundle=resolve
fast_gate.main()
'''
    result = subprocess.run([sys.executable, '-X', 'utf8', '-c', code, str(scripts), str(frozen), str(tmp/'calls'),
                             'start', '--project', str(project), '--key', 'manual', '--kind', 'change',
                             '--no-ui', '--no-data', '--request', 'Fix isolated fixture'], env=env,
                            text=True, encoding='utf-8', capture_output=True, timeout=60)
    (out / 'start.txt').write_text(result.stdout + result.stderr,encoding='utf-8')
    run = json.loads((project/'.factory/fast/run.json').read_text(encoding='utf-8')) if result.returncode == 0 else {}
    summary = {'exit':result.returncode,'receipt_created':(project/'.factory/entry-bundle.json').exists(),
               'selection_calls':int((tmp/'calls').exists()),'bundle_recorded':bool(run.get('bundle')),
               'check_selection':run.get('check_selection'),'suite_policy':run.get('suite_policy')}
    sys.path.insert(0,str(scripts))
    import resolve_bundle
    pinned = tmp/'pinned'; pinned.mkdir()
    resolve_bundle.select_for_project(pinned,frozen,None,tmp/'cache','safe-engine')
    calls=[]
    def remote(*args,**kwargs):
        calls.append(1)
        raise RuntimeError('remote discovery probe')
    resolve_bundle.resolve_bundle=remote
    selected=resolve_bundle.select_for_project(pinned,None,None,tmp/'cache','safe-engine',new_run=True)
    summary.update(explicit_remote_calls=len(calls),explicit_notice=selected.get('notice'))
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
