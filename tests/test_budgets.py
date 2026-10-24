"""Byte budgets: method files and gate messages may not grow past tests/budgets.json.

Every run re-sends its method text and gate output each turn, so growth costs every run. Raise a budget only
on purpose, with the reason in the PR; `python scripts/token_report.py [--gate] --against <base>` shows the change.
"""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import gate_output  # noqa: E402
import token_report  # noqa: E402

BUDGETS = json.loads((ROOT / "tests/budgets.json").read_text(encoding="utf-8"))


class BudgetTests(unittest.TestCase):
    def test_every_method_file_stays_within_its_byte_budget(self):
        files = token_report.expand(token_report.KINDS["all methods"], None)
        self.assertEqual(sorted(files), sorted(BUDGETS["methods"]))  # a new file needs a budget; a gone one, none
        for path, size in token_report.sizes(files, None).items():
            with self.subTest(file=path):
                self.assertLessEqual(size, BUDGETS["methods"][path])

    def test_every_gate_message_stays_within_its_byte_budget(self):
        found = gate_output.measure(ROOT)
        self.assertEqual(sorted(found), sorted(BUDGETS["gate"]))
        for name, size in found.items():
            with self.subTest(message=name):
                self.assertLessEqual(size, BUDGETS["gate"][name])


if __name__ == "__main__":
    unittest.main()
