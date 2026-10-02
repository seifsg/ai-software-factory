"""Run with python -m safe_engine --project /absolute/project <command>."""

import argparse
import json
import sys

from .project import EngineError, discover, project_root
from .storage import locked, read_json
from .workflow import Workflow


def main():
    parser = argparse.ArgumentParser(description="Safe Engine local delivery pilot")
    parser.add_argument("--project", required=True, help="Git project/worktree root")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("discover", help="Propose a profile without executing project scripts")
    init = commands.add_parser("init", help="Start one reviewed task from a clean project")
    init.add_argument("--task", required=True)
    init.add_argument("--profile", required=True)
    init.add_argument("--max-repairs", type=int,
                      help="Deprecated historical metadata only; repairs have no numerical limit")
    record = commands.add_parser("record", help="Save a method artifact and advance the appropriate phase")
    record.add_argument("kind", choices=("analysis", "plan", "batch", "improvement"))
    record.add_argument("--file", required=True)
    commands.add_parser("check", help="Execute the configured verification batch")
    review = commands.add_parser("review", help="Launch a fresh read-only Codex CLI assessment")
    review.add_argument("--timeout", required=True, type=int)
    for name in ("repair", "cancel"):
        command = commands.add_parser(name)
        command.add_argument("--reason", required=True)
    commands.add_parser("status", help="Read saved progress and evidence freshness")
    commands.add_parser("handoff", help="Validate current acceptance and write a local report")
    args = parser.parse_args()
    try:
        project = project_root(args.project)
        workflow = Workflow(project)
        if args.command == "discover":
            result = discover(project)
        else:
            # The runtime directory must already be excluded from Git by the project owner.
            if args.command == "init":
                from .project import git
                try:
                    git(project, "check-ignore", "-q", ".factory/state.json")
                except EngineError:
                    raise EngineError("Add .factory/ to the project's Git ignore rules before initialization")
            with locked(workflow.directory):
                if args.command == "init":
                    result = workflow.initialize(read_json(args.task), read_json(args.profile), args.max_repairs)
                elif args.command == "record":
                    result = workflow.record(args.kind, args.file)
                elif args.command == "review":
                    result = workflow.review(args.timeout)
                elif args.command in ("repair", "cancel"):
                    result = getattr(workflow, args.command)(args.reason)
                else:
                    result = getattr(workflow, args.command)()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.command == "check" and not result["checks_passed"]:
            return 1
        if args.command == "review" and result["phase"] != "ready":
            return 1
        return 0
    except (EngineError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted. Saved progress remains available; rerun the incomplete operation.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
