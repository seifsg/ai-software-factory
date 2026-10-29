"""Real copied procedural inputs and command counters; no live app acceptance."""
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_feature_batches as feature
from safe_engine.project import EngineError, bundle_input_paths, fingerprint


class BundleInputTests(unittest.TestCase):
    def setUp(self):
        self.fixture = feature.FeatureBatchTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.bundle = self.fixture.root / '.factory/bundle'
        self.source = Path(__file__).resolve().parents[1]
        contract = json.loads((self.source / 'safe_engine/bundle-inputs.json').read_text(encoding='utf-8'))
        for name in set(bundle_input_paths(self.source)) | set(contract.get('historical_files', [])):
            target = self.bundle / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.source / name, target)
        self.binding = patch('safe_engine.project.__file__', str(self.bundle / 'safe_engine/project.py'))
        self.binding.start()
        self.addCleanup(self.binding.stop)

    def test_app_defaults_change_inputs_and_cannot_be_omitted(self):
        def current():
            return fingerprint(self.fixture.root, self.fixture.profile, self.fixture.task,
                               self.fixture.flow.directory)
        for default in ('product-bar', 'fast-run'):
            with self.subTest(default=default):
                name = f'.agents/skills/safe-engine/references/{default}.md'
                self.assertIn(name, bundle_input_paths(self.bundle))
                before = current()
                path = self.bundle / name
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b'\nChanged app guidance fixture.\n')
                    self.assertNotEqual(current(), before)
                    path.unlink()
                    with self.assertRaisesRegex(EngineError, f'Required factory input.*{default}'):
                        bundle_input_paths(self.bundle)
                finally:
                    path.write_bytes(original)

    def test_mandatory_decision_change_runs_every_real_command(self):
        self.fixture.full()
        path = self.bundle / 'AGENTS.md'
        path.write_text(path.read_text(encoding='utf-8') + '\nChanged approved guidance fixture.\n', encoding='utf-8')
        result = self.fixture.final()
        self.assertFalse(result['checks_reused'])
        self.assertTrue(result['checks_passed'])
        self.assertEqual(self.fixture.counts(), (2, 2))
        self.assertEqual(result['phase'], 'review')

    def test_cadence_readme_and_portable_inputs_change_fingerprint(self):
        self.fixture.full()
        before = self.fixture.flow.current(self.fixture.flow.load())
        for name in ('.agents/skills/safe-engine/references/fast-run.md', 'README.md', 'docs/install.md',
                     '.agents/skills/safe-engine/references/controller.md',
                     '.agents/skills/safe-engine/references/app-releases.md',
                     '.agents/skills/safe-engine/references/github.md', 'docs/app-releases.md',
                     '.agents/skills/deep-review/references/security.md',
                     '.agents/skills/ux-quality/SKILL.md',
                     '.agents/skills/ux-quality/references/assets.md',
                     '.agents/skills/ux-quality/references/web-seo.md',
                     '.agents/skills/database-schema/SKILL.md',
                     'skills/improve-factory/scripts/resolve_bundle.py'):
            with self.subTest(input=name):
                path = self.bundle / name
                original = path.read_bytes()
                path.write_bytes(original + b'\nChanged actual operative input fixture.\n')
                self.assertNotEqual(self.fixture.flow.current(self.fixture.flow.load()), before)
                path.write_bytes(original)
                self.assertEqual(self.fixture.flow.current(self.fixture.flow.load()), before)
        path = self.bundle / '.agents/skills/safe-engine/references/fast-run.md'
        path.write_bytes(path.read_bytes() + b'\nChanged cadence fixture.\n')
        self.assertFalse(self.fixture.final()['checks_reused'])
        self.assertEqual(self.fixture.counts(), (2, 2))

    def test_missing_required_inputs_block_final_without_reusing_or_erasing(self):
        self.fixture.full()
        self.fixture.flow.record('improvement', self.fixture.draft('improvement'))
        before = self.fixture.flow.load()
        for name in ('AGENTS.md', 'docs/install.md', 'docs/hosts.md', 'safe_engine/bundle-inputs.json',
                     '.agents/skills/safe-engine/references/fast-run.md',
                     '.agents/skills/safe-engine/references/product-bar.md',
                     '.agents/skills/safe-engine/references/controller.md',
                     '.agents/skills/safe-engine/references/app-releases.md',
                     '.agents/skills/safe-engine/references/github.md', 'docs/app-releases.md',
                     '.agents/skills/safe-engine/references/work-record-sample.md',
                     '.agents/skills/ux-quality/SKILL.md',
                     '.agents/skills/database-schema/SKILL.md',
                     'skills/safe-engine/SKILL.md', 'skills/.claude-plugin/plugin.json',
                     'safe_engine/workflow.py', 'skills/safe-engine/scripts/fast_gate.py'):
            with self.subTest(input=name):
                path = self.bundle / name
                original = path.read_bytes()
                path.unlink()
                try:
                    with self.assertRaisesRegex(EngineError, 'Required factory input'):
                        self.fixture.flow.check()
                    self.assertEqual(self.fixture.flow.load(), before)
                    self.assertEqual(self.fixture.counts(), (1, 1))
                finally:
                    path.write_bytes(original)

    def test_added_guidance_invalidates_and_nonoperative_preview_is_scoped_out(self):
        self.fixture.full()
        before = self.fixture.flow.current(self.fixture.flow.load())
        preview = self.bundle / 'preview/index.html'
        preview.parent.mkdir()
        preview.write_text('<p>Unrelated walkthrough resource</p>', encoding='utf-8')
        self.assertEqual(self.fixture.flow.current(self.fixture.flow.load()), before)
        addition = self.bundle / 'docs/new-operative-guidance.md'
        addition.write_text('Additional reviewed guidance fixture.\n', encoding='utf-8')
        self.assertNotEqual(self.fixture.flow.current(self.fixture.flow.load()), before)
        self.assertFalse(self.fixture.final()['checks_reused'])
        self.assertEqual(self.fixture.counts(), (2, 2))

    def test_invalid_contracts_and_missing_source_area_are_rejected(self):
        path = self.bundle / 'safe_engine/bundle-inputs.json'
        original = path.read_bytes()
        valid = json.loads(original)
        cases = [dict(valid, required_files=['../outside']), dict(valid, required_files=['/absolute']),
                 dict(valid, required_files=['README.md', 'readme.md']),
                 dict(valid, required_files=[42]), dict(valid, source_trees=['missing-area']),
                 dict(valid, version=99)]
        for invalid in cases:
            with self.subTest(contract=invalid):
                path.write_text(json.dumps(invalid), encoding='utf-8')
                with self.assertRaises(EngineError):
                    bundle_input_paths(self.bundle)
        path.write_bytes(original)

    def test_history_changes_do_not_invalidate_but_remain_required(self):
        contract = self.bundle / 'safe_engine/bundle-inputs.json'
        value = json.loads(contract.read_text(encoding='utf-8'))
        contract.write_text(json.dumps(dict(value, historical_files=['docs/history.md'])), encoding='utf-8')
        path = self.bundle / 'docs/history.md'
        path.write_text('Historical evidence fixture.\n', encoding='utf-8')
        self.assertNotIn('docs/history.md', bundle_input_paths(self.bundle))
        self.fixture.build()
        before = self.fixture.flow.current(self.fixture.flow.load())
        path.write_text('Historical evidence appendix.\n', encoding='utf-8')
        self.assertEqual(self.fixture.flow.current(self.fixture.flow.load()), before)
        path.unlink()
        with self.assertRaisesRegex(EngineError, 'Missing historical document'):
            bundle_input_paths(self.bundle)


if __name__ == '__main__':
    unittest.main()
