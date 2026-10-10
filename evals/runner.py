"""Run every sample in both arms, each in a fresh temp copy with a time limit, and score it from a private copy."""
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
import subprocess
import tempfile
import time

from evals import agent, catalog, isolation, proc
from evals.check import load_rubric

ARMS = ("factory", "plain")
PROMPTS = Path(__file__).resolve().parent / "prompts"
GIT_COMMIT = ["-c", "user.name=evals", "-c", "user.email=evals@localhost", "-c", "commit.gpgsign=false",
              "commit", "-q", "--no-verify", "-m", "Fixture"]


def prompt_text(sample, arm, factory):
    """The arm's prompt around the sample's request: the same request, with or without the factory."""
    request = (sample / "request.md").read_text(encoding="utf-8").strip()
    text = (PROMPTS / f"{arm}.md").read_text(encoding="utf-8")
    return text.replace("{factory}", Path(factory).as_posix() if factory else "").replace("{request}", request)


def git_init(work):
    """Make the copy a repository with the fixture as its first commit; skipped when Git is missing or fails."""
    for args in (["init", "-q"], ["add", "-A"], GIT_COMMIT):
        try:
            if subprocess.run(["git", *args], cwd=work, capture_output=True, timeout=60).returncode:
                return
        except (OSError, subprocess.SubprocessError):
            return


def outcome(sample, work, root, env, timed_out, guard):
    """(void reason, failing items): a void run or a timeout fails every item; otherwise the rubric decides."""
    items, void = list(load_rubric(sample).CHECKS), guard()
    if void or timed_out:
        return void, {item: f"void: {void}" if void else "agent timed out" for item in items}
    return None, catalog.score(sample, work, root, env)


def run_one(sample, arm, template, minutes, base, logs, guard, keep=False):
    """One sample in one arm: copy, prompt, agent with a time limit, rubric. Returns its row, or None if stopped."""
    root = Path(tempfile.mkdtemp(prefix=f"{sample.name}-{arm}-", dir=base))
    try:
        work = catalog.copy_fixture(sample, root)
        git_init(work)
        factory = isolation.export_factory(root / "factory") if arm == "factory" else ""
        prompt = root / "prompt.md"
        prompt.write_text(prompt_text(sample, arm, factory), encoding="utf-8")
        env, seen, started = isolation.run_env(root), isolation.temp_entries(), time.monotonic()
        values = {"prompt_file": prompt, "workdir": work, "arm": arm, "sample": sample.name, "factory": factory}
        log = logs / f"{sample.name}-{arm}.log"
        code, timed_out = agent.run(template, values, work, prompt, log, minutes * 60, env)
        spent, escapes = (time.monotonic() - started) / 60, sorted(isolation.temp_entries() - seen)
        if proc.STOPPING.is_set():
            return None
        void, failing = outcome(sample, work, root, env, timed_out, guard)
        total = len(load_rubric(sample).CHECKS)
    finally:
        if not keep:
            catalog.remove(root)
    row = {"sample": sample.name, "arm": arm, "delivered": total - len(failing), "total": total, "failing": failing,
           "minutes": round(spent, 2), "exit": code, "timed_out": timed_out, "void": void, "escapes": escapes}
    return {**row, "workdir": str(work)} if keep else row


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


def guard_for(private):
    """A check that names why runs are void: the checkout's eval files or the private copy changed since the start."""
    def marks():
        return [isolation.digest(folder) for folder in (catalog.ROOT, isolation.EVALS, private)]
    start = marks()

    def guard():
        now = marks()
        if now[:2] != start[:2]:
            return "the checkout's eval files changed during the run"
        return "the private rubric copy changed during the run" if now[2] != start[2] else None
    return guard


def run_all(template, out, names=None, minutes=30.0, jobs=1, keep=False, factory_template=None):
    """Every chosen sample in both arms, `jobs` at a time; returns the report. Logs go to out/logs.

    `factory_template` replaces `template` in the factory arm, for hosts that load the factory by a flag.
    """
    templates = {"factory": factory_template or template, "plain": template}
    for text in templates.values():
        agent.fill(text, dict.fromkeys(agent.PLACEHOLDERS, ""))  # reject an empty template before any work
    if minutes <= 0 or jobs < 1:
        raise ValueError("timeout must be above 0 minutes and jobs at least 1")
    chosen, logs = catalog.find(names), Path(out) / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    private, base = Path(tempfile.mkdtemp(prefix="eval-rubrics-")), Path(tempfile.mkdtemp(prefix="eval-runs-"))
    try:
        samples = isolation.snapshot(chosen, private)  # before any agent starts
        guard = guard_for(private)
        tasks = [lambda s=s, a=a: run_one(s, a, templates[a], minutes, base, logs, guard, keep)
                 for s in samples for a in ARMS]
        runs, interrupted = execute(tasks, jobs)
    finally:
        proc.STOPPING.clear()  # an interrupt stops this run only
        catalog.remove(private)
        if not keep:
            catalog.remove(base)
    return {"timeout_minutes": minutes, "interrupted": interrupted, "runs": runs}
