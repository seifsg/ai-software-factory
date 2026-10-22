"""The owner's live view: gate-written state, the try command, hook refreshes, the server and the snapshot
(fast-run.md#live-view)."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
GATE = SCRIPTS / "fast_gate.py"
RECORD = """# cockpit
## Tickets
**Ticket:** https://github.com/o/r/issues/11 Cockpit
**Backlog:** searched "cockpit": nothing open
## Plan
**Success:** the gauges move.
### Todos
- T1 App shell → open /cockpit and see it
- T2 Gauges </script><!--<script>alert(1)</script> → watch three gauges move
## Build log
"""


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class LiveViewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="live view ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.project = self.root / "app ü"
        (self.project / ".factory/fast/shots").mkdir(parents=True)
        self.env = dict(os.environ, SAFE_ENGINE_HOME=str(self.root / "home"), GH_CONFIG_DIR=str(self.root / "gh"))
        for name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"):
            self.env.pop(name, None)
        self.gate("start", "--key", "cockpit", "--kind", "change", "--no-ui", "--no-data", "--request", "live gauges")
        self.record = self.project / ".factory/fast/work-record.md"
        self.view = self.root / "home" / "view"

    def tearDown(self):
        log = self.root / "home" / "logs" / "gate.log"
        if log.exists():  # a view failure is logged; none may happen
            text = log.read_text(encoding="utf-8")
            self.assertNotIn("view.write_failed", text)
            self.assertNotIn("hook.error", text)

    def run_gate(self, *args):
        return subprocess.run([sys.executable, str(GATE), *args, "--project", str(self.project)],
                              capture_output=True, text=True, encoding="utf-8", env=self.env)

    def gate(self, *args):
        result = self.run_gate(*args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def hook(self, name="PreToolUse", **extra):
        event = {"hook_event_name": name, "session_id": "s1", "cwd": str(self.project), "tool_name": "Bash",
                 "tool_input": {"command": "ls"}, **extra}
        result = subprocess.run([sys.executable, str(GATE), "hook", "--host", "claude"], input=json.dumps(event).encode(),
                                capture_output=True, env=self.env)
        out = result.stdout.decode("utf-8").strip()
        return json.loads(out) if out else None

    def state(self):
        return json.loads((self.view / "state.json").read_text(encoding="utf-8"))

    def run_view(self):
        return self.state()["runs"][0]

    def todos_file(self):
        return next(self.view.glob("cockpit-*.todos.json"))

    def plan(self, log=""):
        self.record.write_text(RECORD + log, encoding="utf-8")
        self.gate("done", "tickets", "--offline", "test")
        self.gate("done", "plan", "--offline", "test")

    def test_gate_commands_write_the_view_with_the_cards_counts(self):
        self.plan("- T1 pre: a do: b post: c\n**Now:** T2\n")
        run = self.run_view()
        self.assertEqual([(s["id"], s["s"]) for s in run["steps"]][:3], [("tickets", "done"), ("plan", "done"), ("build", "now")])
        self.assertEqual((run["done"], run["total"], run["pct"]), (1, 2, 50))  # the card says ▰▱ 1/2
        self.assertEqual([t["id"] for t in run["now"]], ["T2"])
        self.assertEqual(run["last"]["id"], "T1")
        self.assertEqual(run["ticket"], "#11 Cockpit")
        todos = json.loads(self.todos_file().read_text(encoding="utf-8"))
        self.assertEqual([(t["id"], t["state"]) for t in todos], [("T2", "now"), ("T1", "done")])

    def test_try_refuses_bad_targets_and_records_a_good_one(self):
        self.plan("- T1 pre: a do: b post: c\n")
        for args, why in ((("T9", "--cmd", "pnpm dev"), "T9 is not a todo"),
                          (("T1", "--url", "javascript:alert(1)"), "http:// or https://"),
                          (("T1", "--file", "../outside.txt"), "is not a file inside"),
                          (("T1", "--cmd", "a\nb"), "one line")):
            result = self.run_gate("try", *args)
            self.assertNotEqual(result.returncode, 0, args)
            self.assertIn(why, result.stderr)
            self.assertIn("Form: fast_gate.py try T3", result.stderr)
        (self.project / ".factory/fast/shots/shell.png").write_bytes(b"\x89PNG")
        self.gate("try", "T1", "--url", "http://localhost:5173/cockpit")
        self.gate("try", "t1", "--file", ".factory/fast/shots/shell.png")
        self.assertIn("**Try:** T1 file .factory/fast/shots/shell.png\n", self.record.read_text(encoding="utf-8"))
        ready = self.state()["ready"]
        self.assertEqual([(t["id"], t["kind"], t["run"]) for t in ready], [("T1", "file", "cockpit")])  # the last Try line wins
        self.assertRegex(ready[0]["thumb"], r"^shots/cockpit-[0-9a-f]{6}-T1\.png$")
        self.assertTrue((self.view / ready[0]["thumb"]).is_file())

    def test_hooks_refresh_the_view_from_delegates_without_using_up_the_owners_message(self):
        self.plan()
        self.hook()
        self.record.write_text(RECORD + "- T1 pre: a do: b post: c\n", encoding="utf-8")
        self.assertIsNone(self.hook(agent_id="agent-1"))  # a delegate: no message, but the view moves
        self.assertEqual(self.run_view()["done"], 1)
        self.assertIn("✅ App shell done", self.hook()["systemMessage"])  # the main thread still gets it
        stamp = (self.view / "state.json").stat().st_mtime_ns
        self.assertIsNone(self.hook())
        self.assertEqual((self.view / "state.json").stat().st_mtime_ns, stamp)  # nothing changed: nothing written

    def test_stop_keeps_the_hosts_background_agents(self):
        tasks = [{"id": "a1", "type": "subagent", "status": "running", "description": "T2 gauges"},
                 {"id": "b1", "type": "shell", "status": "running"}]
        self.hook(name="Stop", background_tasks=tasks)
        first = self.run_view()
        self.assertEqual(first["agents"], [{"id": "a1", "desc": "T2 gauges", "run": True, "status": "working"}])
        self.hook(name="Stop", background_tasks=tasks)  # the same work was observed again
        observed = self.run_view()["agentsObservedAt"]
        self.assertGreater(observed, first["agentsObservedAt"])
        self.assertEqual(self.run_view()["subsessions"][0]["updated"], observed)
        self.gate("pause", "--reason", "Which colour?")  # a later write keeps the snapshot
        run = self.run_view()
        self.assertEqual(run["agents"][0]["id"], "a1")
        self.assertEqual(run["agentsObservedAt"], observed)
        self.assertEqual(run["subsessions"][0]["updated"], observed)
        self.assertEqual(run["paused"]["reason"], "Which colour?")
        self.gate("resume")
        self.assertEqual(self.run_view()["agentsObservedAt"], observed)
        self.assertEqual([e["text"] for e in self.state()["events"]][-2:], ["waits on you", "resumed"])

    def test_closed_runs_stay_until_the_next_day(self):
        self.gate("close", "--abandon", "owner stopped it")
        run = self.run_view()
        self.assertEqual(run["closed"], "stopped")
        view = module("fast_view")
        tomorrow = run["closedAt"] + 86_400_000
        with view.Lock(self.view):
            view.save_state(self.view, self.state()["runs"], tomorrow)
        self.assertEqual(self.state()["runs"], [])
        self.assertEqual(list(self.view.glob("cockpit-*.todos.json")), [])

    def test_server_answers_unchanged_polls_with_304_and_refuses_other_hosts(self):
        self.plan()
        server = subprocess.Popen([sys.executable, str(GATE), "view", "--project", str(self.project), "--port", "0"], stdout=subprocess.PIPE,
                                  text=True, encoding="utf-8", env=self.env)
        self.addCleanup(server.stdout.close)
        self.addCleanup(server.wait)
        self.addCleanup(server.kill)
        url = server.stdout.readline().split()[2]
        self.assertTrue(url.startswith("http://127.0.0.1:"), url)
        with urllib.request.urlopen(url + "state.json") as response:
            tag, body = response.headers["ETag"], json.loads(response.read())
            self.assertIn("connect-src 'self'", response.headers["Content-Security-Policy"])
        self.assertEqual(body["runs"][0]["label"], "cockpit")
        with self.assertRaises(urllib.error.HTTPError) as unchanged:
            urllib.request.urlopen(urllib.request.Request(url + "state.json", headers={"If-None-Match": tag}))
        self.assertEqual(unchanged.exception.code, 304)
        again = subprocess.run([sys.executable, str(GATE), "view", "--project", str(self.project), "--port", "0"], capture_output=True, text=True,
                               encoding="utf-8", env=self.env, timeout=60)  # a second view never starts a second server
        self.assertIn(f"Live view already running: {url}", again.stdout)
        with self.assertRaises(urllib.error.HTTPError) as rebound:
            urllib.request.urlopen(urllib.request.Request(url + "state.json", headers={"Host": "evil.example"}))
        self.assertEqual(rebound.exception.code, 403)
        with urllib.request.urlopen(url) as page:
            self.assertIn(b"<title>Factory progress</title>", page.read())

    def test_snapshot_holds_the_state_and_record_text_cannot_end_its_script(self):
        self.plan()
        out = self.root / "floor.html"
        subprocess.run([sys.executable, str(GATE), "view", "--project", str(self.project), "--snapshot", str(out)], check=True, capture_output=True,
                       env=self.env)
        html = out.read_text(encoding="utf-8")
        inline = html.split('<script id="snapshot" type="application/json">', 1)[1].split("</script>", 1)[0]
        self.assertNotIn("<", inline)  # neither </script> nor <!--<script in record text can end or nest the block
        self.assertIn("<!--<script>", json.dumps(json.loads(inline)["runs"][0]["open"], ensure_ascii=False))
        self.assertEqual(json.loads(inline)["runs"][0]["label"], "cockpit")

    def test_same_key_runs_in_two_projects_keep_their_own_views(self):
        other = self.root / "other app"
        other.mkdir()
        start = subprocess.run([sys.executable, str(GATE), "start", "--key", "cockpit", "--kind", "change", "--no-ui",
                                "--no-data", "--request", "other", "--project", str(other)], capture_output=True, env=self.env)
        self.assertEqual(start.returncode, 0, start.stderr)
        self.plan("- T1 pre: a do: b post: c\n")
        runs = self.state()["runs"]
        self.assertEqual(sorted(r["label"] for r in runs), ["cockpit", "cockpit"])
        self.assertEqual(len({r["key"] for r in runs}), 2)
        self.assertEqual(sorted(r["done"] for r in runs), [0, 1])  # no run's progress shows as the other's

    def test_a_fresh_gate_home_writes_an_empty_snapshot(self):
        out, home = self.root / "empty.html", self.root / "fresh home"
        result = subprocess.run([sys.executable, str(GATE), "view", "--project", str(self.project), "--snapshot", str(out)], capture_output=True,
                                env=dict(self.env, SAFE_ENGINE_HOME=str(home)))
        self.assertEqual(result.returncode, 0, result.stderr)
        inline = out.read_text(encoding="utf-8").split('<script id="snapshot" type="application/json">', 1)[1].split("</script>", 1)[0]
        self.assertEqual({k: json.loads(inline)[k] for k in ("runs", "ready", "events")}, {"runs": [], "ready": [], "events": []})

    def test_the_owner_gets_the_views_link_on_the_first_prompt_and_every_sixth(self):
        def reminders():
            answer = self.hook(name="UserPromptSubmit", prompt="go")
            return [line for line in (answer or {}).get("systemMessage", "").splitlines() if "Live view" in line]
        shown = [reminders() for _ in range(7)]
        self.assertEqual([bool(lines) for lines in shown], [True, False, False, False, False, False, True])
        self.assertIn("Live view is off", shown[0][0])  # no server yet: how to start it
        delegate = self.hook(name="UserPromptSubmit", prompt="go", agent_id="agent-1")
        self.assertNotIn("systemMessage", delegate)  # a delegate's prompt neither shows nor counts
        server = subprocess.Popen([sys.executable, str(GATE), "view", "--project", str(self.project), "--port", "0"], stdout=subprocess.PIPE,
                                  text=True, encoding="utf-8", env=self.env)
        self.addCleanup(server.stdout.close)
        self.addCleanup(server.wait)
        self.addCleanup(server.kill)
        url = server.stdout.readline().split()[2]
        for _ in range(5):
            reminders()
        self.assertEqual(reminders(), [f"🏭 Live view for this project: {url}"])  # the 13th prompt stays in this project

    def other_project(self):
        """A second same-key run makes accidental cross-project aggregation visible."""
        other = self.root / "other app"
        other.mkdir()
        subprocess.run([sys.executable, str(GATE), "start", "--project", str(other), "--key", "cockpit",
                        "--kind", "change", "--no-ui", "--no-data", "--request", "other"],
                       capture_output=True, check=True, env=self.env)
        return other

    def server(self):
        """An owned server, shared by both project URLs during each integration check."""
        process = subprocess.Popen([sys.executable, str(GATE), "view", "--project", str(self.project), "--port", "0"],
                                   stdout=subprocess.PIPE, text=True, encoding="utf-8", env=self.env)
        self.addCleanup(process.stdout.close)
        self.addCleanup(process.wait)
        self.addCleanup(process.kill)
        return process.stdout.readline().split()[2]

    def test_scoped_server_reuse_and_foreign_resources_are_isolated(self):
        self.plan("- T1 pre: a do: b post: c\n")
        local_shot = self.project / ".factory/fast/shots/local.png"
        local_shot.write_bytes(b"sample png")
        self.gate("try", "T1", "--file", str(local_shot))
        other = self.other_project()
        (self.view / "url").write_text("http://127.0.0.1:8765/", encoding="utf-8")
        (self.view / "index.html").write_text("legacy preview", encoding="utf-8")
        url = self.server()
        with urllib.request.urlopen(url + "state.json") as response:
            state = json.loads(response.read())
        self.assertEqual([r["project"] for r in state["runs"]], [str(self.project)])
        foreign = next(r for r in self.state()["runs"] if r["project"] == str(other))
        with urllib.request.urlopen(url + state["runs"][0]["key"] + ".todos.json") as response:
            self.assertEqual(len(json.loads(response.read())), 2)
        with urllib.request.urlopen(url + state["ready"][0]["thumb"]) as response:
            self.assertEqual(response.read(), b"sample png")
        base = url.split("/projects/")[0] + "/"
        for denied in (url + foreign["key"] + ".todos.json", base, base + "state.json", url + "shots/", url + "../state.json"):
            with self.assertRaises(urllib.error.HTTPError) as blocked:
                urllib.request.urlopen(denied)
            self.assertEqual(blocked.exception.code, 404, denied)
        reused = subprocess.run([sys.executable, str(GATE), "view", "--project", str(other)],
                                capture_output=True, text=True, encoding="utf-8", env=self.env, check=True)
        other_url = reused.stdout.split()[-1]
        self.assertTrue(other_url.startswith(base + "projects/"))
        self.assertNotEqual(url, other_url)
        with urllib.request.urlopen(other_url + "state.json") as response:
            self.assertEqual([r["project"] for r in json.loads(response.read())["runs"]], [str(other)])
        self.assertEqual((self.view / "url").read_text(encoding="utf-8"), "http://127.0.0.1:8765/")
        self.assertEqual((self.view / "index.html").read_text(encoding="utf-8"), "legacy preview")

    def test_snapshot_and_sections_filter_before_global_limits(self):
        self.plan("- T1 pre: a do: b post: c\n")
        self.gate("try", "T1", "--cmd", "local-only")
        other = self.other_project()
        views = module("fast_view")
        state = self.state()
        foreign = next(r for r in state["runs"] if r["project"] == str(other))
        foreign["ready"] = [{"key": f"foreign/{n}", "at": 9_999_999_999_999 + n} for n in range(30)]
        views.dump(self.view / "state.json", state)
        selected = views.scoped_state(self.view, views.scope_for(self.project))
        self.assertEqual(selected["readyTotal"], 1)
        self.assertEqual(selected["ready"][0]["value"], "local-only")
        out = self.root / "scoped.html"
        views.snapshot(self.view, out, views.scope_for(self.project))
        inline = out.read_text(encoding="utf-8").split('<script id="snapshot" type="application/json">')[1].split("</script>")[0]
        self.assertNotIn("<", inline)
        self.assertNotIn(str(other), json.dumps(json.loads(inline)))
        self.assertNotIn("foreign/", inline)

    def test_unchanged_and_unrelated_updates_keep_scoped_etag(self):
        other = self.other_project()
        url = self.server()
        with urllib.request.urlopen(url + "state.json") as response:
            tag = response.headers["ETag"]
        state = self.state()
        next(r for r in state["runs"] if r["project"] == str(other))["ticket"] = "foreign change"
        state["at"] += 1
        module("fast_view").dump(self.view / "state.json", state)
        with self.assertRaises(urllib.error.HTTPError) as unchanged:
            urllib.request.urlopen(urllib.request.Request(url + "state.json", headers={"If-None-Match": tag}))
        self.assertEqual(unchanged.exception.code, 304)

    def test_repo_worktrees_share_identity_but_clones_and_folders_do_not(self):
        views = module("fast_view")
        def git(*args):
            return subprocess.run(["git", "-C", str(self.project), *args], capture_output=True, check=True)
        git("init")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-m", "fixture")
        linked = self.root / "linked tree"
        git("worktree", "add", "-b", "linked", str(linked))
        nested = linked / "nested"
        nested.mkdir()
        self.assertEqual(views.scope_for(self.project), views.scope_for(nested))
        other = self.other_project()
        subprocess.run(["git", "init", str(other)], capture_output=True, check=True)
        self.assertNotEqual(views.scope_for(self.project)["id"], views.scope_for(other)["id"])
        plain = self.root / "plain"
        plain.mkdir()
        child = plain / "nested"
        child.mkdir()
        self.assertNotEqual(views.scope_for(plain)["id"], views.scope_for(child)["id"])

    def test_empty_project_snapshot_and_invalid_project_have_actionable_scope(self):
        empty = self.root / "empty"
        empty.mkdir()
        out = self.root / "empty-scoped.html"
        subprocess.run([sys.executable, str(GATE), "view", "--project", str(empty), "--snapshot", str(out)],
                       capture_output=True, check=True, env=self.env)
        inline = out.read_text(encoding="utf-8").split('<script id="snapshot" type="application/json">')[1].split("</script>")[0]
        state = json.loads(inline)
        self.assertEqual(state["scope"]["project"], str(empty))
        self.assertEqual(state["runs"], [])
        self.assertGreater(state["at"], 0)
        bad = subprocess.run([sys.executable, str(GATE), "view", "--project", str(empty / "missing"), "--snapshot", str(out)],
                             capture_output=True, text=True, env=self.env)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("view --project <existing-folder>", bad.stderr)

    def test_default_cwd_prefers_nested_repository_over_registered_parent(self):
        child = self.project / "child repository"
        child.mkdir()
        subprocess.run(["git", "init", str(child)], capture_output=True, check=True)
        out = self.root / "nested.html"
        subprocess.run([sys.executable, str(GATE), "view", "--snapshot", str(out)], cwd=child,
                       capture_output=True, check=True, env=self.env)
        inline = out.read_text(encoding="utf-8").split('<script id="snapshot" type="application/json">')[1].split("</script>")[0]
        state = json.loads(inline)
        self.assertEqual(state["scope"]["project"], str(child))
        self.assertEqual(state["runs"], [])
        plain = self.project / "ordinary child"
        plain.mkdir()
        subprocess.run([sys.executable, str(GATE), "view", "--snapshot", str(out)], cwd=plain,
                       capture_output=True, check=True, env=self.env)
        inline = out.read_text(encoding="utf-8").split('<script id="snapshot" type="application/json">')[1].split("</script>")[0]
        self.assertEqual(json.loads(inline)["scope"]["project"], str(self.project))

    def test_identity_cache_avoids_git_until_repository_metadata_changes(self):
        views = module("fast_view")
        first = views.scope_id(self.view, self.project)
        with patch.object(views, "scope_for", wraps=views.scope_for) as discover:
            self.assertEqual(views.scope_id(self.view, self.project), first)
            discover.assert_not_called()
            subprocess.run(["git", "init", str(self.project)], capture_output=True, check=True)
            self.assertNotEqual(views.scope_id(self.view, self.project), first)
            self.assertEqual(discover.call_count, 1)

    def test_git_environment_and_legacy_cached_ids_cannot_mix_projects(self):
        views = module("fast_view")
        other = self.other_project()
        for folder in (self.project, other):
            subprocess.run(["git", "init", str(folder)], capture_output=True, check=True)
        selected, foreign = views.scope_for(self.project), views.scope_for(other)
        inherited = {"GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other), "GIT_COMMON_DIR": str(other / ".git")}
        with patch.dict(os.environ, inherited):
            self.assertEqual(views.scope_for(self.project), selected)
            marker = self.project / ".git"
            info = marker.stat()
            markers = [str(marker), info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size]
            old = repr((markers, sorted((k, v) for k, v in os.environ.items() if k.startswith("GIT_"))))
            key, _ = views.identity_stamp(self.project)
            views.dump(self.view / "identities" / f"{key}.json", {"stamp": hashlib.sha256(old.encode()).hexdigest(), "id": foreign["id"]})
            self.assertEqual(views.scope_id(self.view, self.project), selected["id"])
            old_run = {**self.run_view(), "project": str(self.project), "scopeId": foreign["id"]}
            old_run.pop("scopeVersion", None)
            self.assertEqual(views.project_state({"runs": [old_run]}, foreign)["runs"], [])

    def test_the_page_never_turns_record_text_into_markup_or_script(self):
        page = (SCRIPTS / "view" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("x-html", page)
        self.assertNotIn("innerHTML", page)
        self.assertIn('x-if="t.kind===\'url\' && safeUrl(t.value)"', page)  # only http(s) links become links
        self.assertIn("safeSrc:v=>/^shots\\/[\\w.-]+$/", page)  # images only from the view folder


class ViewWriteTests(unittest.TestCase):
    def test_a_writer_holding_the_lock_is_waited_for_and_a_dead_ones_lock_is_taken_over(self):
        view = module("fast_view")
        with tempfile.TemporaryDirectory() as folder:
            lock = Path(folder) / "state.lock"
            lock.touch()
            old = time.time() - 5
            os.utime(lock, (old, old))
            with view.Lock(Path(folder)):
                self.assertTrue(lock.exists())
            self.assertFalse(lock.exists())


if __name__ == "__main__":
    unittest.main()
