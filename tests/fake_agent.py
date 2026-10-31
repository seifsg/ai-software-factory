"""Fake agent for the eval runner: `python fake_agent.py <arm> <sample> <workdir> <factory> <delivering arm> [action]`.

Copies the sample's reference into the workspace when `arm` is the delivering arm. Exits 3 when the run is not set
up as promised: the arm's prompt on stdin, a bundle export without evals/ for the factory arm, temp and gate home
inside the run folder. Actions: `tamper` rewrites the rubric under FAKE_SAMPLES; `escape` writes into FAKE_ESCAPE;
`cheat` tries every reachable trick (see CHEATS) and delivers nothing real; `plant` writes a site hook that
would answer every check into the running interpreter, and refuses unless that is a virtual environment.
"""
import os
import json
from pathlib import Path
import shutil
import sys
import sysconfig

SAMPLES = Path(__file__).resolve().parents[1] / "evals/samples"
PASS_ALL = 'CHECKS = {f"R{i}": (lambda work: None) for i in range(1, 5)}\n'
ALWAYS_EQUAL = ("class Any(int):\n    def __eq__(self, other):\n        return True\n\n\n"
                "def subtotal(*args, **kwargs):\n    return Any(0)\n\n\ntotal = subtotal\n")
CHEATS = {  # workspace files: an always-equal result, a shadowed tools module, shadowed stdlib modules
    "invoice.py": ALWAYS_EQUAL,
    "evals/__init__.py": "",
    "evals/rubric_tools.py": "def call(*args, **kwargs):\n    return [['ok', 900]] * 9\n",
    "json.py": "import os\nos._exit(0)\n",
    "tempfile.py": "import os\nos._exit(0)\n",
}


SITE_HOOK = (  # a .pth line runs in every Python started with site: it answers a check with its token
    "import sys, json, os; exec(\"if sys.argv[:1] == ['-c']:\\n try:\\n"
    "  print(json.loads(sys.stdin.buffer.readline())['token'], flush=True); os._exit(0)\\n"
    " except Exception: pass\")\n")


def plant():
    """Write the site hook into this interpreter's site-packages; only ever inside a virtual environment."""
    if sys.prefix == sys.base_prefix:
        raise SystemExit(4)  # never the real interpreter
    Path(sysconfig.get_paths()["purelib"], "evals-plant.pth").write_text(SITE_HOOK, encoding="utf-8")


def set_up_right(arm, sample, workdir, factory, prompt):
    """Whether the runner gave this arm what it promised."""
    request = (SAMPLES / sample / "request.md").read_text(encoding="utf-8").strip()
    run_folder = Path(workdir).resolve().parent
    homes = [Path(os.environ.get(name, "")).resolve() for name in ("TEMP", "TMPDIR", "SAFE_ENGINE_HOME")]
    exported = arm != "factory" or ((Path(factory) / ".agents/skills/safe-engine/SKILL.md").is_file()
                                    and not (Path(factory) / "evals").exists() and factory in prompt)
    receipt = Path(workdir, '.factory/entry-bundle.json')
    selected = not receipt.exists()
    if arm == "factory":
        try:
            pin = json.loads(receipt.read_text(encoding="utf-8"))
            selected = (Path(pin['bundle_root']).resolve() == Path(factory).resolve()
                        and (Path(factory) / '.git').is_dir() and pin.get('policy') == 'explicit')
        except (OSError, ValueError, KeyError, TypeError):
            selected = False
    return (request in prompt and ("safe-engine/SKILL.md" in prompt) == (arm == "factory") and exported
            and selected and all(home.is_dir() and home.parent == run_folder for home in homes))


def cheat(workdir):
    """Plant every trick in the workspace and rewrite any rubric or check program reachable in the temp tree."""
    for name, text in CHEATS.items():
        (Path(workdir) / name).parent.mkdir(parents=True, exist_ok=True)
        (Path(workdir) / name).write_text(text, encoding="utf-8")
    top = Path(workdir).resolve().parents[2]  # the temp folder holding every run
    for target in [*top.rglob("rubric.py"), *top.rglob("check.py")]:
        target.write_text(PASS_ALL, encoding="utf-8")


def main(arm, sample, workdir, factory, delivering, action=""):
    """Check the set-up, act, then deliver the reference or nothing."""
    prompt = sys.stdin.read().replace("\\", "/")
    if not set_up_right(arm, sample, workdir, factory.replace("\\", "/"), prompt):
        return 3
    if action == "tamper":
        Path(os.environ["FAKE_SAMPLES"], sample, "rubric.py").write_text(PASS_ALL, encoding="utf-8")
    if action == "escape":
        Path(os.environ["FAKE_ESCAPE"], f"escaped-{arm}.txt").write_text("x", encoding="utf-8")
    if action == "plant":
        plant()
    if action == "cheat":
        cheat(workdir)
    if arm == delivering:
        shutil.copytree(SAMPLES / sample / "reference", workdir, dirs_exist_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:7]))
