"""Run ledgers and the run registry for fast_gate.py: comparable paths, where a project's run files live, and which
runs are active. The registry in the gate home is the source of truth: a registered run whose ledger is missing or
unreadable stays active, gate closed, until the owner closes it.
"""
import json
import os
import re
from pathlib import Path

VERSION = 1
FAST, LEDGER, RECORD = (".factory", "fast"), "run.json", "work-record.md"  # a project's run files


def native(path):
    """Git Bash /c/... paths as Windows paths; everything else unchanged."""
    text = str(path)
    match = re.match(r"^/([a-zA-Z])(/.*)?$", text) if os.name == "nt" else None
    return match.group(1) + ":" + (match.group(2) or "/") if match else text


def norm(path, base=None):
    """Comparable path: absolute, real (symlinks, junctions, mapped drives resolved), case-normalized."""
    full = Path(native(path))
    if not full.is_absolute():
        full = Path(native(base or os.getcwd())) / full
    return os.path.normcase(os.path.realpath(str(full)))


def inside(child, parent):
    return child == parent or child.startswith(parent.rstrip("\\/") + os.sep)


def load(path):
    """JSON from path. utf-8-sig: a byte-order mark (PowerShell Out-File) still reads."""
    with open(path, encoding="utf-8-sig") as source:
        return json.load(source)


def load_stamped(path):
    """JSON and its mtime from one open handle, so both describe the same write."""
    with open(path, encoding="utf-8-sig") as source:
        return json.load(source), os.fstat(source.fileno()).st_mtime_ns


def ledger_path(project):
    return Path(project, *FAST, LEDGER)


def record_path(project):
    return Path(project, *FAST, RECORD)


def registry_path(active, project):
    """The registration file for project in the gate home's active folder."""
    import hashlib
    return active / (hashlib.sha1(norm(project).encode("utf-8")).hexdigest()[:16] + ".json")


def readable(project):
    """The project's run ledger when it is a current one (a JSON object of this VERSION), else None."""
    try:
        run = load(ledger_path(project))
    except (OSError, ValueError):
        return None
    return run if isinstance(run, dict) and run.get("version") == VERSION else None


def registrations(active):
    """(entry, registration, project) for each well-formed registration; a malformed one is skipped."""
    for entry in active.glob("*.json"):
        try:
            registration = load(entry)
            yield entry, registration, Path(registration["project"])
        except Exception:  # noqa: BLE001 - malformed entry: skip it, keep gating the rest
            continue


def active_runs(active):
    """Open runs from the registry. A missing, unreadable or foreign ledger makes a lost run, gate closed; one bad or
    unreachable entry never disables the others."""
    runs = []
    for entry, registration, project in registrations(active):
        run = readable(project) or (lost(registration) if project.is_dir() else forget(entry, project))
        if run and not run.get("closed"):
            runs.append((entry, registration, run))
    return runs


def lost(registration):
    """Stand-in for a run whose ledger was deleted, moved or broken: gate closed, every destructive rule on."""
    return {"version": VERSION, "project": registration["project"], "key": registration.get("key", "?"),
            "mode": "fast", "kind": "change", "done": {}, "lost": True}


def forget(entry, project):
    """Drop a registration whose project folder is gone from a reachable parent; unmounted drives keep theirs."""
    if project.parent.exists():
        entry.unlink(missing_ok=True)
    return None


def registered(active, folder):
    """The registered project that holds folder (the deepest), or None: close finds its run from any subfolder."""
    here = norm(folder)
    found = [project for _, _, project in registrations(active) if inside(here, norm(project))]
    return max(found, key=lambda project: len(str(project)), default=None)
