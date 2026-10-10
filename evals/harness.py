"""Run candidate code for a rubric in its own process: `python -I -S -c <source> <request.json> <channel>`.

The channel (an inherited pipe handle on Windows, a file descriptor elsewhere) is opened before any candidate code
loads; the one result record goes there, never to stdout. The request names a module and operations; results are
plain typed data, so the rubric's process never imports candidate code. The check program also loads these
functions (without running `main`) to compute expected answers from the private reference solution.
"""
import importlib
import io
import json
import os
import sys
import types
import unittest
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


def run_tests(source):
    """Run a unittest module's source (the fixture's original tests) here: {run, failures, errors}."""
    original = types.ModuleType("original_tests")
    exec(compile(source, "original_tests", "exec"), original.__dict__)
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromModule(original).run(result)
    return {"run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)}


def step(module, op):
    """Run one operation: ["call", name, args, kwargs], ["wsgi", name, method, path, body, query] or
    ["tests", "", source]."""
    kind, name, *rest = op
    if kind == "tests":
        return run_tests(*rest)
    target = getattr(module, name)
    return target(*rest[0], **rest[1]) if kind == "call" else wsgi(target, *rest)


def outcome(module, op):
    """["ok", plain value] or ["error", reason] for one operation."""
    try:
        return ["ok", plain(step(module, op))]
    except Exception as error:  # noqa: BLE001 - a failing call is a result, not a crash
        return ["error", f"{type(error).__name__}: {error}"]


def open_channel(handle):
    """The result pipe passed by the caller, opened for writing before candidate code can load."""
    if os.name == "nt":
        import msvcrt
        return os.fdopen(msvcrt.open_osfhandle(int(handle), os.O_WRONLY), "w", encoding="utf-8")
    return os.fdopen(int(handle), "w", encoding="utf-8")


def record(folder, name):
    """Write the files behind every loaded module and the search path to `folder` (for the interpreter guard)."""
    files = {getattr(m, a, None) or "" for m in list(sys.modules.values()) for a in ("__file__", "__cached__")}
    with open(os.path.join(folder, name), "w", encoding="utf-8") as handle:
        json.dump({"files": sorted(f for f in files if f), "path": sys.path}, handle)


def main(path, handle):
    """Open the channel, import the candidate module from the workspace, run every operation, send one record."""
    channel = open_channel(handle)
    with open(path, encoding="utf-8") as source:
        request = json.load(source)
    sys.path.insert(0, os.getcwd())  # after this file's own imports, so candidate files cannot shadow them
    try:
        module = importlib.import_module(request["module"])
        results = [outcome(module, op) for op in request["ops"]]
    except BaseException as error:  # noqa: BLE001 - import failed or the candidate exited
        results = [["error", f"{type(error).__name__}: {error}"]] * len(request["ops"])
    if request.get("record"):
        record(request["record"], f"harness-{os.getpid()}.json")
    with channel:
        channel.write(json.dumps(results) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
