import json
from pathlib import Path
import subprocess
import sys
from evals import isolation, runner
from safe_engine import distribution

base = Path(sys.argv[1] if len(sys.argv) > 1 else '.factory/eval-selection-proof/after').resolve()
base.mkdir(parents=True, exist_ok=True)
work = base / 'work'
work.mkdir(exist_ok=True)
runner.git_init(work)
bundle = isolation.read_bundle()
factory = isolation.export_factory(bundle, base / 'factory')
runner.git_init(factory, origin=distribution.REPOSITORY)
selected = distribution.select_for_project(work, factory, None, base / 'cache', 'safe-engine')
env = isolation.run_env(base)
code = "import sys;sys.path.insert(0,sys.argv.pop(1));import fast_gate,resolve_bundle\ndef offline(*a,**k): raise RuntimeError('isolated manual fixture: offline')\nresolve_bundle.resolve_bundle=offline\nfast_gate.main()"
command = [sys.executable, '-c', code, str(factory / 'skills/safe-engine/scripts'), 'start', '--project', str(work),
           '--key', 'eval-manual', '--kind', 'change', '--no-ui', '--no-data', '--request', 'Fix the synthetic invoice']
result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', env=env, timeout=60)
assert result.returncode == 0, result.stdout + result.stderr
observation = isolation.observed_run(env['SAFE_ENGINE_HOME'], work, selected)
assert observation['status'] == 'observed' and observation['policies']['check_selection'] and observation['policies']['suite_policy']
summary = {'factory_setup': {'snapshot_revision': selected['revision'], 'source': isolation.bundle_identity(bundle),
                            'selection_policy': selected['selection_policy']}, 'factory_run': observation}
(base / 'result.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
(base / 'start.txt').write_text(result.stdout, encoding='utf-8')
print(json.dumps(summary))
