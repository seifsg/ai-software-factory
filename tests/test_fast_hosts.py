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
from unittest import mock

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

    def test_only_running_background_agents_make_a_stop_wait(self):
        def waiting(*tasks):
            return hosts.read("claude", {"hook_event_name": "Stop", "background_tasks": list(tasks)})["waiting"]
        agent = {"id": "a", "type": "subagent", "status": "running", "agent_type": "general-purpose"}
        self.assertTrue(waiting(agent))
        self.assertTrue(waiting({"type": "workflow", "status": "pending"}, {"type": "shell", "status": "running"}))
        for kind in ("shell", "monitor", "teammate", "cloud session", "MCP task", "dream", "auto-mode scan",
                     "memory import"):  # may never end (a server, a watcher) or belong to the host itself
            self.assertFalse(waiting({"type": kind, "status": "running"}), kind)
        self.assertFalse(waiting({**agent, "status": "completed"}))
        self.assertFalse(waiting())
        for malformed in ("[]", {"type": "subagent", "status": "running"}, ["subagent"], [{"type": "subagent"}], None):
            event = {"hook_event_name": "Stop", "background_tasks": malformed}
            self.assertFalse(hosts.read("claude", event)["waiting"], malformed)
        self.assertFalse(hosts.read("cursor", {"hook_event_name": "stop", "background_tasks": [agent]}).get("waiting"))

    def test_cursor_events_and_answers(self):
        shell = hosts.read("cursor", {"hook_event_name": "beforeShellExecution", "command": "npm i", "cwd": "/p",
                                      "conversation_id": "k"})
        self.assertEqual((shell["kind"], shell["tool"], shell["command"], shell["session"]), ("pre_tool", "shell", "npm i", "k"))
        write = hosts.read("cursor", {"hook_event_name": "preToolUse", "tool_name": "Write",
                                      "tool_input": {"file_path": "/p/a.ts"}, "workspace_roots": ["/p"]})
        self.assertEqual((write["tool"], write["paths"], write["cwd"]), ("edit", ["/p/a.ts"], "/p"))
        self.assertTrue(hosts.read("cursor", {"hook_event_name": "stop", "loop_count": 1})["again"])
        for status, again in (("aborted", True), ("error", True), ("cancelled", True), ("completed", False), (None, False)):
            stop = {"hook_event_name": "stop", "loop_count": 0, "status": status}  # only a completed turn gets pushed
            self.assertEqual(hosts.read("cursor", stop)["again"], again, status)
        self.assertFalse(hosts.read("cursor", {"hook_event_name": "stop", "loop_count": 0})["again"])  # older Cursor
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
        gate_home = mock.patch.dict(os.environ, {"SAFE_ENGINE_HOME": str(self.root / "gate")})  # install records here
        gate_home.start()
        self.addCleanup(gate_home.stop)
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
        stop = {"hook_event_name": "stop", "conversation_id": "k", "loop_count": 0, "workspace_roots": [str(self.project)]}
        code, out, _ = self.launch("cursor", stop)
        self.assertIn("Next:", out["followup_message"])
        self.assertEqual(self.launch("cursor", {**stop, "status": "aborted"})[:2], (0, None))  # the owner's stop stands

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

    def fake_claude(self, fail="", listed=True):
        """A stand-in Claude Code CLI: logs each call with its CLAUDE_CONFIG_DIR, fails calls starting with `fail`."""
        script, calls = self.root / "fake_claude.py", self.root / "claude-calls.txt"
        rows = [{"id": "safe-engine@ai-software-factory", "version": "9.9.9", "scope": "user", "enabled": True}]
        script.write_text(
            "import json, os, sys\nargs = ' '.join(sys.argv[1:])\n"
            f"open({str(calls)!r}, 'a', encoding='utf-8').write(os.environ.get('CLAUDE_CONFIG_DIR', '') + '|' + args + '\\n')\n"
            f"if {fail!r} and args.startswith({fail!r}):\n    print('boom'); sys.exit(1)\n"
            f"if args.startswith('plugin list'):\n    print(json.dumps({rows if listed else []!r}))\n", encoding="utf-8")
        patch = mock.patch.object(installer, "find_claude", return_value=[sys.executable, str(script)])
        patch.start()
        self.addCleanup(patch.stop)
        return lambda: [line.split("|", 1) for line in calls.read_text(encoding="utf-8").splitlines()]

    def test_installer_enables_installs_and_verifies_the_claude_plugin(self):
        settings = self.home / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps({"theme": "light"}), encoding="utf-8")
        calls, lines = self.fake_claude(), []
        installer.install("claude", home=self.home, log=lines.append)
        data = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(data["theme"], "light")
        self.assertTrue(data["enabledPlugins"]["safe-engine@ai-software-factory"])
        source = data["extraKnownMarketplaces"]["ai-software-factory"]["source"]
        self.assertEqual((source["source"], source["url"]), ("git", "https://github.com/seifsg/ai-software-factory.git"))
        self.assertTrue(settings.with_name("settings.json.bak-before-safe-engine").exists())
        self.assertEqual(calls(), [[str(self.home / ".claude"), "plugin marketplace update ai-software-factory"],
                                   [str(self.home / ".claude"), "plugin install safe-engine@ai-software-factory --scope user"],
                                   [str(self.home / ".claude"), "plugin list --json"]])  # never the real user's config
        self.assertIn("installed safe-engine@ai-software-factory 9.9.9", lines[-1])

    def test_an_unknown_marketplace_is_added_before_the_plugin_installs(self):
        calls = self.fake_claude(fail="plugin marketplace update")
        installer.install("claude", home=self.home, log=lambda line: None)
        self.assertEqual([args for _, args in calls()][:3],
                         ["plugin marketplace update ai-software-factory",
                          "plugin marketplace add https://github.com/seifsg/ai-software-factory.git",
                          "plugin install safe-engine@ai-software-factory --scope user"])

    def test_a_plugin_left_uninstalled_fails_loudly_with_the_fix(self):
        settings = self.home / ".claude" / "settings.json"
        for fake in ({"fail": "plugin install"}, {"listed": False}, None):
            with self.subTest(fake=fake):
                if fake is None:  # no CLI anywhere
                    patch = mock.patch.object(installer, "find_claude", return_value=None)
                    patch.start()
                    self.addCleanup(patch.stop)
                else:
                    self.fake_claude(**fake)
                with self.assertRaises(SystemExit) as stop:
                    installer.install("claude", home=self.home, log=lambda line: None)
                self.assertIn("enabled but not installed", str(stop.exception))
                self.assertIn("claude plugin install safe-engine@ai-software-factory --scope user", str(stop.exception))
                self.assertTrue(json.loads(settings.read_text(encoding="utf-8"))["enabledPlugins"]
                                ["safe-engine@ai-software-factory"])  # settings stay written

    def test_the_claude_cli_is_found_off_path(self):
        appdata = self.root / "appdata"
        for version in ("2.1.99", "2.1.308"):
            exe = appdata / "Claude" / "claude-code" / version / "abc" / "claude.exe"
            exe.parent.mkdir(parents=True)
            exe.write_text("", encoding="utf-8")
        env = {"APPDATA": str(appdata), "HOME": str(self.home), "USERPROFILE": str(self.home)}
        with mock.patch.dict(os.environ, env), mock.patch.object(installer.shutil, "which", return_value=None):
            os.environ.pop("SAFE_ENGINE_CLAUDE", None)
            self.assertEqual(installer.find_claude(), [str(appdata / "Claude/claude-code/2.1.308/abc/claude.exe")])
            with mock.patch.dict(os.environ, {"SAFE_ENGINE_CLAUDE": "/opt/claude"}):
                self.assertEqual(installer.find_claude(), ["/opt/claude"])
            shutil.rmtree(appdata)
            self.assertIsNone(installer.find_claude())

    def test_start_reports_a_claude_plugin_enabled_but_not_installed(self):
        setup = module("fast_setup")
        claude = self.home / ".claude"
        claude.mkdir(parents=True)
        (claude / "settings.json").write_text(json.dumps({"enabledPlugins": {"safe-engine@ai-software-factory": True}}),
                                              encoding="utf-8")
        with mock.patch.dict(os.environ, {"HOME": str(self.home), "USERPROFILE": str(self.home)}):
            self.assertIn("enabled but not installed", setup.hook_status(self.project))
            (claude / "plugins").mkdir()
            (claude / "plugins" / "installed_plugins.json").write_text(json.dumps(
                {"version": 2, "plugins": {"safe-engine@ai-software-factory": [{"scope": "user"}]}}), encoding="utf-8")
            self.assertEqual(setup.hook_status(self.project), "Claude Code")

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

    def plugin_hook(self, root, home, event):
        """The plugin's real PreToolUse command through bash, as the host's shell form runs it."""
        plugin = json.loads((SCRIPTS.parents[1] / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        command = plugin["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        env = {**self.env, "CLAUDE_PLUGIN_ROOT": str(root), "SAFE_ENGINE_HOME": str(home)}
        result = subprocess.run([shutil.which("bash"), "-c", command], input=json.dumps(event).encode(),
                                capture_output=True, env=env)
        out = result.stdout.decode("utf-8").strip()
        return result.returncode, json.loads(out) if out else None

    def test_the_plugin_sources_the_launcher_in_the_host_shell(self):
        if not shutil.which("bash"):
            self.skipTest("no bash")
        write = {"hook_event_name": "PreToolUse", "session_id": "s", "cwd": str(self.project), "tool_name": "Write",
                 "tool_input": {"file_path": str(self.project / "src" / "a.ts")}}
        code, out = self.plugin_hook(SCRIPTS.parents[1], self.root / "gate", write)
        self.assertEqual((code, out["hookSpecificOutput"]["permissionDecision"]), (0, "deny"))
        self.assertEqual(self.plugin_hook(SCRIPTS.parents[1], self.root / "idle", write), (0, None))  # no run: no process
        self.assertEqual(self.plugin_hook(self.root / "nowhere", self.root / "gate", write), (0, None))  # no launcher
        self.assertTrue(list((self.root / "gate" / "pycache").rglob("fast_gate*.pyc")))  # the gate loads from its cache

    def test_both_launchers_wake_for_a_run_whose_registration_was_deleted(self):
        for entry in (self.root / "gate" / "active").glob("*.json"):
            entry.unlink()  # rm ~/.safe-engine/active/*.json: the open state in runs/ remains
        write = {"hook_event_name": "PreToolUse", "session_id": "s", "cwd": str(self.project), "tool_name": "Write",
                 "tool_input": {"file_path": str(self.project / "src" / "a.ts")}}
        if shutil.which("bash"):
            code, out = self.plugin_hook(SCRIPTS.parents[1], self.root / "gate", write)
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        windows = subprocess.run([sys.executable, "-c", installer.HOME_PY + installer.GUARD_PY + installer.RUN_PY,
                                  str(SCRIPTS), "codex"], input=json.dumps(write).encode(), capture_output=True,
                                 env=self.env)
        self.assertEqual(json.loads(windows.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(len(list((self.root / "gate" / "active").glob("*.json"))), 1)  # re-registered

    def test_launcher_and_installer_boot_the_gate_the_same_way(self):
        self.assertIn(f'boot="{installer.BOOT}"', (SCRIPTS / "run-gate.sh").read_text(encoding="utf-8"))

    def test_the_windows_command_leaves_before_loading_the_gate(self):
        raises = self.root / "raises"
        raises.mkdir()
        (raises / "fast_gate.py").write_text("raise SystemExit('loaded')\n", encoding="utf-8")
        code = installer.HOME_PY + installer.GUARD_PY + installer.RUN_PY
        idle = subprocess.run([sys.executable, "-c", code, str(raises), "codex"], input=b"{}", capture_output=True,
                              env={**self.env, "SAFE_ENGINE_HOME": str(self.root / "idle")})
        self.assertEqual((idle.returncode, idle.stderr), (0, b""))  # no run: the gate is never loaded
        patch = {"hook_event_name": "PreToolUse", "session_id": "s", "cwd": str(self.project), "tool_name": "apply_patch",
                 "tool_input": {"command": "*** Begin Patch\n*** Add File: src/x.ts\n+x\n*** End Patch"}}
        active = subprocess.run([sys.executable, "-c", code, str(SCRIPTS), "codex"], input=json.dumps(patch).encode(),
                                capture_output=True, env=self.env)
        self.assertEqual(json.loads(active.stdout)["hookSpecificOutput"]["permissionDecision"], "deny", active.stderr)
        self.assertIn(f'"{SCRIPTS.as_posix()}" codex', installer.commands(SCRIPTS, "codex")[1])  # folder as an argument

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
