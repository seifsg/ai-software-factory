"""A named host in a ticket is not a link until the name itself is tested."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/safe-engine/SKILL.md"
FAST = ROOT / ".agents/skills/safe-engine/references/fast-run.md"


class NamedHostTests(unittest.TestCase):
    def test_skill_forbids_treating_a_written_address_as_a_link(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("is not a link", text)
        self.assertIn("Do not call a check you can run unverified", text)
        self.assertIn("documented IP", text)

    def test_deferred_rule_requires_the_name_itself(self):
        text = FAST.read_text(encoding="utf-8")
        self.assertIn("is not a link", text)
        self.assertIn("not the link", text)
        self.assertIn("write the test result on the ticket", text)


if __name__ == "__main__":
    unittest.main()
