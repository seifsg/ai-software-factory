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
import fast_progress as facts  # noqa: E402

PAGE = HERE / "view" / "index.html"
OPEN_TILES, EVENTS, READY = 7, 12, 20  # belt tiles per run, events kept per run, Ready to try cards sent
SHOT = re.compile(r"\.(?:png|jpe?g|gif|webp)$", re.I)
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
        rows.append((ICON.get(step, "construction"), f"step {step} started", "step"))
    if new["paused"] and not old.get("paused"):
        rows.append(("front_hand", "waits on you", "wait"))
    if old.get("paused") and not new["paused"] and not new["closed"]:
        rows.append(("bolt", "resumed", "resume"))
    if new["closed"] and not old.get("closed"):
        rows.append(("inventory_2" if new["closed"] == "finished" else "block", f"run {new['closed']}", "finish"))
    fresh = [{"id": now_ms * 100 + i, "t": now_ms, "run": new["key"], "icon": icon, "text": text, "kind": kind}
             for i, (icon, text, kind) in enumerate(rows)]
    return ((old.get("events") or []) + fresh)[-EVENTS:]


def shot(folder, project, key, n, value):
    """A screenshot inside the run's shots folder, copied into the view folder once; its page path, else None."""
    source = Path(project, value).resolve()
    if not SHOT.search(value) or not str(source).startswith(str(Path(project, ".factory", "fast", "shots").resolve()) + os.sep):
        return None
    name = f"{key}-T{n}{source.suffix.lower()}"
    try:
        target = folder / "shots" / name
        if not target.exists() or target.stat().st_size != source.stat().st_size:
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, target)
        return f"shots/{name}"
    except OSError:
        return None


class Lock:
    """One writer of state.json at a time across gate processes (atomic create); a lock older than 2 s is a crashed
    writer's and is taken over."""

    def __init__(self, folder):
        self.path = folder / "state.lock"

    def __enter__(self):
        for _ in range(100):
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 2:
                        self.path.unlink()
                except OSError:
                    pass
                time.sleep(0.005)
        raise TimeoutError(f"{self.path} stays held")

    def __exit__(self, *_):
        self.path.unlink(missing_ok=True)


def write(folder, project, run, steps, sessions=0, agents=None, now_ms=None):
    """Update this run in state.json (one atomic replace per change) and write its todo list for the detail.
    agents=None keeps the last snapshot."""
    folder, now_ms = Path(folder), now_ms or int(time.time() * 1000)
    folder.mkdir(parents=True, exist_ok=True)
    key, record = run["key"], Path(project, ".factory", "fast", "work-record.md")
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
        "key": key, "name": Path(project).name, "project": str(project), "kind": run.get("kind"), "mode": run.get("mode"),
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
    }
    with Lock(folder):
        state = read(folder / "state.json", {}) or {}
        runs = {r["key"]: r for r in state.get("runs") or [] if isinstance(r, dict) and "key" in r}
        old = runs.get(key) or {}
        first = {t["key"]: t["at"] for t in old.get("ready") or []}
        view["agents"] = (old.get("agents") or []) if agents is None else agents
        view["ready"] = [{"key": f"{key}/{t['id']}", "run": key, "id": t["id"], "title": t["title"], "result": t["result"],
                          "kind": t["kind"], "value": t["value"], "cwd": str(project),
                          "at": first.get(f"{key}/{t['id']}", now_ms),
                          **({"thumb": shot(folder, project, key, t["id"][1:], t["value"])} if t["kind"] == "file" else {})}
                         for t in todos if t["state"] == "done" and t.get("kind")]
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
        (folder / f"{gone}.todos.json").unlink(missing_ok=True)
    kept.sort(key=lambda r: (bool(r.get("closed")), not r.get("paused"), r.get("done") == r.get("total"), r["key"]))
    ready = sorted((t for r in kept for t in r.get("ready") or []), key=lambda t: -t["at"])
    events = sorted((e for r in kept for e in r.get("events") or []), key=lambda e: e["id"])[-EVENTS * 2:]
    dump(folder / "state.json", {"at": now_ms, "runs": kept, "ready": ready[:READY], "readyTotal": len(ready),
                                 "events": events})


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
    target = folder / "index.html"
    if not target.exists() or target.stat().st_size != PAGE.stat().st_size or target.read_bytes() != PAGE.read_bytes():
        shutil.copyfile(PAGE, target)


def snapshot(folder, out):
    """One file: the page with the current state inside it, no live updates."""
    state = (folder / "state.json").read_text(encoding="utf-8") if (folder / "state.json").exists() else '{"runs":[]}'
    html = PAGE.read_text(encoding="utf-8").replace('<script id="snapshot" type="application/json"></script>',
                                                    '<script id="snapshot" type="application/json">'
                                                    + state.replace("</", "<\\/") + "</script>", 1)
    Path(out).write_text(html, encoding="utf-8")
    return Path(out).resolve()


CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
       "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")


def serve(folder, port=0, log=print):
    """Serve the view folder on 127.0.0.1 until stopped: ETags so an unchanged poll is one 304, other Hosts refused."""
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    folder.mkdir(parents=True, exist_ok=True)
    page(folder)
    if not (folder / "state.json").exists():
        with Lock(folder):
            save_state(folder, [])

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(folder), **kwargs)

        def send_head(self):
            if self.headers.get("Host", "").rsplit(":", 1)[0] not in ("127.0.0.1", "localhost"):
                self.send_error(403, "Use the address fast_gate.py view printed")  # DNS rebinding
                return None
            path = Path(self.translate_path(self.path))
            self.tag = None
            if path.is_file():
                stat = path.stat()
                self.tag = f'"{stat.st_mtime_ns:x}-{stat.st_size:x}"'
                if self.headers.get("If-None-Match") == self.tag:
                    self.send_response(304)
                    self.end_headers()
                    return None
            del self.headers["If-Modified-Since"]  # second-resolution dates would hide a change: ETags decide
            return super().send_head()

        def end_headers(self):
            for name, value in (("Cache-Control", "no-cache"), ("Content-Security-Policy", CSP),
                                ("X-Content-Type-Options", "nosniff"), ("ETag", getattr(self, "tag", None))):
                if value:
                    self.send_header(name, value)
            super().end_headers()

        def log_message(self, *args):
            pass  # one request every 2 s: no console noise

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError:  # the port is taken (another view, another app): any free one
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    log(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return url
