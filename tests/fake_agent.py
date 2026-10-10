"""Fake agent for the eval runner: `python fake_agent.py <arm> <sample> <workdir> <delivering arm>`.

Copies the sample's reference solution into the workspace when `arm` is the delivering arm, else does nothing.
Exits 3 when the prompt on stdin is not the arm's prompt, so tests see a wrong arm prompt as a bad exit code.
"""
from pathlib import Path
import shutil
import sys

SAMPLES = Path(__file__).resolve().parents[1] / "evals/samples"


def main(arm, sample, workdir, delivering):
    """Check the arm's prompt, then deliver the reference or nothing."""
    prompt = sys.stdin.read()
    request = (SAMPLES / sample / "request.md").read_text(encoding="utf-8").strip()
    if request not in prompt or ("safe-engine/SKILL.md" in prompt) != (arm == "factory"):
        return 3
    if arm == delivering:
        shutil.copytree(SAMPLES / sample / "reference", workdir, dirs_exist_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
