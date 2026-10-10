"""Run every sample in both arms, each in a fresh temp copy with a time limit, and score it."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import tempfile
import time

from evals import agent, catalog
from evals.check import load_rubric

ARMS = ("factory", "plain")
FACTORY = Path(__file__).resolve().parents[1]
PROMPTS = Path(__file__).resolve().parent / "prompts"


def prompt_text(sample, arm):
    """The arm's prompt around the sample's request: the same request, with or without the factory."""
    request = (sample / "request.md").read_text(encoding="utf-8").strip()
    text = (PROMPTS / f"{arm}.md").read_text(encoding="utf-8")
    return text.replace("{factory}", FACTORY.as_posix()).replace("{request}", request)


def git_init(work):
    """Make the copy a fresh repository, as agents and the factory gate expect; skipped when Git is missing."""
    try:
        subprocess.run(["git", "init", "-q"], cwd=work, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        pass


def run_one(sample, arm, template, minutes, logs, keep=False):
    """One sample in one arm: copy, prompt, agent with a time limit, rubric. Returns its report row."""
    root = Path(tempfile.mkdtemp(prefix=f"eval-{sample.name}-{arm}-"))
    try:
        work = catalog.copy_fixture(sample, root)
        git_init(work)
        prompt = root / "prompt.md"
        prompt.write_text(prompt_text(sample, arm), encoding="utf-8")
        values = {"prompt_file": prompt, "workdir": work, "arm": arm, "sample": sample.name, "factory": FACTORY}
        started = time.monotonic()
        code, timed_out = agent.run(template, values, work, prompt, logs / f"{sample.name}-{arm}.log", minutes * 60)
        spent = (time.monotonic() - started) / 60
        items = list(load_rubric(sample))
        failing = {item: "agent timed out" for item in items} if timed_out else catalog.score(sample, work)
    finally:
        if not keep:
            catalog.remove(root)
    row = {"sample": sample.name, "arm": arm, "delivered": len(items) - len(failing), "total": len(items),
           "failing": failing, "minutes": round(spent, 2), "exit": code, "timed_out": timed_out}
    return {**row, "workdir": str(work)} if keep else row


def run_all(template, out, names=None, minutes=30.0, jobs=1, keep=False, factory_template=None):
    """Every chosen sample in both arms, `jobs` at a time; returns the report. Logs go to out/logs.

    `factory_template` replaces `template` in the factory arm, for hosts that load the factory by a flag.
    """
    templates = {"factory": factory_template or template, "plain": template}
    for text in templates.values():
        agent.fill(text, dict.fromkeys(agent.PLACEHOLDERS, ""))  # reject an empty template before any work
    if minutes <= 0 or jobs < 1:
        raise ValueError("timeout must be above 0 minutes and jobs at least 1")
    chosen = catalog.find(names)
    logs = Path(out) / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    pairs = [(sample, arm) for sample in chosen for arm in ARMS]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        runs = list(pool.map(lambda pair: run_one(*pair, templates[pair[1]], minutes, logs, keep), pairs))
    return {"timeout_minutes": minutes, "runs": runs}
