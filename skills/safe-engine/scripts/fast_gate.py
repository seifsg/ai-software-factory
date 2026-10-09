"""Fast/Lucky run gate: record each factory step, check it, and answer host hooks.

Method: .agents/skills/safe-engine/references/fast-run.md#the-gate. Python 3.9+, stdlib only.
Step checks live in fast_record.py (loaded only by `done`).
Checks prove a step was recorded, not that it was good.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
# argparse, hashlib, subprocess and tempfile load lazily: hooks run on every tool call and must start fast.

VERSION = 1
HOME = Path(os.environ.get("SAFE_ENGINE_HOME") or Path.home() / ".safe-engine")
ACTIVE = HOME / "active"
LOG = HOME / "logs" / "gate.log"
MODES = ("fast", "lucky")
KINDS = ("product", "feature", "change")
KEY = re.compile(r"[a-z][a-z0-9-]{0,63}")
# (step, modes, kinds, run flag or "!flag"): ordered steps; everything before "build" gates source edits.
STEPS = (
    ("research", ("fast",), ("product", "feature"), None),
    ("kickoff", ("fast",), ("product", "feature"), None),
    ("tickets", MODES, KINDS, None),
    ("analysis", MODES, ("product", "feature"), None),
    ("analysis", MODES, ("change",), "!light"),  # a light-lane change plans without a separate analysis
    ("plan", MODES, KINDS, None),
    ("design", ("fast",), KINDS, "ui"),
    ("schema", ("fast",), KINDS, "data"),
    ("build", MODES, KINDS, None),
    ("done-run", ("fast",), KINDS, None),
    ("done-run", ("lucky",), KINDS, "ticket_checks"),
    ("handoff", MODES, KINDS, None),
)
TITLES = {"research": "Research", "kickoff": "Kickoff", "tickets": "Tickets", "analysis": "Analysis",
          "plan": "Plan", "design": "Design", "schema": "Schema", "build": "Build log",
          "done-run": "Done-run", "handoff": "Handoff"}
HINTS = {
    "research": ">=3 '### <competitor>' subsections each citing a source URL, a feature matrix table, "
                "an Opportunities line; product runs also '### Stack options' with a 3-row table",
    "kickoff": "Features, Approach, Answered by lines; product runs also Size and Stack",
    "tickets": "an Epic URL line, a Backlog line; product/feature runs >=1 Sub-issue URL line; "
               "online: each listed ticket has a Definition of done",
    "analysis": "a Success line and a fenced ASCII chart",
    "plan": "### Files, ### Critique, ### Phases, ### Todos (T1..), ### Whole plan, Logging and Efficiency lines; "
            "online: each listed ticket has checklist items",
    "design": ">=4 hex colors; UI kit, Font, Logo, Icons, Layout lines; Theme line naming light mode; "
              "Journeys line with counts and a minimum",
    "schema": "a 3-option table, a Chosen line, a fenced ERD or DDL",
    "build": "one line per plan todo: 'T1 pre: ... do: ... post: ...'",
    "done-run": ">=1 PASS line, a Logs line; UI runs >=1 existing screenshot path",
    "handoff": "Run, Statuses, Unverified, Follow-ups lines; sign-in runs a Dev sign-in line; "
               "online: each listed ticket fully ticked, or Blocked, Backlog or not planned",
}
COVERAGE_HINTS = {  # runs whose methods define coverage and the light lane
    "tickets": "an Epic URL line (a change: a Ticket line, its URL or 'none (why)'), a Backlog line; product/feature "
               "runs >=1 Sub-issue URL line and a Requested line (R1, R2, ...); online: each listed ticket is open "
               "with a Definition of done, and its criteria name every requested item not marked owner-deferred",
    "plan": "### Files, ### Critique, ### Phases, ### Todos (T1..), ### Whole plan, Logging and Efficiency lines "
            "(light lane: a Success line and ### Todos); online: each listed ticket has checklist items naming "
            "every criterion, they hold every plan todo, and criteria still name every requested item not "
            "owner-deferred",
    "handoff": "Run, Statuses, Unverified, Follow-ups lines; sign-in runs a Dev sign-in line; online: each listed "
               "ticket fully ticked, or Blocked, Backlog or not planned; items name every criterion and hold every "
               "plan todo; criteria name every requested item not owner-deferred",
}
HERE = Path(__file__).resolve().parent  # sibling modules: fast_record.py (step checks), fast_shell.py (commands)


def sibling(name):
    """Import a module that sits beside this script, whatever the caller's sys.path."""
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    return __import__(name)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(event, **data):
    """Append one JSON line to the gate log; never raise, so logging cannot break a hook."""
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        if LOG.exists() and LOG.stat().st_size > 1_000_000:
            os.replace(LOG, LOG.with_name("gate.log.1"))
        with LOG.open("a", encoding="utf-8") as out:
            out.write(json.dumps({"t": now(), "event": event, **data}, default=str)[:4000] + "\n")
    except OSError:
        pass


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


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
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def save(path, data):
    """Atomic JSON write: readers never see a half-written ledger."""
    import tempfile
    import time
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=2)
            out.write("\n")
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
    return Path(project) / ".factory" / "fast" / "run.json"


def record_path(project):
    return Path(project) / ".factory" / "fast" / "work-record.md"


def registry_path(project):
    import hashlib
    return ACTIVE / (hashlib.sha1(norm(project).encode("utf-8")).hexdigest()[:16] + ".json")


def applies(run, flag):
    """A step's run flag: None always applies, 'x' when the run has x, '!x' when it does not."""
    return flag is None or bool(run.get(flag.lstrip("!"))) != flag.startswith("!")


def steps_for(run):
    return [name for name, modes, kinds, flag in STEPS
            if run["mode"] in modes and run["kind"] in kinds and applies(run, flag)]


def next_step(run):
    return next((step for step in steps_for(run) if step not in run["done"]), None)


def open_before_build(run):
    steps = steps_for(run)
    return [step for step in steps[:steps.index("build")] if step not in run["done"]]


# ---- commands ---------------------------------------------------------------

def find_project(given):
    """The given project, or the nearest folder above cwd holding a run ledger."""
    if given:
        return Path(native(given)).resolve()
    here = Path.cwd().resolve()
    for folder in (here, *here.parents):
        if ledger_path(folder).is_file():
            return folder
    fail("No Fast/Lucky run here. Start one: fast_gate.py start --project <dir> ...")


def open_run(given):
    project = find_project(given)
    try:
        run = load(ledger_path(project))
    except (OSError, ValueError) as error:
        fail(f"Cannot read run ledger in {project}: {error}")
    if run.get("version") != VERSION:
        fail(f"Unsupported run ledger version {run.get('version')}")
    return project, run


def status_text(run):
    lines = [f"{run['mode']} {run['kind']} run '{run['key']}' at {run['project']}"
             f" (ui={run.get('ui')}, data={run.get('data')}, auth={run.get('auth')})"]
    lines += [f"  [{'x' if step in run['done'] else ' '}] {step}" for step in steps_for(run)]
    blocked = open_before_build(run)
    lines.append("Gate: " + ("open, source edits allowed" if not blocked else "closed until " + ", ".join(blocked)))
    if run.get("paused"):
        lines.append("Paused: " + run["paused"]["reason"])
    lines.append("Next: " + ("closed" if run.get("closed") else next_step(run) or "close"))
    return "\n".join(lines)


def skeleton(run):
    quoted = ["> " + line for line in run["request"].splitlines()]  # quoted: request headings never become sections
    lines = [f"# {run['key']}: {run['mode']} {run['kind']} run", "",
             "<!-- Fill each section, then `fast_gate.py done <step>`. Markers: fast-run.md#work-record -->", "",
             "## Request", "", *quoted, ""]
    hints = {**HINTS, **COVERAGE_HINTS} if run.get("coverage") else HINTS
    for step in steps_for(run):
        lines += [f"## {TITLES[step]}", "", f"<!-- gate: {hints[step]} -->", ""]
    return "\n".join(lines)


LAYOUT = ".agents/skills/ticketing/references/ticket-layout.md"
FAST_RUN = ".agents/skills/safe-engine/references/fast-run.md"
# run flag -> (method file, phrase): a check applies only when the methods the run reads define it
FLAGS = {"ticket_checks": (LAYOUT, "Definition of done"), "coverage": (LAYOUT, "Every criterion has"),
         "light": (FAST_RUN, "Light lane")}


def method_flags(bundle, project):
    """Run flags from the methods this run reads: its bundle, else this project. Older methods leave them off."""
    root, flags = Path(bundle["root"] if bundle else project), {}
    for flag, (path, phrase) in FLAGS.items():
        try:
            flags[flag] = phrase in (root / path).read_text(encoding="utf-8")
        except (OSError, ValueError):
            flags[flag] = not bundle  # a product without a resolved bundle follows the current methods
    return flags


def bundle_receipt(project):
    """The entry resolver's selection for this project, if any (fast-run.md#the-gate)."""
    try:
        receipt = load(Path(project) / ".factory" / "entry-bundle.json")
        return {"root": receipt["bundle_root"], "revision": receipt["revision"]}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def ignore_factory(project):
    """Keep run records out of Git: add .factory/ to .gitignore when Git would track it."""
    import subprocess
    try:
        probe = subprocess.run(["git", "-C", str(project), "check-ignore", "-q", ".factory/fast/run.json"],
                               capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return "not checked (git unavailable)"
    if probe.returncode == 0:
        return ".factory/ already ignored"
    if probe.returncode != 1:
        return "not a Git repository; keep .factory/ out of version control"
    gitignore = Path(project) / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    gitignore.write_text(text + ("\n" if text and not text.endswith("\n") else "") + ".factory/\n", encoding="utf-8")
    return "added .factory/ to .gitignore"


def hook_status(project):
    """Hosts wired to call this gate: an enabled Claude Code plugin, or factory entries in Codex/Cursor hook files."""
    home = Path.home()
    found = []
    try:
        plugins = json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8")).get("enabledPlugins", {})
        if any(name.startswith("safe-engine@") and value is True for name, value in plugins.items()):
            found.append("Claude Code")
    except (OSError, ValueError, AttributeError):
        pass
    for name, folder in (("Codex", ".codex"), ("Cursor", ".cursor")):
        for base in (home, Path(project)):
            try:
                text = (base / folder / "hooks.json").read_text(encoding="utf-8")
            except OSError:
                continue
            if name not in found and ("fast_gate" in text or "run-gate" in text):
                found.append(name)
    return ", ".join(found) or "none detected: the gate records steps but nothing blocks; follow the order yourself"


def cmd_start(args):
    project = Path(native(args.project or os.getcwd())).resolve()
    if not project.is_dir():
        fail(f"Project directory not found: {project}")
    if not KEY.fullmatch(args.key):
        fail("Key: lowercase letter first, then lowercase letters, digits or hyphens (max 64)")
    try:
        request = Path(args.request_file).read_text(encoding="utf-8") if args.request_file else (args.request or "")
    except OSError as error:
        fail(f"Cannot read the request file: {error}")
    if not request.strip():
        fail("Give the owner's request verbatim with --request or --request-file")
    ledger = ledger_path(project)
    if ledger.exists():
        old = load(ledger)
        if not old.get("closed"):
            fail(f"Run '{old.get('key')}' is still open here; close it first")
        archive = ledger.parent / "archive" / f"{old.get('key')}-{old.get('closed_at', now())[:19].replace(':', '')}"
        archive.mkdir(parents=True, exist_ok=True)
        for item in (ledger, record_path(project)):
            if item.exists():
                os.replace(item, archive / item.name)
    product, bundle = args.kind == "product", bundle_receipt(project)
    run = {"version": VERSION, "key": args.key, "project": str(project), "mode": args.mode, "kind": args.kind,
           "ui": product if args.ui is None else args.ui, "data": product if args.data is None else args.data,
           "auth": args.auth, "request": request.strip(), "created": now(), "done": {}, "paused": None,
           "closed": False, "bundle": bundle, **method_flags(bundle, project)}
    if "analysis" not in steps_for(run):  # older hook copies still require it before build: mark it skipped
        run["done"]["analysis"] = {"at": now(), "skipped": "light lane"}
    save(ledger, run)
    record = record_path(project)
    if not record.exists():
        record.write_text(skeleton(run), encoding="utf-8")
    save(registry_path(project), {"project": str(project), "key": args.key, "sessions": []})
    git_note, hooks = ignore_factory(project), hook_status(project)
    log("run.start", key=args.key, project=str(project), mode=args.mode, kind=args.kind, bundle=run["bundle"], hooks=hooks)
    bundle = (f"{run['bundle']['root']} @ {run['bundle']['revision'][:12]}" if run["bundle"] else
              "no .factory/entry-bundle.json; run the entry's resolver first (skip only for factory maintenance)")
    print(status_text(run) + f"\nRecord: {record}\nBundle: {bundle}\nGit: {git_note}\nHooks: {hooks}")


def cmd_done(args):
    project, run = open_run(args.project)
    steps, step = steps_for(run), args.step
    if run.get("closed"):
        fail("This run is closed")
    if step not in steps:
        fail(f"'{step}' does not apply to this {run['mode']} {run['kind']} run. Steps: {', '.join(steps)}")
    earlier = [name for name in steps[:steps.index(step)] if name not in run["done"]]
    if earlier:
        fail("Finish first: " + ", ".join(earlier))
    record = sibling("fast_record")  # checks load only here; hooks never need them
    CHECKS, sections = record.CHECKS, record.sections
    try:
        all_sections = sections(record_path(project).read_text(encoding="utf-8", errors="replace"))
    except OSError as error:
        fail(f"Cannot read the work record: {error}")
    body = all_sections.get(TITLES[step].lower(), "")
    problems = (CHECKS[step](run, body, project=project, offline=args.offline, all_sections=all_sections)
                if body.strip() else [f"section '## {TITLES[step]}' is missing or empty"])
    if problems:
        log("step.refused", key=run["key"], step=step, problems=problems)
        fail(f"'{step}' not recorded:\n- " + "\n- ".join(problems))
    run["done"][step] = {"at": now(), **({"unverified": args.offline} if args.offline else {})}
    if step == "tickets":  # later ticket checks keep reading these even if the record drops one
        epic, subs = record.ticket_urls(body)
        run["tickets"] = list(dict.fromkeys(run.get("tickets", []) + epic + subs))
    run["paused"] = None
    save(ledger_path(project), run)
    log("step.done", key=run["key"], step=step, unverified=args.offline)
    print(status_text(run))


def cmd_status(args):
    print(status_text(open_run(args.project)[1]))


def cmd_pause(args, reason):
    project, run = open_run(args.project)
    run["paused"] = {"reason": reason, "at": now()} if reason else None
    save(ledger_path(project), run)
    log("run.pause" if reason else "run.resume", key=run["key"], reason=reason)
    print(status_text(run))


def cmd_close(args):
    project, run = open_run(args.project)
    if "handoff" not in run["done"] and not args.abandon:
        fail("Record the handoff first, or close --abandon \"<the owner's reason>\"")
    run.update(closed=True, closed_at=now(), abandoned=args.abandon, paused=None)
    save(ledger_path(project), run)
    try:
        registry_path(project).unlink()
    except FileNotFoundError:
        pass
    log("run.close", key=run["key"], abandoned=args.abandon)
    print(status_text(run))


# ---- hooks (every host; dialects in fast_hosts.py, wiring in fast_install.py) ----

def active_runs():
    """Open runs from the registry. One bad or unreachable entry never disables the others."""
    runs = []
    for entry in ACTIVE.glob("*.json"):
        try:
            registration = load(entry)
            run = load(ledger_path(registration["project"]))
        except FileNotFoundError:
            forget(entry)
            continue
        except Exception:  # noqa: BLE001 - malformed entry: skip it, keep gating the rest
            continue
        if isinstance(run, dict) and not run.get("closed") and run.get("version") == VERSION:
            runs.append((entry, registration, run))
    return runs


def forget(entry):
    """Drop a registration whose ledger is gone from a reachable folder; unmounted drives keep theirs."""
    try:
        if Path(load(entry)["project"]).parent.exists():
            entry.unlink(missing_ok=True)
    except Exception:  # noqa: BLE001 - cleanup is best effort
        pass


def owner(runs, path):
    """The run whose project contains path; the deepest project wins."""
    matches = [item for item in runs if inside(path, norm(item[2]["project"]))]
    return max(matches, key=lambda item: len(item[2]["project"]), default=None)


def mentioned(runs, command):
    flat = command.replace("\\", "/").lower()
    for item in runs:
        project = item[2]["project"].replace("\\", "/").lower()
        drive = re.match(r"^([a-z]):(/.*)$", project)
        if project in flat or (drive and f"/{drive.group(1)}{drive.group(2)}" in flat):
            return item
    return None


def bind(item, session):
    """Remember the session working on this run so its Stop and prompt hooks find it; best effort."""
    entry, registration, _ = item
    if not session or session in registration.get("sessions", []):
        return
    try:
        latest = load(entry)  # re-read: parallel hooks may have bound other sessions
        latest["sessions"] = (latest.get("sessions", []) + [session])[-20:]
        save(entry, latest)
        registration["sessions"] = latest["sessions"]
    except Exception as error:  # noqa: BLE001 - a locked or odd file must never cancel a deny
        log("hook.bind_failed", error=repr(error))


def refusal(item, path):
    """Why a write to path must wait, or None. Only this script ever writes the ledger."""
    project = item[2]["project"]
    if path == norm(ledger_path(project)):
        return f"writing {path}: run.json changes only through fast_gate.py commands"
    if not inside(path, norm(Path(project) / ".factory")) and open_before_build(item[2]):
        return f"writing {path}"
    return None


def deny_reason(run, what):
    blocked = open_before_build(run)
    steps = (f" Record these steps first: {', '.join(blocked)}. Fill .factory/fast/work-record.md and run "
             "`fast_gate.py done <step>` (fast-run.md). .factory/ stays writable.") if blocked else ""
    log("hook.deny", key=run["key"], what=what, blocked=blocked)
    return f"Factory {run['mode']} run '{run['key']}' blocks {what}.{steps}"


def pre_tool(event, runs, cwd, session):
    """Deny reason for a project write before the gate opens, or None. Sessions bind only through real work."""
    if event["tool"] == "edit":
        targets = [norm(path, cwd) for path in event["paths"]]
    elif event["tool"] == "shell":
        shell = sibling("fast_shell")
        targets = [norm(name, cwd) for name in shell.writes(event["command"])]
    else:
        return None
    for path in targets:
        item = owner(runs, path)
        if item:
            bind(item, session)
            reason = refusal(item, path)
            if reason:
                return deny_reason(item[2], reason)
    if event["tool"] == "shell":
        item = owner(runs, cwd)
        if item:
            bind(item, session)
        item = item or mentioned(runs, event["command"])
        if item and open_before_build(item[2]) and shell.scaffolds(event["command"]):
            bind(item, session)
            return deny_reason(item[2], "scaffold and install commands")
    return None


def mine(runs, cwd, session):
    bound = [item for item in runs if session and session in item[1].get("sessions", [])]
    item = owner(runs, cwd)
    if item and not bound:
        bind(item, session)
    return bound or ([item] if item else [])


def stop(event, runs, cwd, session):
    """Reason to keep working when a run is unfinished; once per stop, never for paused runs."""
    if event["again"]:
        return None  # one reminder per stop; never trap the session
    for _, _, run in mine(runs, cwd, session):
        if not run.get("paused"):
            step = next_step(run)
            log("hook.block_stop", key=run["key"], next=step)
            return (f"Factory {run['mode']} run '{run['key']}' is not finished. Next: "
                    f"{step or 'close'}. Continue it. Waiting on the owner? `fast_gate.py pause --reason \"...\"`. "
                    "The owner stopped it? `fast_gate.py close --abandon \"<their reason>\"`.")
    return None


def context(event, runs, cwd, session):
    lines = []
    for _, _, run in mine(runs, cwd, session)[:3]:
        line = (f"Factory {run['mode']} run '{run['key']}' at {run['project']}: next step "
                f"{next_step(run) or 'close'}; gate {'open' if not open_before_build(run) else 'closed (no source edits)'}")
        if run.get("paused"):
            line += f"; paused: {run['paused']['reason']}"
        lines.append(line + ". Method: .agents/skills/safe-engine/references/fast-run.md.")
    return "\n".join(lines) or None


def cmd_hook(host="claude"):
    """Answer one host hook event from stdin in that host's dialect. Fail open: never break the session."""
    try:
        runs = active_runs()
        if not runs:
            return 0
        hosts = sibling("fast_hosts")
        raw = json.loads(sys.stdin.buffer.read().decode("utf-8-sig") or "{}")  # hosts send UTF-8
        event = hosts.read(host, raw if isinstance(raw, dict) else {})
        cwd, session = norm(event["cwd"] or os.getcwd()), event["session"]
        if event["kind"] == "pre_tool":
            reason = pre_tool(event, runs, cwd, session)
            if reason:
                out, code = hosts.deny(host, reason)
                print(out) if out else print(reason, file=sys.stderr)
                log("hook.answer", host=host, hook_event=event["name"], answer="deny", exit=code)
                return code
        elif event["kind"] == "stop":
            reason = stop(event, runs, cwd, session)
            out = hosts.keep_going(host, reason) if reason else None
            if out:
                print(out)
                log("hook.answer", host=host, hook_event=event["name"], answer="keep_going")
        elif event["kind"] in ("prompt", "session"):
            text = context(event, runs, cwd, session)
            out = hosts.context(host, event["name"], text) if text else None
            if out:
                print(out)
    except Exception as error:  # noqa: BLE001 - any failure must leave the host session working
        log("hook.error", host=host, error=repr(error))
    return 0


def main():
    if sys.version_info < (3, 9):
        sys.exit("fast_gate.py needs Python 3.9+")  # non-zero: the hook launcher tries the next Python
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="backslashreplace")  # any path prints, whatever the console code page
    if sys.argv[1:2] == ["hook"] and not {"-h", "--help"} & set(sys.argv):  # hot path: skip argparse
        flags = " ".join(sys.argv[2:]).replace("--host=", "--host ").split()
        host = flags[flags.index("--host") + 1] if "--host" in flags[:-1] else "claude"
        sys.exit(cmd_hook(host))
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", help="Run project; default: nearest folder with .factory/fast/run.json")
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start", parents=[common], help="Begin a run and register it for hooks")
    start.add_argument("--key", required=True)
    start.add_argument("--mode", choices=MODES, default="fast")
    start.add_argument("--kind", choices=KINDS, required=True)
    for flag in ("ui", "data"):
        start.add_argument(f"--{flag}", dest=flag, action="store_true", default=None)
        start.add_argument(f"--no-{flag}", dest=flag, action="store_false", default=None)
    start.add_argument("--auth", action="store_true", help="The product has sign-in")
    start.add_argument("--request")
    start.add_argument("--request-file")
    done = sub.add_parser("done", parents=[common], help="Check and record one step")
    done.add_argument("step", choices=list(TITLES))
    done.add_argument("--offline", help="Record tickets, plan or handoff without reading tickets through gh, with the reason")
    sub.add_parser("status", parents=[common])
    pause = sub.add_parser("pause", parents=[common], help="Waiting on the owner; lets the session stop")
    pause.add_argument("--reason", required=True)
    sub.add_parser("resume", parents=[common])
    close = sub.add_parser("close", parents=[common])
    close.add_argument("--abandon", help="The owner stopped the run: their reason")
    install = sub.add_parser("install", help="Install the entry skills and gate hooks for one host")
    install.add_argument("--host", required=True, choices=("claude", "codex", "cursor", "other"),
                         help="other: entry skills only, for agents you wire by hand")
    install.add_argument("--project", help="Install into this project instead of your user folders")
    hook = sub.add_parser("hook", help="Answer one host hook event from stdin")
    hook.add_argument("--host", default="claude", help="claude, codex, cursor, or any other hook-capable agent")
    args = parser.parse_args()
    actions = {"start": cmd_start, "done": cmd_done, "status": cmd_status, "close": cmd_close, "hook": lambda a: sys.exit(cmd_hook(a.host)),
               "install": lambda a: sibling("fast_install").install(a.host, a.project, log=lambda line: (print(line), log("install.write", line=line))),
               "pause": lambda a: cmd_pause(a, a.reason), "resume": lambda a: cmd_pause(a, None)}
    actions[args.command](args)


if __name__ == "__main__":
    main()
