"""Keep runs apart from the checkout and the machine: private sample snapshot, bundle export, run env, escapes."""
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

from safe_engine.project import bundle_input_paths

FACTORY = Path(__file__).resolve().parents[1]
EVALS = Path(__file__).resolve().parent  # runner, checks, prompts and samples


def digest(folder):
    """One hash over every file path and content under `folder`, to notice any edit."""
    root = Path(folder)
    files = sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    hasher = hashlib.sha256()
    for path in files:
        hasher.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return hasher.hexdigest()


def snapshot(samples, dest):
    """Copy the chosen samples to a private folder before any agent starts; scoring reads only this copy."""
    for sample in samples:
        shutil.copytree(sample, Path(dest) / sample.name, ignore=shutil.ignore_patterns("__pycache__"))
    return [Path(dest) / sample.name for sample in samples]


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
    """Names in the system temp folder; new ones after a run are writes that escaped the run folder."""
    try:
        return set(os.listdir(tempfile.gettempdir()))
    except OSError:
        return set()
