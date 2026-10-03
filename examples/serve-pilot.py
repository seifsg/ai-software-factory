"""Show the task-notes fixture locally without exposing its runtime records."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/model.mjs": ("model.mjs", "text/javascript; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--port", default=0, type=int, help="0 chooses an available local port")
    args = parser.parse_args()
    root = args.project.resolve()
    for filename, _ in FILES.values():
        path = root / filename
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            parser.error(f"Missing or unsupported public fixture file: {path}")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            item = FILES.get(urlsplit(self.path).path)
            if item is None:
                self.send_error(404)
                return
            filename, content_type = item
            try:
                path = root / filename
                if path.is_symlink() or not path.resolve().is_relative_to(root):
                    self.send_error(404)
                    return
                content = path.read_bytes()
            except OSError:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)

    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Task-notes preview: http://127.0.0.1:{server.server_port}/", flush=True)
        print("Interactive inspection only. No factory checks or review are running.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
