"""Portable installation boundaries, using real disposable Git repositories."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/improve-factory/scripts/resolve_bundle.py"
SPEC = importlib.util.spec_from_file_location("factory_distribution", SCRIPT)
resolver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(resolver)


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="factory distribution ")
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "source bundle"
        self.source.mkdir()
        self.git("init", "-q", cwd=self.source)
        self.git("remote", "add", "origin", resolver.REPOSITORY, cwd=self.source)
        for name in resolver.REQUIRED:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")
        self.git("add", "--", *resolver.REQUIRED, cwd=self.source)
        self.git("-c", "user.name=Distribution Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "fixture", cwd=self.source)
        self.revision = self.git("rev-parse", "HEAD", cwd=self.source)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def git(*args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                              text=True, encoding="utf-8").stdout.strip()

    def test_explicit_bundle_is_offline_read_only_and_reports_dirty_inputs(self):
        path = self.source / "AGENTS.md"
        path.write_text("local change\n", encoding="utf-8")
        untracked = self.source / "in-progress.txt"
        untracked.write_text("preserve me\n", encoding="utf-8")
        before = self.git("status", "--porcelain", cwd=self.source)
        process = subprocess.run([sys.executable, str(SCRIPT), "--bundle", str(self.source)],
                                 check=True, capture_output=True, text=True)
        result = json.loads(process.stdout)
        self.assertEqual(result["revision"], self.revision)
        self.assertTrue(result["dirty"])
        self.assertEqual(result["bundle_root"], str(self.source))
        self.assertEqual(self.git("status", "--porcelain", cwd=self.source), before)
        self.assertEqual(untracked.read_text(), "preserve me\n")
        # The origin is real GitHub, but the command only inspects the local checkout.

    def test_subdirectory_wrong_origin_and_missing_dependency_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "checkout root"):
            resolver.inspect_bundle(self.source / ".agents")
        self.git("remote", "set-url", "origin", "https://example.invalid/other.git", cwd=self.source)
        with self.assertRaisesRegex(RuntimeError, "origin"):
            resolver.inspect_bundle(self.source)
        self.git("remote", "set-url", "origin", resolver.REPOSITORY, cwd=self.source)
        (self.source / resolver.REQUIRED[-1]).unlink()
        with self.assertRaisesRegex(RuntimeError, "Incomplete"):
            resolver.inspect_bundle(self.source)

    def test_cached_bundle_must_match_revision_and_be_clean(self):
        cache = self.root / "cache"
        cache.mkdir()
        destination = cache / self.revision
        self.source.rename(destination)
        result = resolver.resolve_bundle(cache, self.revision)
        self.assertEqual(result["revision"], self.revision)
        with self.assertRaisesRegex(RuntimeError, "requested commit"):
            resolver.inspect_bundle(destination, expected="0" * 40)
        (destination / "AGENTS.md").write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "local changes"):
            resolver.resolve_bundle(cache, self.revision)
        self.assertEqual((destination / "AGENTS.md").read_text(), "changed\n")

    def test_download_detaches_and_reuses_one_resolved_commit(self):
        # Only the remote transport is substituted; clone/checkout/validation are real Git.
        real_git = resolver.git
        network = []

        def local_transport(*args, cwd=None):
            if args[0] == "ls-remote":
                network.append("resolve")
                return f"{self.revision}\trefs/heads/{resolver.DEFAULT_REF}"
            if args[0] == "clone":
                network.append("clone")
                result = real_git("clone", "--no-checkout", "--", str(self.source), args[-1])
                real_git("remote", "set-url", "origin", resolver.REPOSITORY, cwd=args[-1])
                return result
            return real_git(*args, cwd=cwd)

        cache = self.root / "download cache"
        with patch.object(resolver, "git", side_effect=local_transport):
            result = resolver.resolve_bundle(cache, resolver.DEFAULT_REF)
            again = resolver.resolve_bundle(cache, self.revision)
        self.assertEqual(result, again)
        self.assertEqual(network, ["resolve", "clone"])
        self.assertEqual(self.git("rev-parse", "--abbrev-ref", "HEAD", cwd=result["bundle_root"]), "HEAD")
        self.assertFalse(result["dirty"])

    def test_bad_ref_or_remote_response_cannot_create_cache_path(self):
        cache = self.root / "not created"
        with self.assertRaisesRegex(RuntimeError, "branch name"):
            resolver.resolve_bundle(cache, "--upload-pack=other")
        for response in ("../../outside\trefs/heads/main", f"{self.revision}\trefs/heads/other"):
            with patch.object(resolver, "git", return_value=response):
                with self.assertRaisesRegex(RuntimeError, "exact remote branch"):
                    resolver.resolve_bundle(cache, "main")
        self.assertFalse(cache.exists())

    def test_failed_acquisition_preserves_diagnostic_directory(self):
        cache = self.root / "partial cache"
        with patch.object(resolver, "git", side_effect=RuntimeError("transport unavailable")):
            with self.assertRaisesRegex(RuntimeError, "partial checkout preserved"):
                resolver.resolve_bundle(cache, self.revision)
        pending = list(cache.iterdir())
        self.assertEqual(len(pending), 1)
        self.assertIn(".pending-", pending[0].name)

    def add_contract(self, required=None):
        path = self.source / 'safe_engine/bundle-inputs.json'
        path.write_text(json.dumps({'version': 1, 'required_files': required or
            ['docs/safe-engine-decisions.md', 'docs/safe-engine-fast-delivery.md'],
            'source_trees': ['safe_engine', 'docs', '.agents/skills']}), encoding='utf-8')
        cadence = self.source / 'docs/safe-engine-fast-delivery.md'
        cadence.write_text('Required cadence fixture.\n', encoding='utf-8')
        return path

    def test_current_contract_requires_all_declared_guidance(self):
        self.add_contract()
        self.assertTrue(resolver.inspect_bundle(self.source)['dirty'])
        (self.source / 'docs/safe-engine-fast-delivery.md').unlink()
        with self.assertRaisesRegex(RuntimeError, 'Incomplete.*fast-delivery'):
            resolver.inspect_bundle(self.source)

    def test_deleted_committed_contract_cannot_fall_back_to_legacy(self):
        path = self.add_contract()
        self.git('add', '--', str(path), cwd=self.source)
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'new input contract', cwd=self.source)
        self.git('rm', '-f', '--', str(path), cwd=self.source)
        with self.assertRaisesRegex(RuntimeError, 'Incomplete.*bundle-inputs'):
            resolver.inspect_bundle(self.source)

    def test_unsafe_current_contract_is_rejected_before_outside_read(self):
        self.add_contract(required=['../outside-file'])
        with self.assertRaisesRegex(RuntimeError, 'Invalid required_files'):
            resolver.inspect_bundle(self.source)


if __name__ == "__main__":
    unittest.main()
