"""Run candidate code for a rubric in its own process: `python -I -c <this source> <request.json>`, cwd = workspace.

The request names a module and a list of operations; the answer is one `RESULT <json>` line of plain typed data,
so the rubric's process never imports candidate code or compares candidate objects.
"""
import importlib
import io
import json
import os
import sys
from wsgiref.util import setup_testing_defaults


def plain(value):
    """`value` as JSON-ready data of exact built-in types; anything else (custom objects) is refused."""
    if value is None or type(value) in (bool, int, float, str):
        return value
    if type(value) in (list, tuple):
        return [plain(item) for item in value]
    if type(value) is dict and all(type(key) is str for key in value):
        return {key: plain(item) for key, item in value.items()}
    raise TypeError(f"not plain data: {type(value).__name__}")


def wsgi(app, method, path, body, query):
    """One request to a WSGI app: [status code, JSON-decoded body (or text)]."""
    data = body.encode("utf-8")
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query, "CONTENT_TYPE": "application/json",
               "CONTENT_LENGTH": str(len(data)), "wsgi.input": io.BytesIO(data)}
    setup_testing_defaults(environ)
    seen = []
    payload = b"".join(app(environ, lambda status, headers, exc_info=None: seen.append(status)))
    if not seen:
        raise RuntimeError("app never called start_response")
    try:
        decoded = json.loads(payload or b"null")
    except ValueError:
        decoded = payload.decode("utf-8", "replace")
    return [int(str(seen[0]).split()[0]), decoded]


def step(module, op):
    """Run one operation: ["call", name, args, kwargs] or ["wsgi", name, method, path, body, query]."""
    kind, name, *rest = op
    target = getattr(module, name)
    return target(*rest[0], **rest[1]) if kind == "call" else wsgi(target, *rest)


def main(path):
    """Import the candidate module from the workspace, run every operation, print one RESULT line."""
    with open(path, encoding="utf-8") as handle:
        request = json.load(handle)
    sys.path.insert(0, os.getcwd())  # after this file's own imports, so candidate files cannot shadow them
    try:
        module = importlib.import_module(request["module"])
        results = []
        for op in request["ops"]:
            try:
                results.append(["ok", plain(step(module, op))])
            except Exception as error:  # noqa: BLE001 - a failing call is a result, not a crash
                results.append(["error", f"{type(error).__name__}: {error}"])
    except BaseException as error:  # noqa: BLE001 - import failed or the candidate exited
        results = [["error", f"{type(error).__name__}: {error}"]] * len(request["ops"])
    sys.stdout.write("\nRESULT " + json.dumps(results) + "\n")
    sys.stdout.flush()


main(sys.argv[1])
