"""Orchestrator setup: the agent it creates, the files it writes and the Codex home that carries the gate."""
import argparse
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import urllib.error

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
spec = importlib.util.spec_from_file_location("fast_orchestrate", SCRIPTS / "fast_orchestrate.py")
orchestrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orchestrate)


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeApi:
    """Records each request; answers GET with the listed agents and writes with an id."""

    def __init__(self, listed=None, error=None):
        self.listed, self.error, self.calls = listed if listed is not None else [], error, []

    def __call__(self, request, timeout):
        body = json.loads(request.data) if request.data else None
        self.calls.append((request.get_method(), request.full_url, body, request.get_header("Authorization")))
        if self.error:
            raise self.error
        answer = self.listed if request.get_method() == "GET" else {"id": "agent-1", **body}
        return Response(json.dumps(answer).encode())


class OrchestrateTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.user = self.temp / "home"
        (self.user / ".codex").mkdir(parents=True)
        (self.user / ".codex/auth.json").write_text("{}", encoding="utf-8")
        (self.user / ".codex/config.toml").write_text('model = "m"\n', encoding="utf-8")
        self.project = self.temp / "product"
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        patch = mock.patch.dict(os.environ, {"HOME": str(self.user), "USERPROFILE": str(self.user), "SAFE_ENGINE_HOME": str(self.temp / "gate")})
        patch.start()
        self.addCleanup(patch.stop)
        self.lines = []

    def args(self, *extra):
        parser = argparse.ArgumentParser()
        orchestrate.arguments(parser)
        return parser.parse_args(["paperclip", "--company", "c1", "--project", str(self.project), *extra])

    def run_setup(self, api, *extra):
        return orchestrate.run(self.args(*extra), log=self.lines.append, opener=api)

    def test_codex_gets_its_own_home_with_hooks_login_and_settings_and_no_trust_bypass(self):
        api = FakeApi()
        self.run_setup(api, "--agent", "codex")
        method, url, agent, _ = api.calls[-1]
        self.assertEqual((method, url), ("POST", "http://127.0.0.1:3100/api/companies/c1/agents"))
        home = self.temp / "gate/orchestrators/paperclip/codex-home"
        self.assertEqual(agent["adapterConfig"]["env"], {"CODEX_HOME": str(home)})
        self.assertEqual((agent["adapterType"], agent["runner"], agent["adapterConfig"]["engine"]),
                         ("codex_local", "legacy", "cli"))
        self.assertNotIn("extraArgs", agent["adapterConfig"])
        hooks = json.loads((home / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.assertIn("run-gate", hooks["PreToolUse"][0]["hooks"][0]["command"])
        self.assertTrue(os.path.samefile(home / "auth.json", self.user / ".codex/auth.json")  # linked, not copied
                        or not hasattr(os, "link"))
        self.assertEqual((home / "config.toml").read_text(encoding="utf-8"), 'model = "m"\n')
        self.assertTrue((self.user / ".agents/skills/safe-engine/SKILL.md").exists())
        self.assertTrue(any("/hooks" in line for line in self.lines))

    def test_instructions_route_every_task_into_the_orchestrated_run(self):
        api = FakeApi()
        self.run_setup(api, "--agent", "claude")
        agent = api.calls[-1][2]
        text = Path(agent["adapterConfig"]["instructionsFilePath"]).read_text(encoding="utf-8")
        self.assertIn("references/orchestrated-run.md", text)
        self.assertIn("references/paperclip.md", text)
        self.assertEqual(agent["adapterConfig"]["workspaceStrategy"], {"type": "git_worktree"})
        settings = json.loads((self.user / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertTrue(settings["enabledPlugins"]["safe-engine@ai-software-factory"])

    def test_an_agent_with_the_same_name_is_updated_not_duplicated(self):
        api = FakeApi({"agents": [{"id": "a9", "name": "Factory engineer (Claude Code)"}]})
        self.run_setup(api, "--agent", "claude")
        self.assertEqual([call[:2] for call in api.calls],
                         [("GET", "http://127.0.0.1:3100/api/companies/c1/agents"),
                          ("PATCH", "http://127.0.0.1:3100/api/agents/a9")])

    def test_dry_run_changes_nothing_and_sends_nothing(self):
        api = FakeApi()
        agent = self.run_setup(api, "--agent", "codex", "--dry-run", "--base-ref", "origin/dev")
        self.assertEqual(api.calls, [])
        self.assertFalse((self.temp / "gate").exists())
        self.assertEqual(agent["adapterConfig"]["workspaceStrategy"]["baseRef"], "origin/dev")

    def test_board_key_is_sent_from_the_named_variable(self):
        api = FakeApi()
        with mock.patch.dict(os.environ, {"MY_KEY": "pcp_board_x"}):
            self.run_setup(api, "--agent", "claude", "--token-env", "MY_KEY")
        self.assertEqual({call[3] for call in api.calls}, {"Bearer pcp_board_x"})

    def test_failures_stop_with_the_reason(self):
        with self.assertRaisesRegex(SystemExit, "not a Git repository"):
            orchestrate.run(argparse.Namespace(**{**vars(self.args("--agent", "claude")), "project": str(self.temp)}),
                            log=self.lines.append, opener=FakeApi())
        error = urllib.error.HTTPError("u", 403, "Forbidden", {}, io.BytesIO(b"board access required"))
        with self.assertRaisesRegex(SystemExit, "HTTP 403 board access required"):
            self.run_setup(FakeApi(error=error), "--agent", "claude")
        with self.assertRaisesRegex(SystemExit, "Is the orchestrator running"):
            self.run_setup(FakeApi(error=urllib.error.URLError("refused")), "--agent", "claude")


if __name__ == "__main__":
    unittest.main()
