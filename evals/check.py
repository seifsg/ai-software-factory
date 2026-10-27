"""Rubric check program. The runner reads this source once, before any agent starts, and sends it with the
rubric, the shipped modules, the fixture and the reference solution to `python -I -S -B -c BOOT` (no site hooks)
as one JSON line on a stdin pipe. No file the agent could reach is read and no path to these sources is passed.
The verdict goes back over a stdout pipe only the runner holds: the check passes only when this program prints the
token last, after the check returned.
"""
import json
import os
from pathlib import Path
import sys
import types

BOOT = ("import json, sys; payload = json.loads(sys.stdin.buffer.readline()); scope = {'__name__': 'evals_check'}; "
        "exec(compile(payload.pop('check'), 'check', 'exec'), scope); sys.exit(scope['run'](payload))")
MODULES = ("safe_engine.windows_job", "evals.winjob", "evals.proc", "evals.rubric_tools")  # import order


def install(payload):
    """Make `evals.<module>` importable for the rubric, each built from the sent source."""
    for name in ("safe_engine", "evals"):
        package = types.ModuleType(name)
        package.__path__ = []
        sys.modules[name] = package
    for name in MODULES:
        parent, part = name.split(".")
        if part in ("windows_job", "winjob") and os.name != "nt":
            continue
        module = types.ModuleType(name)
        sys.modules[name] = module
        setattr(sys.modules[parent], part, module)
        exec(compile(payload[part], name, "exec"), module.__dict__)
    tools = sys.modules["evals.rubric_tools"]
    tools.HARNESS, tools.RECORD = payload["harness"], payload.get("record")


def record(folder, item):
    """Write the files behind every loaded module and the search path (interpreter guard probe only)."""
    files = {getattr(m, a, None) or "" for m in list(sys.modules.values()) for a in ("__file__", "__cached__")}
    with open(os.path.join(folder, f"check-{item}.json"), "w", encoding="utf-8") as handle:
        json.dump({"files": sorted(f for f in files if f), "path": sys.path}, handle)


def run(payload):
    """Run one rubric item; print the token only after it returned."""
    token = payload.pop("token")
    try:
        install(payload)
        rubric = {"__name__": "rubric", "FIXTURE": payload["fixture"], "REFERENCE": payload["reference"]}
        exec(compile(payload["rubric"], "rubric", "exec"), rubric)
        rubric["CHECKS"][payload["item"]](Path(payload["workdir"]))
    except BaseException as error:  # noqa: BLE001 - any exit or error fails the item
        print(f"{type(error).__name__}: {error}".strip(), file=sys.stderr)
        return 1
    finally:
        if payload.get("record"):
            record(payload["record"], payload["item"])
    sys.stderr.flush()
    print(token, flush=True)
    return 0
