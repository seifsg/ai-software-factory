"""Delegate roles: each Claude Code agent file matches its role in the delegate method and ships in every bundle."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "skills/agents"
METHOD = ROOT / ".agents/skills/safe-engine/references/delegate.md"
HOSTS = ROOT / "docs/hosts.md"
MODELS = {"haiku", "sonnet", "opus", "fable", "inherit"}  # aliases; a full ID starts with claude-
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
WRITES = {"Write", "Edit", "NotebookEdit"}
READERS = {"Read", "Grep", "Glob", "Bash", "PowerShell", "WebFetch", "WebSearch", "ToolSearch"}  # no spawn, write or MCP tool


def frontmatter(path):
    """(fields, body) of an agent file: one `key: value` per line, quotes stripped."""
    head, body = path.read_text(encoding="utf-8").split("---\n", 2)[1:]
    fields = dict(line.split(": ", 1) for line in head.strip().splitlines())
    return {key: value.strip().strip('"') for key, value in fields.items()}, body


def roles():
    """Role -> (tier, edits, handback shape), from the method's Roles table."""
    rows = re.findall(r"^\| (\w+) \| (light|standard|deep) \| (yes|no) \| [^|]+ \| ([^|]+) \|$",
                      METHOD.read_text(encoding="utf-8"), re.M)
    return {role: (tier, edits == "yes", shape.strip()) for role, tier, edits, shape in rows}


def shared_lines():
    """The handback lines every role adds: the method's bullets after 'Every handback then adds'."""
    text = METHOD.read_text(encoding="utf-8").split("Every handback then adds:", 1)[1]
    return [line[2:].rstrip(";.") for line in text.strip().split("\n\n", 1)[0].splitlines()]


def tier_map():
    """Tier -> (model, effort) on Claude Code, from the hosts page's Delegation table."""
    row = re.search(r"^\| Tier models, light / standard / deep \| ([^|]+) \|", HOSTS.read_text(encoding="utf-8"), re.M)
    pairs = re.findall(r"`(\w+)` (\w+)", row.group(1))
    return dict(zip(("light", "standard", "deep"), pairs))


class AgentTests(unittest.TestCase):
    def test_every_role_has_one_agent_named_for_it(self):
        self.assertEqual(len(roles()), 5)
        self.assertEqual({path.stem for path in AGENTS.glob("*.md")}, set(roles()))
        for path in AGENTS.glob("*.md"):
            with self.subTest(agent=path.stem):
                fields, _ = frontmatter(path)
                self.assertEqual(fields["name"], path.stem)
                self.assertLessEqual(len(fields["description"]), 1024)
                self.assertNotIn("—", path.read_text(encoding="utf-8"))  # the prose rule holds for agent prompts too

    def test_model_and_effort_are_allowed_and_follow_the_tier_map(self):
        tiers = tier_map()
        self.assertEqual(set(tiers), {"light", "standard", "deep"})
        for role, (tier, _, _) in roles().items():
            with self.subTest(role=role):
                fields, _ = frontmatter(AGENTS / f"{role}.md")
                self.assertTrue(fields["model"] in MODELS or fields["model"].startswith("claude-"))
                self.assertIn(fields["effort"], EFFORTS)
                self.assertEqual((fields["model"], fields["effort"]), tiers[tier])

    def test_read_only_roles_have_no_write_tools_and_no_role_spawns(self):
        for role, (_, edits, _) in roles().items():
            with self.subTest(role=role):
                fields, _ = frontmatter(AGENTS / f"{role}.md")
                allowed = set(re.split(r",\s*", fields["tools"])) if "tools" in fields else None
                denied = set(re.split(r",\s*", fields.get("disallowedTools", "")))
                if edits:  # writers keep every tool but Agent: only the coordinator spawns
                    self.assertEqual((allowed, denied), (None, {"Agent"}))
                else:  # an allowlist of reading tools, so inherited write-capable and MCP tools stay out too
                    self.assertTrue(allowed and allowed <= READERS)
        self.assertFalse(roles()["reviewer"][1])

    def test_handbacks_follow_the_method(self):
        shared = shared_lines()
        self.assertEqual(len(shared), 3)
        for role, (_, _, shape) in roles().items():
            with self.subTest(role=role):
                _, body = frontmatter(AGENTS / f"{role}.md")
                for line in (shape, *shared):
                    self.assertIn(line, body)

    def test_bundle_contract_requires_the_roles_and_method(self):
        required = set(json.loads((ROOT / "safe_engine/bundle-inputs.json").read_text(encoding="utf-8"))["required_files"])
        names = {f"skills/agents/{role}.md" for role in roles()} | {METHOD.relative_to(ROOT).as_posix()}
        self.assertLessEqual(names, required)
        market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        roots = [Path(s if isinstance(s, str) else s["path"]).as_posix() for s in (p["source"] for p in market["plugins"])]
        self.assertEqual(roots, ["skills"])  # the root that holds agents/, local or pinned to a release tag
        plugin = json.loads((ROOT / "skills/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("agents", plugin)  # an agents key would replace the agents/ scan

    def test_methods_name_tiers_and_roles_never_models(self):
        model = re.compile(r"\b(?:haiku|sonnet|opus|fable|composer-\d[\w.-]*|gpt-\d[\w.-]*|gemini-\d[\w.-]*"
                           r"|claude-(?:haiku|sonnet|opus|fable)[\w.-]*)\b", re.I)
        for path in (*(ROOT / ".agents/skills").rglob("*.md"), *(ROOT / "skills").glob("*/SKILL.md"), ROOT / "AGENTS.md"):
            with self.subTest(file=path.relative_to(ROOT).as_posix()):
                self.assertIsNone(model.search(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
