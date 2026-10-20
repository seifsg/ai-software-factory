"""Fast/Lucky run gate: record each factory step, check it, and answer host hooks.

Method: .agents/skills/safe-engine/references/fast-run.md#the-gate. Python 3.9+, stdlib only.
Step checks live in fast_record.py (loaded by `done`, and by `start` for a UI snapshot; never by hooks);
the owner's dashboard in fast_card.py.
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
              "Journeys line with counts and a minimum; current methods also Map, Hierarchy (naming the primary "
              "action) and Labels lines",
    "schema": "a 3-option table, a Chosen line, a fenced ERD or DDL",
    "build": "one line per plan todo: 'T1 pre: ... do: ... post: ...'",
    "done-run": ">=1 PASS line from using it, a Logs line; UI runs >=1 existing screenshot path. Current methods only: "
                "runs that changed UI files count as UI runs, and each UI run also needs a verdict line per U1..U10 "
                "(no open FAIL) and a UX judge line",
    "handoff": "Run, Statuses, Unverified, Follow-ups lines; sign-in runs a Dev sign-in line; "
               "online: each listed ticket fully ticked, or Blocked, Backlog or not planned",
}
COVERAGE_HINTS = {  # runs whose methods define coverage and the light lane
    "tickets": "an Epic URL line (a change: a Ticket line, its URL or 'none (why)'), a Backlog line; product/feature "
               "runs >=1 Sub-issue URL line and a Requested line (R1, R2, ...); online: each listed ticket is open "
               "with a Definition of done, and its criteria name every requested item not marked owner-deferred",
    "plan": "### Files, ### Critique, ### Phases, ### Todos ('T1 <title> → <result> (#ticket, A1)'), ### Whole plan, "
            "Logging and Efficiency lines (light lane: a Success line and ### Todos); online: each listed ticket has checklist items naming "
            "every criterion, they hold every plan todo, and criteria still name every requested item not "
            "owner-deferred",
    "handoff": "Run, Statuses, Unverified, Follow-ups lines; sign-in runs a Dev sign-in line; online: each listed "
               "ticket fully ticked, or Blocked, Backlog or not planned; items name every criterion and hold every "
               "plan todo; criteria name every requested item not owner-deferred",
}
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
    view(project, run)


def view(project, run, agents=None):
    """Rewrite the owner's live view of this run (fast_view.py); a failure is logged, never raised."""
    try:
        entry = registry_path(project)
        registration = load(entry) if entry.is_file() else {}
        sessions = len(sessions_of(registration)) if isinstance(registration, dict) else 0
        sibling("fast_view").write(HOME / "view", project, run, steps_for(run), sessions, agents)
    except Exception as error:  # noqa: BLE001 - the view is a courtesy: the run's state is already saved
        log("view.write_failed", key=run.get("key"), error=repr(error))


def mirror(project, run):
    """Rewrite the project's run.json from the run state; a failure is logged, never raised."""
    try:
        save(ledger_path(project), run)
    except OSError as error:
        log("state.mirror_failed", key=run["key"], error=repr(error))


SHOWN, SEEN, VIEWED = "shown", "seen", "viewed"  # progress claims; newest change shown, and written to the view


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
    """The owner's run card, then the step list, gate and next step."""
    if all_sections is None:
        all_sections = sibling("fast_progress").read(record_path(run["project"]))
    lines = [sibling("fast_card").card(run, steps_for(run), all_sections, now()), "",
             f"{run['mode']} {run['kind']} run '{run['key']}' at {run['project']}"
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
    hints = {**HINTS, **COVERAGE_HINTS} if run.get("coverage") else dict(HINTS)
    if run.get("scans"):  # Size starts with POC, MVP, production or none (<why>); Lucky has no kickoff to hold it
        if run["mode"] == "lucky" and run["kind"] != "change":
            hints["tickets"] += "; Lucky product/feature runs: a Size line"
        hints["done-run"] += "; sized MVP or production: Secrets, Dependencies, Static lines"
    if run.get("pr_proof"):
        hints["handoff"] += ("; a PR line naming the draft PR, whose Before & after section has one heading per outcome, "
                             "each Before and After with an image, a recording or a fenced block")
    if run.get("credit"):
        hints["handoff"] += "; the PR body's last line is the factory credit line (how-to-make-a-pr credit.md)"
    if sibling("fast_record").hidden(run):
        hints["done-run"] += "; a Hidden checks block: '#<n> <ID>: PASS' per criterion of every listed ticket"
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
         "credit": (PR, "references/credit.md")}


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
    run = {"version": VERSION, "key": args.key, "project": str(project), "mode": args.mode, "kind": args.kind,
           "ui": product if args.ui is None else args.ui, "data": product if args.data is None else args.data,
           "auth": args.auth, "request": request.strip(), "created": now(), "done": {}, "paused": None,
           "closed": False, "bundle": bundle, **method_flags(bundle, project)}
    if "analysis" not in steps_for(run):  # older hook copies still require it before build: mark it skipped
        run["done"]["analysis"] = {"at": now(), "skipped": "light lane"}
    if run.get("ux_rules") and not run["ui"]:  # only these runs later ask which UI files they changed
        run.update(sibling("fast_record").ui_start(project))
    setup = sibling("fast_setup")
    git_note, hooks = setup.ignore_factory(project), setup.hook_status(project)
    put(project, run)
    record = record_path(project)
    if not record.exists():
        record.write_text(skeleton(run), encoding="utf-8")
    save(registry_path(project), store.new_registration(project, args.key))
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
    record = sibling("fast_record")  # checks load here and in `start`; hooks never need them
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
    if step in ("kickoff", "tickets") and record.run_size(all_sections) and "size" not in run:
        run.update(size=record.run_size(all_sections), size_at=step)  # frozen: editing the line later skips nothing
    if step == "plan":  # who owes the epic's integration todos is read from the plan as recorded here
        run["todos"] = list(dict.fromkeys(run.get("todos", []) + [f"T{n}" for n in record.todo_ids(all_sections)]))
    if step == "tickets":  # later ticket checks keep reading these even if the record drops one
        epic, subs = record.ticket_urls(body)
        run["tickets"] = list(dict.fromkeys(run.get("tickets", []) + epic + subs))
    run["paused"] = None
    put(project, run)
    log("step.done", key=run["key"], step=step, unverified=args.offline)
    print(status_text(run, all_sections))


def cmd_status(args):
    print(status_text(open_run(args.project)[1]))


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
    line = views.add_try(record, n, kind, value)
    view(project, run)
    log("run.try", key=run["key"], todo=f"T{n}", kind=kind)
    print(f"Recorded in the Build log: {line}")


def cmd_view(args):
    """Serve the owner's live view on 127.0.0.1 until stopped, or write it as one snapshot file."""
    views = sibling("fast_view")
    for _, _, run in active_runs():  # every open run shows, even one started before the view existed
        if not run.get("lost"):
            view(run["project"], run)
    if args.snapshot:
        views.page(HOME / "view")
        print(f"Snapshot: {views.snapshot(HOME / 'view', args.snapshot)}")
        return
    log("view.serve", port=args.port)
    views.serve(HOME / "view", args.port, log=lambda url: print(f"Live view: {url}  (Ctrl+C stops it)", flush=True))


def cmd_close(args):
    project = Path(store.registered(ACTIVE, native(args.project or os.getcwd())) or find_project(args.project))
    run = home_run(project)
    if run.get("lost"):
        return close_lost(project, args.abandon) if args.abandon else fail(lost_text(project))
    if "handoff" not in run["done"] and not args.abandon:
        fail("Record the handoff first, or close --abandon \"<the owner's reason>\"")
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
    print(status_text(run))


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
    print(f"Closed the run at {project} without a readable run state. Reason: {reason}")


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
    git_note = sibling("fast_setup").ignore_factory(project)
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
    for stamp in (SEEN, VIEWED):
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
    steps = (f" Record these steps first: {', '.join(blocked)}. Fill .factory/fast/work-record.md and run "
             "`fast_gate.py done <step>` (fast-run.md). .factory/ stays writable.") if blocked else ""
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
    rule = item and sibling("fast_guard").Judge(norm(item[2]["project"]), norm, inside, str(HOME)).rule(
        command, cwd, dialect)
    return rule and deny_reason(item[2], rule, " Destructive commands are the owner's: ask the owner to run it, "
                                               "or to approve another approach.")


def pre_tool(event, runs, cwd, session):
    """Deny reason for a destructive command, or a project write before the gate opens, or None.
    Sessions bind only through real work."""
    if event["tool"] == "shell":
        reason = guard(event["command"], runs, cwd, session, event.get("dialect"))
        if reason:
            return reason
    if event["tool"] == "edit":
        targets = [norm(path, cwd) for path in event["paths"]]
    elif event["tool"] == "shell":
        shell = sibling("fast_shell")
        targets = [norm(name, cwd) for name in shell.writes(event["command"])]
    else:
        return None
    vault = (norm(ACTIVE), norm(HOME / "runs")) if targets else ()
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
    if stamp > viewed:
        view(project, run)
        mark(project, VIEWED, stamp)
    if run.get("closed") or not (show and stamp > seen):
        return []  # the final report carries the close card
    at = now()  # loads datetime from the standard library before the card module's cached import
    lines = sibling("fast_card").news(run, steps_for(run), record_path(project), claims_path(project, run), ledger_ns, at)
    mark(project, SEEN, stamp)
    return lines


def note_agents(runs, cwd, session, agents):
    """Keep the host's background agents in this session's run views when the list changed (Stop events only)."""
    try:
        for entry, _, run in mine(runs, cwd, session, bind_cwd=False)[:3]:
            if not run.get("lost") and sibling("fast_view").agents_of(HOME / "view", run["key"]) != agents:
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
        if run.get("lost"):
            line += "; its run state in the gate home is missing: the owner closes it with --abandon"
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
    done.add_argument("--offline", help="Record tickets, plan, handoff or a hidden-check done-run without reading tickets "
                                         "through gh, with the reason")
    sub.add_parser("status", parents=[common])
    pause = sub.add_parser("pause", parents=[common], help="Waiting on the owner; lets the session stop")
    pause.add_argument("--reason", required=True)
    sub.add_parser("resume", parents=[common])
    tried = sub.add_parser("try", parents=[common], help="How the owner tries a finished todo: a command, link or file")
    tried.add_argument("todo", help="The todo's ID, such as T3")
    target = tried.add_mutually_exclusive_group(required=True)
    for flag, what in (("cmd", "a command to run"), ("url", "an http(s) link"), ("file", "a path inside the project")):
        target.add_argument(f"--{flag}", help=what)
    shown = sub.add_parser("view", help="Serve the owner's live view of every open run on 127.0.0.1")
    shown.add_argument("--port", type=int, default=8765, help="Default 8765; a busy port falls back to a free one")
    shown.add_argument("--snapshot", help="Write one HTML file with the current state instead of serving")
    close = sub.add_parser("close", parents=[common])
    close.add_argument("--abandon", help="The owner stopped the run: their reason")
    rehome = sub.add_parser("rehome", parents=[common],
                            help="Owner only: bring in an open run from another machine or folder")
    rehome.add_argument("--from", dest="source", required=True, help="The folder the run's run.json records")
    install = sub.add_parser("install", help="Install the entry skills and gate hooks for one host")
    install.add_argument("--host", required=True, choices=("claude", "codex", "cursor", "other"),
                         help="other: entry skills only, for agents you wire by hand")
    install.add_argument("--project", help="Install into this project instead of your user folders")
    hook = sub.add_parser("hook", help="Answer one host hook event from stdin")
    hook.add_argument("--host", default="claude", help="claude, codex, cursor, or any other hook-capable agent")
    args = parser.parse_args()
    actions = {"start": cmd_start, "done": cmd_done, "status": cmd_status, "close": cmd_close, "rehome": cmd_rehome,
               "try": cmd_try, "view": cmd_view,
               "hook": lambda a: sys.exit(cmd_hook(a.host)),
               "install": lambda a: sibling("fast_install").install(a.host, a.project, log=lambda line: (print(line), log("install.write", line=line))),
               "pause": lambda a: cmd_pause(a, a.reason), "resume": lambda a: cmd_pause(a, None)}
    actions[args.command](args)


if __name__ == "__main__":
    main()
