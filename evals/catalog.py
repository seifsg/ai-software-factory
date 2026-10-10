"""Sample requests: discovery, isolated workspace copies, rubric scoring and the rubric self-check."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time

from evals.check import load_rubric

ROOT = Path(__file__).resolve().parent / "samples"
CHECK = Path(__file__).resolve().with_name("check.py")
PARTS = ("request.md", "fixture", "reference", "rubric.py")
CHECK_SECONDS = 60


def find(names=None):
    """Sample folders, all or the named ones, sorted; raises ValueError for an unknown or incomplete sample."""
    found = {path.name: path for path in sorted(ROOT.iterdir())
             if path.is_dir() and not path.name.startswith(("_", "."))}
    unknown = sorted(set(names or ()) - set(found))
    if unknown:
        raise ValueError(f"unknown sample(s): {', '.join(unknown)}; known: {', '.join(found)}")
    chosen = [found[name] for name in found if not names or name in names]
    for sample in chosen:
        missing = [part for part in PARTS if not (sample / part).exists()]
        if missing:
            raise ValueError(f"sample {sample.name} lacks {', '.join(missing)}")
    return chosen


def copy_fixture(sample, root):
    """A fresh copy of the sample's fixture at root/work; the rubric and reference stay outside it."""
    work = Path(root) / "work"
    shutil.copytree(sample / "fixture", work, ignore=shutil.ignore_patterns("__pycache__"))
    return work


def remove(path):
    """Delete a temp tree, read-only files included (Git objects on Windows)."""
    def retry(function, name, _):
        os.chmod(name, stat.S_IWRITE)
        function(name)
    handler = {"onexc": retry} if sys.version_info >= (3, 12) else {"onerror": retry}
    for _ in range(3):  # processes killed a moment ago can still hold files on Windows
        try:
            return shutil.rmtree(path, **handler)
        except OSError:
            time.sleep(0.5)
    shutil.rmtree(path, ignore_errors=True)  # a locked leftover in the temp dir must not fail the eval


def check_item(sample, work, item):
    """Why one rubric item fails, or None when it passes; runs in its own process with a time limit."""
    try:
        done = subprocess.run([sys.executable, "-B", str(CHECK), str(sample), str(work), item], cwd=work,
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=CHECK_SECONDS)
    except subprocess.TimeoutExpired:
        return f"check timed out after {CHECK_SECONDS}s"
    return (done.stderr.strip().splitlines() or [f"exit {done.returncode}"])[-1] if done.returncode else None


def score(sample, work):
    """Failing items with their reason; the items run at once, each in its own process."""
    items = list(load_rubric(sample))
    with ThreadPoolExecutor(max_workers=len(items)) as pool:
        reasons = list(pool.map(lambda item: check_item(sample, work, item), items))
    return {item: why for item, why in zip(items, reasons) if why}


def self_check(sample):
    """Rubric problems: an item that passes on the untouched fixture or fails on the reference solution."""
    root = Path(tempfile.mkdtemp(prefix=f"eval-check-{sample.name}-"))
    try:
        work = copy_fixture(sample, root)
        passing = set(load_rubric(sample)) - set(score(sample, work))
        shutil.copytree(sample / "reference", work, dirs_exist_ok=True)
        failing = score(sample, work)
    finally:
        remove(root)
    return ([f"{item} passes on the untouched fixture" for item in sorted(passing)]
            + [f"{item} fails on the reference: {why}" for item, why in sorted(failing.items())])
