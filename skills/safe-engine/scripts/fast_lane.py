"""Gate command wiring for owned lane stacks."""
import argparse
from functools import lru_cache
import importlib
import json
from pathlib import Path
import sys


@lru_cache(maxsize=1)
def runtime_root():
    """Portable entries contain no engine; commands must reach a validated full bundle."""
    root = Path(__file__).resolve().parents[3]
    if not (root / "safe_engine/lanes.py").is_file():
        raise RuntimeError("Lane resources need a selected full factory bundle; resolve it for --project first")
    from resolve_bundle import inspect_bundle
    selected = inspect_bundle(root, entrypoint="safe-engine")
    sys.path.insert(0, selected["bundle_root"])


def runtime(module):
    runtime_root()
    return importlib.import_module(f"safe_engine.{module}")


def parser(sub, common):
    cmd = sub.add_parser("lane", help="Start, inspect or stop an owned lane stack")
    actions = cmd.add_subparsers(dest="lane_action", required=True)
    for action in ("start", "stop", "status"):
        item = actions.add_parser(action, parents=[common])
        item.add_argument("--name", required=True)
        if action == "start":
            item.add_argument("--ports", required=True, help="Comma-separated fixed ports, all initially free")
            item.add_argument("argv", nargs=argparse.REMAINDER, help="-- executable arguments")
        elif action == "stop":
            item.add_argument("--generation", help="Refuse a stop if this generation is no longer current")


def run(args, gate):
    try:
        lanes = runtime("lanes")
        if not args.project:
            raise ValueError("lane requires --project with the helper's working directory")
        project = Path(args.project).resolve(strict=True)
        if args.lane_action == "start":
            argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
            ports = [int(value) for value in args.ports.split(",")]
            run_key = next((run["key"] for _, _, run in gate.active_runs()
                            if Path(run["project"]).resolve() == project), None)
            result = lanes.start(project, args.name, argv, ports, run_key)
        elif args.lane_action == "stop":
            result = lanes.stop(project, args.name, args.generation)
        else:
            result = lanes.status(lanes.folder(project, args.name))
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, RuntimeError) as error:
        gate.fail(f"lane: {error}")
