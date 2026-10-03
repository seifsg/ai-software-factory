"""Resolve a complete, revision-pinned factory; never mutate an existing app/bundle."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile


REPOSITORY = "https://github.com/seifsg/ai-software-factory.git"
DEFAULT_REF = "main"
ENTRYPOINTS = ("safe-engine", "improve-factory")
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


def inspect_bundle(root, expected=None, clean=False, entrypoint="improve-factory"):
    if entrypoint not in ENTRYPOINTS:
        raise RuntimeError("Unknown factory entrypoint")
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
    required = list(REQUIRED)
    contract_name = "safe_engine/bundle-inputs.json"
    contract_path = root / contract_name
    tracked_contract = git("ls-tree", "--name-only", "HEAD", "--", contract_name, cwd=root)
    if contract_path.exists() or tracked_contract:
        if contract_path.is_symlink() or not contract_path.is_file():
            raise RuntimeError("Incomplete factory bundle: " + contract_name)
        try:
            contract = json.loads(contract_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as error:
            raise RuntimeError(f"Invalid factory input contract: {error}") from error
        if (not isinstance(contract, dict) or contract.get("version") != 1
                or set(contract) != {"version", "required_files", "source_trees"}):
            raise RuntimeError("Invalid factory input contract")
        for key in ("required_files", "source_trees"):
            names = contract[key]
            if (not isinstance(names, list) or not names
                    or any(not isinstance(name, str) or not name or "\\" in name or ":" in name
                           or any(part in ("", ".", "..") for part in name.split("/")) for name in names)
                    or len({name.casefold() for name in names}) != len(names)):
                raise RuntimeError(f"Invalid {key} in factory input contract")
        for name in contract["source_trees"]:
            folder = root / name
            if folder.is_symlink() or not folder.is_dir() or not folder.resolve().is_relative_to(root):
                raise RuntimeError("Incomplete factory source area: " + name)
        required += [contract_name, *contract["required_files"]]
    missing = [name for name in required if not (root / name).is_file() or (root / name).is_symlink()]
    if missing:
        raise RuntimeError("Incomplete factory bundle: " + ", ".join(missing))
    if any(not (root / name).resolve().is_relative_to(root) for name in required):
        raise RuntimeError("Required factory file resolves outside the bundle")
    status = git("status", "--porcelain", "--untracked-files=all", cwd=root)
    if clean and status:
        raise RuntimeError("Cached bundle has local changes; preserve it and use a fresh cache directory")
    return {"bundle_root": str(root), "revision": revision, "dirty": bool(status),
            "git_status": status, "source_url": remote,
            "entrypoint": str(root / f".agents/skills/{entrypoint}/SKILL.md")}


def resolve_bundle(cache, ref, entrypoint="improve-factory"):
    if entrypoint not in ENTRYPOINTS:
        raise RuntimeError("Unknown factory entrypoint")
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
        return inspect_bundle(destination, expected=revision, clean=True, entrypoint=entrypoint)
    pending = Path(tempfile.mkdtemp(prefix=f"{revision}.pending-", dir=cache))
    try:
        git("clone", "--no-checkout", "--", REPOSITORY, str(pending))
        git("checkout", "--detach", revision, cwd=pending)
        inspect_bundle(pending, expected=revision, clean=True, entrypoint=entrypoint)
        try:
            pending.rename(destination)
        except OSError:
            if not destination.exists():
                raise
            # Another installer may have completed this revision; validate it below.
        result = inspect_bundle(destination, expected=revision, clean=True, entrypoint=entrypoint)
        if pending.exists():
            result["retained_temporary_checkout"] = str(pending)
        return result
    except Exception as error:
        raise RuntimeError(f"Bundle resolution failed; partial checkout preserved at {pending}: {error}") from error


def select_for_project(project, bundle, ref, cache, entrypoint):
    """Record a selection once; resume never resolves a newer remote branch."""
    project = Path(project).expanduser().resolve()
    if not project.is_dir():
        raise RuntimeError("Create or locate the target project directory first")
    directory = project / ".factory"
    receipt = directory / "entry-bundle.json"
    if directory.is_symlink() or receipt.is_symlink():
        raise RuntimeError("Factory selection paths must not be symlinks")
    if receipt.exists():
        try:
            saved = json.loads(receipt.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise RuntimeError(f"Cannot read existing bundle selection: {error}") from error
        if (not isinstance(saved, dict) or saved.get("version") != 1
                or not isinstance(saved.get("bundle_root"), str)
                or not Path(saved["bundle_root"]).is_absolute()
                or not isinstance(saved.get("revision"), str)
                or not re.fullmatch(r"[0-9a-f]{40}", saved["revision"])):
            raise RuntimeError("Invalid bundle selection; preserve it and establish the original identity")
        if ref is not None or (bundle and Path(bundle).expanduser().resolve() != Path(saved["bundle_root"]).resolve()):
            raise RuntimeError("An existing selection cannot be upgraded here; use improve-factory")
        result = inspect_bundle(saved["bundle_root"], expected=saved["revision"], entrypoint=entrypoint)
        result["selection_record"] = str(receipt)
        return result
    if (directory / "state.json").exists() and not bundle:
        raise RuntimeError("Existing run has no bundle path record; establish its original bundle and use --bundle")
    result = (inspect_bundle(bundle, entrypoint=entrypoint) if bundle
              else resolve_bundle(cache, ref or DEFAULT_REF, entrypoint=entrypoint))
    directory.mkdir(exist_ok=True)
    # Exclusive creation protects a concurrent selection; never overwrite runtime evidence.
    try:
        with receipt.open("x", encoding="utf-8") as output:
            json.dump({"version": 1, "bundle_root": result["bundle_root"],
                       "revision": result["revision"]}, output, indent=2)
            output.write("\n")
    except FileExistsError as error:
        raise RuntimeError("Another entry selected a bundle; inspect its record before continuing") from error
    result["selection_record"] = str(receipt)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--bundle", type=Path, help="Inspect the exact existing checkout; no fetch/update")
    choice.add_argument("--ref", help="Branch or full SHA for a new run/case; defaults to main")
    parser.add_argument("--cache-dir", type=Path, default=Path.home() / ".safe-engine" / "bundles")
    parser.add_argument("--project", type=Path, help="Remember this project's selection; reuse it offline on resume")
    installed_name = Path(__file__).resolve().parent.parent.name
    parser.add_argument("--entrypoint", choices=ENTRYPOINTS,
                        default=installed_name if installed_name in ENTRYPOINTS else "safe-engine")
    args = parser.parse_args()
    try:
        if args.project:
            result = select_for_project(args.project, args.bundle, args.ref, args.cache_dir, args.entrypoint)
        else:
            result = (inspect_bundle(args.bundle, entrypoint=args.entrypoint) if args.bundle else
                      resolve_bundle(args.cache_dir, args.ref or DEFAULT_REF, entrypoint=args.entrypoint))
        print(json.dumps(result, indent=2))
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"Factory unavailable: {error}\nUse existing authorized Git credentials; do not paste tokens into chat.\n")


if __name__ == "__main__":
    main()
