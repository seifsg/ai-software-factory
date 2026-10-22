"""Run state and the run registry for fast_gate.py: comparable paths, where a run's files live, and which runs are
active. The gate home holds the truth: active/<h>.json registers a run, runs/<h>.json holds its state. The project's
run.json is a mirror for agents to read; nothing here trusts it, except once to move an older run home, and the
gate's owner-run `rehome`, which takes it home only where held() finds nothing in, around or inside either folder.
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


def save(path, data, new=False):
    """Atomic JSON write: readers never see a half-written file. new: only when path does not exist yet
    (FileExistsError otherwise), so a first write never replaces one that landed meanwhile."""
    import tempfile
    import time
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=2)
            out.write("\n")
        if new:
            os.link(temp, path)  # a link never replaces: the earlier writer wins
            os.unlink(temp)
            return
        for attempt in range(25):
            try:
                os.replace(temp, path)
                break
            except PermissionError:  # Windows: a hook may hold the file open for a moment
                if attempt == 24:
                    raise
                time.sleep(0.02)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


def ledger_path(project):
    return Path(project, *FAST, LEDGER)


def record_path(project):
    return Path(project, *FAST, RECORD)


def registry_path(active, project):
    """The registration file for project in the gate home's active folder."""
    import hashlib
    return active / (hashlib.sha1(norm(project).encode("utf-8")).hexdigest()[:16] + ".json")


def state_path(entry):
    """A run's state in the gate home, named like its registration entry: hooks hash nothing."""
    return entry.parent.parent / "runs" / entry.name


def closed_path(entry):
    """Where a closed run's state rests until the next start: outside runs/*.json, so hooks never read it."""
    return entry.parent.parent / "runs" / "closed" / entry.name


def closed_run(entry):
    """The last closed run for a registration name, or None."""
    try:
        return current(load(closed_path(entry)))
    except (OSError, ValueError):
        return None


def held(active, project):
    """What this gate home holds for project, reading only: ("open" | "lost" | "closed", project) for the folder itself,
    ("nested", folder) for a registered or open run in a folder around or inside it, else None."""
    entry = registry_path(active, project)
    if entry.exists() or state_path(entry).exists():
        try:
            run = current(load(state_path(entry)))
        except (OSError, ValueError):
            run = None
        return ("closed" if run and run.get("closed") else "open" if run else "lost"), str(project)
    if closed_path(entry).exists():
        return "closed", str(project)
    here = norm(project)
    for folder in (active, active.parent / "runs"):
        for name in listing(folder):
            try:
                there = load(folder / name)["project"]
                if inside(here, norm(there)) or inside(norm(there), here):
                    return "nested", str(there)
            except (OSError, ValueError, KeyError, TypeError):
                continue  # unreadable: the hooks skip it too
    return None


def new_registration(project, key):
    """The registration a run started or brought in by this gate gets: its home mark keeps a deleted state lost."""
    return {"project": str(project), "key": key, "sessions": [], "home": True}


def current(run):
    """run when it is a JSON object of this VERSION, else None."""
    return run if isinstance(run, dict) and run.get("version") == VERSION else None


def readable(project):
    """The project's mirror when it is a current run, else None."""
    try:
        return current(load(ledger_path(project)))
    except (OSError, ValueError):
        return None


def state(entry, registration, log):
    """The run the gate home holds for a registration. An older run with no home state moves home from an open
    mirror of the same key, once; anything else is a lost run, gate closed."""
    path = state_path(entry)
    try:
        run = current(load(path))
    except FileNotFoundError:
        run = migrate(path, registration, log)
    except (OSError, ValueError):
        run = None
    return run or lost(registration)


def migrate(path, registration, log):
    """Move an older run's open mirror into the gate home; None when the mirror is not that run, or the run was
    started by this gate (its registration says so: a deleted state then stays lost)."""
    if registration.get("home"):
        return None
    run = readable(registration["project"])
    if not run or run.get("closed") or run.get("key") != registration.get("key"):
        return None
    run["project"] = registration["project"]
    try:
        save(path, run, new=True)
        log("run.migrate", key=run["key"], project=run["project"])
    except FileExistsError:  # a parallel hook or gate command moved it home first: that state wins
        try:
            return current(load(path))
        except (OSError, ValueError):
            return None
    except OSError:
        pass  # no hard links here: gated from memory, the next gate command saves it home
    return run


def listing(folder):
    """The .json names in folder; [] when it is missing."""
    try:
        return [name for name in os.listdir(folder) if name.endswith(".json")]
    except OSError:
        return []


def registrations(active, log=None):
    """(entry, registration, project) for each run the gate home knows: every well-formed registration, and every open
    state whose registration is gone, re-registered here, so deleting one of the two files never switches a run off."""
    names = set(listing(active))
    for name in sorted(names.union(listing(active.parent / "runs"))):
        entry = active / name
        try:
            registration = load(entry) if name in names else reregister(entry, log)
            if registration:
                yield entry, registration, Path(registration["project"])
        except Exception:  # noqa: BLE001 - malformed entry: skip it, keep gating the rest
            continue


def reregister(entry, log):
    """The registration rebuilt from an open home state whose registration was deleted; None for a closed one."""
    run = current(load(state_path(entry)))
    if not run or run.get("closed"):
        return None
    restored = new_registration(run["project"], run["key"])
    try:
        save(entry, restored, new=True)
        if log:
            log("run.reregistered", key=run["key"], project=run["project"])
    except FileExistsError:  # a parallel hook restored it first
        return load(entry)
    except OSError:
        pass  # gated from memory; the next hook tries again
    return restored


def active_runs(active, log):
    """Open runs from the registry and the home state. A missing or unreadable state makes a lost run, gate closed;
    one bad or unreachable entry never disables the others."""
    runs = []
    for entry, registration, project in registrations(active, log):
        run = state(entry, registration, log) if project.is_dir() else forget(entry, project)
        if run and not run.get("closed"):
            runs.append((entry, registration, run))
    return runs


def lost(registration):
    """Stand-in for a run whose home state is missing or broken: gate closed, every destructive rule on."""
    return {"version": VERSION, "project": registration["project"], "key": registration.get("key", "?"),
            "mode": "fast", "kind": "change", "done": {}, "lost": True}


def forget(entry, project):
    """Drop a run whose project folder is gone from a reachable parent; unmounted drives keep theirs."""
    if project.parent.exists():
        for path in (entry, state_path(entry)):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass  # locked: the next hook tries again
    return None


def registered(active, folder):
    """The registered project that holds folder (the deepest), or None: close finds its run from any subfolder."""
    here = norm(folder)
    found = [project for _, _, project in registrations(active) if inside(here, norm(project))]
    return max(found, key=lambda project: len(str(project)), default=None)
