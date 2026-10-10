"""Sample requests held in memory, workspace copies, scoring in child processes and the rubric self-check.

Everything a check needs (rubric, check program, tools, fixture) is read once, before any agent starts. The parent
reads item ids from the rubric's syntax tree and never runs rubric code itself.
"""
import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
from pathlib import Path
import secrets
import shutil
import sys
import tempfile

from evals import isolation, proc
from evals.check import BOOT

ROOT = Path(__file__).resolve().parent / "samples"
CODE = Path(__file__).resolve().parent
PARTS = ("request.md", "fixture", "reference", "rubric.py")
CHECK_SECONDS = 60


@dataclass(frozen=True)
class Sample:
    """One sample, read into memory: what the agent sees (request, fixture) and what scores it (rubric)."""
    name: str
    request: str
    fixture: dict  # relative POSIX path -> bytes
    rubric: str
    items: tuple
    keep: frozenset
    reference: Path  # live folder, read only by the self-check


def rubric_items(source, name):
    """(CHECKS ids, KEEP ids) from the rubric's syntax tree, without running it; ValueError when malformed."""
    found = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and [getattr(t, "id", "") for t in node.targets] in (["CHECKS"], ["KEEP"]):
            keys = node.value.keys if isinstance(node.value, ast.Dict) else None
            found[node.targets[0].id] = [ast.literal_eval(k) for k in keys] if keys is not None else list(
                ast.literal_eval(node.value))
    items, keep = found.get("CHECKS", []), found.get("KEEP", [])
    if not items or any(type(i) is not str or not i for i in items) or len(set(items)) != len(items) \
            or not set(keep) <= set(items):
        raise ValueError(f"sample {name}: rubric needs CHECKS with unique string ids, and KEEP within them")
    return tuple(items), frozenset(keep)


def read_sample(folder):
    """A sample folder read into memory; raises ValueError when a part is missing."""
    missing = [part for part in PARTS if not (folder / part).exists()]
    if missing:
        raise ValueError(f"sample {folder.name} lacks {', '.join(missing)}")
    fixture = {p.relative_to(folder / "fixture").as_posix(): p.read_bytes()
               for p in sorted((folder / "fixture").rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    rubric = (folder / "rubric.py").read_text(encoding="utf-8")
    items, keep = rubric_items(rubric, folder.name)
    return Sample(folder.name, (folder / "request.md").read_text(encoding="utf-8").strip(), fixture, rubric, items,
                  keep, folder / "reference")


def load(names=None):
    """The chosen samples (all when none named), sorted and read into memory; ValueError for unknown names."""
    found = {path.name: path for path in sorted(ROOT.iterdir())
             if path.is_dir() and not path.name.startswith(("_", "."))}
    unknown = sorted(set(names or ()) - set(found))
    if unknown:
        raise ValueError(f"unknown sample(s): {', '.join(unknown)}; known: {', '.join(found)}")
    return [read_sample(found[name]) for name in found if not names or name in names]


def kit():
    """The check program, tools and harness sources, read once with the samples."""
    return {name: (CODE / f"{file}.py").read_text(encoding="utf-8")
            for name, file in (("check", "check"), ("tools", "rubric_tools"), ("harness", "harness"))}


def write_fixture(sample, work):
    """A fresh copy of the sample's fixture at `work`, from memory."""
    for name, data in sample.fixture.items():
        (Path(work) / name).parent.mkdir(parents=True, exist_ok=True)
        (Path(work) / name).write_bytes(data)
    Path(work).mkdir(parents=True, exist_ok=True)
    return Path(work)


def check_item(sample, sources, work, item, folder, env):
    """Why one item fails, or None: a child gets everything over a pipe and must print its token last."""
    token, log = secrets.token_hex(16), folder / f"{item}.out"
    payload = {"token": token, "item": item, "workdir": str(work), "rubric": sample.rubric, **sources,
               "fixture": {name: data.decode("utf-8", "replace") for name, data in sample.fixture.items()}}
    code, timed_out = proc.run_limited([sys.executable, "-I", "-B", "-c", BOOT], folder, log, CHECK_SECONDS,
                                       env=env, stdin_data=json.dumps(payload).encode("utf-8") + b"\n")
    if timed_out:
        return f"check timed out after {CHECK_SECONDS}s"
    lines = log.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    if code == 0 and lines and lines[-1].strip() == token:
        return None
    reasons = [line for line in lines if line.strip() and line.strip() != token]
    return "check stopped" if code is None else (reasons or [f"exit {code} without the pass marker"])[-1]


def score(sample, sources, work, root, env):
    """Failing items with their reason; the items run at once, outputs under root/checks."""
    folder = Path(root) / "checks"
    folder.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=len(sample.items)) as pool:
        reasons = list(pool.map(lambda item: check_item(sample, sources, work, item, folder, env), sample.items))
    return {item: why for item, why in zip(sample.items, reasons) if why}


def self_check(sample, sources):
    """Rubric problems: a new item passing on the untouched fixture, a KEEP item failing there, any item failing
    on the reference solution."""
    root = Path(tempfile.mkdtemp(prefix=f"eval-check-{sample.name}-"))
    try:
        env, work = isolation.run_env(root), write_fixture(sample, root / "work")
        before = score(sample, sources, work, root, env)
        shutil.copytree(sample.reference, work, dirs_exist_ok=True)
        after = score(sample, sources, work, root, env)
    finally:
        isolation.remove(root)
    return ([f"{item} passes on the untouched fixture" for item in sample.items if item not in {*before, *sample.keep}]
            + [f"{item} (KEEP) fails on the untouched fixture: {before[item]}"
               for item in sorted(sample.keep & {*before})]
            + [f"{item} fails on the reference: {why}" for item, why in sorted(after.items())])
