"""CLI for local factory-run metrics: report, compare, export, delete."""
import json
from pathlib import Path

import fast_design as evidence
import fast_metrics as metrics


def parser(sub, common):
    command = sub.add_parser("metrics", parents=[common], help="Local run metrics report, compare, export or delete")
    command.add_argument("action", choices=("report", "compare", "export", "delete", "overhead"))
    command.add_argument("--key", help="Run key under .factory/metrics/")
    command.add_argument("--keys", nargs="+", help="Run keys for compare")
    command.add_argument("--dest", help="Export destination directory")
    command.add_argument("--events", type=int, default=200, help="Paired operations for overhead fixture")


def run(args, gate):
    try:
        project = Path(gate.find_project(args.project)).resolve()
        mod = metrics.module()
        if args.action == "report":
            key = args.key
            if not key:
                project, state = gate.open_run(project)
                key = state["key"]
            evidence.require(key, "report needs --key or an open run")
            # Preserve prior abort/fail; omit outcome so finalize does not relabel.
            report = mod.finalize(project, key)
            evidence.require(report is not None, "Could not write metrics report")
            print(mod.markdown(report))
            return
        if args.action == "compare":
            keys = args.keys or []
            evidence.require(keys, "Pass --keys for compare")
            print(json.dumps(mod.compare(project, keys), indent=2))
            return
        if args.action == "export":
            evidence.require(args.key and args.dest, "export needs --key and --dest")
            path = mod.export(project, args.key, args.dest)
            evidence.require(path, "Export failed")
            print(path)
            return
        if args.action == "delete":
            evidence.require(args.key, "delete needs --key")
            evidence.require(mod.delete(project, args.key), "Delete failed")
            print(f"Deleted metrics for {args.key}")
            return
        if args.action == "overhead":
            key = args.key or "overhead-fixture"
            result = mod.measure_overhead(project, key, event_count=args.events)
            evidence.require(result is not None, "Overhead measurement failed")
            print(json.dumps(result, indent=2))
            return
    except (OSError, ValueError, KeyError, TypeError) as error:
        gate.fail("Metrics: " + str(error))
