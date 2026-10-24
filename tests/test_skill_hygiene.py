"""Skill hygiene: each skill stands alone, stays owner- and date-neutral, and keeps its size limits."""
import hashlib
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents/skills"
LINK = re.compile(r"\]\(([^)#\s]+)")
MONTH = "January|February|March|April|May|June|July|August|September|October|November|December"
DATE = re.compile(rf"\b20\d\d-\d\d-\d\d\b|\b\d{{1,2}} (?:{MONTH})\b|\b(?:{MONTH}) \d{{1,2}}\b")
BANNED = {"498710fed19a", "6eece5dbd794", "758d3dd5df1e"}  # hashed person/source names, so this guard never spells them
CREDIT = SKILLS / "how-to-make-a-pr/references/credit.md"  # the factory's credit line names its maker (owner's call)
# Phrases whose presence turns a gate check on (fast_gate.FLAGS) or that PR-proof adoption requires
# (fast_pr_policy.source_digest). Losing one silently turns its check off for new runs.
PHRASES = {
    "ticketing/references/ticket-layout.md": ("Definition of done", "Every criterion has"),
    "safe-engine/references/fast-run.md": ("Light lane", "what the owner can do once it is done", "**Hidden checks:**",
                                           "**Secrets:**", "`**PR:**`"),
    "ux-quality/SKILL.md": ("| U10 |",),
    "how-to-make-a-pr/SKILL.md": ("references/credit.md", "**Visual:**", "**Journey:**"),
}


def prose():
    """Every authored Markdown file an agent or reader sees."""
    return [*SKILLS.rglob("*.md"), ROOT / "AGENTS.md", ROOT / "README.md",
            *(ROOT / "docs").glob("*.md"), *(ROOT / "skills").glob("*/SKILL.md")]


def banned_words(text):
    """Words whose hash is on the banned list."""
    return {word for word in re.findall(r"[a-z]+", text.lower())
            if hashlib.sha1(word.encode()).hexdigest()[:12] in BANNED}


class SkillHygieneTests(unittest.TestCase):
    def test_skills_link_only_inside_their_own_folder(self):
        for md in SKILLS.rglob("*.md"):
            home = (SKILLS / md.relative_to(SKILLS).parts[0]).resolve()
            for target in LINK.findall(md.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://")):
                    continue
                path = (md.parent / target).resolve()
                with self.subTest(file=md.relative_to(ROOT).as_posix(), link=target):
                    self.assertTrue(path.exists())
                    self.assertIn(home, path.parents)

    def test_frontmatter_and_sizes(self):
        for skill in (path for path in SKILLS.iterdir() if path.is_dir()):
            with self.subTest(skill=skill.name):
                text = (skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertRegex(text, rf"(?m)^name: {re.escape(skill.name)}\s*$")
                description = re.search(r"(?m)^description: (.+)$", text)
                self.assertTrue(description and len(description.group(1).strip().strip('"')) <= 1024)
                self.assertLess(text.count("\n"), 500)
                for ref in skill.glob("references/*.md"):
                    self.assertLess(ref.read_text(encoding="utf-8").count("\n"), 200, ref.name)

    def test_gate_trigger_phrases_stay_in_their_methods(self):
        spec = importlib.util.spec_from_file_location("hygiene_gate", ROOT / "skills/safe-engine/scripts/fast_gate.py")
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        pinned = {(f".agents/skills/{path}", phrase) for path, phrases in PHRASES.items() for phrase in phrases}
        self.assertLessEqual(set(gate.FLAGS.values()), pinned)  # a new or moved trigger gets pinned here too
        for path, phrase in sorted(pinned):
            with self.subTest(file=path, phrase=phrase):
                self.assertTrue(phrase in (ROOT / path).read_text(encoding="utf-8"), f"{phrase!r} left {path}")

    def test_no_names_dates_or_em_dashes(self):
        for path in prose():
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.relative_to(ROOT).as_posix()):
                self.assertEqual(banned_words(text) if path != CREDIT else set(), set())  # the one exemption
                self.assertIsNone(DATE.search(text))
                self.assertNotIn("—", text)


if __name__ == "__main__":
    unittest.main()
