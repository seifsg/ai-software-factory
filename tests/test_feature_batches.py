"""Actual subprocess feedback/version boundaries; provider reviews remain test doubles elsewhere."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from safe_engine.project import EngineError, bundle_input_paths, validate_profile
from safe_engine.storage import atomic_json
from safe_engine.workflow import Workflow


class FeatureBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.git('init', '-q')
        (self.root / '.gitignore').write_text('.factory/\n__pycache__/\n')
        (self.root / 'app.py').write_text('value = 1\n')
        (self.root / 'accept.py').write_text(
            "import sys\nfrom pathlib import Path\nfrom app import value\n"
            "name=sys.argv[1]\np=Path('.factory/count-'+name)\n"
            "p.write_text(str(int(p.read_text())+1 if p.exists() else 1))\n"
            "assert value == 1 and not Path('.factory/fail-'+name).exists()\n"
            "out=Path('.factory/outputs/'+name+'.txt')\n"
            "out.parent.mkdir(parents=True, exist_ok=True)\nout.write_text('fresh '+name)\n"
            "print('Actual configured feature check', name)\n")
        self.git('add', '.gitignore', 'app.py', 'accept.py')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'baseline')
        self.profile = {'version': 1, 'interface': 'library', 'reuse_unchanged_checks': True,
            'checks': [{'id': name, 'kind': 'unit', 'argv': ['{python}', 'accept.py', name],
                        'timeout_seconds': 10, 'artifacts': ['.factory/outputs/'+name+'.txt']} for name in ('a','b')],
            'protected_paths': ['accept.py'], 'input_files': [], 'environment_inputs': []}
        self.task = {'request': 'Build two coherent capabilities then verify the complete version',
            'acceptance': [{'id': 'A1', 'text': 'Both complete version checks pass', 'checks': ['a','b']}]}
        self.flow = Workflow(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def draft(self, kind):
        p=self.root/'.factory'/('draft-'+kind+'.md')
        p.parent.mkdir(exist_ok=True)
        p.write_text('# '+kind+'\nExplicit behavioral fixture; no real method or independent approval claimed.\n')
        return p

    def build(self):
        self.flow.initialize(self.task, self.profile)
        for kind in ('analysis','plan'):
            self.flow.record(kind, self.draft(kind))

    def full(self):
        self.build()
        self.flow.record('batch', self.draft('batch'))
        return self.flow.check()

    def final(self):
        self.flow.record('improvement', self.draft('improvement'))
        return self.flow.check()

    def counts(self):
        return tuple(int((self.root/'.factory'/('count-'+name)).read_text())
                     if (self.root/'.factory'/('count-'+name)).exists() else 0 for name in ('a','b'))

    def test_multiple_capabilities_are_feedback_then_full_version(self):
        self.build()
        for name, expected in [('a',(1,0)),('b',(1,1))]:
            (self.root/'app.py').write_text('value = 1\n# capability '+name+'\n')
            result=self.flow.feature_check([name],self.draft(name))
            self.assertTrue(result['feature_checks_passed'])
            self.assertEqual(result['phase'],'build')
            self.assertFalse(result['checks_passed'])
            self.assertEqual(self.counts(),expected)
            self.assertEqual(result['missing_required_checks'], ['b' if name=='a' else 'a'])
            with self.assertRaises(EngineError): self.flow.require_checks(self.flow.load())
            with self.assertRaises(EngineError): self.flow.review(10)
            with self.assertRaises(EngineError): self.flow.handoff()
        self.flow.record('batch',self.draft('batch'))
        self.assertTrue(self.flow.check()['checks_passed'])
        self.assertEqual(self.counts(),(2,2))
        self.assertTrue(self.final()['checks_reused'])
        self.assertEqual(self.counts(),(2,2))
        self.assertEqual(self.flow.status()['phase'],'review')
        self.assertEqual(len([k for k in self.flow.load()['artifacts'] if k.startswith('feature-results')]),2)

    def test_even_all_selected_feature_checks_never_accept_version(self):
        self.build()
        result=self.flow.feature_check(['a','b'],self.draft('both'))
        self.assertEqual(result['missing_required_checks'],[])
        self.assertFalse(result['checks_passed'])
        self.assertIsNone(self.flow.load()['checks'])
        with self.assertRaises(EngineError): self.flow.check()

    def test_legacy_profile_keeps_fresh_final_execution(self):
        self.profile.pop('reuse_unchanged_checks')
        self.full()
        self.assertFalse(self.final()['checks_reused'])
        self.assertEqual(self.counts(),(2,2))
        self.assertEqual(self.flow.load()['schema_version'],1)
        self.assertNotIn('feature_checks',self.flow.load())

    def test_fresh_override_executes_every_command(self):
        self.full();self.flow.record('improvement',self.draft('improvement'))
        self.assertFalse(self.flow.check(fresh=True)['checks_reused'])
        self.assertEqual(self.counts(),(2,2))

    def test_changed_improvement_source_executes_full_suite(self):
        self.full();(self.root/'app.py').write_text('value = 1\n# worthwhile improvement\n')
        self.assertFalse(self.final()['checks_reused'])
        self.assertEqual(self.counts(),(2,2))

    def test_changed_declared_environment_executes_full_suite(self):
        self.profile['environment_inputs']=['SAFE_ENGINE_FEATURE_FIXTURE']
        with patch.dict(os.environ,{'SAFE_ENGINE_FEATURE_FIXTURE':'one'}):
            self.full()
            with patch.dict(os.environ,{'SAFE_ENGINE_FEATURE_FIXTURE':'two'}):
                self.assertFalse(self.final()['checks_reused'])
        self.assertEqual(self.counts(),(2,2))

    def test_changed_declared_file_executes_full_suite(self):
        f=self.root/'.factory/runtime-input';f.parent.mkdir();f.write_text('one')
        self.profile['input_files']=['.factory/runtime-input'];self.full();f.write_text('two')
        self.assertFalse(self.final()['checks_reused'])
        self.assertEqual(self.counts(),(2,2))

    def test_changed_bundle_inputs_execute_full_suite(self):
        copied=self.root/'.factory/bundle';copied.mkdir(parents=True)
        source=Path(__file__).resolve().parents[1]
        contract = json.loads((source / 'safe_engine/bundle-inputs.json').read_text(encoding='utf-8'))
        for name in set(bundle_input_paths(source)) | set(contract.get('historical_files', [])):
            target=copied/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,target)
        with patch('safe_engine.project.__file__',str(copied/'safe_engine/project.py')):
            self.full();f=copied/'safe_engine/__init__.py';f.write_text(f.read_text()+'\n# actual changed bundle fixture\n')
            self.assertFalse(self.final()['checks_reused'])
        self.assertEqual(self.counts(),(2,2))

    def test_changes_after_recorded_final_anchor_require_repair(self):
        self.full();self.flow.record('improvement',self.draft('improvement'))
        (self.root/'app.py').write_text('value = 1\n# late mutation\n')
        with self.assertRaisesRegex(EngineError,'repair'):self.flow.check()
        self.assertEqual(self.counts(),(1,1))

    def test_log_tamper_refuses_reuse_preserving_evidence(self):
        self.full();self.flow.record('improvement',self.draft('improvement'))
        before=self.flow.load();Path(before['checks']['results'][0]['log']).write_text('tampered')
        with self.assertRaisesRegex(EngineError,'evidence'):self.flow.check()
        self.assertEqual(self.flow.load(),before)
        self.assertEqual(self.counts(),(1,1))

    def test_output_tamper_or_deletion_refuses_reuse(self):
        self.full();self.flow.record('improvement',self.draft('improvement'))
        out=self.root/'.factory/outputs/a.txt';out.write_text('tampered')
        with self.assertRaisesRegex(EngineError,'output evidence'):self.flow.check()
        out.unlink()
        with self.assertRaisesRegex(EngineError,'not a file'):self.flow.check()
        self.assertEqual(self.counts(),(1,1))

    def test_missing_duplicate_or_altered_command_results_refuse_acceptance(self):
        self.full();self.flow.record('improvement',self.draft('improvement'))
        for mutation in ('missing','duplicate','command'):
            state=self.flow.load()
            if mutation=='missing':state['checks']['results'].pop()
            elif mutation=='duplicate':state['checks']['results'].append(state['checks']['results'][0])
            else:state['checks']['results'][0]['argv']=['fake']
            with self.assertRaises(EngineError):self.flow.require_checks(state)

    def test_profile_or_task_edits_cannot_enable_reuse_after_init(self):
        self.full();before=self.flow.load()
        for field in ('task','profile'):
            state=json.loads(json.dumps(before))
            if field=='task':state[field]['request']='Different requirement'
            else:state[field]['reuse_unchanged_checks']=False
            atomic_json(self.root/'.factory/state.json',state)
            with self.assertRaisesRegex(EngineError,'Task or profile changed'):self.flow.load()
        atomic_json(self.root/'.factory/state.json',before)

    def test_invalid_subset_and_phase_rejected_without_commands(self):
        self.build()
        for ids in ([],['missing'],['a','a']):
            with self.assertRaisesRegex(EngineError,'unique configured'):self.flow.feature_check(ids,self.draft('feature'))
        self.assertEqual(self.counts(),(0,0))
        self.flow.record('batch',self.draft('batch'))
        with self.assertRaises(EngineError):self.flow.feature_check(['a'],self.draft('feature'))

    def test_failed_feature_requires_diagnosed_repair(self):
        self.build();failure=self.root/'.factory/fail-a';failure.write_text('failed dependency')
        self.assertFalse(self.flow.feature_check(['a'],self.draft('feature'))['feature_checks_passed'])
        failed=self.flow.load();failure.unlink()
        with self.assertRaisesRegex(EngineError,'repair'):self.flow.feature_check(['a'],self.draft('corrected'))
        with self.assertRaisesRegex(EngineError,'repair'):self.flow.record('batch',self.draft('batch'))
        self.assertEqual(self.flow.load(),failed)
        self.assertEqual(self.flow.repair('Dependency recovered; preserve failed feature record')['repairs_used'],1)
        self.assertTrue(self.flow.feature_check(['a'],self.draft('corrected'))['feature_checks_passed'])
        self.flow.record('batch',self.draft('batch'));self.assertTrue(self.flow.check()['checks_passed'])
        self.assertEqual(self.counts(),(3,1))

    def test_failed_full_check_cannot_be_reused_or_rerolled(self):
        self.build();(self.root/'.factory/fail-b').write_text('failed')
        self.flow.record('batch',self.draft('batch'));self.assertFalse(self.flow.check()['checks_passed'])
        with self.assertRaisesRegex(EngineError,'repair'):self.flow.check()
        with self.assertRaises(EngineError):self.flow.record('improvement',self.draft('improvement'))

    def test_feature_records_and_protected_checks_remain_intact(self):
        self.build();self.flow.feature_check(['a'],self.draft('feature'))
        artifact=next(v for k,v in self.flow.load()['artifacts'].items() if k.startswith('feature-results'))
        (self.root/'.factory'/artifact['path']).write_text('{}')
        with self.assertRaisesRegex(EngineError,'artifact changed'):self.flow.feature_check(['b'],self.draft('second'))
        (self.root/'accept.py').write_text("print('fake')")
        with self.assertRaisesRegex(EngineError,'Protected acceptance'):self.flow.feature_check(['b'],self.draft('second'))

    def test_interrupted_feature_is_not_acceptance_and_rerun_preserves_record(self):
        self.build()
        with patch('safe_engine.workflow.run_command',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.flow.feature_check(['a'],self.draft('feature'))
        self.assertEqual(self.flow.status()['pending_operation'],'feature-checks')
        self.assertFalse(self.flow.status()['checks_passed'])
        with self.assertRaisesRegex(EngineError,'incomplete'):self.flow.record('batch',self.draft('batch'))
        self.assertTrue(self.flow.feature_check(['a'],self.draft('rerun'))['feature_checks_passed'])
        self.assertIsNone(self.flow.status()['pending_operation'])

    def test_cancelled_run_cannot_execute_partial_or_full_checks(self):
        self.build();self.flow.feature_check(['a'],self.draft('feature'));self.flow.cancel('Owner stop')
        for action in (lambda:self.flow.feature_check(['b'],self.draft('second')),self.flow.check,
                       lambda:self.flow.repair('Must not revive'),lambda:self.flow.record('batch',self.draft('batch'))):
            with self.assertRaises(EngineError):action()
        self.assertEqual(self.counts(),(1,0))

    def test_reuse_flag_requires_boolean(self):
        for invalid in ('true',1,None):
            self.profile['reuse_unchanged_checks']=invalid
            with self.assertRaisesRegex(EngineError,'boolean'):validate_profile(self.profile)

    def test_cli_feature_feedback_exit_codes_and_no_version_acceptance(self):
        self.build()
        def cli(*args):return subprocess.run([sys.executable,'-m','safe_engine','--project',str(self.root),*args],
            cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True)
        artifact=str(self.draft('feature'))
        good=cli('feature-check','--checks','a','--file',artifact)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertFalse(json.loads(good.stdout)['checks_passed'])
        (self.root/'.factory/fail-b').write_text('failed')
        failed=cli('feature-check','--checks','b','--file',artifact)
        self.assertEqual(failed.returncode,1,failed.stderr)
        invalid=cli('feature-check','--checks','a','--file',artifact)
        self.assertEqual(invalid.returncode,2)


if __name__ == '__main__':
    unittest.main()
