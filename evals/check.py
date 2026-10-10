"""Rubric check program. The runner reads this source once, before any agent starts, and sends it with the
rubric, the tools and the fixture to `python -I -S -B -c BOOT` (no site hooks) as one JSON line on a stdin pipe.
No file the agent could reach is read and no path to these sources is passed. The verdict goes back over a stdout
pipe only the runner holds: the check passes only when this program prints the token last, after the check.
"""
import os
from pathlib import Path
import sys
import types

BOOT = ("import json, sys; payload = json.loads(sys.stdin.buffer.readline()); scope = {'__name__': 'evals_check'}; "
        "exec(compile(payload.pop('check'), 'check', 'exec'), scope); sys.exit(scope['run'](payload))")
MODULES = ("winjob", "proc", "rubric_tools")  # in import order; winjob exists only for Windows


def install(payload):
    """Make `evals.<module>` importable for the rubric, each built from the sent source."""
    package = types.ModuleType("evals")
    package.__path__ = []
    sys.modules["evals"] = package
    for name in MODULES:
        if name == "winjob" and os.name != "nt":
            continue
        module = types.ModuleType(f"evals.{name}")
        sys.modules[module.__name__] = module
        setattr(package, name, module)
        exec(compile(payload[name], name, "exec"), module.__dict__)
    package.rubric_tools.HARNESS = payload["harness"]


def run(payload):
    """Run one rubric item; print the token only after it returned."""
    token = payload.pop("token")
    try:
        install(payload)
        rubric = {"__name__": "rubric", "FIXTURE": payload["fixture"]}
        exec(compile(payload["rubric"], "rubric", "exec"), rubric)
        rubric["CHECKS"][payload["item"]](Path(payload["workdir"]))
    except BaseException as error:  # noqa: BLE001 - any exit or error fails the item
        print(f"{type(error).__name__}: {error}".strip(), file=sys.stderr)
        return 1
    sys.stderr.flush()
    print(token, flush=True)
    return 0
