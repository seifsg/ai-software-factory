"""Keep runs apart from the checkout and the machine: digests, bundle export, run env, temp listing, cleanup."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import time

from safe_engine.project import bundle_input_paths
from safe_engine import distribution

FACTORY = Path(__file__).resolve().parents[1]
EVALS = Path(__file__).resolve().parent  # runner, checks, prompts and samples
DROPPED_ENV = ("PWD", "OLDPWD")  # they would name the runner's own folder


def digest(folder):
    """One hash over every file path and content under `folder`, to notice any edit."""
    root = Path(folder)
    hasher = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        hasher.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return hasher.hexdigest()


def read_bundle():
    """The factory bundle (the inputs an install ships; no evals/ or tests/) read into memory once."""
    return {name: (FACTORY / name).read_bytes() for name in bundle_input_paths(FACTORY)}


def bundle_identity(bundle):
    """Describe captured bytes separately from the checkout's possibly dirty provenance."""
    hashed = hashlib.sha256()
    for name, data in sorted(bundle.items()):
        hashed.update(name.encode() + b"\0" + data + b"\0")
    try:
        revision = distribution.git("rev-parse", "HEAD", cwd=FACTORY)
        dirty = bool(distribution.git("status", "--porcelain", cwd=FACTORY))
    except (RuntimeError, OSError):
        revision, dirty = None, None
    return {"checkout_revision": revision, "checkout_dirty": dirty, "bundle_sha256": hashed.hexdigest()}


def export_factory(bundle, dest):
    """Write the in-memory bundle to `dest` for the factory arm."""
    for name, data in bundle.items():
        target = Path(dest) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return Path(dest)


def observed_run(home, work, selected):
    """Report bounded gate-home observations, never use them to grade the candidate."""
    paths = list(Path(home, "runs").glob("*.json"))
    if not paths:
        paths = list(Path(home, "runs/closed").glob("*.json"))
    if len(paths) <= 16:
        for path in paths:
            try:
                if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_048_576:
                    continue
                run = json.loads(path.read_text(encoding="utf-8-sig"))
                if (not isinstance(run, dict) or type(run.get("version")) is not int or run.get("version") != 1
                        or run.get("project") != str(work.resolve())
                        or run.get("bundle") != {"root": selected["bundle_root"], "revision": selected["revision"]}):
                    continue
                policies = {key: run.get(key) for key in ("check_selection", "show_first", "suite_policy")}
                if not all(type(value) is bool for value in policies.values()) or type(run.get("closed")) is not bool:
                    continue
                return {"status": "observed", "revision": selected["revision"],
                        "policies": policies, "closed": run["closed"]}
            except (OSError, ValueError, TypeError):
                continue
    return {"status": "not_observed"}


def run_env(root):
    """The run's environment: temp folders and the factory gate's home inside the run folder."""
    tmp, gate_home = Path(root) / "tmp", Path(root) / "gate-home"
    tmp.mkdir()
    gate_home.mkdir()
    env = {key: value for key, value in os.environ.items() if key not in DROPPED_ENV}
    return {**env, "TEMP": str(tmp), "TMP": str(tmp), "TMPDIR": str(tmp), "SAFE_ENGINE_HOME": str(gate_home)}


def temp_entries():
    """Names in the system temp folder; new ones after a run are possible writes outside the run folder."""
    try:
        return set(os.listdir(tempfile.gettempdir()))
    except OSError:
        return set()


def remove(path):
    """Delete a temp tree, read-only files included; returns why it could not, or None."""
    def retry(function, name, _):
        os.chmod(name, stat.S_IWRITE)
        function(name)
    handler = {"onexc": retry} if sys.version_info >= (3, 12) else {"onerror": retry}
    error = None
    for _ in range(3):  # processes stopped a moment ago can still hold files on Windows
        try:
            shutil.rmtree(path, **handler)
            return None
        except OSError as failure:
            error = failure
            time.sleep(0.5)
    shutil.rmtree(path, ignore_errors=True)
    return None if not Path(path).exists() else f"could not delete {path}: {error}"
