"""Docs stay in sync with the code: every owner command, install flag, release step, doc page, skill, host and
top-level folder is documented, so a change that adds one fails here until README.md and docs/ say how to use it."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "skills/safe-engine/scripts/fast_gate.py"
README = (ROOT / "README.md").read_text(encoding="utf-8")
DOCS = {path.name: path.read_text(encoding="utf-8") for path in (ROOT / "docs").glob("*.md")}
OWNER = README + "".join(DOCS.values())
METHODS = OWNER + "".join(p.read_text(encoding="utf-8") for p in (ROOT / ".agents/skills").rglob("*.md"))
INTERNAL = {"hook"}  # host hooks call it; docs/hosts.md wires it as run-gate


def helptext(script, *args):
    """`script [args] -h` output, run in a throwaway gate home."""
    env = {**os.environ, "SAFE_ENGINE_HOME": tempfile.mkdtemp(), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, str(script), *args, "-h"], capture_output=True, text=True, env=env,
                          check=True, encoding="utf-8").stdout


def choices(text):
    """The first `{a,b,c}` choice list in a help text."""
    return set(re.search(r"\{([^}]+)\}", text).group(1).split(","))


def flags(text):
    return set(re.findall(r"(?<![\w-])--[a-z][a-z-]+", text)) - {"--help"}


class DocsSyncTests(unittest.TestCase):
    def has(self, needle, text, where):
        self.assertTrue(needle in text, f"{needle!r} is not documented in {where}")

    def test_every_gate_command_is_documented(self):
        lines = [line for line in METHODS.splitlines() if "fast_gate.py" in line]  # 'fast_gate.py status | pause' counts
        for command in choices(helptext(GATE)) - INTERNAL:
            with self.subTest(command=command):
                found = any(re.search(rf"fast_gate\.py\b.*(?<![\w-]){re.escape(command)}(?![\w-])", line) for line in lines)
                self.assertTrue(found, f"fast_gate.py {command} is not documented in README, docs or methods")

    def test_owner_commands_and_every_install_flag_are_in_the_owner_docs(self):
        for command in ("install", "version", "verify", "view", "orchestrate", "rehome"):
            with self.subTest(command=command):
                self.has(f"fast_gate.py {command}", OWNER, "README or docs")
        for flag in flags(helptext(GATE, "install")):
            with self.subTest(flag=flag):
                self.has(flag, DOCS["install.md"], "docs/install.md")
        self.assertLessEqual(flags(helptext(GATE, "view")), flags(METHODS))

    def test_every_install_host_is_in_the_readme(self):
        host = re.search(r"--host \{([^}]+)\}", helptext(GATE, "install")).group(1).split(",")
        for name in host:
            with self.subTest(host=name):
                self.has(f"`{name}`", README, "README.md")

    def test_every_release_step_is_in_releasing(self):
        for command in choices(helptext(ROOT / "scripts/release.py")):
            with self.subTest(command=command):
                self.has(f"release.py {command}", DOCS["releasing.md"], "docs/releasing.md")

    def test_every_doc_page_skill_and_top_level_folder_is_in_the_readme(self):
        for name in DOCS:
            with self.subTest(doc=name):
                self.has(f"docs/{name}", README, "README.md")
        for skill in (ROOT / ".agents/skills").iterdir():
            with self.subTest(skill=skill.name):
                self.has(f"| `{skill.name}` |", README, "README.md")
        tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True).stdout
        layout = README.split("## 🗂️ Layout", 1)[1]
        for folder in {line.split("/", 1)[0] for line in tracked.splitlines() if "/" in line}:
            with self.subTest(folder=folder):
                self.has(f"{folder}/", layout, "the README layout")
        self.has("skills/agents/", layout, "the README layout")  # the delegate roles' agent files


if __name__ == "__main__":
    unittest.main()
