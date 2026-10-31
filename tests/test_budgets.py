"""Byte budgets: method files and gate messages may not grow past tests/budgets.json.

Every run re-sends its method text and gate output each turn, so growth costs every run. Raise a budget only
on purpose, with the reason in the PR; `python scripts/token_report.py [--gate] --against <base>` shows the change.
"""
import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import gate_output  # noqa: E402
import token_report  # noqa: E402

BUDGETS = json.loads((ROOT / "tests/budgets.json").read_text(encoding="utf-8"))


class BudgetTests(unittest.TestCase):
    def test_archived_gate_fixture_retains_selected_methods_and_real_git_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source"
            scripts = gate_output.scripts(ROOT, "HEAD", source)
            self.assertEqual(scripts, source / gate_output.GATE)
            self.assertEqual(Path(subprocess.check_output(
                ["git", "-C", str(source), "rev-parse", "--show-toplevel"], text=True).strip()).resolve(), source.resolve())
            method = ".agents/skills/safe-engine/references/fast-run.md"
            self.assertEqual((source / method).read_bytes(), subprocess.check_output(
                ["git", "-C", str(ROOT), "show", f"HEAD:{method}"]))
            self.assertTrue((source / "safe_engine/bundle-inputs.json").is_file())

    def test_every_method_file_stays_within_its_byte_budget(self):
        files = token_report.expand(token_report.KINDS["all methods"], None)
        self.assertEqual(sorted(files), sorted(BUDGETS["methods"]))  # a new file needs a budget; a gone one, none
        for path, size in token_report.sizes(files, None).items():
            with self.subTest(file=path):
                self.assertLessEqual(size, BUDGETS["methods"][path])

    def test_product_and_change_loads_stay_within_their_caps(self):
        self.assertLessEqual(set(BUDGETS["loads"]), set(token_report.KINDS))  # a renamed kind never skips its cap
        for kind, _, total in token_report.report():  # caps: 80% of the f9990e1 load, the #137 target
            if kind in BUDGETS["loads"]:
                with self.subTest(kind=kind):
                    self.assertLessEqual(total, BUDGETS["loads"][kind])

    def test_conditional_text_proxy_is_honest(self):
        rows = {kind: {path for path, size in files if isinstance(size, int)}
                for kind, files, _ in token_report.report()}
        quality = ".agents/skills/safe-engine/references/quality-cases.md"
        media = ".agents/skills/how-to-make-a-pr/references/media-proof.md"
        self.assertNotIn(quality, rows["change"])
        self.assertIn(quality, rows["+quality case"])
        self.assertNotIn(media, rows["change"])
        self.assertIn(media, rows["+ui"])
        output = StringIO()
        with redirect_stdout(output):
            token_report.main(["--totals"])
        self.assertIn("not billed tokens", output.getvalue())
        self.assertIn("Phase/condition rows overlap", output.getvalue())

    def test_every_gate_message_stays_within_its_byte_budget(self):
        found = gate_output.measure(ROOT)
        self.assertEqual(sorted(found), sorted(BUDGETS["gate"]))
        for name, size in found.items():
            with self.subTest(message=name):
                self.assertLessEqual(size, BUDGETS["gate"][name])


if __name__ == "__main__":
    unittest.main()
