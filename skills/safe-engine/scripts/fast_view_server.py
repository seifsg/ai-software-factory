"""Allowlisted, scope-bound HTTP resources for the shared loopback view."""
import hashlib
import json
import os
import threading
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

import fast_view_scope as scopes

PROTOCOL = "factory-project-view-v1"
CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
       "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")


class Responses:
    """Reuse one global read and at most 32 projections; unrelated changes keep each ETag."""

    def __init__(self, folder, views):
        self.folder, self.views = folder, views
        self.stamp, self.state, self.cache = None, {}, OrderedDict()
        self.scopes_stamp, self.scopes = None, {}
        self.lock = threading.Lock()

    def scope(self, key):
        """Read new registrations only when the shared scope file changes."""
        with self.lock:
            path = self.folder / "scopes.json"
            stat = path.stat()
            stamp = stat.st_mtime_ns, stat.st_size
            if stamp != self.scopes_stamp:
                self.scopes = self.views.read(path, {}) or {}
                self.scopes_stamp = stamp
            return self.scopes.get(key)

    def selected(self, scope):
        with self.lock:
            path = self.folder / "state.json"
            stat = path.stat()
            stamp = stat.st_mtime_ns, stat.st_size
            if self.stamp != stamp:
                state = self.views.read(path)
                if not isinstance(state, dict) or not isinstance(state.get("runs"), list):
                    raise ValueError("Progress state is unavailable")
                for run in state["runs"]:
                    if isinstance(run, dict) and run.get("scopeVersion") != scopes.VERSION:
                        run["scopeId"] = scopes.run_scope(run)
                        run["scopeVersion"] = scopes.VERSION
                self.state, self.stamp = state, stamp
            key = scope["id"]
            old = self.cache.pop(key, None)
            if old and old[0] == stamp and old[1] == scope:
                result = old
            else:
                state = scopes.project_state(self.state, scope)
                data = json.dumps(state, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                tag = '"' + hashlib.sha256(data).hexdigest() + '"'
                result = stamp, scope, state, data, tag
            self.cache[key] = result
            if len(self.cache) > 32:
                self.cache.popitem(last=False)
            return result[2:]


def serve(views, folder, port=0, log=print, scope=None):
    """Serve registered scopes, with no global root or directory browsing."""
    folder, scope = Path(folder), scope or dict(scopes.ALL)
    views.register_scope(folder, scope)
    if not (folder / "state.json").exists():
        with views.Lock(folder):
            if not (folder / "state.json").exists():
                views.save_state(folder, [])
    responses = Responses(folder, views)

    class Server(ThreadingHTTPServer):
        allow_reuse_address = os.name != "nt"

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            if self.headers.get("Host", "").rsplit(":", 1)[0] not in ("127.0.0.1", "localhost"):
                self.send_error(403, "Use the address fast_gate.py view printed")
                return
            try:
                resource = self.resource(unquote(urlsplit(self.path).path))
                if resource is None:
                    self.send_error(404, "Open a project with fast_gate.py view --project <folder>")
                    return
                data, kind, tag = resource if len(resource) == 3 else (*resource, None)
                tag = tag or '"' + hashlib.sha256(data).hexdigest() + '"'
                self.send_response(304 if self.headers.get("If-None-Match") == tag else 200)
                self.send_header("Content-Type", kind)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("ETag", tag)
                self.end_headers()
                if self.command != "HEAD" and self.headers.get("If-None-Match") != tag:
                    self.wfile.write(data)
            except (OSError, ValueError, KeyError, TypeError):
                self.send_error(503, "Progress is unavailable; retry now or restart fast_gate.py view --project <folder>")

        def resource(self, path):
            if path == "/.well-known/factory-view":
                return PROTOCOL.encode(), "text/plain; charset=utf-8"
            if path.startswith("/all/"):
                selected, name = dict(scopes.ALL), path[len("/all/"):]
            elif path.startswith("/projects/"):
                parts = path.split("/", 3)
                if len(parts) != 4:
                    return None
                selected = responses.scope(parts[2])
                if not selected or selected.get("kind") not in ("repository", "folder"):
                    return None
                name = parts[3]
            else:
                return None
            if name in ("", "index.html"):
                return views.PAGE.read_bytes(), "text/html; charset=utf-8"
            state, data, tag = responses.selected(selected)
            if name == "state.json":
                return data, "application/json; charset=utf-8", tag
            allowed = {f"{run['key']}.todos.json" for run in state["runs"]}
            allowed.update(t["thumb"] for run in state["runs"] for t in run.get("ready") or [] if t.get("thumb"))
            allowed.update(p["thumb"] for run in state["runs"] for p in run.get("pictures", []) if p.get("thumb"))
            allowed.update(item["picture"]["thumb"] for run in state["runs"]
                           for item in (run.get("ownerReport") or {}).get("items", [])
                           if item.get("picture", {}).get("thumb"))
            if name not in allowed:
                return None
            target = (folder / name).resolve()
            if folder.resolve() not in target.parents or not target.is_file():
                return None
            import mimetypes
            return target.read_bytes(), mimetypes.guess_type(name)[0] or "application/octet-stream"

        def end_headers(self):
            for name, value in (("Cache-Control", "no-cache"), ("Content-Security-Policy", CSP),
                                ("X-Content-Type-Options", "nosniff")):
                self.send_header(name, value)
            super().end_headers()

        def log_message(self, *args):
            pass

    try:
        server = Server(("127.0.0.1", port), Handler)
    except OSError:
        server = Server(("127.0.0.1", 0), Handler)
    base = f"http://127.0.0.1:{server.server_address[1]}/"
    (folder / "project-url").write_text(base, encoding="utf-8")
    url = base.rstrip("/") + scopes.route(scope)
    log(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if views.read_text(folder / "project-url") == base:
            (folder / "project-url").unlink(missing_ok=True)
    return url
