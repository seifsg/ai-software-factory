"""Run with python -m safe_engine --project /absolute/project <command>."""

import argparse
import json
import sys

from .project import EngineError, discover, project_root, snapshot
from .storage import locked, read_json
from .workflow import Workflow


def main():
    parser = argparse.ArgumentParser(description="Safe Engine local delivery pilot")
    parser.add_argument("--project", required=True, help="Git project/worktree root")
    parser.add_argument("--ticket", help="Canonical ticket key; select its preserved version 2 run")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("discover", help="Propose a profile without executing project scripts")
    preflight = commands.add_parser("preflight", help="Inspect tools and bundle identity; no tests or product launch")
    preflight.add_argument("--profile", required=True)
    for name in ("contract-proposal", "seal", "amend"):
        transition = commands.add_parser(name, help="Inspect or independently review final acceptance bindings")
        transition.add_argument("--task", required=True)
        transition.add_argument("--profile", required=True)
        if name != "contract-proposal":
            transition.add_argument("--review", required=True)
        if name == "amend":
            transition.add_argument("--reason", required=True)
    init = commands.add_parser("init", help="Start one reviewed task from a clean project")
    init.add_argument("--task", required=True)
    init.add_argument("--profile", required=True)
    init.add_argument("--session", help="Dedicated builder session identity; required for ticket runs")
    init.add_argument("--max-repairs", type=int,
                      help="Deprecated historical metadata only; repairs have no numerical limit")
    record = commands.add_parser("record", help="Save a method artifact and advance the appropriate phase")
    record.add_argument("kind", choices=("analysis", "plan", "implementation", "manual", "batch", "improvement"))
    record.add_argument("--file", required=True)
    check = commands.add_parser("check", help="Validate the full configured version batch")
    check.add_argument("--fresh", action="store_true", help="Execute all commands even when unchanged reuse is eligible")
    feature = commands.add_parser("feature-check", help="Run partial feature feedback while staying in build")
    feature.add_argument("--checks", nargs="+", required=True, help="Configured check IDs covering the completed feature and consumers")
    feature.add_argument("--file", required=True, help="Substantive completed-feature 0-4 batch artifact")
    review = commands.add_parser("review", help="Launch a fresh read-only Codex CLI assessment")
    review.add_argument("--timeout", type=int, help="Codex review timeout in seconds")
    review.add_argument("--report", help="Without Codex: report from a fresh read-only host subagent")
    review.add_argument("--reviewer", help="Without Codex: host/agent id/model that produced --report")
    outbox = commands.add_parser("review-packet", help="Without Codex: write the review prompt for a host subagent")
    outbox.add_argument("--out", required=True)
    for name in ("repair", "cancel"):
        command = commands.add_parser(name)
        command.add_argument("--reason", required=True)
        if name == "repair":
            command.add_argument("--records-only", action="store_true",
                                 help="Reassess records using eligible exact-input raw evidence; version 2 opt-in only")
    extend = commands.add_parser("extend-reviews", help="Owner-approved extra review rounds after the cap")
    extend.add_argument("--rounds", required=True, type=int)
    extend.add_argument("--reason", required=True)
    commands.add_parser("status", help="Read saved progress and evidence freshness")
    commands.add_parser("handoff", help="Validate current acceptance and write a local report")
    capture = commands.add_parser("ticket-capture", help="Import a complete actual MCP read; performs no remote action")
    capture.add_argument("--source", required=True)
    capture.add_argument("--unchanged", action="store_true",
                         help="Record a cheap observation whose remote updated_at equals the current capture's")
    packet = commands.add_parser("ticket-render", help="Render proposed remote body; performs no remote action")
    packet.add_argument("--source", required=True)
    failure = commands.add_parser("ticket-refresh-failed", help="Invalidate a stale capture after failed/uncertain remote read")
    failure.add_argument("--reason", required=True)
    commands.add_parser("ticket-status", help="Read imported ticket scope/freshness limits")
    proof = commands.add_parser("ticket-proof", help="Bind latest expectations to actual before/after evidence before review")
    proof.add_argument("--file", required=True)
    draft = commands.add_parser("ticket-proof-draft", help="Pre-fill ticket-proof JSON from recorded evidence")
    draft.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        with snapshot():
            result = run(args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.command == "check" and not result["checks_passed"]:
            return 1
        if args.command == "feature-check" and not result["feature_checks_passed"]:
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


def run(args):
    """Dispatch one command inside its scan snapshot."""
    project = project_root(args.project)
    workflow = Workflow(project, args.ticket)
    if args.command == "discover":
        result = discover(project)
    elif args.command == "preflight":
        from .project import validate_profile
        from .review_packet import preflight
        result = preflight(project, validate_profile(read_json(args.profile), draft=True), workflow.directory)
    elif args.command.startswith("ticket-") and args.command not in ("ticket-proof", "ticket-proof-draft"):
        from .tickets import render_ticket, scope_digest
        if not args.ticket:
            raise EngineError("Ticket commands require --ticket")
        store = workflow.store
        if args.command == "ticket-capture":
            try:
                supplied = read_json(args.source)
                if not isinstance(supplied, dict) or supplied.get("key") != args.ticket:
                    raise EngineError("Capture key must match --ticket")
                result = store.unchanged(supplied) if args.unchanged else store.capture(supplied)
            except (EngineError, OSError, ValueError, TypeError, KeyError) as error:
                store.failed(args.ticket, str(error))
                raise
        elif args.command == "ticket-render":
            contract = read_json(args.source)
            result = {"body": render_ticket(contract), "scope_digest": scope_digest(contract), "remote_write": False}
        elif args.command == "ticket-refresh-failed":
            store.failed(args.ticket, args.reason)
            result = store.status(args.ticket)
        else:
            result = store.status(args.ticket)
    elif args.command != "init" and not (workflow.directory / "state.json").exists():
        raise EngineError(f"No saved run at {workflow.directory}; init it or select its --ticket")
    elif args.command == "status":
        result = workflow.status()  # Read-only: no lock, no directory creation.
    else:
        # The runtime directory must already be excluded from Git by the project owner.
        if args.command == "init":
            from .project import git
            try:
                git(project, "check-ignore", "-q", (workflow.directory / "state.json").relative_to(project).as_posix())
            except EngineError:
                raise EngineError("Add .factory/ to the project's Git ignore rules before initialization")
        with locked(workflow.directory):
            if args.command == "init":
                result = workflow.initialize(read_json(args.task), read_json(args.profile), args.max_repairs, args.session)
            elif args.command == "record":
                result = workflow.record(args.kind, args.file)
            elif args.command == "ticket-proof":
                result = workflow.ticket_proof(args.file)
            elif args.command == "check":
                result = workflow.check(fresh=args.fresh)
            elif args.command == "feature-check":
                result = workflow.feature_check(args.checks, args.file)
            elif args.command == "review":
                result = workflow.review(args.timeout, args.report, args.reviewer)
            elif args.command == "review-packet":
                result = workflow.review_packet(args.out)
            elif args.command == "ticket-proof-draft":
                result = workflow.ticket_proof_draft(args.out)
            elif args.command == "contract-proposal":
                result = workflow.contract_proposal(read_json(args.task), read_json(args.profile))
            elif args.command == "seal":
                result = workflow.seal(read_json(args.task), read_json(args.profile), read_json(args.review))
            elif args.command == "amend":
                result = workflow.amend(read_json(args.task), read_json(args.profile), read_json(args.review), args.reason)
            elif args.command == "repair":
                result = workflow.repair(args.reason, records_only=args.records_only)
            elif args.command == "extend-reviews":
                result = workflow.extend_reviews(args.rounds, args.reason)
            elif args.command == "cancel":
                result = workflow.cancel(args.reason)
            else:
                result = getattr(workflow, args.command)()
    return result


if __name__ == "__main__":
    sys.exit(main())
