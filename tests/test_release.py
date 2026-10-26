"""Release identity: one version everywhere, the changelog format, the sha256 manifest, the release check, the
release script, the gate's version command and card line."""
from datetime import date
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import safe_engine
from safe_engine import distribution as release
from safe_engine.workflow import resumable

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "skills/safe-engine/scripts/fast_gate.py"
VERSION = (ROOT / release.VERSION_FILE).read_text(encoding="utf-8").strip()
HEADING = re.compile(r"^## \[([^\]]+)\](?: - (\d{4}-\d{2}-\d{2}))?$", re.M)


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main",
                           *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def run(*args, cwd=ROOT, env=None):
    return subprocess.run([sys.executable, *map(str, args)], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})})


class VersionTests(unittest.TestCase):
    def test_one_version_everywhere(self):
        self.assertRegex(VERSION, r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
        plugin = json.loads((ROOT / "skills/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
        entry = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))["plugins"][0]
        released = [name for name, _ in HEADING.findall((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
                    if name != "Unreleased"]
        self.assertEqual(plugin["version"], VERSION)
        self.assertEqual(entry["source"], {"source": "git-subdir", "url": release.REPOSITORY, "path": "skills",
                                           "ref": f"v{VERSION}"})
        self.assertNotIn("version", entry)  # plugin.json wins silently: never two copies to drift (Claude Code docs)
        self.assertEqual(safe_engine.__version__, VERSION)
        self.assertEqual(released[0], VERSION)
        self.assertEqual(release.read_manifest(ROOT)["version"], VERSION)
        with tempfile.TemporaryDirectory(prefix="factory gate home ") as home:  # never the developer's own gate home
            self.assertEqual(run(GATE, "version", env={"SAFE_ENGINE_HOME": home}).stdout.splitlines()[0],
                             f"Factory {VERSION}")

    def test_the_factory_origin_in_any_spelling_and_nothing_else(self):
        for url in (release.REPOSITORY, "git@github.com:seifsg/ai-software-factory", "https://github.com/SeifSG/"
                    "AI-Software-Factory/", "https://user:token@github.com/seifsg/ai-software-factory.git",
                    "ssh://git@github.com/seifsg/ai-software-factory"):
            self.assertTrue(release.factory_origin(url), url)
        for url in ("https://github.com/someone/ai-software-factory.git", "https://evil.example/github.com/seifsg/"
                    "ai-software-factory", "https://github.com.evil.example/seifsg/ai-software-factory",
                    "https://github.com/seifsg/ai-software-factory-fork", "C:/fixtures/remote.git",
                    "http://github.com/seifsg/ai-software-factory.git", "git://github.com/seifsg/ai-software-factory",
                    "file://github.com/seifsg/ai-software-factory", "github.com/seifsg/ai-software-factory"):
            self.assertFalse(release.factory_origin(url), url)

    def test_saved_safe_runs_resume_on_the_same_major_only(self):
        major = int(VERSION.split(".")[0])
        self.assertTrue(resumable(VERSION))
        self.assertTrue(resumable("0.1.0") if major == 1 else True)  # the label every bundle carried before 1.0.0
        self.assertFalse(resumable(f"{major + 1}.0.0"))
        self.assertFalse(resumable(f"{major}.{int(VERSION.split('.')[1]) + 1}.0"))  # never an older bundle
        for broken in (None, 3, "1.0", "1.0.0-rc.1"):
            self.assertFalse(resumable(broken))


class ChangelogTests(unittest.TestCase):
    def test_keep_a_changelog_order_dates_and_links(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        headings = HEADING.findall(text)
        self.assertEqual(headings[0], ("Unreleased", ""))
        versions = [tuple(map(int, name.split("."))) for name, _ in headings[1:]]
        self.assertEqual(versions, sorted(set(versions), reverse=True))  # descending, no duplicates
        for name, day in headings[1:]:
            with self.subTest(version=name):
                self.assertEqual(date.fromisoformat(day).isoformat(), day)
                self.assertRegex(text, rf"(?m)^\[{re.escape(name)}\]: https://github\.com/\S+v{re.escape(name)}$")
        self.assertRegex(text, rf"(?m)^\[Unreleased\]: https://github\.com/\S+/compare/v{headings[1][0]}\.\.\.HEAD$")
        upgrading = (ROOT / "UPGRADING.md").read_text(encoding="utf-8")
        for name, _ in headings[1:]:
            self.assertRegex(upgrading, rf"(?m)^## {re.escape(name)}$")


class FixtureRepository(unittest.TestCase):
    """A disposable factory-shaped repository with a main branch on a bare origin."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="factory release ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()

    def repository(self, files):
        repo = self.root / "repo"
        for name, text in files.items():
            (repo / name).parent.mkdir(parents=True, exist_ok=True)
            (repo / name).write_bytes(text.encode("utf-8"))
        git(self.root, "init", "-q", "--bare", "origin.git")
        git(repo, "init", "-q")
        git(repo, "remote", "add", "origin", str(self.root / "origin.git"))
        return repo

    @staticmethod
    def commit(repo, message, manifest=True):
        git(repo, "add", "-A")
        if manifest:
            (repo / release.MANIFEST).write_text(json.dumps(release.build_manifest(repo)), encoding="utf-8")
            git(repo, "add", "-A")
        git(repo, "commit", "-qm", message)
        git(repo, "push", "-q", "origin", "HEAD:main")
        git(repo, "fetch", "-q", "origin")


class ManifestTests(FixtureRepository):
    def setUp(self):
        super().setUp()
        self.repo = self.repository({release.VERSION_FILE: "1.0.0\n", "README.md": "readme\n",
                                     "skills/safe-engine/SKILL.md": "launcher\r\n",
                                     "skills/improve-factory/SKILL.md": "maintenance\n",
                                     "skills/.claude-plugin/plugin.json": "{}\n", "safe_engine/x.py": "x = 1\n"})
        self.commit(self.repo, "release")
        self.manifest = release.read_manifest(self.repo)

    def test_a_checkout_names_every_changed_missing_and_extra_file(self):
        self.assertEqual(self.manifest["version"], "1.0.0")
        self.assertNotIn(release.MANIFEST, self.manifest["files"])
        self.assertEqual(self.manifest["files"]["skills/safe-engine/SKILL.md"],
                         hashlib.sha256(b"launcher\n").hexdigest())  # CRLF read as LF
        self.assertEqual(release.verify(self.repo, self.manifest), [])
        (self.repo / "README.md").write_bytes(b"readme\r\n")  # line endings alone change nothing
        self.assertEqual(release.verify(self.repo, self.manifest), [])
        (self.repo / "README.md").write_text("tampered\n", encoding="utf-8")
        (self.repo / "safe_engine/x.py").unlink()
        (self.repo / "safe_engine/new.py").write_text("y = 2\n", encoding="utf-8")
        self.assertEqual(release.verify(self.repo, self.manifest),
                         ["changed: README.md", "missing: safe_engine/x.py", "extra: safe_engine/new.py"])

    def test_an_installed_copy_checks_only_its_entries(self):
        skills = self.root / "home" / ".agents" / "skills"
        for name in ("safe-engine", "improve-factory"):
            shutil.copytree(self.repo / "skills" / name, skills / name)
        installer = importlib.util.spec_from_file_location("fast_install", GATE.with_name("fast_install.py"))
        loaded = importlib.util.module_from_spec(installer)
        installer.loader.exec_module(loaded)
        self.assertEqual(loaded.MARKER, release.MARKER)  # the installer's ownership mark is never a factory file
        (skills / "safe-engine" / release.MARKER).write_text("ours\n", encoding="utf-8")
        (skills / "safe-engine" / "__pycache__").mkdir()
        (skills / "safe-engine" / "__pycache__" / "x.pyc").write_bytes(b"cache")
        (skills / "another-skill").mkdir()
        (skills / "another-skill" / "SKILL.md").write_text("not ours\n", encoding="utf-8")
        self.assertEqual(release.verify(skills, self.manifest), [])  # no .claude-plugin here: not expected
        plugin = self.root / "plugin"
        shutil.copytree(self.repo / "skills", plugin)
        self.assertEqual(release.verify(plugin, self.manifest), [])
        (plugin / ".claude-plugin" / "plugin.json").write_text('{"hooks": "changed"}\n', encoding="utf-8")
        shutil.rmtree(skills / "improve-factory")
        self.assertEqual(release.verify(plugin, self.manifest), ["changed: skills/.claude-plugin/plugin.json"])
        self.assertEqual(release.verify(skills, self.manifest), ["missing: skills/improve-factory/SKILL.md"])

    def test_a_tampered_manifest_is_refused(self):
        path = self.repo / release.MANIFEST
        for change in ({"files": {**self.manifest["files"], "README.md": "0" * 64}},
                       {"files": {**self.manifest["files"], "../outside": "0" * 64}}, {"version": 1}):
            with self.subTest(change=list(change)):
                path.write_text(json.dumps({**self.manifest, **change}), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "malformed or its tree digest"):
                    release.read_manifest(self.repo)
        path.unlink()
        with self.assertRaisesRegex(RuntimeError, "No readable release manifest"):
            release.read_manifest(self.repo)

    def test_the_release_check_needs_main_the_tag_version_and_matching_files(self):
        release.check_release(self.repo, "v1.0.0")
        with self.assertRaisesRegex(RuntimeError, "version differs from v1.1.0"):
            release.check_release(self.repo, "v1.1.0")
        git(self.repo, "checkout", "-q", "-b", "side")
        (self.repo / "side.md").write_text("side\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "side")
        with self.assertRaisesRegex(RuntimeError, "v1.0.0 is not on main"):
            release.check_release(self.repo, "v1.0.0")

    def test_release_tags_sort_newest_first_and_peel(self):
        listing = "\n".join([f"{'1' * 40}\trefs/tags/v1.0.0", f"{'2' * 40}\trefs/tags/v1.0.0^{{}}",
                             f"{'3' * 40}\trefs/tags/v1.10.0", f"{'4' * 40}\trefs/tags/history-archive",
                             f"{'5' * 40}\trefs/tags/v01.0.0", f"{'6' * 40}\trefs/tags/v1.2.0-rc.1",
                             f"{'7' * 40} refs/tags/v1.2.0", f"{'8' * 40}\trefs/heads/v9.0.0", "garbage"])
        self.assertEqual(release.releases(listing), [("v1.10.0", "3" * 40), ("v1.2.0", "7" * 40),
                                                     ("v1.0.0", "2" * 40)])


class ReleaseScriptTests(FixtureRepository):
    """scripts/release.py in a copy of this checkout: cut a release, then check its tag as the workflow does."""

    def setUp(self):
        super().setUp()
        names = git(ROOT, "ls-files", "-co", "--exclude-standard").splitlines()
        self.repo = self.repository({name: (ROOT / name).read_text(encoding="utf-8") for name in names
                                     if (ROOT / name).is_file()})
        self.commit(self.repo, "baseline")
        self.script = self.repo / "scripts" / "release.py"

    def edit(self, name, old, new):
        path = self.repo / name
        path.write_text(path.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")

    def test_cut_then_check(self):
        major, minor, _ = map(int, VERSION.split("."))
        new = f"{major}.{minor + 1}.0"
        refused = run(self.script, "cut", new, cwd=self.repo)
        self.assertIn(f"Write the upgrade steps under '## {new}'", refused.stderr)
        self.edit("UPGRADING.md", f"## {VERSION}\n", f"## {new}\n\n- Nothing to do.\n\n## {VERSION}\n")
        self.edit("CHANGELOG.md", "## [Unreleased]\n", "## [Unreleased]\n\n### Fixed\n\n- A fixture fix.\n")
        self.assertIn("Commit or remove local changes", run(self.script, "cut", new, cwd=self.repo).stderr)
        git(self.repo, "commit", "-qam", "notes")
        self.assertIn("older than the current version", run(self.script, "cut", "0.0.1", cwd=self.repo).stderr)
        cut = run(self.script, "cut", new, cwd=self.repo)
        self.assertEqual(cut.returncode, 0, cut.stderr)
        self.assertEqual((self.repo / release.VERSION_FILE).read_text(encoding="utf-8").strip(), new)
        plugin = json.loads((self.repo / "skills/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
        entry = json.loads((self.repo / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))["plugins"][0]
        self.assertEqual((plugin["version"], entry["source"]["ref"]), (new, f"v{new}"))
        changelog = (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## [Unreleased]\n\n## [{new}] - {date.today().isoformat()}\n\n### Fixed\n\n- A fixture fix.",
                      changelog)
        self.assertIn(f"[Unreleased]: {release.REPOSITORY.removesuffix('.git')}/compare/v{new}...HEAD", changelog)
        self.assertIn(f"[{new}]: {release.REPOSITORY.removesuffix('.git')}/compare/v{VERSION}...v{new}", changelog)
        self.commit(self.repo, "release", manifest=False)
        self.assertEqual(release.verify(self.repo, release.read_manifest(self.repo)), [])
        git(self.repo, "tag", "-a", f"v{new}", "-m", new)
        git(self.repo, "push", "-q", "origin", f"v{new}")
        out = self.root / "dist"
        checked = run(self.script, "check", f"v{new}", "--out", out, cwd=self.repo)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        sums = (out / "SHA256SUMS").read_bytes()
        manifest = json.loads((out / "release-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(sums).hexdigest(), manifest["tree"])
        self.assertIn("- A fixture fix.", (out / "notes.md").read_text(encoding="utf-8"))
        temp = {name: str(self.root) for name in ("TMP", "TEMP", "TMPDIR")}  # the default folder lands in the fixture
        default = run(self.script, "check", f"v{new}", cwd=self.repo, env=temp)  # again, no --out: still verifies
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertNotIn(str(self.repo), default.stdout.rsplit("release files in ", 1)[1])
        inside = run(self.script, "check", f"v{new}", "--out", self.repo / "dist", cwd=self.repo)
        self.assertIn("is inside the checkout", inside.stderr)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        self.assertIn("is published; never re-publish", run(self.script, "cut", new, cwd=self.repo).stderr)
        for tag, reason in ((f"v{VERSION}", "version differs"), ("1.0", "no release tag")):
            self.assertIn(reason, run(self.script, "check", tag, "--out", out, cwd=self.repo).stderr)


class PublishTests(unittest.TestCase):
    """release.py publish: the check, the suite, then the GitHub release; no CI, nothing after a failed step."""

    def setUp(self):
        spec = importlib.util.spec_from_file_location("release_script", ROOT / "scripts/release.py")
        self.script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.script)
        self.calls = []
        self.script.check = lambda tag, out: self.calls.append(("check", tag))

    def publish(self, codes):
        codes = iter(codes)
        self.script.subprocess = mock.Mock(run=lambda cmd, cwd: (self.calls.append(tuple(cmd[:3])),
                                                                 mock.Mock(returncode=next(codes)))[1])
        self.script.publish("v9.9.9")

    def test_check_then_suite_then_release(self):
        self.publish([0, 0])
        self.assertEqual([call[:2] for call in self.calls],
                         [("check", "v9.9.9"), (sys.executable, str(ROOT / "tests/run.py")), ("gh", "release")])

    def test_a_red_suite_publishes_nothing(self):
        with self.assertRaisesRegex(RuntimeError, "failed; nothing published"):
            self.publish([1])
        self.assertNotIn("gh", [call[0] for call in self.calls])


class GateTests(unittest.TestCase):
    """`fast_gate.py version`, `verify` and the card line, in an isolated gate home."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="factory gate version ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.env = {"SAFE_ENGINE_HOME": str(self.root / "gate")}
        (self.root / "gate").mkdir()

    def test_version_names_version_commit_channel_route_and_digest(self):
        lines = run(GATE, "version", env=self.env).stdout.splitlines()
        self.assertEqual([line.split(":")[0] for line in lines[1:5]], ["Commit", "Channel", "Route", "Digest"])
        self.assertEqual((lines[2], lines[3]), ("Channel: stable", f"Route: checkout {ROOT}"))
        self.assertRegex(lines[4], rf"^Digest: sha256:[0-9a-f]{{64}} \({re.escape(VERSION)} manifest\): ")
        (self.root / "gate" / "install.json").write_text('{"channel": "edge", "auto": false}', encoding="utf-8")
        (self.root / "gate" / "update-notice.txt").write_text("Factory updated from 1.0.0 to 1.1.0.\n")
        shown = run(GATE, "version", env=self.env).stdout
        self.assertIn("Channel: edge (auto-update off)", shown)
        self.assertTrue(shown.rstrip().endswith("Factory updated from 1.0.0 to 1.1.0."))
        self.assertNotIn("Factory updated", run(GATE, "version", env=self.env).stdout)  # once
        plugin = self.root / "plugin"
        shutil.copytree(ROOT / "skills", plugin, ignore=shutil.ignore_patterns("__pycache__"))
        copied = run(plugin / "safe-engine/scripts/fast_gate.py", "version", env=self.env).stdout.splitlines()
        self.assertEqual(copied[3], f"Route: Claude Code plugin {plugin}")
        self.assertEqual(copied[1], f"Commit: the commit of tag v{VERSION} (no Git here)")
        shutil.rmtree(plugin / ".claude-plugin")  # a plain copy names no tag it cannot prove
        plain = run(plugin / "safe-engine/scripts/fast_gate.py", "version", env=self.env).stdout.splitlines()
        self.assertEqual((plain[1], plain[3]), ("Commit: unknown (no Git here)", f"Route: copy {plugin}"))

    def test_verify_exits_nonzero_and_names_each_difference(self):
        plugin = self.root / "plugin"
        shutil.copytree(ROOT / "skills", plugin, ignore=shutil.ignore_patterns("__pycache__"))
        clean = run(GATE, "verify", "--path", plugin, env=self.env)
        problems = [line for line in clean.stdout.splitlines()[:-1]]
        (plugin / "safe-engine" / "SKILL.md").write_text("tampered\n", encoding="utf-8")
        dirty = run(GATE, "verify", "--path", plugin, env=self.env)
        self.assertEqual(dirty.returncode, 1)
        self.assertIn("changed: skills/safe-engine/SKILL.md", dirty.stdout)
        self.assertEqual(clean.returncode, 1 if problems else 0)
        self.assertIn("No readable release manifest", run(GATE, "verify", "--path", self.root, env=self.env).stderr)

    def test_start_and_status_cards_show_the_version(self):
        project = self.root / "project"
        project.mkdir()
        git(project, "init", "-q")
        bundle = {"version": 1, "bundle_root": str(ROOT), "revision": "0" * 40}
        (project / ".factory").mkdir()
        (project / ".factory" / "entry-bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
        (project / "request.md").write_text("Fix one thing.\n", encoding="utf-8")
        start = run(GATE, "start", "--project", project, "--key", "card", "--kind", "change",
                    "--request-file", project / "request.md", env=self.env)
        line = f"Version: {VERSION} (stable); run bundle {VERSION}"
        self.assertIn(line, start.stdout, start.stderr)
        self.assertIn(line, run(GATE, "status", "--project", project, env=self.env).stdout)
        run(GATE, "close", "--project", project, "--abandon", "test done", env=self.env)


if __name__ == "__main__":
    unittest.main()
