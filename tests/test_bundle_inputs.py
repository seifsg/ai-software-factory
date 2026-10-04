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
        for name in bundle_input_paths(self.source):
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
        for default in ('app-diagnostics', 'app-efficiency'):
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
        path = self.bundle / 'docs/current-decisions.md'
        path.write_text(path.read_text(encoding='utf-8') + '\nChanged approved guidance fixture.\n', encoding='utf-8')
        result = self.fixture.final()
        self.assertFalse(result['checks_reused'])
        self.assertTrue(result['checks_passed'])
        self.assertEqual(self.fixture.counts(), (2, 2))
        self.assertEqual(result['phase'], 'review')

    def test_cadence_readme_and_portable_inputs_change_fingerprint(self):
        self.fixture.full()
        before = self.fixture.flow.current(self.fixture.flow.load())
        for name in ('docs/safe-engine-fast-delivery.md', 'README.md',
                     '.agents/skills/safe-engine/references/clear-writing.md',
                     '.agents/skills/ux-quality/SKILL.md',
                     '.agents/skills/ux-quality/references/assets-and-sources.md',
                     '.agents/skills/database-schema/SKILL.md',
                     'skills/improve-factory/scripts/resolve_bundle.py'):
            with self.subTest(input=name):
                path = self.bundle / name
                original = path.read_bytes()
                path.write_bytes(original + b'\nChanged actual operative input fixture.\n')
                self.assertNotEqual(self.fixture.flow.current(self.fixture.flow.load()), before)
                path.write_bytes(original)
                self.assertEqual(self.fixture.flow.current(self.fixture.flow.load()), before)
        path = self.bundle / 'docs/safe-engine-fast-delivery.md'
        path.write_bytes(path.read_bytes() + b'\nChanged cadence fixture.\n')
        self.assertFalse(self.fixture.final()['checks_reused'])
        self.assertEqual(self.fixture.counts(), (2, 2))

    def test_missing_required_inputs_block_final_without_reusing_or_erasing(self):
        self.fixture.full()
        self.fixture.flow.record('improvement', self.fixture.draft('improvement'))
        before = self.fixture.flow.load()
        for name in ('docs/current-decisions.md', 'docs/safe-engine-decisions.md', 'safe_engine/bundle-inputs.json',
                     '.agents/skills/safe-engine/references/clear-writing.md',
                     '.agents/skills/ux-quality/SKILL.md',
                     '.agents/skills/ux-quality/references/assets-and-sources.md',
                     '.agents/skills/database-schema/SKILL.md',
                     'skills/safe-engine/references/local-trials.md',
                     'safe_engine/workflow.py', '.agents/skills/deep-review/references/theme-security.md',
                     '.agents/skills/how-to-review-a-pr/references/theme-change-guard.md',
                     '.agents/skills/how-to-review-a-pr/references/mobile-rules/dont-code.mdc'):
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
                 dict(valid, version=2)]
        for invalid in cases:
            with self.subTest(contract=invalid):
                path.write_text(json.dumps(invalid), encoding='utf-8')
                with self.assertRaises(EngineError):
                    bundle_input_paths(self.bundle)
        path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
