"""Fake agent for the eval runner: `python fake_agent.py <arm> <sample> <workdir> <factory> <delivering arm> [action]`.

Copies the sample's reference into the workspace when `arm` is the delivering arm. Exits 3 when the run is not set
up as promised: the arm's prompt on stdin, a bundle export without evals/ for the factory arm, temp and gate home
inside the run folder. Actions: `tamper` rewrites the rubric under FAKE_SAMPLES to pass everything; `escape`
writes a file into FAKE_ESCAPE.
"""
import os
from pathlib import Path
import shutil
import sys

SAMPLES = Path(__file__).resolve().parents[1] / "evals/samples"
CHEAT = 'CHECKS = {f"R{i}": (lambda work: None) for i in range(1, 5)}\n'


def set_up_right(arm, sample, workdir, factory, prompt):
    """Whether the runner gave this arm what it promised."""
    request = (SAMPLES / sample / "request.md").read_text(encoding="utf-8").strip()
    run_folder = Path(workdir).resolve().parent
    homes = [Path(os.environ.get(name, "")).resolve() for name in ("TEMP", "TMPDIR", "SAFE_ENGINE_HOME")]
    exported = arm != "factory" or ((Path(factory) / ".agents/skills/safe-engine/SKILL.md").is_file()
                                    and not (Path(factory) / "evals").exists() and factory in prompt)
    return (request in prompt and ("safe-engine/SKILL.md" in prompt) == (arm == "factory") and exported
            and all(home.is_dir() and home.parent == run_folder for home in homes))


def main(arm, sample, workdir, factory, delivering, action=""):
    """Check the set-up, act, then deliver the reference or nothing."""
    prompt = sys.stdin.read().replace("\\", "/")
    if not set_up_right(arm, sample, workdir, factory.replace("\\", "/"), prompt):
        return 3
    if action == "tamper":
        Path(os.environ["FAKE_SAMPLES"], sample, "rubric.py").write_text(CHEAT, encoding="utf-8")
    if action == "escape":
        Path(os.environ["FAKE_ESCAPE"], f"escaped-{arm}.txt").write_text("x", encoding="utf-8")
    if arm == delivering:
        shutil.copytree(SAMPLES / sample / "reference", workdir, dirs_exist_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:7]))
