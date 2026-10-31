"""Committed legacy bundles and offline discovery for real gate consumer tests."""
from pathlib import Path
import shutil
import subprocess
import sys

from safe_engine import distribution

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/safe-engine/scripts"


def legacy_bundle(bundle):
    """Supply real Git identity and gate scripts with methods predating current flags."""
    bundle.mkdir()
    for name in distribution.REQUIRED:
        path = bundle / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Legacy method fixture without light-lane markers.\n", encoding="utf-8")
    shutil.copytree(SCRIPTS, bundle / "skills/safe-engine/scripts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(SCRIPTS.parent / "VERSION", bundle / distribution.VERSION_FILE)
    for args in (("init", "-q"), ("remote", "add", "origin", distribution.REPOSITORY), ("add", "."),
                 ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "legacy fixture")):
        subprocess.run(["git", "-C", str(bundle), *args], check=True, capture_output=True)
    revision = subprocess.check_output(["git", "-C", str(bundle), "rev-parse", "HEAD"], text=True).strip()
    return {"version": 1, "bundle_root": str(bundle), "revision": revision}


def offline_gate():
    """Replace only remote discovery; inspection, selection and pinned subprocesses stay real."""
    code = ("import sys;sys.path.insert(0,sys.argv.pop(1));import fast_gate,resolve_bundle\n"
            "def offline(*args,**kwargs): raise RuntimeError('offline fixture')\n"
            "resolve_bundle.resolve_bundle=offline\nfast_gate.main()")
    return [sys.executable, "-X", "utf8", "-c", code, str(SCRIPTS)]


def historical_gate():
    """Construct pre-selection run state; other commands still exercise the real CLI.

    This is a compatibility fixture, never proof of current public startup.
    """
    code = ("import sys;sys.path.insert(0,sys.argv.pop(1));import fast_gate\n"
            "if sys.argv[1:2] == ['start']:\n"
            " args=fast_gate.sibling('fast_cli').parse(fast_gate)\n"
            " if (fast_gate.Path(args.project)/'.factory/entry-bundle.json').exists(): fast_gate.main()\n"
            " else: fast_gate.cmd_start(args)\n"
            "else: fast_gate.main()")
    return [sys.executable, "-X", "utf8", "-c", code, str(SCRIPTS)]
