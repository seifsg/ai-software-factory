"""Rubric check program. The runner reads this source once, before any agent starts, and sends it with the
rubric, the tools and the fixture to `python -I -B -c BOOT` as one JSON line on a stdin pipe. No file the agent
could reach is read, and no path to these sources is passed. The check passes only when this program prints the
token as its last line, after the check returned.
"""
from pathlib import Path
import sys
import types

BOOT = ("import json, sys; payload = json.loads(sys.stdin.buffer.readline()); scope = {'__name__': 'evals_check'}; "
        "exec(compile(payload.pop('check'), 'check', 'exec'), scope); sys.exit(scope['run'](payload))")


def install_tools(source, harness):
    """Make `evals.rubric_tools` importable for the rubric, built from the sent source."""
    tools = types.ModuleType("evals.rubric_tools")
    exec(compile(source, "rubric_tools", "exec"), tools.__dict__)
    tools.HARNESS = harness
    package = types.ModuleType("evals")
    package.__path__, package.rubric_tools = [], tools
    sys.modules.update({"evals": package, "evals.rubric_tools": tools})


def run(payload):
    """Run one rubric item; print the token only after it returned."""
    token = payload.pop("token")
    try:
        install_tools(payload["tools"], payload["harness"])
        rubric = {"__name__": "rubric", "FIXTURE": payload["fixture"]}
        exec(compile(payload["rubric"], "rubric", "exec"), rubric)
        rubric["CHECKS"][payload["item"]](Path(payload["workdir"]))
    except BaseException as error:  # noqa: BLE001 - any exit or error fails the item
        print(f"{type(error).__name__}: {error}".strip(), file=sys.stderr)
        return 1
    sys.stderr.flush()
    print(token, flush=True)
    return 0
