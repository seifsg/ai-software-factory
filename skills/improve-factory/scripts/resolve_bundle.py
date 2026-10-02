"""Resolve a complete, revision-pinned factory; never mutate an existing app/bundle."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile


REPOSITORY = "https://github.com/seifsg/ai-software-factory.git"
DEFAULT_REF = "docs/skill-lifecycle-map"
SKILLS = ("improve-factory", "safe-engine", "analyze-start", "get-ready-to-code",
          "deep-review", "change-guard", "compliance-check", "how-to-make-a-pr",
          "how-to-review-a-pr", "research-market")
REQUIRED = ["AGENTS.md", "docs/safe-engine-decisions.md", "docs/pr-workflow.md",
            "docs/pilot-usage.md", "docs/skill-provenance.md", "safe_engine/__main__.py",
            ".agents/skills/safe-engine/references/session-contract.md",
            ".agents/skills/improve-factory/references/live-session.md"]
REQUIRED += [f".agents/skills/{name}/SKILL.md" for name in SKILLS]


def git(*args, cwd=None):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                            text=True, encoding="utf-8", timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Git command failed")
    return result.stdout.strip()


def inspect_bundle(root, expected=None, clean=False):
    root = Path(root).expanduser().resolve()
    actual_root = Path(git("rev-parse", "--show-toplevel", cwd=root)).resolve()
    if root != actual_root:
        raise RuntimeError("Bundle path must be the Git checkout root, not a subdirectory")
    remote = git("remote", "get-url", "origin", cwd=root)
    allowed = {REPOSITORY, REPOSITORY.removesuffix(".git"),
               "git@github.com:seifsg/ai-software-factory.git",
               "ssh://git@github.com/seifsg/ai-software-factory.git"}
    if remote not in allowed:
        raise RuntimeError("Bundle origin does not identify seifsg/ai-software-factory")
    revision = git("rev-parse", "HEAD", cwd=root)
    if expected and revision != expected:
        raise RuntimeError("Cached checkout does not match the requested commit")
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing:
        raise RuntimeError("Incomplete factory bundle: " + ", ".join(missing))
    if any(not (root / name).resolve().is_relative_to(root) for name in REQUIRED):
        raise RuntimeError("Required factory file resolves outside the bundle")
    status = git("status", "--porcelain", "--untracked-files=all", cwd=root)
    if clean and status:
        raise RuntimeError("Cached bundle has local changes; preserve it and use a fresh cache directory")
    return {"bundle_root": str(root), "revision": revision, "dirty": bool(status),
            "git_status": status, "source_url": remote,
            "entrypoint": str(root / ".agents/skills/improve-factory/SKILL.md")}


def resolve_bundle(cache, ref):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", ref):
        raise RuntimeError("Use a branch name or full 40-character commit SHA")
    if re.fullmatch(r"[0-9a-fA-F]{40}", ref):
        revision = ref.lower()
    else:
        line = git("ls-remote", "--exit-code", REPOSITORY, f"refs/heads/{ref}")
        fields = line.split()
        if (len(fields) != 2 or fields[1] != f"refs/heads/{ref}"
                or not re.fullmatch(r"[0-9a-f]{40}", fields[0])):
            raise RuntimeError("Could not resolve one exact remote branch")
        revision = fields[0]
    cache = Path(cache).expanduser().resolve()
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / revision
    if destination.exists():
        return inspect_bundle(destination, expected=revision, clean=True)
    pending = Path(tempfile.mkdtemp(prefix=f"{revision}.pending-", dir=cache))
    try:
        git("clone", "--no-checkout", "--", REPOSITORY, str(pending))
        git("checkout", "--detach", revision, cwd=pending)
        inspect_bundle(pending, expected=revision, clean=True)
        try:
            pending.rename(destination)
        except OSError:
            if not destination.exists():
                raise
            # Another installer may have completed this revision; validate it below.
        result = inspect_bundle(destination, expected=revision, clean=True)
        if pending.exists():
            result["retained_temporary_checkout"] = str(pending)
        return result
    except Exception as error:
        raise RuntimeError(f"Bundle resolution failed; partial checkout preserved at {pending}: {error}") from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--bundle", type=Path, help="Inspect the exact existing checkout; no fetch/update")
    choice.add_argument("--ref", default=DEFAULT_REF, help="Branch or full SHA for a new maintenance case")
    parser.add_argument("--cache-dir", type=Path, default=Path.home() / ".safe-engine" / "bundles")
    args = parser.parse_args()
    try:
        result = inspect_bundle(args.bundle) if args.bundle else resolve_bundle(args.cache_dir, args.ref)
        print(json.dumps(result, indent=2))
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"Factory unavailable: {error}\nUse existing authorized Git credentials; do not paste tokens into chat.\n")


if __name__ == "__main__":
    main()
