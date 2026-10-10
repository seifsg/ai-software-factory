"""Keep runs apart from the checkout and the machine: checkout digest, bundle export, run env, temp listing, cleanup."""
import hashlib
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import time

from safe_engine.project import bundle_input_paths

FACTORY = Path(__file__).resolve().parents[1]
EVALS = Path(__file__).resolve().parent  # runner, checks, prompts and samples


def digest(folder):
    """One hash over every file path and content under `folder`, to notice any edit."""
    root = Path(folder)
    hasher = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        hasher.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return hasher.hexdigest()


def export_factory(dest):
    """A copy of the factory bundle (the inputs an install ships; no evals/ or tests/) for the factory arm."""
    for name in bundle_input_paths(FACTORY):
        target = Path(dest) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(FACTORY / name, target)
    return Path(dest)


def run_env(root):
    """The run's environment: temp folders and the factory gate's home inside the run folder."""
    tmp, gate_home = Path(root) / "tmp", Path(root) / "gate-home"
    tmp.mkdir()
    gate_home.mkdir()
    return {**os.environ, "TEMP": str(tmp), "TMP": str(tmp), "TMPDIR": str(tmp), "SAFE_ENGINE_HOME": str(gate_home)}


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
