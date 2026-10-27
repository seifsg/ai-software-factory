"""Exercise browser helper observations in a real browser when the host has Playwright."""
import os
from pathlib import Path
import shutil
import subprocess
import unittest


class BrowserHelperTests(unittest.TestCase):
    def test_rendered_browser_traps(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node is unavailable')
        available = subprocess.run([node, '-e', "require.resolve('@playwright/test')"],
                                   capture_output=True, env=os.environ, timeout=10)
        if available.returncode:
            self.skipTest('Playwright is unavailable')
        script = Path(__file__).with_name('playwright_checks_fixture.mjs')
        result = subprocess.run([node, str(script)], capture_output=True, text=True,
                                encoding='utf-8', errors='replace', env=os.environ, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('duplicate PASS', result.stdout)
