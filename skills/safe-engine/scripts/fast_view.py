"""The owner's live view: brief JSON the gate writes when a run changes, a 127.0.0.1 file server, and the page.

Writers: fast_gate.py only (gate commands, and hooks after their file-time check saw a change). Stdlib only.
Method: .agents/skills/safe-engine/references/fast-run.md#live-view. Page: view/index.html.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # loaded by file path (tests): find the sibling modules
import fast_card as card  # noqa: E402 - the chat card's facts, so chat and view always agree
import fast_wait  # noqa: E402 - the gate's recorded helper state outranks the last report
import fast_progress as facts  # noqa: E402
import fast_view_model as model  # noqa: E402
from fast_view_scope import scope_for, project_state, route, identity_stamp, VERSION as SCOPE_VERSION  # noqa: E402

PAGE = HERE / "view" / "index.html"
OPEN_TILES, EVENTS, READY = 7, 12, 20  # belt tiles per run, events kept per run, Ready to try cards sent
SHOT = re.compile(r"\.png$", re.I)
UNSUPPORTED_IMAGE = re.compile(r"\.(?:jpe?g|gif|webp|svg|bmp|tiff?|avif)$", re.I)
ICON = {"research": "search", "kickoff": "forum", "tickets": "confirmation_number", "analysis": "psychology",
        "plan": "map", "design": "palette", "schema": "database", "build": "construction", "done-run": "science",
        "handoff": "inventory_2"}  # Material Symbols names for the chat card's step icons


def ms(iso, fallback=0):
    """Epoch milliseconds from an ISO time; fallback when missing or invalid."""
    try:
        return int(datetime.fromisoformat(iso).timestamp() * 1000)
    except (TypeError, ValueError):
        return fallback


def dump(path, data):
    """Atomic compact JSON write: the server and parallel hooks never read half a file. json.dumps uses the C
    encoder (json.dump to a stream does not)."""
    text = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            out.write(text)
        for wait in (0.01, 0.03, 0.1, 0):  # Windows: the server may be sending the old file right now
            try:
                os.replace(temp, path)
                break
            except PermissionError:
                if not wait:
                    raise
                time.sleep(wait)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


def read(path, fallback=None):
    """JSON from path, else fallback (missing, mid-replace on Windows, or broken)."""
    try:
        with open(path, encoding="utf-8") as source:
            return json.load(source)
    except (OSError, ValueError):
        return fallback


def steps_of(run, steps, now_ms):
    """Each step's state and seconds, the current step's index and when it began (steps finish in order)."""
    done = run.get("done") or {}
    current = next((i for i, step in enumerate(steps) if step not in done), None)
    start, since, rows = ms(run.get("created"), now_ms), now_ms, []
    for i, step in enumerate(steps):
        end = ms((done.get(step) or {}).get("at"), start) if step in done else None
        state = "done" if end is not None else "now" if i == current and not run.get("closed") else "left"
        since = start if state == "now" else since
        until = end if end is not None else now_ms if state == "now" else start
        rows.append({"id": step, "s": state, "secs": max(0, (until - start) // 1000)})
        start = end if end is not None else start
    return rows, len(steps) - 1 if current is None else current, since if current is not None else start


def todo_rows(v, tries):
    """Every plan todo as the page shows it: now, next, later, then done (newest first)."""
    following, rows = v.later[:1], []
    for n in v.now + v.later + list(reversed(v.built)):
        state = "done" if n in v.done else "now" if n in v.now else "next" if n in following else "later"
        kind, value = tries.get(n, (None, None))
        rows.append({"id": f"T{n}", "title": card.title(v, n), "result": card.result(v, n), "state": state,
                     **({"kind": kind, "value": value} if kind else {})})
    return rows


def events_of(old, new, todos, now_ms):
    """What changed since the last write, as feed rows: done todos, a new step, a pause, a resume, the close.
    The first write has no earlier view, so it adds none."""
    rows, was = [], set(old.get("doneIds") or [])
    for row in todos:
        if row["state"] == "done" and row["id"] not in was and old:
            rows.append(("check_circle", f"{row['id']} {row['title']} done", "done"))
    if old and old.get("at") != new["at"] and not new["closed"]:
        step = new["steps"][new["at"]]["id"]
        rows.append((ICON.get(step, "construction"), f"{step.capitalize()} started", "step"))
    if new["paused"] and not old.get("paused"):
        rows.append(("front_hand", "waits on you", "wait"))
    if old.get("paused") and not new["paused"] and not new["closed"]:
        rows.append(("bolt", "resumed", "resume"))
    if new["closed"] and not old.get("closed"):
        rows.append(("inventory_2" if new["closed"] == "finished" else "block", f"run {new['closed']}", "finish"))
    fresh = [{"id": now_ms * 100 + i, "t": now_ms, "run": new["label"], "icon": icon, "text": text, "kind": kind}
             for i, (icon, text, kind) in enumerate(rows)]
    return ((old.get("events") or []) + fresh)[-EVENTS:]


def shot(folder, project, vid, n, value, accepted=None):
    """A screenshot inside the run's shots folder, copied into the view folder when new or changed; its page path."""
    source = Path(project, value).resolve()
    if not SHOT.search(value) or not str(source).startswith(str(Path(project, ".factory", "fast", "shots").resolve()) + os.sep):
        return None
    name = f"{vid}-T{n}{source.suffix.lower()}"
    try:
        if accepted and str(source) in accepted:
            import fast_design
            digest, thumb = accepted[str(source)]
            return thumb if thumb and fast_design.file_hash(source) == digest else None
        import fast_design, fast_image
        _, _, digest = fast_image.check(source, project=project, with_digest=True)
        target = folder / "shots" / name
        if not target.exists() or fast_design.file_hash(target) != digest:
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, target)
        return f"shots/{name}"
    except (OSError, ValueError):
        return None


def owner_report(folder, project, key, run):
    """Project accepted reports and immutable checked pictures, never expose arbitrary paths."""
    import fast_design, fast_report
    report = run.get("owner_report")
    if not report:
        return None
    result = {"at": report["at"], "items": []}
    for index, item in enumerate(report["items"]):
        row = {**item}
        if picture := item.get("picture"):
            row["picture"] = {"caption": picture["caption"]}
            try:
                source = fast_report.checked_picture(picture, project)
                name = f"{key}-report-{index}-{picture['sha256'][:16]}.png"
                target = folder / "shots" / name
                target.parent.mkdir(exist_ok=True)
                if not target.exists() or fast_design.file_hash(target) != picture["sha256"]:
                    shutil.copyfile(source, target)
                fast_design.require(fast_design.file_hash(target) == picture["sha256"], "Picture changed during projection")
                row["picture"]["thumb"] = "shots/" + name
            except (OSError, ValueError) as error:
                row["picture"]["error"] = str(error)
        result["items"].append(row)
    return result


def show_pictures(folder, project, key, run):
    """Show accepted captures only while the candidate and every shown image retain their identities."""
    import fast_design
    report = (run.get("show") or {}).get("report") or {}
    if not report.get("screens"):
        return []
    try:
        import fast_show
        fast_show.current(project, run)
        sources = []
        for screen in report["screens"]:
            capture = screen["capture"]
            source = fast_design.local(project, capture["path"])
            fast_design.require(fast_design.file_hash(source) == capture["sha256"], "Show capture changed")
            sources.append((screen, capture, source))
    except (OSError, ValueError, KeyError, TypeError):
        return []
    names = {s["id"]: s["name"] for s in (run.get("show") or {}).get("plan", {}).get("surfaces", [])}
    pictures = []
    for screen, capture, source in sources:
        try:
            name = f"{key}-show-{screen['id']}-{capture['sha256'][:16]}.png"
            target = folder / "shots" / name
            target.parent.mkdir(exist_ok=True)
            if not target.exists() or fast_design.file_hash(target) != capture["sha256"]:
                shutil.copyfile(source, target)
            fast_design.require(fast_design.file_hash(target) == capture["sha256"], "Show capture changed during projection")
            pictures.append({"thumb": "shots/" + name,
                             "caption": " · ".join((names.get(screen["surface"], screen["surface"]), screen["theme"], screen["device"]))})
        except (OSError, ValueError, KeyError, TypeError):
            return []
    return pictures


class Lock:
    """One writer of state.json at a time across gate processes (atomic create); a lock older than 2 s is a crashed
    writer's and is taken over."""

    def __init__(self, folder):
        self.path = folder / "state.lock"

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(100):
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 2:  # a crashed writer's: one waiter wins the rename
                        stale = self.path.with_name(f"state.lock.{os.getpid()}")
                        os.replace(self.path, stale)
                        if time.time() - stale.stat().st_mtime > 2:
                            stale.unlink()
                        else:  # another waiter took it over first: give its fresh lock back
                            os.replace(stale, self.path)
                except OSError:
                    pass
                time.sleep(0.005)
        raise TimeoutError(f"{self.path} stays held")

    def __exit__(self, *_):
        self.path.unlink(missing_ok=True)


def scope_id(folder, project):
    """Reuse Git discovery across gate processes; one replaceable entry per project folder."""
    key, stamp = identity_stamp(project)
    path = folder / "identities" / f"{key}.json"
    saved = read(path, {}) or {}
    if saved.get("stamp") == stamp and saved.get("id"):
        return saved["id"]
    selected = scope_for(project)["id"]
    path.parent.mkdir(parents=True, exist_ok=True)
    dump(path, {"stamp": stamp, "id": selected})
    return selected


def write(folder, project, run, steps, sessions=0, agents=None, now_ms=None, vid=None):
    """Update this run in state.json (one atomic replace per change) and write its todo list for the detail.
    vid: the view's id, unique across projects (the gate passes key plus project hash). agents=None keeps the last
    snapshot."""
    folder, now_ms = Path(folder), now_ms or int(time.time() * 1000)
    folder.mkdir(parents=True, exist_ok=True)
    label, record = run["key"], Path(project, ".factory", "fast", "work-record.md")
    key = vid or label
    sections = facts.read(record)
    v = card.view(run, sections)
    todos = todo_rows(v, facts.try_items(sections))
    rows, at, since = steps_of(run, steps, now_ms)
    paused, opened = run.get("paused"), [t for t in todos if t["state"] != "done"]
    try:
        edited = os.stat(record).st_mtime_ns // 1_000_000
    except OSError:
        edited = 0
    view = {
        "key": key, "scopeId": scope_id(folder, project), "scopeVersion": SCOPE_VERSION,
        "label": label, "name": Path(project).name, "project": str(project), "kind": run.get("kind"), "mode": run.get("mode"),
        "ticket": f"#{v.focus} {v.tickets.get(v.focus, '')}".strip() if v.focus else "",
        "steps": rows, "at": at, "stepSince": since, "created": ms(run.get("created"), now_ms),
        "changed": max(edited, since, ms((paused or {}).get("at"), 0)),  # Quiet: no record edit, step or pause for 15 min
        "paused": {"reason": paused.get("reason"), "since": ms(paused.get("at"), now_ms)} if paused else None,
        "closed": ("stopped" if run.get("abandoned") else "finished") if run.get("closed") else None,
        "closedAt": ms(run.get("closed_at"), now_ms) if run.get("closed") else None,
        "error": None if sections else f"Record unreadable: {record}",
        "record": str(record), "sessions": sessions,
        "done": len(v.built), "total": len(v.ids), "pct": round(100 * len(v.built) / len(v.ids)) if v.ids else 0,
        "now": [{"id": t["id"], "title": t["title"]} for t in todos if t["state"] == "now"],
        "last": next(({"id": t["id"], "title": t["title"]} for t in todos if t["state"] == "done"), None),
        "open": opened[:OPEN_TILES], "more": max(0, len(opened) - OPEN_TILES),
        "doneIds": [t["id"] for t in todos if t["state"] == "done"],
        "tasks": todos, "tickets": model.tickets(sections, v), **model.metadata(sections),
    }
    view["ownerReport"] = owner_report(folder, project, key, run)
    waiting = fast_wait.state(folder.parent, run)
    view["helperWait"] = {**waiting, "message": fast_wait.describe(waiting),
                          "suppressReport": fast_wait.suppress_report(waiting, run.get("owner_report"))} if waiting["recorded"] or waiting["problems"] else None
    accepted = {str(Path(item["picture"]["path"]).resolve()):
                (item["picture"]["sha256"], row["picture"].get("thumb"))
                for item, row in zip((run.get("owner_report") or {}).get("items", []),
                                     (view["ownerReport"] or {}).get("items", [])) if item.get("picture")}
    tried = [t for t in todos if t["state"] == "done" and t.get("kind")]
    thumbs = {t["id"]: shot(folder, project, key, t["id"][1:], t["value"], accepted) for t in tried if t["kind"] == "file"}  # copies stay out of the lock
    view["pictures"] = [{"thumb": thumbs[t["id"]], "caption": t["result"] or t["title"]}
                        for t in tried if thumbs.get(t["id"])]
    if not view["ownerReport"] and not view["pictures"]:
        view["pictures"] = show_pictures(folder, project, key, run)
    with Lock(folder):
        state = read(folder / "state.json", {}) or {}
        runs = {r["key"]: r for r in state.get("runs") or [] if isinstance(r, dict) and "key" in r}
        old = runs.get(key) or {}
        old = {} if old.get("closed") and not view["closed"] else old  # the same key started again: a fresh history
        first = {t["key"]: t["at"] for t in old.get("ready") or []}
        view["agents"] = (old.get("agents") or []) if agents is None else agents
        view["agentsObservedAt"] = old.get("agentsObservedAt") if agents is None else now_ms
        view["subsessions"] = model.subsessions(view["subsessions"], view["agents"], view["agentsObservedAt"])
        view["ready"] = [{"key": f"{key}/{t['id']}", "run": label, "id": t["id"], "title": t["title"], "result": t["result"],
                          "kind": t["kind"], "value": t["value"], "cwd": str(project),
                          "at": first.get(f"{key}/{t['id']}", now_ms),
                          **({"thumb": thumbs[t["id"]]} if t["id"] in thumbs else {})}
                         for t in tried]
        view["events"] = events_of(old, view, todos, now_ms)
        runs[key] = view
        save_state(folder, runs.values(), now_ms)
    try:  # read only by an open detail; a torn read there just waits for the next poll
        (folder / f"{key}.todos.json").write_text(json.dumps(todos, separators=(",", ":"), ensure_ascii=False),
                                                  encoding="utf-8")
    except OSError:
        pass
    return view


def save_state(folder, runs, now_ms=None):
    """state.json: open runs (waiting first, all-done last), runs closed today, newest results and events. Runs
    closed before today drop out. The caller holds the Lock."""
    now_ms = now_ms or int(time.time() * 1000)
    today = datetime.fromtimestamp(now_ms / 1000).date()
    kept = [r for r in runs if not r.get("closed") or datetime.fromtimestamp((r.get("closedAt") or 0) / 1000).date() >= today]
    for gone in {r["key"] for r in runs} - {r["key"] for r in kept}:
        for stale in [folder / f"{gone}.todos.json", *folder.glob(f"shots/{gone}-*")]:
            stale.unlink(missing_ok=True)
    kept.sort(key=lambda r: (bool(r.get("closed")), not r.get("paused"), r.get("done") == r.get("total"), r["key"]))
    ready = sorted((t for r in kept for t in r.get("ready") or []), key=lambda t: -t["at"])
    events = sorted((e for r in kept for e in r.get("events") or []), key=lambda e: e["id"])[-EVENTS * 2:]
    dump(folder / "state.json", {"at": now_ms, "runs": kept, "ready": ready[:READY], "readyTotal": len(ready),
                                 "events": events})


def prune(folder, keep):
    """Drop open runs the gate no longer holds (a lost run closed elsewhere); closed runs stay until the next day."""
    with Lock(folder):
        state = read(folder / "state.json", {}) or {}
        runs = [r for r in state.get("runs") or [] if isinstance(r, dict) and "key" in r]
        kept = [r for r in runs if r.get("closed") or r["key"] in keep]
        if len(kept) != len(runs):
            for gone in {r["key"] for r in runs} - {r["key"] for r in kept}:
                for stale in [folder / f"{gone}.todos.json", *folder.glob(f"shots/{gone}-*")]:
                    stale.unlink(missing_ok=True)
            save_state(folder, kept)


def agents_of(folder, key):
    """The agents snapshot the view holds for this run, or None."""
    state = read(Path(folder) / "state.json", {}) or {}
    return next((r.get("agents") for r in state.get("runs") or [] if isinstance(r, dict) and r.get("key") == key), None)


def try_problem(project, sections, n, kind, value):
    """Why a Try target is refused, else None: the todo must be in the plan, links http(s), files in the project."""
    value = (value or "").strip()
    if n not in facts.todo_ids(sections):
        return f"T{n} is not a todo in the plan's ### Todos"
    if not value or "\n" in value or len(value) > 300:
        return "the target must be one line of at most 300 characters"
    if kind == "url" and not re.fullmatch(r"https?://\S+", value):
        return "a link must start with http:// or https:// and hold no spaces"
    if kind == "file":
        target = Path(project, value).resolve()
        if not str(target).startswith(str(Path(project).resolve()) + os.sep) or not target.is_file():
            return f"{value} is not a file inside {project}"
        if UNSUPPORTED_IMAGE.search(value):
            return "Picture: use a supported PNG screenshot (.png); convert this image first"
        if SHOT.search(value):
            try:
                import fast_image
                fast_image.check(target, project=project)
            except (OSError, ValueError) as error:
                return str(error)
    return None


def add_try(record, n, kind, value):
    """Append '**Try:** T3 url <value>' at the end of the Build log section."""
    text = record.read_text(encoding="utf-8")
    line = f"**Try:** T{n} {kind} {value.strip()}"
    head = re.search(r"^## Build log[ \t]*$", text, re.M)
    if not head:
        raise ValueError("the work record has no '## Build log' section")
    end = re.search(r"^## ", text[head.end():], re.M)
    cut = head.end() + end.start() if end else len(text)
    body = text[:cut].rstrip("\n")
    record.write_text(body + "\n" + line + "\n\n" + text[cut:].lstrip("\n"), encoding="utf-8")
    return line


def page(folder):
    """Copy the page into the view folder when it is missing or differs."""
    folder.mkdir(parents=True, exist_ok=True)  # a gate home that never wrote a view
    target = folder / "index.html"
    if not target.exists() or target.stat().st_size != PAGE.stat().st_size or target.read_bytes() != PAGE.read_bytes():
        shutil.copyfile(PAGE, target)


def register_scope(folder, scope):
    """Share an explicitly opened project with the running server, even when it has no runs."""
    folder = Path(folder)
    with Lock(folder):
        path = folder / "scopes.json"
        scopes = read(path, {}) or {}
        if scopes.get(scope["id"]) != scope:
            scopes[scope["id"]] = scope
            dump(path, scopes)


def scoped_state(folder, scope):
    """Project the same nested data for live and snapshot responses."""
    return project_state(read(Path(folder) / "state.json", {}) or {}, scope, READY, EVENTS * 2)


def snapshot(folder, out, scope=None):
    """One file containing only the requested project's current state."""
    selected = scoped_state(folder, scope or scope_for(all_projects=True))
    selected["at"] = selected["at"] or int(time.time() * 1000)
    state = json.dumps(selected, separators=(",", ":"), ensure_ascii=False)
    html = PAGE.read_text(encoding="utf-8").replace('<script id="snapshot" type="application/json"></script>',
                                                    '<script id="snapshot" type="application/json">'
                                                    + state.replace("<", "\\u003c") + "</script>", 1)
    Path(out).write_text(html, encoding="utf-8")
    return Path(out).resolve()


def serve(folder, port=0, log=print, scope=None):
    """Start the allowlisted shared server; the selected scope owns the printed URL."""
    from types import SimpleNamespace
    import fast_view_server
    helpers = SimpleNamespace(PAGE=PAGE, register_scope=register_scope, Lock=Lock, save_state=save_state,
                              read=read, read_text=read_text)
    return fast_view_server.serve(helpers, folder, port, log, scope)


def read_text(path):
    """A small file's text, else ''."""
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def live_url(folder, scope=None):
    """Reuse only a server supporting scoped routes; never mistake an older global server for it."""
    from http.client import HTTPConnection, HTTPException
    from urllib.parse import urlsplit
    from fast_view_server import PROTOCOL
    connection = None
    try:
        base = read_text(Path(folder) / "project-url")
        parsed = urlsplit(base)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port:
            return None
        connection = HTTPConnection("127.0.0.1", parsed.port, timeout=0.3)
        connection.request("GET", "/.well-known/factory-view")
        response = connection.getresponse()
        if response.status != 200 or response.read(100).decode() != PROTOCOL:
            return None
        selected = scope or scope_for(all_projects=True)
        register_scope(folder, selected)
        return f"http://127.0.0.1:{parsed.port}" + route(selected)
    except (OSError, ValueError, UnicodeError, HTTPException):
        return None
    finally:
        if connection:
            connection.close()
