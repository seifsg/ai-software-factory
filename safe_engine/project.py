"""Discover projects and bind evidence to explicit inputs."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys


REPARSE = stat.FILE_ATTRIBUTE_REPARSE_POINT
WORKERS = min(32, (os.cpu_count() or 1) * 4)
_scope = None  # Per-command scan memo; None outside snapshot().


class EngineError(Exception):
    """An actionable workflow or configuration problem."""


@contextmanager
def snapshot():
    """Share one project/bundle scan per command; nested scopes reuse it."""
    global _scope
    if _scope is not None:
        yield
        return
    _scope = {}
    try:
        yield
    finally:
        _scope = None


def cached(key, compute):
    if _scope is None:
        return compute()
    if key not in _scope:
        _scope[key] = compute()
    return _scope[key]


def rescan():
    """Forget scans after a check or reviewer process may have changed files."""
    if _scope is not None:
        _scope.clear()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def sha256_file(path):
    """Chunked SHA-256; Python 3.9 has no hashlib.file_digest. 64 KiB: larger reads cost an allocation per file."""
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 16), b""):
            value.update(block)
    return value.hexdigest()


def file_hash(path):
    if path.is_symlink():
        raise EngineError(f"Symlink inputs are unsupported in this pilot: {path}")
    if not path.is_file():
        raise EngineError(f"Required input is not a file: {path}")
    return sha256_file(path)


def git(project, *args):
    try:
        result = subprocess.run(["git", "-C", str(project), *args], capture_output=True, timeout=30)
    except subprocess.TimeoutExpired as error:
        raise EngineError(f"Git timed out after 30s: git {' '.join(args[:2])}") from error
    if result.returncode:
        raise EngineError(result.stderr.decode(errors="replace").strip() or "Git command failed")
    return result.stdout.decode("utf-8", errors="surrogateescape").rstrip("\r\n")


def git_dirs(path):
    """Top-level and common Git directories from one rev-parse."""
    path = Path(path)

    def read():
        lines = git(path, "rev-parse", "--show-toplevel", "--git-common-dir").splitlines()
        if len(lines) != 2:
            raise EngineError("Unexpected git rev-parse output")
        return Path(lines[0]).resolve(), Path(os.path.abspath(path / lines[1]))
    return cached(("git-dirs", str(path)), read)


@lru_cache(maxsize=None)
def bundle_revision(bundle):
    """Informational bundle HEAD, read once per process."""
    return git(bundle, "rev-parse", "HEAD")


def project_root(path):
    path = Path(path).resolve()
    root = git_dirs(path)[0]
    if root != path:
        raise EngineError(f"Use the project root: {root}")
    return root


def inside(project, value):
    path = project / value
    if path.is_symlink() or not path.resolve().is_relative_to(project):
        raise EngineError(f"Path must remain within the project: {value}")
    return path


def aliased(info):
    return stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE


def escapes(root, name):
    return not Path(root, name).resolve().is_relative_to(root)


def check_directories(root, names):
    """lstat each ancestor directory once; an alias must still resolve inside root."""
    seen = set()
    for name in names:
        parts = name.split("/")[:-1]
        for depth in range(1, len(parts) + 1):
            relative = "/".join(parts[:depth])
            if relative in seen:
                continue
            seen.add(relative)
            try:
                info = os.lstat(os.path.join(root, relative))
            except (FileNotFoundError, NotADirectoryError):
                break
            if aliased(info) and escapes(root, relative):
                raise EngineError(f"Path must remain within the project: {relative}")


def hash_entry(root, name, missing):
    """One lstat + one open; rejects what inside() and file_hash() reject."""
    path = os.path.join(root, name)
    try:
        info = os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):
        if missing is None:
            raise EngineError(f"Required input is not a file: {path}") from None
        return missing
    if stat.S_ISLNK(info.st_mode) or (aliased(info) and escapes(root, name)):
        raise EngineError(f"Path must remain within the project: {name}")
    if not stat.S_ISREG(info.st_mode):
        raise EngineError(f"Required input is not a file: {path}")
    return sha256_file(path)


def scan_hashes(root, names, missing="DELETED"):
    """Hash root-relative files in parallel; missing=None makes absence an error."""
    root, names = Path(root), sorted(set(names))
    check_directories(root, names)
    pool = ThreadPoolExecutor(WORKERS)
    try:
        return dict(zip(names, pool.map(lambda name: hash_entry(root, name, missing), names)))
    finally:
        pool.shutdown(cancel_futures=True)


def reject_path_aliases(path, root):
    """Reject symlinks/reparse points before following a generated-state path."""
    path, root = Path(path).absolute(), Path(root).absolute()
    if not path.is_relative_to(root) or ".." in path.parts:
        raise EngineError(f"Generated state must remain within {root}: {path}")
    current = root
    for part in (None, *path.relative_to(root).parts):
        if part is not None:
            current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise EngineError(f"Generated state must not use symlinks or reparse points: {current}")


def relative_input_path(value, *, allow_factory=False):
    """Accept one portable project-relative file/directory name, never a pattern."""
    if (not isinstance(value, str) or not value or "\\" in value
            or any(char in value for char in ':*?[]\x00')
            or any(part in ("", ".", "..") for part in value.split("/"))
            or any(part.casefold() == ".git" for part in value.split("/"))
            or (not allow_factory and value.split("/")[0].casefold() == ".factory")):
        raise EngineError(f"Expected a literal relative project path: {value!r}")
    return value


def validate_profile(profile, draft=False):
    if not isinstance(profile, dict) or profile.get("version") not in (1, 2):
        raise EngineError("Profile must be an object with version 1 or 2")
    version_two = profile["version"] == 2
    if profile.get("interface") not in ("web", "cli", "library", "desktop", "mobile", "game", "service"):
        raise EngineError("Profile interface must be web, cli, library, desktop, mobile, game, or service")
    if "reuse_unchanged_checks" in profile and type(profile["reuse_unchanged_checks"]) is not bool:
        raise EngineError("reuse_unchanged_checks must be an explicit boolean")
    if "parallel_checks" in profile and type(profile["parallel_checks"]) is not bool:
        raise EngineError("parallel_checks must be an explicit boolean")
    if "reuse_record_evidence" in profile:
        if not version_two or type(profile["reuse_record_evidence"]) is not bool:
            raise EngineError("reuse_record_evidence requires a version 2 profile and explicit boolean")
    checks = profile.get("checks")
    if not isinstance(checks, list) or (not checks and not version_two):
        raise EngineError("Configure at least one real check in the reviewed profile")
    ids = set()
    outputs = set()
    for check in checks:
        if not isinstance(check, dict):
            raise EngineError("Each check must be an object")
        identifier = check.get("id", "")
        if not isinstance(identifier, str) or not identifier or not identifier.replace("-", "").isalnum():
            raise EngineError("Check IDs must use letters, numbers, and hyphens")
        if identifier.casefold() in ids:
            raise EngineError(f"Duplicate check ID (case-insensitive): {identifier}")
        ids.add(identifier.casefold())
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise EngineError(f"{identifier}: argv must be a nonempty array of strings")
        timeout = check.get("timeout_seconds")
        if type(timeout) is not int or not 1 <= timeout <= 3600:
            raise EngineError(f"{identifier}: specify timeout_seconds between 1 and 3600")
        if check.get("kind") not in ("unit", "integration", "browser", "build", "security",
                                     "interaction", "api", "performance"):
            raise EngineError(f"{identifier}: unsupported check kind")
        artifacts = check.get("artifacts", [])
        if not isinstance(artifacts, list):
            raise EngineError(f"{identifier}: artifacts must be an array of output paths")
        for name in artifacts:
            if (not isinstance(name, str) or not (name.startswith(".factory/outputs/")
                    or re.match(r"^\.factory/runs/[a-z][a-z0-9-]{0,63}/outputs/", name))
                    or any(part in ("", ".", "..") for part in name.split("/"))
                    or "\\" in name or ":" in name or name.casefold() in outputs):
                raise EngineError("Artifact paths must be unique files within the selected run's outputs/")
            outputs.add(name.casefold())
    if not version_two and profile["interface"] == "web" and not any(c["kind"] == "browser" for c in checks):
        raise EngineError("A web profile requires a real browser check")
    if not version_two and profile["interface"] in ("desktop", "mobile", "game") and not any(c["kind"] == "interaction" for c in checks):
        raise EngineError("A desktop, mobile, or game profile requires a real interaction check")
    if not version_two and profile["interface"] == "service" and not any(c["kind"] in ("api", "integration") for c in checks):
        raise EngineError("A service profile requires a real API or integration check")
    for key in ("environment_inputs", "input_files", "protected_paths"):
        if not isinstance(profile.get(key), list) or not all(isinstance(x, str) and x for x in profile[key]):
            raise EngineError(f"{key} must be an explicit array of input names or paths")
    if not profile["protected_paths"] and (not version_two or (checks and not draft)):
        raise EngineError("Declare the acceptance check files in protected_paths")
    if version_two:
        if profile.get("exposure", "local") not in ("local", "public", "production"):
            raise EngineError("exposure must be local, public, or production")
        paths = profile.get("test_paths", [])
        if not isinstance(paths, list):
            raise EngineError("test_paths must be an array of literal file/directory paths")
        seen = set()
        for path in paths:
            relative_input_path(path)
            folded = path.casefold()
            if folded in seen:
                raise EngineError(f"Duplicate test path: {path}")
            seen.add(folded)
        scopes = profile.get("review_scopes", [])
        allowed = {"ui", "assets", "persistence", "research", "seo", "security", "integrations", "release"}
        if (not isinstance(scopes, list) or any(not isinstance(scope, str) or scope not in allowed for scope in scopes)
                or len(scopes) != len(set(scopes))):
            raise EngineError("review_scopes must contain unique supported scope names")
    return profile


def validate_task(task, profile, draft=False):
    if not isinstance(task, dict) or not isinstance(task.get("request"), str) or not task["request"].strip():
        raise EngineError("Task needs a nonempty original request")
    criteria = task.get("acceptance")
    if not isinstance(criteria, list) or not criteria:
        raise EngineError("Task needs explicit acceptance criteria")
    check_ids = {c["id"] for c in profile["checks"]}
    version_two = profile.get("version") == 2
    seen = set()
    for criterion in criteria:
        if not isinstance(criterion, dict):
            raise EngineError("Acceptance criteria must be objects")
        identifier = criterion.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
            raise EngineError("Acceptance IDs must be nonempty and unique")
        seen.add(identifier)
        if not isinstance(criterion.get("text"), str) or not criterion["text"].strip():
            raise EngineError(f"{identifier}: missing acceptance text")
        checks = criterion.get("checks")
        if version_two:
            mode = criterion.get("mode", "automated")
            if mode not in ("manual", "automated", "mixed"):
                raise EngineError(f"{identifier}: mode must be manual, automated, or mixed")
            if not isinstance(checks, list) or not all(isinstance(c, str) and c in check_ids for c in checks):
                raise EngineError(f"{identifier}: checks must reference configured executable checks")
            if len(checks) != len(set(checks)):
                raise EngineError(f"{identifier}: duplicate check references")
            if mode == "manual" and checks:
                raise EngineError(f"{identifier}: manual criteria must have an empty checks array")
            if mode != "manual" and not checks and not draft:
                raise EngineError(f"{identifier}: automated/mixed criteria need executable checks before sealing")
            continue
        if not isinstance(checks, list) or not checks or not all(isinstance(c, str) and c in check_ids for c in checks):
            raise EngineError(f"{identifier}: link to configured executable checks")
    return task


def command_argv(check, project, run_dir):
    return [arg.replace("{python}", sys.executable).replace("{project}", str(project))
            .replace("{run}", str(run_dir)) for arg in check["argv"]]


def protected_inputs(project, profile):
    return {name: file_hash(inside(project, name)) for name in profile["protected_paths"]}


def tree_files(bundle, folder):
    """Guidance/code files under a source area from cached DirEntry data; symlinks are rejected."""
    with os.scandir(folder) as entries:
        for entry in entries:
            if entry.name == "__pycache__":
                continue
            if entry.is_symlink():
                raise EngineError(f"Symlink factory inputs are unsupported: {entry.path}")
            if entry.is_dir():
                yield from tree_files(bundle, entry.path)
            elif entry.is_file() and os.path.splitext(entry.name)[1].lower() in (".py", ".md", ".json", ".yaml", ".yml"):
                yield Path(entry.path).relative_to(bundle).as_posix()


def bundle_input_paths(bundle):
    """The required procedural contract plus added code/guidance in its areas."""
    contract_name = "safe_engine/bundle-inputs.json"
    contract_path = inside(bundle, contract_name)
    # Require the contract even when a directory walk would silently omit it.
    if not contract_path.is_file():
        raise EngineError(f"Required factory input is not a file: {contract_path}")
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise EngineError(f"Cannot read factory input contract: {error}") from error
    version = contract.get("version") if isinstance(contract, dict) else None
    keys = {"version", "required_files", "source_trees"}
    if version == 2:
        keys.add("historical_files")
    if version not in (1, 2) or set(contract) != keys:
        raise EngineError("Unsupported factory input contract")
    for key in ("required_files", "source_trees"):
        names = contract[key]
        if (not isinstance(names, list) or not names
                or any(not isinstance(name, str) or not name or "\\" in name or ":" in name
                       or any(part in ("", ".", "..") for part in name.split("/")) for name in names)
                or len({name.casefold() for name in names}) != len(names)):
            raise EngineError(f"Factory {key} must be unique relative paths within the bundle")
    names = set(contract["required_files"])
    names.add(contract_name)
    for name in sorted(names):
        # One lstat each; hashing later applies the full alias rules.
        try:
            regular = stat.S_ISREG(os.lstat(bundle / name).st_mode)
        except OSError:
            regular = False
        if not regular:
            raise EngineError(f"Required factory input is not a file: {bundle / name}")
    for name in contract["source_trees"]:
        folder = inside(bundle, name)
        if not folder.is_dir():
            raise EngineError(f"Required factory source area is not a directory: {folder}")
        names.update(tree_files(bundle, folder))
    if version == 2:
        historical = contract["historical_files"]
        if (not isinstance(historical, list) or any(not isinstance(name, str) for name in historical)
                or len(historical) != len(set(historical))):
            raise EngineError("historical_files must be an explicit unique file list")
        for name in historical:
            relative_input_path(name)
            if not name.startswith("docs/") or not name.endswith(".md") or name == "docs/current-decisions.md":
                raise EngineError("Only reviewed historical Markdown documents may be excluded")
            if not inside(bundle, name).is_file():
                raise EngineError(f"Missing historical document: {name}")
        names.difference_update(historical)
    return sorted(names)


def project_files(project):
    """Tracked and nonignored untracked contents, scanned once per command scope."""
    def scan():
        names = git(project, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0")
        return scan_hashes(project, [name for name in names
                                     if name and name != ".factory" and not name.startswith(".factory/")])
    return cached(("files", str(project)), scan)


def source_inputs(project, excluded=()):
    excluded = [os.path.normcase(path) for path in excluded]
    separator = os.path.normcase("/")
    return {name: value for name, value in project_files(project).items()
            if not any(os.path.normcase(name) == path or os.path.normcase(name).startswith(path + separator)
                       for path in excluded)}


def production_fingerprint(project, profile, ticket=None):
    """Bind manual QA to production contents; only reviewed test paths are excluded."""
    paths = profile.get("test_paths", []) if profile.get("version") == 2 else []
    for path in paths:
        relative_input_path(path)
    value = {"project": str(project), "files": source_inputs(project, paths),
                   "declared": declared_inputs(project, profile),
                   "environment": {name: os.environ.get(name) for name in profile["environment_inputs"]},
                   "bundle": factory_inputs()}
    if ticket is not None:
        value["ticket"] = ticket
    return digest(value)


def declared_inputs(project, profile):
    declared = {}
    for name in profile["input_files"]:
        path = Path(name) if Path(name).is_absolute() else inside(project, name)
        declared[name] = file_hash(path)
    return declared


def factory_inputs():
    bundle = Path(__file__).resolve().parent.parent
    return cached(("bundle", str(bundle)),
                  lambda: scan_hashes(bundle, bundle_input_paths(bundle), missing=None))


def executable_hash(name):
    found = shutil.which(name)
    return file_hash(Path(found)) if found else None


def fingerprint(project, profile, task, run_dir, draft=False, ticket=None):
    files = source_inputs(project)
    declared = declared_inputs(project, profile)
    executables = {}
    for check in profile["checks"]:
        first = command_argv(check, project, run_dir)[0]
        executables[first] = cached(("executable", first), lambda: executable_hash(first))
        if not executables[first]:
            if not draft or profile.get("version") != 2:
                raise EngineError(f"Check executable unavailable: {first}")
            executables[first] = "MISSING"
    value = {"project": str(project),
                   "files": files, "profile": profile, "task": task, "declared": declared,
                   "environment": {name: os.environ.get(name) for name in profile["environment_inputs"]},
                   "executables": executables, "bundle": factory_inputs()}
    if ticket is not None:
        value["ticket"] = ticket
    return digest(value)


def discover(project):
    package = project / "package.json"
    scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {}) if package.exists() else {}
    return {"project": str(project), "head": git(project, "rev-parse", "HEAD"),
            "branch": git(project, "branch", "--show-current"),
            "worktrees": git(project, "worktree", "list", "--porcelain"),
            "package_scripts": scripts,
            "profile_proposal": {"version": 2, "interface": "web" if package.exists() or (project / "index.html").exists() else "library",
                                 "checks": [], "environment_inputs": [], "input_files": [], "protected_paths": []},
            "next": "Review interface, exposure, scopes and test-only paths. Start draft acceptance now; seal real checks only at the final test phase. Discovery executes no project scripts."}
