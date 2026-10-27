"""Wait commands use protected receipts without rewriting concurrent run progress."""
import json

import fast_wait as wait


def parser(sub, common):
    command = sub.add_parser("wait", parents=[common], help="Record finite helper work and reconcile its completion")
    action = command.add_mutually_exclusive_group(required=True)
    action.add_argument("--add", help="Registration JSON file after the host acknowledges a running job")
    action.add_argument("--finish", help="Completion JSON file with the exact returned identity")
    action.add_argument("--status", action="store_true", help="Show current wait receipts and recovery problems")


def run(args, gate):
    try:
        if args.add:
            from resolve_bundle import selection_lock
            project = gate.find_project(args.project)
            with selection_lock(project):
                project, current = gate.open_run(project)
                wait.require(not current.get("closed"), "Cannot register work on a closed run")
                identity = wait.add(gate.HOME, current, wait.read(args.add))
            gate.log("wait.register", key=current["key"], **identity)
            print(json.dumps(identity, indent=2))
        else:
            project, current = gate.open_run(args.project)
            if args.finish:
                result = wait.finish(gate.HOME, current, wait.read(args.finish))
                gate.log("wait.terminal", key=current["key"], status=result)
        print(wait.describe(wait.state(gate.HOME, current)))
    except (OSError, ValueError, KeyError, TypeError) as error:
        gate.fail(f"Wait: {error}")
