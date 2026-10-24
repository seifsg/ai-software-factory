"""Daily self-update of installs without a plugin marketplace: install record, throttle, release tags, rollback,
fail open."""
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

from safe_engine import distribution

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"
# Records each reinstall's arguments; a release carrying fail.flag cannot install.
STUB = ("import pathlib,sys;p=pathlib.Path(__file__);p.with_name('calls.txt').open('a').write(' '.join(sys.argv[1:])"
        "+'\\n');sys.exit(1 if p.with_name('fail.flag').exists() else 0)\n")


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main",
                           *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit(dev, name, release=None, tamper=False, files=None):
    """One commit; a release writes its version and manifest first, a tampered one changes a file afterwards."""
    for path, text in {f"{name}.md": name, **(files or {})}.items():
        (dev / path).parent.mkdir(parents=True, exist_ok=True)
        (dev / path).write_text(text, encoding="utf-8")
    if release:
        (dev / distribution.VERSION_FILE).write_text(release + "\n", encoding="utf-8")
        git(dev, "add", "-A")
        (dev / distribution.MANIFEST).write_text(json.dumps(distribution.build_manifest(dev)), encoding="utf-8")
    if tamper:
        (dev / f"{name}.md").write_text("changed after the manifest", encoding="utf-8")
    git(dev, "add", "-A")
    git(dev, "commit", "-qm", name)
    if release:
        git(dev, "tag", "-a", f"v{release}", "-m", release)
    return git(dev, "rev-parse", "HEAD")


def origin(root):
    """A bare origin and its working clone, seeded with the stub installer."""
    git(root, "init", "-q", "--bare", "remote.git")
    git(root, "clone", "-q", "remote.git", "dev")
    dev = root / "dev"
    (dev / "skills" / "safe-engine" / "scripts").mkdir(parents=True)
    (dev / "skills" / "safe-engine" / "scripts" / "fast_gate.py").write_text(STUB, encoding="utf-8")
    (dev / ".gitignore").write_text("calls.txt\n", encoding="utf-8")
    return dev


class UpdateCase(unittest.TestCase):
    """An isolated gate home, the updater, and the fixture origin trusted like the factory repository."""

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

    def trust(self, url):
        import resolve_bundle  # the copy beside fast_update.py, which update() imports
        trusted = mock.patch.object(resolve_bundle, "ORIGINS", {*resolve_bundle.ORIGINS, url})
        trusted.start()
        self.addCleanup(trusted.stop)

    def install(self, remote, at, **record):
        """The installed clone, checked out at `at`, and its install record."""
        git(self.root, "clone", "-q", str(remote), "clone")
        self.clone = self.root / "clone"
        git(self.clone, "checkout", "-q", "--detach", at)
        self.record = {"clone": str(self.clone), "revision": at, "auto": True,
                       "installs": [{"host": "codex", "project": None}, {"host": "cursor", "project": "/p"}], **record}
        (self.gate / "install.json").write_text(json.dumps(self.record), encoding="utf-8")

    def head(self):
        return git(self.clone, "rev-parse", "HEAD")

    def calls(self):
        calls = self.clone / "skills" / "safe-engine" / "scripts" / "calls.txt"
        return calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []

    def age(self, hours):
        stamp = self.gate / "update.stamp"
        os.utime(stamp, (0, time.time() - hours * 3600))


@unittest.skipUnless(shutil.which("git"), "no git")
class SelfUpdateTests(UpdateCase):
    """Before the first release: stable follows main, as edge does."""

    @classmethod
    def setUpClass(cls):
        """One origin for every test: main at A (the installed revision), then B (the newest), no release tags."""
        temp = tempfile.TemporaryDirectory(prefix="fast self-update ")
        cls.addClassCleanup(temp.cleanup)
        cls.origin = Path(temp.name).resolve()
        dev = origin(cls.origin)
        cls.installed, cls.newest = commit(dev, "A"), commit(dev, "B")
        git(dev, "push", "-q", "origin", "main")

    def setUp(self):
        super().setUp()
        self.trust(str(self.origin / "remote.git"))
        self.install(self.origin / "remote.git", self.installed)
        git(self.clone, "checkout", "-q", "-B", "main", self.installed)

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
        self.assertEqual(self.updater.update({"channel": "edge"}), "nothing installed from a clone")

    def test_fast_forwards_main_and_reruns_each_install(self):
        note = " (no release yet: following main)"
        self.assertEqual(self.updater.update(self.record), f"updated to {self.newest}{note}")
        self.assertEqual(self.head(), self.newest)
        self.assertEqual(self.calls(), ["install --host codex", "install --host cursor --project /p"])
        self.assertEqual(self.updater.update({**self.record, "revision": self.newest}), "current" + note)
        self.assertEqual(len(self.calls()), 2)  # nothing new: no reinstall
        saved = json.loads((self.gate / "install.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["previous"], {"ref": "main", "revision": self.installed, "version": None})

    def test_a_dirty_clone_another_branch_or_commit_a_foreign_origin_or_a_run_bundle_is_left_alone(self):
        (self.clone / "local.txt").write_text("mine\n", encoding="utf-8")
        self.assertEqual(self.updater.update(self.record), "skipped: clone has local changes")
        (self.clone / "local.txt").unlink()
        git(self.clone, "checkout", "-q", "-b", "side")
        self.assertEqual(self.updater.update(self.record), "skipped: clone not on main or a release tag")
        git(self.clone, "checkout", "-q", "--detach", "origin/main")  # checked out by hand: no tag, not the install
        self.assertEqual(self.updater.update(self.record), "skipped: clone not on main or a release tag")
        git(self.clone, "checkout", "-q", "main")
        (self.gate / "runs").mkdir()
        run = self.gate / "runs" / "abc.json"
        run.write_text(json.dumps({"bundle": {"root": str(self.clone), "revision": self.installed}}), encoding="utf-8")
        self.assertEqual(self.updater.update(self.record), "skipped: an open run reads its methods from this clone")
        run.write_text("{unreadable", encoding="utf-8")  # cannot tell: keep the clone
        self.assertEqual(self.updater.update(self.record), "skipped: an open run reads its methods from this clone")
        run.write_text(json.dumps({"bundle": None}), encoding="utf-8")
        git(self.clone, "remote", "set-url", "origin", "https://example.invalid/fork.git")
        self.assertEqual(self.updater.update(self.record), "skipped: clone origin is not the factory repository")
        self.assertEqual((self.head(), self.calls()), (self.installed, []))

    def test_an_interrupted_install_is_redone_and_an_unknown_channel_refused(self):
        git(self.clone, "merge", "-q", "--ff-only", "origin/main")  # the clone moved, its install never finished
        (self.gate / "runs").mkdir()  # a closed run that kept its state here blocks nothing
        (self.gate / "runs" / "old.json").write_text(json.dumps({"closed": True, "bundle": {"root": str(self.clone)}}))
        note = " (no release yet: following main)"
        self.assertEqual(self.updater.update(self.record), f"updated to {self.newest}{note}")
        self.assertEqual(len(self.calls()), 2)
        saved = json.loads((self.gate / "install.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["previous"], {"ref": "HEAD", "revision": self.installed, "version": None})
        with self.assertRaisesRegex(RuntimeError, "Unknown update channel 'beta'"):
            self.updater.update({**self.record, "channel": "beta", "revision": self.installed})
        self.assertEqual(self.head(), self.newest)

    def test_a_diverged_main_is_never_merged(self):
        own = commit(self.clone, "own")
        with self.assertRaises(subprocess.CalledProcessError):
            self.updater.update(self.record)
        self.assertEqual((self.head(), self.calls()), (own, []))

    def test_pinned_bundles_are_never_touched(self):
        bundle = self.gate / "bundles" / "abc"
        bundle.mkdir(parents=True)
        self.assertEqual(self.updater.update({**self.record, "clone": str(bundle)}), "pinned bundle: never updated")

    def run_updater(self, *trusted):
        """fast_update.main in a fresh Python, trusting the given origins as the factory repository."""
        code = (f"import sys;sys.path.insert(0,{str(SCRIPTS)!r});import resolve_bundle;"
                f"resolve_bundle.ORIGINS.update({list(trusted)!r});import fast_update;fast_update.main()")
        return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)

    def log(self):
        path = self.gate / "logs" / "gate.log"
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        return [json.loads(line) for line in lines if json.loads(line)["event"] == "update"]

    def test_offline_fails_open_and_logs_why(self):
        nowhere = str(self.root / "nowhere.git")
        git(self.clone, "remote", "set-url", "origin", nowhere)
        run = self.run_updater(nowhere)
        self.assertEqual((run.returncode, run.stdout), (0, ""))
        self.assertEqual((self.head(), self.calls()), (self.installed, []))
        self.assertTrue(self.log()[-1]["result"].startswith("error: fetch"), self.log()[-1])

    @unittest.skipUnless((SCRIPTS.parents[2] / ".git").exists(), "not a Git checkout")
    def test_installer_records_its_clone_channel_and_wires_the_session_start_update(self):
        installer, home = module("fast_install"), self.root / "home"
        (self.gate / "install.json").unlink()
        installer.install("codex", home=home, log=lambda line: None)
        record = json.loads((self.gate / "install.json").read_text(encoding="utf-8"))
        self.assertEqual(Path(record["clone"]), SCRIPTS.parents[2])
        self.assertEqual((record["auto"], record["channel"], record["installs"]),
                         (True, "stable", [{"host": "codex", "project": None}]))
        self.assertEqual(len(record["revision"]), 40)
        hooks = json.loads((home / ".codex" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        start = hooks["SessionStart"][0]["hooks"][0]
        self.assertTrue(start["command"].endswith("codex update"))
        self.assertIn(installer.UPDATE_PY, start["commandWindows"])
        for event in ("PreToolUse", "Stop", "UserPromptSubmit"):  # the per-call hooks stay as they were
            self.assertTrue(hooks[event][0]["hooks"][0]["command"].endswith("codex"), event)
            self.assertNotIn("fast_update", hooks[event][0]["hooks"][0]["commandWindows"])
        installer.install("cursor", project=self.root / "p", home=home, log=lambda line: None, auto=False,
                          channel="edge")
        record = json.loads((self.gate / "install.json").read_text(encoding="utf-8"))
        self.assertEqual((record["auto"], record["channel"], len(record["installs"])), (False, "edge", 2))
        cursor = json.loads((self.root / "p" / ".cursor" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.assertTrue(cursor["sessionStart"][0]["command"].endswith("cursor"))  # opted out: no extra process at all
        installer.install("claude", home=home, log=lambda line: None)  # keeps the channel and the clone installs
        record = json.loads((self.gate / "install.json").read_text(encoding="utf-8"))
        self.assertEqual((record["channel"], len(record["installs"])), ("edge", 2))
        installer.install("claude", home=home, log=lambda line: None, channel="stable")
        self.assertEqual(json.loads((self.gate / "install.json").read_text(encoding="utf-8"))["channel"], "stable")
        copy = home / ".agents" / "skills" / "safe-engine"  # a file a release dropped leaves the copy
        (copy / "scripts" / "dropped.py").write_text("old\n", encoding="utf-8")
        (copy / "gone" / "deep").mkdir(parents=True)
        (copy / "gone" / "deep" / "old.md").write_text("old\n", encoding="utf-8")
        installer.install("codex", home=home, log=lambda line: None)
        self.assertFalse((copy / "scripts" / "dropped.py").exists() or (copy / "gone").exists())
        self.assertTrue((copy / installer.MARKER).exists() and (copy / "scripts" / "fast_gate.py").exists())

    def test_both_session_start_launchers_update_before_the_gate(self):
        installer = module("fast_install")
        launch = [[sys.executable, "-c", installer.HOME_PY + installer.UPDATE_PY + installer.GUARD_PY, str(SCRIPTS),
                   "codex", "update"]]
        if shutil.which("sh"):
            launch.append([shutil.which("sh"), (SCRIPTS / "run-gate.sh").as_posix(), "codex", "update"])
        for command in launch:  # the real launchers trust only the factory repository: the log proves the call
            (self.gate / "update.stamp").touch()
            self.age(25)
            before = len(self.log())
            plain = subprocess.run(command[:-1], input=b"{}", capture_output=True)  # any other hook: no update
            self.assertEqual((plain.returncode, len(self.log())), (0, before))
            run = subprocess.run(command, input=b"{}", capture_output=True)
            self.assertEqual((run.returncode, len(self.log()), self.log()[-1]["result"]),
                             (0, before + 1, "skipped: clone origin is not the factory repository"), command[0])


@unittest.skipUnless(shutil.which("git"), "no git")
class ReleaseUpdateTests(UpdateCase):
    """Stable follows release tags on main whose files match their manifest; a failed install rolls back."""

    def setUp(self):
        super().setUp()
        self.dev = origin(self.root)
        self.remote = self.root / "remote.git"
        self.trust(str(self.remote))
        self.v100 = commit(self.dev, "A", "1.0.0")

    def publish(self, *refs):
        git(self.dev, "push", "-q", "origin", "main", *refs)

    def test_stable_takes_the_newest_verified_release_on_main(self):
        v110 = commit(self.dev, "B", "1.1.0")
        git(self.dev, "checkout", "-q", "-b", "side")
        commit(self.dev, "S", "1.3.0")  # a release tag off main
        git(self.dev, "checkout", "-q", "main")
        commit(self.dev, "C", "1.2.0", tamper=True)
        self.publish("--tags", "side")
        self.install(self.remote, self.v100)
        result = self.updater.update(self.record)
        self.assertTrue(result.startswith(f"updated to {v110} (v1.1.0; skipped v1.3.0 is not on main; "
                                          "v1.2.0 does not match its manifest: changed: C.md"), result)
        self.assertEqual(self.head(), v110)
        self.assertEqual(self.calls(), ["install --host codex", "install --host cursor --project /p"])
        saved = json.loads((self.gate / "install.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["previous"], {"ref": "HEAD", "revision": self.v100, "version": "1.0.0"})
        notice = (self.gate / "update-notice.txt").read_text(encoding="utf-8")
        self.assertIn("Factory updated from 1.0.0 to 1.1.0", notice)
        self.assertIn("CHANGELOG.md", notice)
        self.assertTrue(self.updater.update({**self.record, "revision": v110}).startswith("current (v1.1.0; skipped"))
        self.assertEqual(len(self.calls()), 2)

    def test_a_failed_install_restores_the_previous_release(self):
        broken = commit(self.dev, "B", "1.1.0", files={"skills/safe-engine/scripts/fail.flag": "x"})
        self.publish("--tags")
        self.install(self.remote, self.v100)
        result = self.updater.update(self.record)
        self.assertTrue(result.startswith(f"rolled back to {self.v100}: install of {broken} failed"), result)
        self.assertEqual(self.head(), self.v100)
        self.assertEqual(self.calls(), ["install --host codex", "install --host codex",
                                        "install --host cursor --project /p"])  # failed new, then the old again
        self.assertIn("failed and was rolled back to 1.0.0",
                      (self.gate / "update-notice.txt").read_text(encoding="utf-8"))

    def test_after_an_interrupted_install_a_failure_returns_to_the_last_completed_one(self):
        v110 = commit(self.dev, "B", "1.1.0")
        broken = commit(self.dev, "C", "1.2.0", files={"skills/safe-engine/scripts/fail.flag": "x"})
        self.publish("--tags")
        self.install(self.remote, v110, revision=self.v100, version="1.0.0")  # 1.1.0's install was cut off
        result = self.updater.update(self.record)
        self.assertTrue(result.startswith(f"rolled back to {self.v100}: install of {broken} failed"), result)
        self.assertEqual(self.head(), self.v100)
        saved = json.loads((self.gate / "install.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["previous"], {"ref": "HEAD", "revision": self.v100, "version": "1.0.0"})
        self.assertIn("rolled back to 1.0.0", (self.gate / "update-notice.txt").read_text(encoding="utf-8"))

    def test_a_rollback_off_any_tag_keeps_updating(self):
        git(self.dev, "tag", "-d", "v1.0.0")  # before the first release: stable follows main
        pulled = commit(self.dev, "B")
        broken = commit(self.dev, "C", files={"skills/safe-engine/scripts/fail.flag": "x"})
        self.publish()
        self.install(self.remote, pulled, revision=self.v100)  # pulled by hand, never reinstalled
        git(self.clone, "checkout", "-q", "-B", "main", pulled)
        result = self.updater.update(self.record)
        self.assertTrue(result.startswith(f"rolled back to {self.v100}: install of {broken} failed"), result)
        self.assertEqual(self.head(), self.v100)  # detached at the last completed install
        (self.dev / "skills/safe-engine/scripts/fail.flag").unlink()
        fixed = commit(self.dev, "D")
        self.publish()
        self.assertEqual(self.updater.update(self.record), f"updated to {fixed} (no release yet: following main)")

    def test_edge_follows_main(self):
        tip = commit(self.dev, "B", "1.1.0", tamper=True)
        self.publish("--tags")
        self.install(self.remote, self.v100, channel="edge")
        self.assertEqual(self.updater.update(self.record), f"updated to {tip}")
        self.assertEqual(git(self.clone, "rev-parse", "--abbrev-ref", "HEAD"), "main")

    def test_releases_that_all_fail_keep_the_install(self):
        git(self.dev, "tag", "-d", "v1.0.0")
        commit(self.dev, "B", "1.1.0", tamper=True)
        self.publish("--tags")
        self.install(self.remote, self.v100)
        git(self.clone, "checkout", "-q", "-B", "main", self.v100)  # on main, before any release it trusts
        with self.assertRaisesRegex(RuntimeError, "no release verifies: v1.1.0 does not match its manifest"):
            self.updater.update(self.record)
        self.assertEqual((self.head(), self.calls()), (self.v100, []))
        self.assertEqual(git(self.clone, "rev-parse", "--abbrev-ref", "HEAD"), "main")  # put back as it was

    def test_a_moved_tag_never_reaches_the_install(self):
        v110 = commit(self.dev, "B", "1.1.0")
        self.publish("--tags")
        self.install(self.remote, self.v100)
        self.updater.update(self.record)
        moved = commit(self.dev, "C")
        git(self.dev, "tag", "-f", "-a", "v1.1.0", "-m", "moved")
        git(self.dev, "push", "-q", "-f", "origin", "main", "v1.1.0")
        with self.assertRaises(subprocess.CalledProcessError) as failure:  # git refuses to clobber a local tag
            self.updater.update({**self.record, "revision": v110})
        self.assertIn("clobber", failure.exception.stderr)
        self.assertNotEqual(self.head(), moved)
        self.assertEqual(self.head(), v110)


if __name__ == "__main__":
    unittest.main()
