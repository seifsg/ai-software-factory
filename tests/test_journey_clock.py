"""Keep journey clock lint from accepting executable wall-time reads."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


LINT = Path(__file__).resolve().parents[1] / 'skills/safe-engine/scripts/journey_clock_lint.mjs'
FIXTURE = 'await fixedBrowserPage(browser, options);\n'


class JourneyClockTests(unittest.TestCase):
    def test_documented_helpers_need_executable_setup(self):
        """Accept either public setup while rejecting mentions and wall-time reads."""
        node = shutil.which('node')
        if not node:
            self.skipTest('Node is unavailable')
        cases = (
            ('await fixedBrowserPage(browser, options);', True),
            ('await fixedBrowserClock(page, instant);', True),
            ('// fixedBrowserClock(page, instant)', False),
            ('const label = "fixedBrowserClock(page, instant)";', False),
            ('const page = await browser.newPage();', False),
            ('await fixedBrowserClock(page, instant); const stamp = Date.now();', False),
            ('await fixedBrowserClock(page, instant); const stamp = new Date();', False),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'version': 1, 'journey_tests': ['journey.mjs']}), encoding='utf-8')
            for source, accepted in cases:
                with self.subTest(source=source):
                    (root / 'journey.mjs').write_text(source + '\n', encoding='utf-8')
                    result = subprocess.run([node, str(LINT), str(manifest)], capture_output=True,
                                            text=True, encoding='utf-8', timeout=10)
                    self.assertEqual(result.returncode, 0 if accepted else 1, result.stdout + result.stderr)

    def test_cli_classifies_executable_time_and_literals(self):
        """Run real manifest files through the CLI to protect lexical boundaries."""
        node = shutil.which('node')
        if not node:
            self.skipTest('Node is unavailable')
        cases = {
            'direct': ('const stamp = Date.now();', 'real-time Date.now()'),
            'empty_date': ('const stamp = new Date();', 'real-time new Date()'),
            'template': ('const stamp = `when ${Date.now()}`;', 'real-time Date.now()'),
            'export_regex': ("export default /'/; const stamp = Date.now(); // '", 'real-time Date.now()'),
            'export_regex_date': ("export default /'/; const stamp = new Date(); // '", 'real-time new Date()'),
            'regex_literal': ('export default /Date.now()/;', None),
            'fixed_date': ('const stamp = new Date("2025-04-05");', None),
            'fixed_components': ('const stamp = new Date(2025, 3, 5);', None),
            'ambiguous': ("if (ok) /'/.test(text);", 'needs manual review'),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, (body, finding) in cases.items():
                with self.subTest(name=name):
                    (root / 'journey.mjs').write_text(FIXTURE + body + '\n', encoding='utf-8')
                    (root / 'manifest.json').write_text(json.dumps({'version': 1, 'journey_tests': ['journey.mjs']}), encoding='utf-8')
                    result = subprocess.run([node, str(LINT), str(root / 'manifest.json')],
                                            capture_output=True, text=True, encoding='utf-8', timeout=10)
                    self.assertEqual(result.returncode, int(finding is not None), result.stdout + result.stderr)
                    self.assertIn(finding or 'Journey clock lint PASS', result.stderr if finding else result.stdout)


if __name__ == '__main__':
    unittest.main()
