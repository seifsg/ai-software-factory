"""Daily self-update for installs without a plugin marketplace (docs/hosts.md#updates).

The session-start hook runs it (`run-gate.sh <host> update`) before the gate loads. At most once a day it
fast-forwards the factory clone that `install` recorded, only when that clone is clean and on main, then reruns
the clone's own installer for each recorded install. Fails open: any problem is logged and the session goes on.
Off with SAFE_ENGINE_NO_UPDATE=1 or `install --no-auto-update`. Pinned project bundles are never touched.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HOME = Path(os.environ.get("SAFE_ENGINE_HOME") or Path.home() / ".safe-engine")
RECORD = HOME / "install.json"  # written by fast_install.remember
STAMP = HOME / "update.stamp"  # its mtime is the last check
DAY = 24 * 3600
OFF = "SAFE_ENGINE_NO_UPDATE"


def due():
    """True once a day for a recorded install that has not opted out; claims the day at once, so failures wait too."""
    if os.environ.get(OFF) or not RECORD.is_file():
        return False
    try:
        if time.time() - STAMP.stat().st_mtime < DAY:
            return False
    except OSError:
        pass  # never checked
    try:
        STAMP.touch()
    except OSError:
        return False  # cannot claim the day: never run unthrottled
    return True


def git(clone, *args, timeout=15):
    """One git command in the clone, never prompting; raises on failure or timeout."""
    return subprocess.run(["git", "-C", str(clone), *args], capture_output=True, text=True, timeout=timeout,
                          check=True, stdin=subprocess.DEVNULL,
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}).stdout.strip()


def update(record):
    """Fast-forward the recorded clone and reinstall when it moved; returns what happened."""
    if not record.get("auto", True):
        return "off"
    clone = Path(record["clone"]).resolve()
    if (HOME / "bundles").resolve() in (clone, *clone.parents):
        return "pinned bundle: never updated"
    if git(clone, "rev-parse", "--abbrev-ref", "HEAD") != "main":
        return "skipped: clone not on main"
    if git(clone, "status", "--porcelain"):
        return "skipped: clone has local changes"
    git(clone, "fetch", "--quiet", timeout=20)
    git(clone, "merge", "--ff-only", "--quiet", "@{upstream}")
    head = git(clone, "rev-parse", "HEAD")
    if head == record.get("revision"):
        return "current"
    gate = clone / "skills" / "safe-engine" / "scripts" / "fast_gate.py"
    for item in record.get("installs", []):  # the new installer rewrites the hooks and this record
        subprocess.run([sys.executable, str(gate), "install", "--host", item["host"],
                        *(["--project", item["project"]] if item.get("project") else [])],
                       capture_output=True, text=True, timeout=30, check=True, stdin=subprocess.DEVNULL)
    return f"updated to {head}"


def main():
    """Exit 0 always: the hook launcher reads non-zero as a missing Python and the session must never break."""
    if not due():
        return
    try:
        result = update(json.loads(RECORD.read_text(encoding="utf-8")))
    except subprocess.CalledProcessError as error:
        step = error.cmd[3] if error.cmd[0] == "git" else "install"
        result = f"error: {step} exit {error.returncode}: {(error.stderr or '').strip()}"
    except Exception as error:  # noqa: BLE001 - offline, missing git, a broken record: fail open
        result = f"error: {error!r}"
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import fast_gate  # the gate's own log; the new copy when the update just replaced it
        fast_gate.log("update", result=result)
    except Exception:  # noqa: BLE001 - a broken copy must not break the session either
        pass


if __name__ == "__main__":
    main()
