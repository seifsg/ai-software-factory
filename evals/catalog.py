"""Sample requests held in memory, workspace copies, scoring in child processes and the rubric self-check.

Everything a check needs (rubric, check program, shipped modules, fixture, reference solution) is read once,
before any agent starts. The parent reads item ids from the rubric's syntax tree and never runs rubric code.
"""
import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
from pathlib import Path
import secrets
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
    """One sample, read into memory: what the agent sees (request, fixture) and what scores it (rubric, solution)."""
    name: str
    request: str
    fixture: dict  # relative POSIX path -> bytes
    rubric: str
    items: tuple
    keep: frozenset
    solution: dict  # the reference solution: relative POSIX path -> bytes, never shown to an agent


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


def read_files(folder):
    """Every file under `folder` as {relative POSIX path: bytes}."""
    return {p.relative_to(folder).as_posix(): p.read_bytes()
            for p in sorted(folder.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def read_sample(folder):
    """A sample folder read into memory; raises ValueError when a part is missing."""
    missing = [part for part in PARTS if not (folder / part).exists()]
    if missing:
        raise ValueError(f"sample {folder.name} lacks {', '.join(missing)}")
    rubric = (folder / "rubric.py").read_text(encoding="utf-8")
    items, keep = rubric_items(rubric, folder.name)
    return Sample(folder.name, (folder / "request.md").read_text(encoding="utf-8").strip(),
                  read_files(folder / "fixture"), rubric, items, keep, read_files(folder / "reference"))


def load(names=None):
    """The chosen samples (all when none named), sorted and read into memory; ValueError for unknown names."""
    found = {path.name: path for path in sorted(ROOT.iterdir())
             if path.is_dir() and not path.name.startswith(("_", "."))}
    unknown = sorted(set(names or ()) - set(found))
    if unknown:
        raise ValueError(f"unknown sample(s): {', '.join(unknown)}; known: {', '.join(found)}")
    return [read_sample(found[name]) for name in found if not names or name in names]


def kit():
    """The check program and the modules it ships to the check child, read once with the samples."""
    return {name: (CODE / f"{name}.py").read_text(encoding="utf-8")
            for name in ("check", "rubric_tools", "harness", "proc", "winjob")}


def write_files(files, work):
    """Write {relative path: bytes} under `work` (created) and return it."""
    for name, data in files.items():
        (Path(work) / name).parent.mkdir(parents=True, exist_ok=True)
        (Path(work) / name).write_bytes(data)
    Path(work).mkdir(parents=True, exist_ok=True)
    return Path(work)


def write_fixture(sample, work):
    """A fresh copy of the sample's fixture at `work`, from memory."""
    return write_files(sample.fixture, work)


def texts(files):
    return {name: data.decode("utf-8", "replace") for name, data in files.items()}


class Compromised(RuntimeError):
    """A check passed that has no rubric: something in the check environment answers for the rubric."""


def check_item(sample, sources, work, item, root, env, record=None):
    """Why one item fails, or None. The child gets everything over a stdin pipe, runs without site hooks, and
    must print its token last on a stdout pipe only this process holds."""
    token = secrets.token_hex(16)
    payload = {"token": token, "item": item, "workdir": str(work), "rubric": sample.rubric, **sources,
               "fixture": texts(sample.fixture), "reference": texts(sample.solution), "record": record}
    code, timed_out, output = proc.run_limited([sys.executable, "-I", "-S", "-B", "-c", BOOT], root, CHECK_SECONDS,
                                               env=env, stdin_data=json.dumps(payload).encode("utf-8") + b"\n")
    if timed_out:
        return f"check timed out after {CHECK_SECONDS}s"
    lines = (output or "").strip().splitlines()
    if code == 0 and lines and lines[-1].strip() == token:
        return None
    reasons = [line for line in lines if line.strip() and line.strip() != token]
    return "check stopped" if code is None else (reasons or [f"exit {code} without the pass marker"])[-1]


def score(sample, sources, work, root, env, record=None):
    """Failing items with their reason; the items run at once, beside a canary item with a random id that has
    no rubric and must fail. Raises Compromised when the canary passes."""
    canary = f"canary-{secrets.token_hex(8)}"
    items = (*sample.items, canary)
    with ThreadPoolExecutor(max_workers=len(items)) as pool:
        reasons = dict(zip(items, pool.map(
            lambda item: check_item(sample, sources, work, item, root, env, record), items)))
    if not reasons.pop(canary):
        raise Compromised("a canary check with no rubric passed: the check environment answers for the rubric")
    return {item: why for item, why in reasons.items() if why}


def scored(sample, sources, solved, record=None):
    """Score the sample's fixture (with the reference laid over it when `solved`) in a throwaway folder."""
    root = Path(tempfile.mkdtemp(prefix=f"eval-check-{sample.name}-"))
    try:
        work = write_fixture(sample, root / "work")
        if solved:
            write_files(sample.solution, work)
        return score(sample, sources, work, root, isolation.run_env(root), record)
    finally:
        isolation.remove(root)


def self_check(sample, sources):
    """Rubric problems: a new item passing on the untouched fixture, a KEEP item failing there, any item failing
    on the reference solution (with fresh random inputs each time)."""
    before, after = scored(sample, sources, False), scored(sample, sources, True)
    return ([f"{item} passes on the untouched fixture" for item in sample.items if item not in {*before, *sample.keep}]
            + [f"{item} (KEEP) fails on the untouched fixture: {before[item]}"
               for item in sorted(sample.keep & {*before})]
            + [f"{item} fails on the reference: {why}" for item, why in sorted(after.items())])


def loaded_modules(samples, sources):
    """(files, folders) that real checks and harnesses load: each sample's reference scored once with recording.

    Files under the throwaway folders (the reference's own modules) are left out.
    """
    folder = Path(tempfile.mkdtemp(prefix="eval-record-"))
    try:
        for sample in samples:
            scored(sample, sources, True, record=str(folder))
        seen = [json.loads(path.read_text(encoding="utf-8")) for path in folder.glob("*.json")]
    finally:
        isolation.remove(folder)
    if not seen:
        raise RuntimeError("the interpreter probe recorded no modules")
    def kept(path):
        return not any(part.startswith("eval-check-") for part in Path(path).parts)
    return ({f for entry in seen for f in entry["files"] if kept(f)},
            {p for entry in seen for p in entry["path"] if kept(p)})
