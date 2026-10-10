"""Sample requests: discovery, workspace copies, rubric scoring and the rubric self-check."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import secrets
import shutil
import stat
import sys
import tempfile
import time

from evals import isolation, proc
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


def check_item(sample, work, item, folder, env):
    """Why one item fails, or None: its own process, tree-killed at the limit, passing only on its token."""
    token, stdin, log = secrets.token_hex(16), folder / f"{item}.in", folder / f"{item}.out"
    stdin.write_text(token + "\n", encoding="utf-8")
    code, timed_out = proc.run_limited([sys.executable, "-B", str(CHECK), str(sample), str(work), item],
                                       work, stdin, log, CHECK_SECONDS, env=env)
    if timed_out:
        return f"check timed out after {CHECK_SECONDS}s"
    lines = log.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    if code == 0 and lines and lines[-1].strip() == token:
        return None
    reasons = [line for line in lines if line.strip() and line.strip() != token]
    return "check stopped" if code is None else (reasons or [f"exit {code} without the pass marker"])[-1]


def score(sample, work, root, env):
    """Failing items with their reason; the items run at once, outputs under root/checks."""
    folder = Path(root) / "checks"
    folder.mkdir(exist_ok=True)
    items = list(load_rubric(sample).CHECKS)
    with ThreadPoolExecutor(max_workers=len(items)) as pool:
        reasons = list(pool.map(lambda item: check_item(sample, work, item, folder, env), items))
    return {item: why for item, why in zip(items, reasons) if why}


def self_check(sample):
    """Rubric problems: a new item passing on the untouched fixture, a KEEP item failing there, any item failing
    on the reference solution."""
    root = Path(tempfile.mkdtemp(prefix=f"eval-check-{sample.name}-"))
    try:
        env, work = isolation.run_env(root), copy_fixture(sample, root)
        rubric, before = load_rubric(sample), score(sample, work, root, env)
        shutil.copytree(sample / "reference", work, dirs_exist_ok=True)
        after = score(sample, work, root, env)
    finally:
        remove(root)
    keep = set(getattr(rubric, "KEEP", ()))
    return ([f"{item} passes on the untouched fixture" for item in rubric.CHECKS if item not in set(before) | keep]
            + [f"{item} (KEEP) fails on the untouched fixture: {before[item]}" for item in sorted(keep & set(before))]
            + [f"{item} fails on the reference: {why}" for item, why in sorted(after.items())])
