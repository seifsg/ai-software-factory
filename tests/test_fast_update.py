"""Daily self-update of installs without a plugin marketplace: install record, throttle, fast-forward, fail open."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
STUB = "import pathlib,sys;pathlib.Path(__file__).with_name('calls.txt').open('a').write(' '.join(sys.argv[1:])+'\\n')\n"


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main",
                           *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@unittest.skipUnless(shutil.which("git"), "no git")
class SelfUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """One origin for every test: main at A (the installed revision), then B (the newest)."""
        temp = tempfile.TemporaryDirectory(prefix="fast self-update ")
        cls.addClassCleanup(temp.cleanup)
        cls.origin = Path(temp.name).resolve()
        git(cls.origin, "init", "-q", "--bare", "remote.git")
        git(cls.origin, "clone", "-q", "remote.git", "dev")
        dev = cls.origin / "dev"
        scripts = dev / "skills" / "safe-engine" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "fast_gate.py").write_text(STUB, encoding="utf-8")  # records each reinstall's arguments
        (dev / ".gitignore").write_text("calls.txt\n", encoding="utf-8")
        for name in ("A", "B"):
            (dev / f"{name}.md").write_text(name, encoding="utf-8")
            git(dev, "add", "-A")
            git(dev, "commit", "-qm", name)
        cls.installed, cls.newest = git(dev, "rev-parse", "HEAD~1"), git(dev, "rev-parse", "HEAD")
        git(dev, "push", "-q", "origin", "main")

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="fast self-update ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.gate = self.root / "gate"
        self.gate.mkdir()
        env = mock.patch.dict(os.environ, {"SAFE_ENGINE_HOME": str(self.gate)})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("SAFE_ENGINE_NO_UPDATE", None)
        self.updater = module("fast_update")
        self.clone = self.root / "clone"  # the installed clone, one commit behind its origin
        git(self.root, "clone", "-q", str(self.origin / "remote.git"), "clone")
        git(self.clone, "reset", "-q", "--hard", self.installed)
        self.record = {"clone": str(self.clone), "revision": self.installed, "auto": True,
                       "installs": [{"host": "codex", "project": None}, {"host": "cursor", "project": "/p"}]}
        (self.gate / "install.json").write_text(json.dumps(self.record), encoding="utf-8")

    def head(self):
        return git(self.clone, "rev-parse", "HEAD")

    def calls(self):
        calls = self.clone / "skills" / "safe-engine" / "scripts" / "calls.txt"
        return calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []

    def age(self, hours):
        stamp = self.gate / "update.stamp"
        os.utime(stamp, (0, time.time() - hours * 3600))

    def test_runs_at_most_once_a_day_and_never_when_off(self):
        self.assertTrue(self.updater.due())
        self.assertFalse(self.updater.due())  # the day is claimed, even if the update then fails
        self.age(23)
        self.assertFalse(self.updater.due())
        self.age(25)
        with mock.patch.dict(os.environ, {"SAFE_ENGINE_NO_UPDATE": "1"}):
            self.assertFalse(self.updater.due())
        self.assertTrue(self.updater.due())
        (self.gate / "install.json").unlink()
        self.age(25)
        self.assertFalse(self.updater.due())  # nothing recorded: nothing to update
        self.assertEqual(self.updater.update({**self.record, "auto": False}), "off")

    def test_fast_forwards_main_and_reruns_each_install(self):
        self.assertEqual(self.updater.update(self.record), f"updated to {self.newest}")
        self.assertEqual(self.head(), self.newest)
        self.assertEqual(self.calls(), ["install --host codex", "install --host cursor --project /p"])
        self.assertEqual(self.updater.update({**self.record, "revision": self.newest}), "current")
        self.assertEqual(len(self.calls()), 2)  # nothing new: no reinstall

    def test_a_dirty_clone_or_another_branch_is_left_alone(self):
        (self.clone / "local.txt").write_text("mine\n", encoding="utf-8")
        self.assertEqual(self.updater.update(self.record), "skipped: clone has local changes")
        (self.clone / "local.txt").unlink()
        git(self.clone, "checkout", "-q", "-b", "side")
        self.assertEqual(self.updater.update(self.record), "skipped: clone not on main")
        git(self.clone, "checkout", "-q", "main")
        self.assertEqual((self.head(), self.calls()), (self.installed, []))

    def test_a_diverged_main_is_never_merged(self):
        (self.clone / "own.md").write_text("own\n", encoding="utf-8")
        git(self.clone, "add", "-A")
        git(self.clone, "commit", "-qm", "own")
        own = self.head()
        with self.assertRaises(subprocess.CalledProcessError):
            self.updater.update(self.record)
        self.assertEqual((self.head(), self.calls()), (own, []))

    def test_pinned_bundles_are_never_touched(self):
        bundle = self.gate / "bundles" / "abc"
        bundle.mkdir(parents=True)
        self.assertEqual(self.updater.update({**self.record, "clone": str(bundle)}), "pinned bundle: never updated")

    def test_offline_fails_open_and_logs_why(self):
        git(self.clone, "remote", "set-url", "origin", str(self.root / "nowhere.git"))
        run = subprocess.run([sys.executable, str(SCRIPTS / "fast_update.py")], capture_output=True, text=True)
        self.assertEqual((run.returncode, run.stdout), (0, ""))
        self.assertEqual((self.head(), self.calls()), (self.installed, []))
        lines = [json.loads(line) for line in (self.gate / "logs" / "gate.log").read_text(encoding="utf-8").splitlines()]
        self.assertTrue(lines[-1]["result"].startswith("error: fetch"), lines[-1])

    @unittest.skipUnless((SCRIPTS.parents[2] / ".git").exists(), "not a Git checkout")
    def test_installer_records_its_clone_and_wires_the_session_start_update(self):
        installer, home = module("fast_install"), self.root / "home"
        (self.gate / "install.json").unlink()
        installer.install("codex", home=home, log=lambda line: None)
        record = json.loads((self.gate / "install.json").read_text(encoding="utf-8"))
        self.assertEqual(Path(record["clone"]), SCRIPTS.parents[2])
        self.assertEqual((record["auto"], record["installs"]), (True, [{"host": "codex", "project": None}]))
        self.assertEqual(len(record["revision"]), 40)
        hooks = json.loads((home / ".codex" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        start = hooks["SessionStart"][0]["hooks"][0]
        self.assertTrue(start["command"].endswith("codex update"))
        self.assertIn(installer.UPDATE_PY, start["commandWindows"])
        for event in ("PreToolUse", "Stop", "UserPromptSubmit"):  # the per-call hooks stay as they were
            self.assertTrue(hooks[event][0]["hooks"][0]["command"].endswith("codex"), event)
            self.assertNotIn("fast_update", hooks[event][0]["hooks"][0]["commandWindows"])
        installer.install("cursor", project=self.root / "p", home=home, log=lambda line: None, auto=False)
        record = json.loads((self.gate / "install.json").read_text(encoding="utf-8"))
        self.assertFalse(record["auto"])
        self.assertEqual(len(record["installs"]), 2)
        cursor = json.loads((self.root / "p" / ".cursor" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.assertTrue(cursor["sessionStart"][0]["command"].endswith("cursor"))  # opted out: no extra process at all

    def test_both_session_start_launchers_update_before_the_gate(self):
        installer = module("fast_install")
        launch = [[sys.executable, "-c", installer.HOME_PY + installer.UPDATE_PY + installer.GUARD_PY, str(SCRIPTS),
                   "codex", "update"]]
        if shutil.which("sh"):
            launch.append([shutil.which("sh"), (SCRIPTS / "run-gate.sh").as_posix(), "codex", "update"])
        for command in launch:
            git(self.clone, "reset", "-q", "--hard", self.installed)
            (self.gate / "update.stamp").touch()
            self.age(25)
            plain = subprocess.run(command[:-1], input=b"{}", capture_output=True)  # any other hook: no update
            self.assertEqual((plain.returncode, self.head()), (0, self.installed))
            run = subprocess.run(command, input=b"{}", capture_output=True)
            self.assertEqual((run.returncode, self.head()), (0, self.newest), command[0])


if __name__ == "__main__":
    unittest.main()
