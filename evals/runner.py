"""Run every sample in both arms, each in a fresh temp copy with a time limit, scored from in-memory sources."""
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
import subprocess
import tempfile
import time

from evals import agent, catalog, isolation, proc

ARMS = ("factory", "plain")
PROMPTS = Path(__file__).resolve().parent / "prompts"
GIT_COMMIT = ["-c", "user.name=evals", "-c", "user.email=evals@localhost", "-c", "commit.gpgsign=false",
              "commit", "-q", "--no-verify", "-m", "Fixture"]


def prompt_text(sample, arm, factory):
    """The arm's prompt around the sample's request: the same request, with or without the factory."""
    text = (PROMPTS / f"{arm}.md").read_text(encoding="utf-8")
    return text.replace("{factory}", Path(factory).as_posix() if factory else "").replace("{request}", sample.request)


def git_init(work):
    """Make the copy a repository with the fixture as its first commit; skipped when Git is missing or fails."""
    for args in (["init", "-q"], ["add", "-A"], GIT_COMMIT):
        try:
            if subprocess.run(["git", *args], cwd=work, capture_output=True, timeout=60).returncode:
                return
        except (OSError, subprocess.SubprocessError):
            return


def row(sample, arm, failing, **fields):
    """A report row; `failing` maps item ids to reasons."""
    base = {"sample": sample.name, "arm": arm, "delivered": len(sample.items) - len(failing),
            "total": len(sample.items), "failing": failing, "minutes": 0.0, "exit": None, "timed_out": False,
            "void": None, "possible_escapes": []}
    return {**base, **fields}


def attempt(sample, arm, template, minutes, base, logs, guard, sources):
    """Agent then rubric in `base`: (row fields, or None when an interrupt stopped it). Raises on setup errors."""
    work = catalog.write_fixture(sample, base / "work")
    git_init(work)
    factory = isolation.export_factory(base / "factory") if arm == "factory" else ""
    prompt = base / "prompt.md"
    prompt.write_text(prompt_text(sample, arm, factory), encoding="utf-8")
    env, seen, started = isolation.run_env(base), isolation.temp_entries(), time.monotonic()
    values = {"prompt_file": prompt, "workdir": work, "arm": arm, "sample": sample.name, "factory": factory}
    code, timed_out = agent.run(template, values, work, prompt, logs / f"{sample.name}-{arm}.log", minutes * 60, env)
    fields = {"minutes": round((time.monotonic() - started) / 60, 2), "exit": code, "timed_out": timed_out,
              "possible_escapes": sorted(isolation.temp_entries() - seen)}
    if proc.STOPPING.is_set():
        return None, work
    void = guard()
    if void or timed_out:
        failing = {item: f"void: {void}" if void else "agent timed out" for item in sample.items}
    else:
        failing = catalog.score(sample, sources, work, base, env)
    return (None if proc.STOPPING.is_set() else {"failing": failing, "void": void, **fields}), work


def run_one(sample, arm, template, minutes, base, logs, guard, sources, keep=False):
    """One sample in one arm; returns its row (an errored row on failure), or None when an interrupt stopped it."""
    root = Path(tempfile.mkdtemp(prefix=f"{sample.name}-{arm}-", dir=base))
    try:
        fields, work = attempt(sample, arm, template, minutes, root, logs, guard, sources)
        result = fields and row(sample, arm, fields.pop("failing"), **fields)
    except Exception as error:  # noqa: BLE001 - one broken run must not abort the others
        reason = f"{type(error).__name__}: {error}"
        result, work = row(sample, arm, {item: f"error: {reason}" for item in sample.items}, error=reason), None
    cleanup = None if keep else isolation.remove(root)
    if result:
        result.update({"cleanup": cleanup} if cleanup else {}, **({"workdir": str(work)} if keep and work else {}))
    return result


def execute(tasks, jobs):
    """Run callables `jobs` at a time. Ctrl-C cancels queued ones and kills running ones: (results, interrupted)."""
    pool, futures = ThreadPoolExecutor(max_workers=jobs), []
    try:
        futures = [pool.submit(task) for task in tasks]
        pending = set(futures)
        while pending:
            _, pending = wait(pending, timeout=0.5)  # short waits keep Ctrl-C responsive on Windows
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)
        proc.stop_all()
        pool.shutdown(wait=True)  # stopped runs clean their temp copies
        finished = [f for f in futures if f.done() and not f.cancelled() and not f.exception()]
        return [f.result() for f in finished if f.result()], True
    pool.shutdown(wait=True)
    return [future.result() for future in futures], False


def guard_for():
    """A check naming why runs are void: the checkout's eval files changed since the start (hashed once each)."""
    folders = [isolation.EVALS] + ([] if isolation.EVALS in catalog.ROOT.parents else [catalog.ROOT])
    start = [isolation.digest(folder) for folder in folders]

    def guard():
        changed = [isolation.digest(folder) for folder in folders] != start
        return "the checkout's eval files changed during the run" if changed else None
    return guard


def check_out(out):
    """Refuse a report folder inside evals/: writing there would void every run."""
    out = Path(out).resolve()
    if out == isolation.EVALS or isolation.EVALS in out.parents:
        raise ValueError(f"--out must be outside {isolation.EVALS}")
    return out


def run_all(template, out, names=None, minutes=30.0, jobs=1, keep=False, factory_template=None):
    """Every chosen sample in both arms, `jobs` at a time; returns the report. Logs go to out/logs.

    `factory_template` replaces `template` in the factory arm, for hosts that load the factory by a flag.
    """
    templates = {"factory": factory_template or template, "plain": template}
    for text in templates.values():
        agent.fill(text, dict.fromkeys(agent.PLACEHOLDERS, ""))  # reject an empty template before any work
    if minutes <= 0 or jobs < 1:
        raise ValueError("timeout must be above 0 minutes and jobs at least 1")
    logs = check_out(out) / "logs"
    samples, sources, guard = catalog.load(names), catalog.kit(), guard_for()  # all read before any agent starts
    logs.mkdir(parents=True, exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix="eval-runs-"))
    try:
        runs, interrupted = execute([lambda s=s, a=a: run_one(s, a, templates[a], minutes, base, logs, guard,
                                                              sources, keep) for s in samples for a in ARMS], jobs)
    finally:
        proc.STOPPING.clear()  # an interrupt stops this run only
        cleanup = None if keep else isolation.remove(base)
    return {"timeout_minutes": minutes, "interrupted": interrupted, "runs": runs,
            **({"cleanup": cleanup} if cleanup else {})}
