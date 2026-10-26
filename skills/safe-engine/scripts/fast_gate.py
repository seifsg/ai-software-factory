"""Fast/Lucky run gate: record each factory step, check it, and answer host hooks.

Method: .agents/skills/safe-engine/references/fast-run.md#the-gate. Python 3.9+, stdlib only.
Step checks live in fast_record.py (loaded by `done`, and by `start` for a UI snapshot; never by hooks), the record
skeleton's hints in fast_hints.py (`start` only), the owner's dashboard in fast_card.py.
Checks prove a step was recorded, not that it was good.
"""
import json
import os
import re
import sys
from pathlib import Path
# argparse, datetime, hashlib, subprocess and tempfile load lazily: hooks run on every tool call and must start fast.

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
    ("show", MODES, KINDS, "show_first"),
    ("done-run", ("fast",), KINDS, None),
    ("done-run", ("lucky",), KINDS, "ticket_checks"),
    ("handoff", MODES, KINDS, None),
)
TITLES = {"research": "Research", "kickoff": "Kickoff", "tickets": "Tickets", "analysis": "Analysis",
          "plan": "Plan", "design": "Design", "schema": "Schema", "build": "Build log",
          "show": "Show", "done-run": "Done-run", "handoff": "Handoff"}
HERE = Path(__file__).resolve().parent  # siblings: fast_record, fast_shell, fast_guard, fast_progress, fast_card


def sibling(name):
    """Import a module that sits beside this script, whatever the caller's sys.path. Its bytecode cache lives in
    the gate's home and is written even where the host turns bytecode writing off: later hooks load it instead of
    compiling it, and no cache ever lands in the plugin folder or a project. Unwritable: it just compiles."""
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    keep = sys.dont_write_bytecode, sys.pycache_prefix
    sys.dont_write_bytecode, sys.pycache_prefix = False, str(HOME / "pycache")
    try:
        return __import__(name)
    finally:
        sys.dont_write_bytecode, sys.pycache_prefix = keep


def now():
    """UTC time, seconds. datetime loads here: most hook calls never need it."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(event, **data):
    """Append one JSON line to the gate log; never raise, so logging cannot break a hook."""
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        if LOG.exists() and LOG.stat().st_size > 1_000_000:
            os.replace(LOG, LOG.with_name("gate.log.1"))
        fields = {key: value[:1000] if isinstance(value, str) else value for key, value in data.items()}
        with LOG.open("a", encoding="utf-8") as out:  # truncate fields, never the line: each line stays JSON
            out.write(json.dumps({"t": now(), "event": event, **fields}, default=str) + "\n")
    except OSError:
        pass


store = sibling("fast_ledger")  # paths, the run state in the gate home, its project mirror and the run registry
VERSION, FAST, LEDGER, RECORD = store.VERSION, store.FAST, store.LEDGER, store.RECORD
native, norm, inside, load, load_stamped = store.native, store.norm, store.inside, store.load, store.load_stamped
ledger_path, record_path, save = store.ledger_path, store.record_path, store.save


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def put(project, run):
    """Write the run state to the gate home, then its mirror for agents to read; a failed mirror never fails."""
    save(state_path(project), run)
    mirror(project, run)
    found = unseen(project, state_path(project))
    if view(project, run) and found:
        mark(project, VIEWED, found[0])  # the next hook need not write it again


def view_id(project, key):
    """The view's id: the run key plus its project's registry hash, so same-key runs in two projects never collide."""
    return f"{key}-{registry_path(project).stem[:6]}"


def view(project, run, agents=None):
    """Rewrite the owner's live view of this run (fast_view.py); True when written. A failure is logged, never raised."""
    try:
        entry = registry_path(project)
        registration = load(entry) if entry.is_file() else {}
        sessions = len(sessions_of(registration)) if isinstance(registration, dict) else 0
        sibling("fast_view").write(HOME / "view", project, run, steps_for(run), sessions, agents,
                                   vid=view_id(project, run["key"]))
        return True
    except Exception as error:  # noqa: BLE001 - the view is a courtesy: the run's state is already saved
        log("view.write_failed", key=run.get("key"), error=repr(error))
        return False


def mirror(project, run):
    """Rewrite the project's run.json from the run state; a failure is logged, never raised."""
    try:
        save(ledger_path(project), run)
    except OSError as error:
        log("state.mirror_failed", key=run["key"], error=repr(error))


SHOWN, SEEN, VIEWED = "shown", "seen", "viewed"  # progress claims; newest change shown, and written to the view
PROMPTS, VIEW_EVERY = "prompts", 6  # prompt counter; the live view's link shows on the first prompt and every sixth after


def shown_path(project):
    return Path(project, *FAST, SHOWN)  # progress already shown to the owner (fast_card.py)


def claims_path(project, run):
    """This run's progress claims, named by its start time: claims another run left never hide its ticks."""
    return shown_path(project) / (re.sub(r"\D", "", str(run.get("created") or ""))[:14] or "run")


def registry_path(project):
    return store.registry_path(ACTIVE, project)


def state_path(project):
    return store.state_path(registry_path(project))


def home_run(project):
    """The run the gate home holds for project: the open one (an older run moves home here), else the last closed
    one, else a lost stand-in."""
    entry = registry_path(project)
    try:
        registration = load(entry)
    except (OSError, ValueError):
        registration = None
    if not isinstance(registration, dict):
        closed = None if store.state_path(entry).exists() else store.closed_run(entry)
        if closed:
            return closed
        registration = {}
    return store.state(entry, {**registration, "project": str(project)}, log)


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
    """The given project, else the registered one holding cwd, else the nearest folder above cwd with a home state."""
    if given:
        return Path(native(given)).resolve()
    here = Path.cwd().resolve()
    found = store.registered(ACTIVE, here)
    if found:
        return Path(found)
    for folder in (here, *here.parents):
        if state_path(folder).is_file():
            return folder
    fail("No Fast/Lucky run here. Start one: fast_gate.py start --project <dir> ...")


def lost_text(project):
    """Why the gate cannot read the run here, and the owner's way on: close a lost run, or bring one in from elsewhere."""
    elsewhere = None if registry_path(project).is_file() else store.readable(project)
    if well_formed(elsewhere):
        return (f"No run state for {project} in this gate home ({HOME / 'runs'}); its run.json records a run from "
                f"{elsewhere['project']}. Only on the owner's instruction, bring it in: fast_gate.py rehome --project "
                f"\"{project}\" --from \"{elsewhere['project']}\"")
    return (f"No readable run state for {project} in {HOME / 'runs'}, so its gate stays closed. The owner closes "
            f"it: fast_gate.py close --project \"{project}\" --abandon \"<reason>\"")


def well_formed(run):
    """An open run of this version whose fields the gate reads have the right shapes: the only mirror it carries home."""
    return bool(run and not run.get("closed") and KEY.fullmatch(str(run.get("key")))
                and isinstance(run.get("project"), str) and run.get("mode") in MODES and run.get("kind") in KINDS
                and isinstance(run.get("done"), dict) and isinstance(run.get("paused") or {}, dict)
                and isinstance(run.get("moves") or [], list))


def open_run(given):
    project = find_project(given)
    run = home_run(project)
    if run.get("lost"):
        fail(lost_text(project))
    return project, run


def status_text(run, all_sections=None):
    """The owner's run card (pause reason first, and the steps still to come), then the run, gate and next step."""
    if all_sections is None:
        all_sections = sibling("fast_progress").read(record_path(run["project"]))
    blocked = open_before_build(run)
    lines = [sibling("fast_card").card(run, steps_for(run), all_sections, now(), left=True),
             f"{run['mode']} {run['kind']} run '{run['key']}' at {run['project']}"
             f" (ui={run.get('ui')}, data={run.get('data')}, auth={run.get('auth')})",
             "Gate: " + ("open, source edits allowed" if not blocked else "closed until " + ", ".join(blocked)),
             "Next: " + ("closed" if run.get("closed") else next_step(run) or "close")]
    lines += list(filter(None, [sibling("fast_pr_policy").notice(HOME, run)]))
    if run.get("show_first"):
        lines.append(sibling("fast_show").notice(run["project"], run))
    return "\n".join(lines)


def skeleton(run):
    quoted = ["> " + line for line in run["request"].splitlines()]  # quoted: request headings never become sections
    lines = [f"# {run['key']}: {run['mode']} {run['kind']} run", "",
             "<!-- Fill each section, then `fast_gate.py done <step>`. Markers: fast-run.md#work-record -->", "",
             "## Request", "", *quoted, ""]
    hints = sibling("fast_hints").record_hints(run)
    for step in steps_for(run):
        lines += [f"## {TITLES[step]}", "", f"<!-- gate: {hints[step]} -->", ""]
    return "\n".join(lines)


LAYOUT = ".agents/skills/ticketing/references/ticket-layout.md"
FAST_RUN = ".agents/skills/safe-engine/references/fast-run.md"
UX = ".agents/skills/ux-quality/SKILL.md"
PR = ".agents/skills/how-to-make-a-pr/SKILL.md"
# run flag -> (method file, phrase): a check applies only when the methods the run reads define it
FLAGS = {"ticket_checks": (LAYOUT, "Definition of done"), "coverage": (LAYOUT, "Every criterion has"),
         "light": (FAST_RUN, "Light lane"), "outcomes": (FAST_RUN, "what the owner can do once it is done"),
         "hidden_checks": (FAST_RUN, "**Hidden checks:**"),
         "scans": (FAST_RUN, "**Secrets:**"), "ux_rules": (UX, "| U10 |"), "pr_proof": (FAST_RUN, "`**PR:**`"),
         "credit": (PR, "references/credit.md"), "pr_demo": (PR, "**Visual:**"), "briefs": (FAST_RUN, "**Ports:**"),
         "worth": (FAST_RUN, "**Findings:**"), "check_selection": (FAST_RUN, "Reasoned proof selection"),
         "show_first": (FAST_RUN, "Look, Show, Prove, Ship")}


def method_flags(bundle, project):
    """Run flags from the methods this run reads: its bundle, else this project. Older methods leave them off."""
    root, flags = Path(bundle["root"] if bundle else project), {}
    for flag, (path, phrase) in FLAGS.items():
        try:
            flags[flag] = phrase in (root / path).read_text(encoding="utf-8")
        except (OSError, ValueError):
            flags[flag] = not bundle and flag not in ("show_first", "check_selection")  # New proof contracts need resolved methods.
    return flags


def bundle_receipt(project):
    """The entry resolver's selection for this project, if any (fast-run.md#the-gate)."""
    try:
        receipt = load(Path(project) / ".factory" / "entry-bundle.json")
        return {"root": receipt["bundle_root"], "revision": receipt["revision"]}
    except (OSError, ValueError, KeyError, TypeError):
        return None


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
    if registry_path(project).is_file():
        fail(f"Run '{home_run(project).get('key')}' is still open here; close it first (a lost one: "
             f"fast_gate.py close --project \"{project}\" --abandon \"<reason>\")")
    archive_run(project)
    forget_shown(project)
    product, bundle = args.kind == "product", bundle_receipt(project)
    if getattr(args, "design_port", False) and args.ui is False:
        fail("--design-port is UI work; remove --no-ui")
    run = {"version": VERSION, "key": args.key, "project": str(project), "mode": args.mode, "kind": args.kind,
           "ui": product if args.ui is None else args.ui, "data": product if args.data is None else args.data,
           "auth": args.auth, "request": request.strip(), "created": now(), "done": {}, "paused": None,
           "closed": False, "bundle": bundle, "pr_instance": os.urandom(16).hex(), **method_flags(bundle, project)}
    run.update(sibling("fast_pr_policy").start(HOME))
    if getattr(args, "design_port", False):
        run.update(design_port=True, ui=True)
    run["show_first"] = bool(run.get("show_first") and run["ui"])
    if "analysis" not in steps_for(run):  # older hook copies still require it before build: mark it skipped
        run["done"]["analysis"] = {"at": now(), "skipped": "light lane"}
    if run.get("ux_rules") and not run["ui"]:  # only these runs later ask which UI files they changed
        run.update(sibling("fast_record").ui_start(project))
    setup = sibling("fast_setup")
    git_note, hooks = setup.ignore_factory(project), setup.hook_status(project)
    scratch = setup.scratch_path(HOME, run)
    put(project, run)
    scratch.mkdir(parents=True, exist_ok=True)  # after the state: a failed start leaves no folder behind
    record = record_path(project)
    if not record.exists():
        record.write_text(skeleton(run), encoding="utf-8")
    save(registry_path(project), store.new_registration(project, args.key))
    log("run.start", key=args.key, project=str(project), mode=args.mode, kind=args.kind, bundle=run["bundle"], hooks=hooks)
    bundle = (f"{run['bundle']['root']} @ {run['bundle']['revision'][:12]}" if run["bundle"] else
              "no .factory/entry-bundle.json: run the entry's resolver first, except for factory maintenance")
    print(status_text(run) + f"\n{sibling('fast_release').card(run, HOME)}\nRecord: {record}\nBundle: {bundle}\n"
          f"Git: {git_note}\nHooks: {hooks}\n" + setup.TEXT.format(scratch))


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
    record = sibling("fast_record")  # checks load here and in `start`; hooks never need them
    CHECKS, sections = record.CHECKS, record.sections
    try:
        all_sections = sections(record_path(project).read_text(encoding="utf-8", errors="replace"))
    except OSError as error:
        fail(f"Cannot read the work record: {error}")
    body = all_sections.get(TITLES[step].lower(), "")
    checked = sibling("fast_pr_policy").effective(HOME, run) if step == "handoff" else run
    problems = (CHECKS[step](checked, body, project=project, offline=args.offline, all_sections=all_sections, runs=active_runs)
                if body.strip() else [f"section '## {TITLES[step]}' is missing or empty"])
    if problems:
        log("step.refused", key=run["key"], step=step, problems=problems)
        fail(f"'{step}' not recorded:\n- " + "\n- ".join(problems))
    run["done"][step] = {"at": now(), **({"unverified": args.offline} if args.offline else {})}
    if step == "handoff" and checked.get("pr_policy"):
        run["done"][step]["pr_policy"] = checked["pr_policy"]["digest"]
    if step in ("kickoff", "tickets") and record.run_size(all_sections) and "size" not in run:
        run.update(size=record.run_size(all_sections), size_at=step)  # frozen: editing the line later skips nothing
    if step == "plan":  # who owes the epic's integration todos is read from the plan as recorded here
        run["todos"] = list(dict.fromkeys(run.get("todos", []) + [f"T{n}" for n in record.todo_ids(all_sections)]))
        if run.get("check_selection"):
            sibling("fast_checks").freeze_ownership(run)
        run["ports"] = sibling("fast_briefs").ports(record.marker(body, "Ports"))  # later lanes' plans avoid them
    if step == "tickets":  # later ticket checks keep reading these even if the record drops one
        epic, subs = record.ticket_urls(body)
        run["tickets"] = list(dict.fromkeys(run.get("tickets", []) + epic + subs))
    run["paused"] = None
    put(project, run)
    log("step.done", key=run["key"], step=step, unverified=args.offline)
    print(status_text(run, all_sections))


def cmd_scratch(args):
    """Print the open run's scratch folder, making it again if it went (or for a run started before scratch folders)."""
    scratch = sibling("fast_setup").scratch_path(HOME, open_run(args.project)[1])
    if scratch is None:
        fail("This run's key or start time is malformed, so it has no scratch folder")
    scratch.mkdir(parents=True, exist_ok=True)
    print(scratch)


def cmd_status(args):
    run = open_run(args.project)[1]
    sibling("fast_pr_policy").notice(HOME, run, strict=True)
    print(status_text(run) + "\n" + sibling("fast_release").card(run, HOME))


def cmd_pause(args, reason):
    project, run = open_run(args.project)
    run["paused"] = {"reason": reason, "at": now()} if reason else None
    put(project, run)
    log("run.pause" if reason else "run.resume", key=run["key"], reason=reason)
    print(status_text(run))


def cmd_try(args):
    """Record how the owner tries a finished todo's result: one checked line in the Build log, then the live view."""
    project, run = open_run(args.project)
    if run.get("closed"):
        fail("This run is closed")
    if not re.fullmatch(r"[Tt]?\d+", args.todo):
        fail("Name the todo by its ID, such as T3")
    kind, value = next((kind, getattr(args, kind)) for kind in ("cmd", "url", "file") if getattr(args, kind))
    n, views, record = str(int(args.todo.lstrip("Tt"))), sibling("fast_view"), record_path(project)
    problem = views.try_problem(project, sibling("fast_progress").read(record), n, kind, value)
    if problem:
        fail(f"Try target refused: {problem}. Form: fast_gate.py try T3 --cmd \"<command>\" | --url <http(s) link> | "
             "--file <path inside the project>")
    try:
        line = views.add_try(record, n, kind, value)
    except (OSError, ValueError) as error:
        fail(f"Cannot record the Try line: {error}")
    view(project, run)
    log("run.try", key=run["key"], todo=f"T{n}", kind=kind)
    print(f"Recorded in the Build log: {line}")


def cmd_view(args):
    """Serve the owner's live view on 127.0.0.1 until stopped, or write it as one snapshot file."""
    views, keep = sibling("fast_view"), set()
    try:
        scope = views.scope_for(native(args.project) if args.project is not None else None, args.all_projects)
        if args.project is None and scope["kind"] == "folder":
            project = store.registered(ACTIVE, os.getcwd())
            if project:
                scope = views.scope_for(project)
    except ValueError as error:
        log("view.scope_failed", reason="project_unavailable")
        fail(str(error))
    for _, _, run in active_runs():  # every open run shows, even one started before the view existed
        if not run.get("lost"):
            view(run["project"], run)
            keep.add(view_id(run["project"], run["key"]))
    views.prune(HOME / "view", keep)  # runs closed while lost, or left by an older home
    if args.snapshot:
        print(f"Snapshot: {views.snapshot(HOME / 'view', args.snapshot, scope)}")
        return
    running = views.live_url(HOME / "view", scope)
    log("view.serve", port=args.port, scope=scope["id"], kind=scope["kind"], reused=bool(running))
    if running:
        print(f"Live view already running: {running}")
        return
    views.serve(HOME / "view", args.port, scope=scope,
                log=lambda url: print(f"Live view: {url}  (Ctrl+C stops it)", flush=True))


def cmd_close(args):
    project = Path(store.registered(ACTIVE, native(args.project or os.getcwd())) or find_project(args.project))
    run = home_run(project)
    if run.get("lost"):
        return close_lost(project, args.abandon) if args.abandon else fail(lost_text(project))
    if "handoff" not in run["done"] and not args.abandon:
        fail("Record the handoff first, or close --abandon \"<the owner's reason>\"")
    if not args.abandon:
        problems = sibling("fast_design").problems(run, project, final=True)
        problems += sibling("fast_show").completion_problems(run, project)
        problems += sibling("fast_checks").problems(run, project, final=True)
        if problems:
            fail("\n".join(problems))
        sibling("fast_pr_policy").close(HOME, run)
    run.update(closed=True, closed_at=now(), abandoned=args.abandon, paused=None)
    put(project, run)
    entry = registry_path(project)
    entry.unlink(missing_ok=True)
    try:  # closed states leave runs/: hooks list only open ones
        store.closed_path(entry).parent.mkdir(parents=True, exist_ok=True)
        os.replace(store.state_path(entry), store.closed_path(entry))
    except OSError as error:
        log("state.retire_failed", key=run["key"], error=repr(error))  # it stays closed in runs/: hooks skip it
    forget_shown(project)
    log("run.close", key=run["key"], abandoned=args.abandon)
    print(status_text(run) + drop_scratch(run["key"], sibling("fast_setup").scratch_path(HOME, run)))


def drop_scratch(key, *folders):
    """Remove a closed run's scratch folders without following links; the line that says what stayed, else ''."""
    left = []
    for folder in filter(None, folders):
        mine = []
        sibling("fast_setup").remove(folder, mine)
        log("run.scratch_left" if mine else "run.scratch_removed", key=key, path=str(folder), count=len(mine),
            first=mine[:1])
        left += mine
    return f"\nScratch: {len(left)} item(s) left, first: {left[0]}" if left else ""


def close_lost(project, reason):
    """Close a run with no readable home state: drop its registration and the broken state, and keep a closed record so
    its mirror never comes back through rehome (the next start archives it)."""
    entry = registry_path(project)
    if not entry.is_file():
        fail(f"No registered run at {project}; nothing was closed")
    try:
        key = load(entry).get("key")
    except (OSError, ValueError, AttributeError):
        key = None
    entry.unlink()
    try:
        state_path(project).unlink(missing_ok=True)
    except OSError:
        pass  # the hooks stand down either way; the next start replaces it
    try:
        save(store.closed_path(entry), {"version": VERSION, "key": key if KEY.fullmatch(str(key)) else "run",
                                        "project": str(project), "mode": "fast", "kind": "change", "done": {},
                                        "paused": None, "closed": True, "closed_at": now(), "abandoned": reason})
    except OSError as error:
        log("state.retire_failed", key=key, error=repr(error))
    forget_shown(project)
    log("run.close", project=str(project), abandoned=reason, lost=True)
    left = drop_scratch(key, *sibling("fast_setup").lost_scratch(HOME, key, project))
    print(f"Closed the run at {project} without a readable run state. Reason: {reason}{left}")


HELD = {  # what the gate home holds for a folder: how a refusal names it, and the owner's way on
    "open": ("an open run", "continue it there with status or resume"),
    "lost": ("a lost run", "its gate stays closed until the owner closes it there with close --abandon"),
    "closed": ("a closed run", "a closed run never comes back in: bring the run into another folder"),
    "nested": ("a run", "runs never nest: bring the run into a folder of its own"),
}


def cmd_rehome(args):
    """The owner brings in an open run whose state sits in another gate home (another machine or folder): its run.json
    comes home once, only where this gate home holds nothing in, around or inside either folder, so no run gated
    here can fall back to a project copy."""
    project = Path(native(args.project or os.getcwd())).resolve()
    run = store.readable(project)
    if not well_formed(run):
        fail(f"No open, well-formed run to bring in at {ledger_path(project)}; nothing was moved")
    if norm(run["project"]) != norm(args.source):
        fail(f"{ledger_path(project)} records its run at {run['project']}, not {args.source}; nothing was moved")
    for folder in (project, args.source):
        held = store.held(ACTIVE, folder)
        if held:
            what, advice = HELD[held[0]]
            fail(f"This gate home holds {what} at {held[1]}; nothing was moved: {advice}")
    source, receipt, local = run["project"], bundle_receipt(project), None
    setup = sibling("fast_setup")
    scratch = setup.scratch_path(HOME, run)  # named by the old folder's tag: it follows the run below
    if receipt and not Path(native(str(receipt["root"]))).is_dir():
        revision = str(receipt["revision"])
        local = HOME / "bundles" / revision
        if not (re.fullmatch(r"[0-9a-f]{40}", revision) and (local / ".agents/skills/safe-engine/SKILL.md").is_file()):
            fail(f"The run's bundle {revision} is not on this machine; nothing was moved. Bring it first with the "
                 f"launcher's resolve_bundle.py --ref {revision}")
        run["bundle"] = {"root": str(local), "revision": revision}
    run["project"] = str(project)
    run["moves"] = [*(run.get("moves") or []), {"from": source, "at": now(),
                                                 **({"bundle_from": str(receipt["root"])} if local else {})}]
    card = status_text(run)  # a run the gate cannot show is refused before anything is written
    if local:  # the same revision, found here: only the receipt's path changes
        path = Path(project, ".factory", "entry-bundle.json")
        save(path, {**load(path), "bundle_root": str(local)})
    try:
        save(state_path(project), run, new=True)  # first writer wins: a parallel rehome never replaces it
    except FileExistsError:
        fail(f"The run at {project} was brought in meanwhile: fast_gate.py status --project \"{project}\"")
    log("run.rehome", key=run["key"], source=source, project=str(project), bundle=run.get("bundle"))
    try:
        save(registry_path(project), store.new_registration(project, run["key"]))
    except OSError as error:  # the open state re-registers on the next hook or gate command
        log("state.register_failed", key=run["key"], error=repr(error))
    mirror(project, run)
    moved = setup.scratch_path(HOME, run)
    if scratch and moved and scratch.is_dir() and not os.path.lexists(moved):
        os.replace(scratch, moved)
    git_note = setup.ignore_factory(project)
    print(card + f"\nBrought in from {source}." + (f"\nBundle: {local}" if local else "") + f"\nGit: {git_note}"
          "\nContinue the run on this machine only: compare this card with status on the old machine, then the owner "
          "retires the copy there with close --abandon.")


def archive_run(project):
    """Set the last run's mirror and record aside, named by its key and close time, before a new run starts."""
    ledger, record, entry = ledger_path(project), record_path(project), registry_path(project)
    old = store.closed_run(entry)
    if not (old or ledger.exists()):
        return  # first run here: a record written before start is kept
    old = old or store.readable(project) or {}
    key = old.get("key") if KEY.fullmatch(str(old.get("key"))) else "run"  # the mirror is the agent's to write
    archive = ledger.parent / "archive" / f"{key}-{re.sub(r'[^0-9T-]', '', str(old.get('closed_at') or now())[:19])}"
    archive.mkdir(parents=True, exist_ok=True)
    for item in (ledger, record):
        if item.exists():
            os.replace(item, archive / item.name)
    try:
        store.closed_path(entry).unlink(missing_ok=True)  # archived: the gate home keeps no stale run
    except OSError:
        pass  # a locked file: the next start retries


def forget_shown(project):
    """Drop the shown-progress claims and stamp: a closed or new run starts its owner messages fresh."""
    import shutil
    shutil.rmtree(shown_path(project), ignore_errors=True)
    for stamp in (SEEN, VIEWED, PROMPTS):
        Path(project, *FAST, stamp).unlink(missing_ok=True)


# ---- hooks (every host; dialects in fast_hosts.py, wiring in fast_install.py) ----

def active_runs():
    """Open runs from the gate home (fast_ledger.py): lost ones included, gate closed."""
    return store.active_runs(ACTIVE, log)


def sessions_of(registration):
    """The sessions bound to a run; [] for a missing or malformed value, so a deny never trips on it."""
    sessions = registration.get("sessions")
    return sessions if isinstance(sessions, list) else []


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
    if not session or session in sessions_of(registration):
        return
    try:
        latest = load(entry)  # re-read: parallel hooks may have bound other sessions
        latest["sessions"] = (sessions_of(latest) + [session])[-20:]
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


def deny_reason(run, what, advice=None):
    """Logged deny text: what is blocked, then the advice, or the steps that unblock it."""
    blocked = open_before_build(run)
    steps = (f" Record first: {', '.join(blocked)}, in .factory/fast/work-record.md, then `fast_gate.py done <step>`"
             " (fast-run.md); .factory/ stays writable.") if blocked else ""
    if run.get("lost"):
        steps = (" Its run state in the gate home is missing or unreadable, so the gate stays closed: the owner "
                 f"runs `fast_gate.py close --project \"{run['project']}\" --abandon \"<reason>\"`.")
        advice = (advice or "") + steps
    log("hook.deny", key=run["key"], what=what, blocked=blocked, lost=bool(run.get("lost")))
    return f"Factory {run['mode']} run '{run['key']}' blocks {what}.{advice or steps}"


def guard(command, runs, cwd, session, dialect=None):
    """Deny reason for a destructive command in any step of the run owning cwd, else this session's or the named one.
    dialect: "bash" or "windows" when the host names its shell, else None (both readings must pass)."""
    item = owner(runs, cwd) or next(iter(mine(runs, cwd, session)), None) or mentioned(runs, command)
    rule = item and sibling("fast_guard").Judge(norm(item[2]["project"]), norm, inside, str(HOME),
                                                lambda: sibling("fast_setup").scratch_path(HOME, item[2])).rule(
        command, cwd, dialect)
    return rule and deny_reason(item[2], rule, " Ask the owner to run it or to approve another approach.")


def where(cds, cwd):
    """The folder a shell write runs in after its cd targets; an unknown one ('', a variable) keeps the folder."""
    for target in cds:
        path = os.path.expandvars(os.path.expanduser(target))
        cwd = cwd if not path or "$" in path else norm(path, cwd)
    return cwd


def pre_tool(event, runs, cwd, session):
    """Deny reason for a destructive command, or a project write before the gate opens, or None.
    Sessions bind only through real work."""
    if event["tool"] == "shell":
        reason = guard(event["command"], runs, cwd, session, event.get("dialect"))
        if reason:
            return reason
        item = owner(runs, cwd) or mentioned(runs, event["command"])
        if item and item[2].get("show_first"):
            reason = sibling("fast_show").suite_guard(event["command"], item[2], item[2]["project"], event.get("dialect"))
            if reason:
                return deny_reason(item[2], reason)
    if event["tool"] == "edit":
        targets = [norm(path, cwd) for path in event["paths"]]
    elif event["tool"] == "shell":
        shell = sibling("fast_shell")
        targets = [norm(name, where(cds, cwd)) for cds, name in shell.writes(event["command"])]
    else:
        return None
    vault = (norm(ACTIVE), norm(HOME / "runs"), norm(HOME / "pr-proof")) if targets else ()
    for path in targets:
        if any(inside(path, folder) for folder in vault):  # the gate home's run files: only gate commands write them
            item = owner(runs, cwd) or next(iter(mine(runs, cwd, session)), None) or runs[0]
            return deny_reason(item[2], f"writing {path}: the gate home's run files change only through fast_gate.py")
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


def mine(runs, cwd, session, bind_cwd=True):
    """The runs this session works on: those it is bound to, else the one owning cwd (bound to it now)."""
    bound = [item for item in runs if session and session in sessions_of(item[1])]
    if bound:
        return bound
    item = owner(runs, cwd)
    if item and bind_cwd:
        bind(item, session)
    return [item] if item else []


def unseen(project, state):
    """(newest run state or record change, when progress was last shown, when the view was last written), or None
    when both are current. One stat, one directory scan and no reads, since this runs on every hooked tool call."""
    times = {}
    try:
        changed = os.stat(state).st_mtime_ns
        with os.scandir(os.path.join(project, *FAST)) as entries:
            for entry in entries:
                if entry.name in (RECORD, SEEN, VIEWED):
                    times[entry.name] = entry.stat().st_mtime_ns
    except OSError:
        return None
    stamp, seen, viewed = max(changed, times.get(RECORD, 0)), times.get(SEEN, 0), times.get(VIEWED, 0)
    return (stamp, seen, viewed) if stamp > min(seen, viewed) else None


def news(runs, cwd, session, show=True):
    """Progress the owner has not seen yet, or None; the live view is refreshed either way. show=False (a delegate,
    or a host without hook messages) refreshes only the view. Never raises: a deny decision must still print."""
    lines = []
    try:
        for entry, _, run in mine(runs, cwd, session, bind_cwd=False)[:3]:
            if not run.get("lost"):  # a lost run has no card
                lines += unseen_lines(run["project"], store.state_path(entry), show)
    except Exception as error:  # noqa: BLE001 - progress is a courtesy; the gate's decision comes first
        log("hook.error", where="news", error=repr(error))
    return "\n".join(lines) or None


def mark(project, name, stamp):
    """Record that the change at stamp was handled: SEEN (shown) or VIEWED (written to the view)."""
    path = Path(project, *FAST, name)
    path.touch()
    os.utime(path, ns=(stamp, stamp))


def unseen_lines(project, state, show=True):
    """One run's unseen progress, after refreshing its live view. The home state is re-read with its own mtime: a gate
    command landing during this hook is shown from its own state, now or by the next hook, never as a stale card."""
    found = unseen(project, state)
    if not found or not (found[0] > found[2] or show and found[0] > found[1]):
        return []
    stamp, seen, viewed = found
    try:
        run, ledger_ns = load_stamped(state)
    except (OSError, ValueError):
        return []  # mid-replace on Windows: show nothing now, the next hook retries with the new state
    if stamp > viewed and view(project, run):
        mark(project, VIEWED, stamp)
    if run.get("closed") or not (show and stamp > seen):
        return []  # the final report carries the close card
    at = now()  # loads datetime from the standard library before the card module's cached import
    lines = sibling("fast_card").news(run, steps_for(run), record_path(project), claims_path(project, run), ledger_ns, at)
    mark(project, SEEN, stamp)
    return lines


def reminder(runs, cwd, session):
    """The live view's link on the first prompt and every sixth after, for this session's run; else None. Prompts only:
    one small counter file per project, never a cost on tool calls. Never raises."""
    try:
        item = next((item for item in mine(runs, cwd, session, bind_cwd=False) if not item[2].get("lost")), None)
        if not item:
            return None
        path = Path(item[2]["project"], *FAST, PROMPTS)
        try:
            count = int(path.read_text(encoding="utf-8").strip() or 0) + 1
        except (OSError, ValueError):
            count = 1
        path.write_text(str(count), encoding="utf-8")
        if count % VIEW_EVERY != 1:
            return None
        views, project = sibling("fast_view"), item[2]["project"]
        url = views.live_url(HOME / "view", views.scope_for(project))
        return (f"🏭 Live view for this project: {url}" if url else
                f'🏭 Live view is off: start `fast_gate.py view --project "{project}"`, then open its link')
    except Exception as error:  # noqa: BLE001 - a courtesy; the prompt's answer comes first
        log("hook.error", where="reminder", error=repr(error))
        return None


def note_agents(runs, cwd, session, agents):
    """Record each explicit Stop observation, including unchanged work, so freshness stays truthful."""
    try:
        for entry, _, run in mine(runs, cwd, session, bind_cwd=False)[:3]:
            if not run.get("lost"):
                view(run["project"], load(store.state_path(entry)), agents)
    except Exception as error:  # noqa: BLE001 - a courtesy for the owner; the stop decision comes first
        log("hook.error", where="agents", error=repr(error))


def stop(event, runs, cwd, session):
    """Reason to keep working when a run is unfinished; once per stop, never for paused runs or background waits."""
    if event["again"]:
        return None  # one reminder per stop; never trap the session
    for _, _, run in mine(runs, cwd, session):
        if not run.get("paused"):
            step = next_step(run)
            if event.get("waiting"):  # a background agent's result starts a new turn, whose stop is checked again
                log("hook.wait_stop", key=run["key"], next=step)
                return None
            log("hook.block_stop", key=run["key"], next=step)
            return (f"Factory {run['mode']} run '{run['key']}' unfinished. Next: {step or 'close'}. Continue it; waiting "
                    "on the owner: `fast_gate.py pause --reason \"...\"`; owner stopped it: `fast_gate.py close --abandon "
                    "\"<their reason>\"`.")
    return None


def context(event, runs, cwd, session):
    lines = []
    for _, _, run in mine(runs, cwd, session)[:3]:
        line = (f"Factory {run['mode']} run '{run['key']}' at {run['project']}: next "
                f"{next_step(run) or 'close'}; gate {'open' if not open_before_build(run) else 'closed (no source edits)'}")
        if run.get("paused"):
            line += f"; paused: {run['paused']['reason']}"
        if run.get("lost"):
            line += "; its run state in the gate home is missing: the owner closes it with --abandon"
        lines.append(line + ". Method: .agents/skills/safe-engine/references/fast-run.md.")
        lines += list(filter(None, [sibling("fast_pr_policy").notice(HOME, run)]))
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
        out, code = None, 0
        if event["kind"] == "pre_tool":
            reason = pre_tool(event, runs, cwd, session)
            if reason:
                out, code = hosts.deny(host, reason)
                if out is None:
                    print(reason, file=sys.stderr)
                log("hook.answer", host=host, hook_event=event["name"], answer="deny", exit=code)
        elif event["kind"] == "stop":
            if event.get("agents") is not None:
                note_agents(runs, cwd, session, event["agents"])
            reason = stop(event, runs, cwd, session)
            out = hosts.keep_going(host, reason) if reason else None
            if out:
                log("hook.answer", host=host, hook_event=event["name"], answer="keep_going")
        elif event["kind"] in ("prompt", "session"):
            text = context(event, runs, cwd, session)
            out = hosts.context(host, event["name"], text) if text else None
        if event["kind"]:  # the view refreshes on every host; delegates' messages may not reach the owner
            show = hosts.notifies(host) and not event.get("delegate")
            lines = news(runs, cwd, session, show)
            if show and event["kind"] == "prompt":
                lines = "\n".join(line for line in (lines, reminder(runs, cwd, session)) if line) or None
            out = hosts.with_message(out, lines) if show else out
        if out:
            print(out)
        return code
    except Exception as error:  # noqa: BLE001 - any failure must leave the host session working
        log("hook.error", host=host, error=repr(error))
    return 0


def main():
    if sys.version_info < (3, 9):
        sys.exit("fast_gate.py needs Python 3.9+")  # non-zero: the hook launcher tries the next Python
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")  # the card's symbols survive any pipe
    if sys.argv[1:2] == ["hook"] and not {"-h", "--help"} & set(sys.argv):  # hot path: skip argparse
        flags = " ".join(sys.argv[2:]).replace("--host=", "--host ").split()
        host = flags[flags.index("--host") + 1] if "--host" in flags[:-1] else "claude"
        sys.exit(cmd_hook(host))
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", help="Run project; default: nearest folder with .factory/fast/run.json")
    sub = parser.add_subparsers(dest="command", required=True)
    sibling("fast_cleanup").parser(sub, common)
    sibling("fast_shots").parser(sub, common)
    sibling("fast_baseline").parser(sub, common)
    sibling("fast_release").parser(sub)
    sibling("fast_design_command").parser(sub, common)
    start = sub.add_parser("start", parents=[common], help="Begin a run and register it for hooks")
    start.add_argument("--key", required=True)
    start.add_argument("--mode", choices=MODES, default="fast")
    start.add_argument("--kind", choices=KINDS, required=True)
    start.add_argument("--design-port", action="store_true", help="UI reference port: require immutable coverage and likeness proof")
    for flag in ("ui", "data"):
        start.add_argument(f"--{flag}", dest=flag, action="store_true", default=None)
        start.add_argument(f"--no-{flag}", dest=flag, action="store_false", default=None)
    start.add_argument("--auth", action="store_true", help="The product has sign-in")
    start.add_argument("--request")
    start.add_argument("--request-file")
    sub.add_parser("pr-proof-method", help="Read the owner-selected PR method for any mode")
    adopt = sub.add_parser("adopt-pr-proof", help="Owner-authorized PR-only policy; preserves existing run state")
    target = adopt.add_mutually_exclusive_group(required=True)
    target.add_argument("--project")
    target.add_argument("--new-runs", action="store_true")
    adopt.add_argument("--method", required=True, help="Absolute canonical PR SKILL.md; preserve its whole folder")
    adopt.add_argument("--reason", required=True, help="Owner instruction and source authorizing adoption")
    done = sub.add_parser("done", parents=[common], help="Check and record one step")
    done.add_argument("step", choices=list(TITLES))
    done.add_argument("--offline", help="Record tickets, plan, handoff or a hidden-check done-run without reading tickets "
                                         "through gh, with the reason")
    sub.add_parser("status", parents=[common])
    sub.add_parser("scratch", parents=[common], help="Print the open run's scratch folder for throwaway data")
    pause = sub.add_parser("pause", parents=[common], help="Waiting on the owner; lets the session stop")
    pause.add_argument("--reason", required=True)
    sub.add_parser("resume", parents=[common])
    tried = sub.add_parser("try", parents=[common], help="How the owner tries a finished todo: a command, link or file")
    tried.add_argument("todo", help="The todo's ID, such as T3")
    target = tried.add_mutually_exclusive_group(required=True)
    for flag, what in (("cmd", "a command to run"), ("url", "an http(s) link"), ("file", "a path inside the project")):
        target.add_argument(f"--{flag}", help=what)
    shown = sub.add_parser("view", help="Serve this project's live progress on 127.0.0.1")
    scope = shown.add_mutually_exclusive_group()
    scope.add_argument("--project", help="Project folder; default: current folder and its repository worktrees")
    scope.add_argument("--all-projects", action="store_true", help="Explicitly show every project's progress")
    shown.add_argument("--port", type=int, default=8765, help="Default 8765; a busy port falls back to a free one")
    shown.add_argument("--snapshot", help="Write one HTML file with the current state instead of serving")
    close = sub.add_parser("close", parents=[common])
    close.add_argument("--abandon", help="The owner stopped the run: their reason")
    rehome = sub.add_parser("rehome", parents=[common],
                            help="Owner only: bring in an open run from another machine or folder")
    rehome.add_argument("--from", dest="source", required=True, help="The folder the run's run.json records")
    sibling("fast_round").parser(sub, common)
    sibling("fast_install").parser(sub)
    orchestrate = sub.add_parser("orchestrate", help="Set up an orchestrator to start factory sessions")
    sibling("fast_orchestrate").arguments(orchestrate)
    hook = sub.add_parser("hook", help="Answer one host hook event from stdin")
    hook.add_argument("--host", default="claude", help="claude, codex, cursor, or any other hook-capable agent")
    sibling("fast_show_command").parser(sub, common)
    sibling("fast_checks_command").parser(sub, common)
    args = parser.parse_args()
    actions = {"start": cmd_start, "done": cmd_done, "status": cmd_status, "close": cmd_close, "rehome": cmd_rehome,
               "try": cmd_try, "view": cmd_view, "scratch": cmd_scratch,
               "fix-round": lambda a: sibling("fast_round").run(a, sys.modules[__name__]),
               "checks": lambda a: sibling("fast_checks_command").run(a, sys.modules[__name__]),
               "design": lambda a: sibling("fast_design_command").run(a, sys.modules[__name__]),
               "show": lambda a: sibling("fast_show_command").run(a, sys.modules[__name__]),
               "prove": lambda a: sibling("fast_show_command").run(a, sys.modules[__name__]),
               "cleanup-temp": lambda a: sibling("fast_cleanup").run(a, sys.modules[__name__]),
               "shots": lambda a: sibling("fast_shots").run(a, sys.modules[__name__]),
               "recover-baseline": lambda a: sibling("fast_baseline").recover(a, sys.modules[__name__]),
               "adopt-pr-proof": lambda a: sibling("fast_pr_policy").adopt(a, sys.modules[__name__]),
               "pr-proof-method": lambda a: sibling("fast_pr_policy").method(HOME),
               "hook": lambda a: sys.exit(cmd_hook(a.host)),
               "install": lambda a: sibling("fast_install").install(a.host, a.project, auto=a.auto, channel=a.channel, codex_home=a.codex_home,
                                                                    log=lambda line: (print(line), log("install.write", line=line))),
               "orchestrate": lambda a: sibling("fast_orchestrate").run(a),
               "version": lambda a: sibling("fast_release").version(HOME), "verify": lambda a: sibling("fast_release").verify(a.path),
               "pause": lambda a: cmd_pause(a, a.reason), "resume": lambda a: cmd_pause(a, None)}
    actions[args.command](args)


if __name__ == "__main__":
    main()
