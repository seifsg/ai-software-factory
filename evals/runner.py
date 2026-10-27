"""Run every sample in both arms, each in a fresh temp copy with a time limit, scored from in-memory sources."""
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from threading import Thread
import subprocess
import tempfile
import time

from evals import agent, catalog, interpreter, isolation, proc

ARMS = ("factory", "plain")
PROMPTS = Path(__file__).resolve().parent / "prompts"
GIT_COMMIT = ["-c", "user.name=evals", "-c", "user.email=evals@localhost", "-c", "commit.gpgsign=false",
              "commit", "-q", "--no-verify", "-m", "Fixture"]
TAINTED = ("the Python interpreter changed during the run (site hooks, packages or bytecode), so every later run "
           "would be tainted: the eval stopped. Restore the interpreter, then rerun")


class Watch:
    """Guards recorded before any agent starts. A checkout edit voids the run; an interpreter change or a passing
    canary voids it and stops the whole eval, because the change outlives the run."""

    def __init__(self, samples, sources):
        self.folders = [isolation.EVALS] + ([] if isolation.EVALS in catalog.ROOT.parents else [catalog.ROOT])
        self.modules = catalog.loaded_modules(samples, sources)  # what real checks load, recorded once
        self.checkout, self.interpreter, self.tainted = self.digests(), interpreter.state(*self.modules), None
        self.cleanup = []

    def digests(self):
        return [isolation.digest(folder) for folder in self.folders]

    def taint(self, reason):
        """Record why the eval stops, stop every run, and return the reason."""
        self.tainted = self.tainted or reason
        self.cleanup.extend(proc.stop_all())
        return reason

    def after_agent(self):
        """Why the run that just ended is void, or None."""
        if interpreter.state(*self.modules) != self.interpreter:
            return self.taint(TAINTED)
        return "the checkout's eval files changed during the run" if self.digests() != self.checkout else None


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


def judge(sample, work, base, env, timed_out, ctx):
    """(void reason, failing items) for a finished agent run."""
    void = ctx["watch"].after_agent()
    if void or timed_out:
        return void, {item: f"void: {void}" if void else "agent timed out" for item in sample.items}
    try:
        return None, catalog.score(sample, ctx["sources"], work, base, env)
    except catalog.Compromised as error:
        void = ctx["watch"].taint(f"{error}; the eval stopped")
        return void, {item: f"void: {void}" for item in sample.items}


def attempt(sample, arm, base, ctx):
    """Agent then rubric in `base`: (row fields, or None when stopped, and the workspace). Raises on setup errors."""
    work = catalog.write_fixture(sample, base / "work")
    git_init(work)
    factory = isolation.export_factory(ctx["bundle"], base / "factory") if arm == "factory" else ""
    prompt = base / "prompt.md"
    prompt.write_text(prompt_text(sample, arm, factory), encoding="utf-8")
    env, seen, started = isolation.run_env(base), isolation.temp_entries(), time.monotonic()
    values = {"prompt_file": prompt, "workdir": work, "arm": arm, "sample": sample.name, "factory": factory}
    code, timed_out = agent.run(ctx["templates"][arm], values, work, prompt, ctx["logs"] / f"{sample.name}-{arm}.log",
                                ctx["minutes"] * 60, env)
    fields = {"minutes": round((time.monotonic() - started) / 60, 2), "exit": code, "timed_out": timed_out,
              "possible_escapes": sorted(isolation.temp_entries() - seen)}
    if proc.STOPPING.is_set():
        return None, work
    void, failing = judge(sample, work, base, env, timed_out, ctx)
    stopped = proc.STOPPING.is_set() and not void  # scored while stopping: not a verdict
    return (None if stopped else {"failing": failing, "void": void, **fields}), work


def run_one(sample, arm, base, ctx):
    """One sample in one arm; returns its row (an errored row on failure), or None when it was stopped."""
    root = Path(tempfile.mkdtemp(prefix=f"{sample.name}-{arm}-", dir=base))
    try:
        fields, work = attempt(sample, arm, root, ctx)
        result = fields and row(sample, arm, fields.pop("failing"), **fields)
    except Exception as error:  # noqa: BLE001 - one broken run must not abort the others
        reason = f"{type(error).__name__}: {error}"
        result, work = row(sample, arm, {item: f"error: {reason}" for item in sample.items}, error=reason), None
    cleanup = None if ctx["keep"] else isolation.remove(root)
    if result:
        kept = {"workdir": str(work)} if ctx["keep"] and work else {}
        result.update({"cleanup": cleanup} if cleanup else {}, **kept)
    return result


def execute(tasks, jobs, cleanup=None):
    """Return (rows, interrupted); append stop failures to `cleanup` without losing finished rows."""
    cleanup = cleanup if cleanup is not None else []
    pool, futures = ThreadPoolExecutor(max_workers=jobs), []
    try:
        for task in tasks:
            futures.append(pool.submit(task))
        pending = set(futures)
        while pending:
            _, pending = wait(pending, timeout=0.5)  # short waits keep Ctrl-C responsive on Windows
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)
        cleanup.extend(proc.stop_all())
        joined = Thread(target=pool.shutdown, kwargs={"wait": True}, daemon=True)
        joined.start()
        joined.join(10)
        if joined.is_alive():
            cleanup.append("eval workers did not finish within 10 seconds")
        finished = [f for f in futures if f.done() and not f.cancelled() and not f.exception()]
        return [f.result() for f in finished if f.result()], True
    pool.shutdown(wait=True)
    return [row for row in (future.result() for future in futures) if row], False


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
    samples, sources = catalog.load(names), catalog.kit()  # everything here is read before any agent starts
    ctx = {"templates": templates, "minutes": minutes, "logs": logs, "keep": keep, "sources": sources,
           "bundle": isolation.read_bundle(), "watch": Watch(samples, sources)}
    logs.mkdir(parents=True, exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix="eval-runs-"))
    failures = []
    try:
        runs, interrupted = execute([lambda s=s, a=a: run_one(s, a, base, ctx) for s in samples for a in ARMS],
                                    jobs, failures)
    finally:
        unresolved = proc.stop_all()
        failures.extend(ctx["watch"].cleanup + unresolved)
        if unresolved or "eval workers did not finish within 10 seconds" in failures:
            ctx["watch"].tainted = ctx["watch"].tainted or "owned process cleanup remains unconfirmed; the eval stopped"
            failures.append(f"retained workspace: {base}")
        else:
            proc.STOPPING.clear()  # only confirmed cleanup permits another eval
            cleanup = None if keep else isolation.remove(base)
            if cleanup:
                failures.append(cleanup)
    extra = {"tainted": ctx["watch"].tainted} if ctx["watch"].tainted else {}
    return {"timeout_minutes": minutes, "interrupted": interrupted, "runs": runs, **extra,
            **({"cleanup": "; ".join(dict.fromkeys(failures))} if failures else {})}
