"""Host adapters for the Fast gate: hook dialects, the launcher's host argument and the per-host installer."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


hosts, installer = module("fast_hosts"), module("fast_install")


class DialectTests(unittest.TestCase):
    def test_claude_and_codex_share_one_contract(self):
        event = hosts.read("codex", {"hook_event_name": "PreToolUse", "session_id": "s", "cwd": "/p",
                                     "tool_name": "apply_patch",
                                     "tool_input": {"command": "*** Begin Patch\n*** Update File: a.ts\n*** End Patch"}})
        self.assertEqual((event["kind"], event["tool"], event["paths"]), ("pre_tool", "edit", ["a.ts"]))
        out, code = hosts.deny("claude", "why")
        self.assertEqual((json.loads(out)["hookSpecificOutput"]["permissionDecision"], code), ("deny", 0))
        self.assertEqual(json.loads(hosts.keep_going("codex", "go"))["decision"], "block")
        read = hosts.read("claude", {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": "a"}})
        self.assertIsNone(read["tool"])  # reads never count as writes

    def test_cursor_events_and_answers(self):
        shell = hosts.read("cursor", {"hook_event_name": "beforeShellExecution", "command": "npm i", "cwd": "/p",
                                      "conversation_id": "k"})
        self.assertEqual((shell["kind"], shell["tool"], shell["command"], shell["session"]), ("pre_tool", "shell", "npm i", "k"))
        write = hosts.read("cursor", {"hook_event_name": "preToolUse", "tool_name": "Write",
                                      "tool_input": {"file_path": "/p/a.ts"}, "workspace_roots": ["/p"]})
        self.assertEqual((write["tool"], write["paths"], write["cwd"]), ("edit", ["/p/a.ts"], "/p"))
        self.assertTrue(hosts.read("cursor", {"hook_event_name": "stop", "loop_count": 1})["again"])
        self.assertEqual(json.loads(hosts.deny("cursor", "why")[0])["permission"], "deny")
        self.assertEqual(json.loads(hosts.keep_going("cursor", "go"))["followup_message"], "go")
        self.assertEqual(json.loads(hosts.context("cursor", "sessionStart", "t"))["additional_context"], "t")
        self.assertIsNone(hosts.context("cursor", "beforeSubmitPrompt", "t"))

    def test_other_agents_are_read_generically_and_denied_by_exit_code(self):
        copilot = hosts.read("copilot", {"sessionId": "p", "cwd": "/p", "toolName": "edit",
                                         "toolArgs": json.dumps({"path": "a.ts"})})  # real payloads carry no event name
        self.assertEqual((copilot["kind"], copilot["tool"], copilot["paths"]), ("pre_tool", "edit", ["a.ts"]))
        gemini = hosts.read("gemini", {"hook_event_name": "BeforeTool", "tool_name": "run_shell_command",
                                       "tool_input": {"command": "npm install"}})
        self.assertEqual((gemini["kind"], gemini["tool"]), ("pre_tool", "shell"))
        self.assertEqual(hosts.deny("gemini", "why"), (None, 2))
        self.assertIsNone(hosts.keep_going("gemini", "go"))


class LauncherAndInstallerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="fast hosts ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.project = self.root / "app"
        self.project.mkdir()
        self.home = self.root / "home"
        self.env = dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "gate"), HOME=str(self.home),
                        USERPROFILE=str(self.home))
        subprocess.run([sys.executable, str(SCRIPTS / "fast_gate.py"), "start", "--project", str(self.project),
                        "--key", "hosts", "--kind", "change", "--request", "x"], check=True, capture_output=True,
                       env=self.env)

    def tearDown(self):
        log = self.root / "gate" / "logs" / "gate.log"
        if log.exists():  # the fail-open guard must never have swallowed an exception
            self.assertNotIn("hook.error", log.read_text(encoding="utf-8"))

    def launch(self, host, event, launcher=None):
        launcher = launcher or SCRIPTS / "run-gate.sh"
        result = subprocess.run([shutil.which("sh"), launcher.as_posix(), host],
                                input=json.dumps(event, ensure_ascii=False).encode("utf-8"), capture_output=True, env=self.env)
        out = result.stdout.decode("utf-8").strip()
        return result.returncode, json.loads(out) if out else None, result.stderr.decode("utf-8", "replace")

    def cursor_write(self):
        return {"hook_event_name": "preToolUse", "conversation_id": "k", "workspace_roots": [str(self.project)],
                "tool_name": "Write", "tool_input": {"file_path": str(self.project / "src" / "a.ts")}}

    def test_launcher_answers_each_host_in_its_own_format(self):
        if not shutil.which("sh"):
            self.skipTest("no POSIX sh")
        code, out, _ = self.launch("cursor", self.cursor_write())
        self.assertEqual((code, out["permission"]), (0, "deny"))
        code, out, err = self.launch("gemini", {"hook_event_name": "BeforeTool", "session_id": "m", "cwd": str(self.project),
                                                "tool_name": "write_file", "tool_input": {"file_path": "src/a.ts"}})
        self.assertEqual((code, out), (2, None))
        self.assertIn("blocks writing", err)
        code, out, _ = self.launch("cursor", {"hook_event_name": "stop", "conversation_id": "k", "loop_count": 0,
                                              "workspace_roots": [str(self.project)]})
        self.assertIn("Next:", out["followup_message"])

    def test_installer_wires_codex_and_cursor_and_keeps_user_hooks(self):
        codex = self.home / ".codex" / "hooks.json"
        codex.parent.mkdir(parents=True)
        codex.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"command": "echo mine"}]}]}}),
                         encoding="utf-8")
        for _ in range(2):  # re-running replaces only the factory's entries
            installer.install("codex", home=self.home, log=lambda line: None)
            installer.install("cursor", home=self.home, log=lambda line: None)
        groups = json.loads(codex.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        self.assertEqual([group["hooks"][0]["command"] for group in groups][0], "echo mine")
        self.assertEqual(len(groups), 2)
        cursor = json.loads((self.home / ".cursor" / "hooks.json").read_text(encoding="utf-8"))
        self.assertEqual((cursor["version"], sorted(cursor["hooks"])), (1, ["preToolUse", "sessionStart", "stop"]))
        skills = self.home / ".agents" / "skills"
        self.assertEqual(sorted(path.name for path in skills.iterdir()), ["improve-factory", "safe-engine"])
        self.assertEqual(list(skills.rglob("__pycache__")), [])
        if shutil.which("sh"):
            code, out, _ = self.launch("cursor", self.cursor_write(), skills / "safe-engine" / "scripts" / "run-gate.sh")
            self.assertEqual(out["permission"], "deny")  # the installed copy gates too

    def test_installer_enables_the_claude_plugin_over_https(self):
        settings = self.home / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps({"theme": "light"}), encoding="utf-8")
        installer.install("claude", home=self.home, log=lambda line: None)
        data = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(data["theme"], "light")
        self.assertTrue(data["enabledPlugins"]["safe-engine@ai-software-factory"])
        source = data["extraKnownMarketplaces"]["ai-software-factory"]["source"]
        self.assertEqual((source["source"], source["url"]), ("git", "https://github.com/seifsg/ai-software-factory.git"))
        self.assertTrue(settings.with_name("settings.json.bak-before-safe-engine").exists())

    def test_a_missing_gate_never_blocks_any_host(self):
        if not shutil.which("sh"):
            self.skipTest("no POSIX sh")
        broken = self.root / "broken"
        broken.mkdir()
        shutil.copy(SCRIPTS / "run-gate.sh", broken / "run-gate.sh")  # launcher without the gate beside it
        for host in ("claude", "cursor", "gemini"):
            code, out, _ = self.launch(host, self.cursor_write(), broken / "run-gate.sh")
            self.assertEqual((code, out), (0, None), host)
        _, windows = installer.commands(self.root / "nowhere", "cursor")
        python = sys.executable.replace("\\", "/")
        result = subprocess.run(f'"{python}" ' + windows.split(" ", 2)[2] if windows.startswith("py -3") else windows,
                                shell=True, input=b"{}", capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0)  # guarded Windows command: missing gate exits 0

    def test_installer_never_overwrites_skills_it_did_not_install(self):
        canonical = self.root / "factory" / ".agents" / "skills" / "safe-engine"
        canonical.mkdir(parents=True)
        (canonical / "SKILL.md").write_text("canonical", encoding="utf-8")
        with self.assertRaises(SystemExit):
            installer.install("codex", project=self.root / "factory", home=self.home, log=lambda line: None)
        self.assertEqual((canonical / "SKILL.md").read_text(encoding="utf-8"), "canonical")
        installer.install("other", project=self.root / "agent", home=self.home, log=lambda line: None)
        installer.install("other", project=self.root / "agent", home=self.home, log=lambda line: None)  # own copy
        self.assertFalse((self.root / "agent" / ".codex").exists())

    def test_hook_flags_and_help_on_the_hot_path(self):
        gate = [sys.executable, str(SCRIPTS / "fast_gate.py"), "hook"]
        result = subprocess.run(gate + ["--host=cursor"], input=json.dumps(self.cursor_write()), capture_output=True,
                                text=True, env=self.env)
        self.assertEqual(json.loads(result.stdout)["permission"], "deny")
        result = subprocess.run(gate + ["--help"], capture_output=True, text=True, env=self.env, timeout=30)
        self.assertIn("--host", result.stdout)

    def test_unknown_host_is_refused(self):
        with self.assertRaises(SystemExit):
            installer.install("vim", home=self.home, log=lambda line: None)


if __name__ == "__main__":
    unittest.main()
