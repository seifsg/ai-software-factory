"""Discover projects and bind evidence to explicit inputs."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


class EngineError(Exception):
    """An actionable workflow or configuration problem."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def file_hash(path):
    if path.is_symlink():
        raise EngineError(f"Symlink inputs are unsupported in this pilot: {path}")
    if not path.is_file():
        raise EngineError(f"Required input is not a file: {path}")
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(project, *args):
    result = subprocess.run(["git", "-C", str(project), *args], capture_output=True, timeout=30)
    if result.returncode:
        raise EngineError(result.stderr.decode(errors="replace").strip() or "Git command failed")
    return result.stdout.decode("utf-8", errors="surrogateescape").rstrip("\r\n")


def project_root(path):
    path = Path(path).resolve()
    root = Path(git(path, "rev-parse", "--show-toplevel")).resolve()
    if root != path:
        raise EngineError(f"Use the project root: {root}")
    return root


def inside(project, value):
    path = project / value
    if path.is_symlink() or not path.resolve().is_relative_to(project):
        raise EngineError(f"Path must remain within the project: {value}")
    return path


def validate_profile(profile):
    if not isinstance(profile, dict) or profile.get("version") != 1:
        raise EngineError("Profile must be an object with version 1")
    if profile.get("interface") not in ("web", "cli", "library"):
        raise EngineError("Profile interface must be web, cli, or library")
    checks = profile.get("checks")
    if not isinstance(checks, list) or not checks:
        raise EngineError("Configure at least one real check in the reviewed profile")
    ids = set()
    outputs = set()
    for check in checks:
        if not isinstance(check, dict):
            raise EngineError("Each check must be an object")
        identifier = check.get("id", "")
        if not isinstance(identifier, str) or not identifier or not identifier.replace("-", "").isalnum():
            raise EngineError("Check IDs must use letters, numbers, and hyphens")
        if identifier in ids:
            raise EngineError(f"Duplicate check: {identifier}")
        ids.add(identifier)
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise EngineError(f"{identifier}: argv must be a nonempty array of strings")
        timeout = check.get("timeout_seconds")
        if type(timeout) is not int or not 1 <= timeout <= 3600:
            raise EngineError(f"{identifier}: specify timeout_seconds between 1 and 3600")
        if check.get("kind") not in ("unit", "integration", "browser", "build", "security"):
            raise EngineError(f"{identifier}: unsupported check kind")
        artifacts = check.get("artifacts", [])
        if not isinstance(artifacts, list):
            raise EngineError(f"{identifier}: artifacts must be an array of output paths")
        for name in artifacts:
            if (not isinstance(name, str) or not name.startswith(".factory/outputs/")
                    or any(part in ("", ".", "..") for part in name.split("/"))
                    or "\\" in name or ":" in name or name.casefold() in outputs):
                raise EngineError("Artifact paths must be unique files within .factory/outputs/")
            outputs.add(name.casefold())
    if profile["interface"] == "web" and not any(c["kind"] == "browser" for c in checks):
        raise EngineError("A web profile requires a real browser check")
    for key in ("environment_inputs", "input_files", "protected_paths"):
        if not isinstance(profile.get(key), list) or not all(isinstance(x, str) and x for x in profile[key]):
            raise EngineError(f"{key} must be an explicit array of input names or paths")
    if not profile["protected_paths"]:
        raise EngineError("Declare the acceptance check files in protected_paths")
    return profile


def validate_task(task, profile):
    if not isinstance(task, dict) or not isinstance(task.get("request"), str) or not task["request"].strip():
        raise EngineError("Task needs a nonempty original request")
    criteria = task.get("acceptance")
    if not isinstance(criteria, list) or not criteria:
        raise EngineError("Task needs explicit acceptance criteria")
    check_ids = {c["id"] for c in profile["checks"]}
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
        if not isinstance(checks, list) or not checks or not all(isinstance(c, str) and c in check_ids for c in checks):
            raise EngineError(f"{identifier}: link to configured executable checks")
    return task


def command_argv(check, project, run_dir):
    return [arg.replace("{python}", sys.executable).replace("{project}", str(project))
            .replace("{run}", str(run_dir)) for arg in check["argv"]]


def protected_inputs(project, profile):
    return {name: file_hash(inside(project, name)) for name in profile["protected_paths"]}


def fingerprint(project, profile, task, run_dir):
    names = git(project, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0")
    files = {}
    for name in sorted(set(names)):
        if not name or name == ".factory" or name.startswith(".factory/"):
            continue
        path = inside(project, name)
        files[name] = file_hash(path) if path.exists() else "DELETED"
    declared = {}
    for name in profile["input_files"]:
        path = Path(name) if Path(name).is_absolute() else inside(project, name)
        declared[name] = file_hash(path)
    executables = {}
    for check in profile["checks"]:
        first = command_argv(check, project, run_dir)[0]
        executable = shutil.which(first)
        if not executable:
            raise EngineError(f"Check executable unavailable: {first}")
        executables[first] = file_hash(Path(executable))
    bundle = Path(__file__).resolve().parent.parent
    bundle_files = {}
    for folder in (bundle / "safe_engine", bundle / ".agents" / "skills"):
        for path in sorted(folder.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix in (".py", ".md", ".json", ".yaml"):
                bundle_files[str(path.relative_to(bundle))] = file_hash(path)
    for name in ("AGENTS.md", "docs/pilot-usage.md", "docs/skill-provenance.md", "docs/start-another-session.md", "docs/pr-workflow.md"):
        bundle_files[name] = file_hash(bundle / name)
    return digest({"project": str(project),
                   "files": files, "profile": profile, "task": task, "declared": declared,
                   "environment": {name: os.environ.get(name) for name in profile["environment_inputs"]},
                   "executables": executables, "bundle": bundle_files})


def discover(project):
    package = project / "package.json"
    scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {}) if package.exists() else {}
    return {"project": str(project), "head": git(project, "rev-parse", "HEAD"),
            "branch": git(project, "branch", "--show-current"),
            "worktrees": git(project, "worktree", "list", "--porcelain"),
            "package_scripts": scripts,
            "profile_proposal": {"version": 1, "interface": "web" if package.exists() or (project / "index.html").exists() else "library",
                                 "checks": [], "environment_inputs": [], "input_files": [], "protected_paths": []},
            "next": "Review/correct the interface and configure real commands and protected acceptance files. Discovery executes no project scripts."}
