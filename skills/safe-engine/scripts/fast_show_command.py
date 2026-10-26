"""Show publication/reply commands and the declared, gated proof-suite entry point."""
from pathlib import Path
import sys

import fast_design as evidence
import fast_show as show


def parser(sub, common):
    """Keep the lifecycle on one small command family."""
    command = sub.add_parser("show", parents=[common], help="Prepare, share and respond to current UI pictures")
    actions = command.add_mutually_exclusive_group()
    for name in ("plan", "prepare", "shared", "reply"):
        actions.add_argument(f"--{name}", help=f"{name} JSON inside the project")
    actions.add_argument("--candidate", action="store_true", help="Current source fingerprint for Show captures")
    prove = sub.add_parser("prove", parents=[common], help="Run the declared suite after the owner checkpoint")
    prove.add_argument("--suite", action="store_true", required=True)


def invalidate(state):
    """New pictures replace the prior checkpoint, never borrow its owner response."""
    stopped = state["show"].get("reply", {}).get("action") == "stop"
    for name in ("shared", *([] if stopped else ["reply"])):
        state["show"].pop(name, None)
    for step in ("show", "done-run", "handoff"):
        state["done"].pop(step, None)


def prove(project, state, gate):
    """Use the existing bounded, cancellable runner; no new process or suite-cache machinery."""
    print(show.ready_for_prove(project, state))
    evidence.require("show" in state["done"], "Record done show before running the suite")
    from resolve_bundle import inspect_bundle
    bundle = state.get("bundle") or {"root": Path(__file__).resolve().parents[3]}
    selected = inspect_bundle(bundle["root"], expected=bundle.get("revision"), entrypoint="safe-engine")
    sys.path.insert(0, selected["bundle_root"])
    from safe_engine.runner import run_command
    plan = show.show_plan(state)
    if state["show"].get("proof") is not None:
        gate.log("show.proof_replaced", key=state["key"], proof=state["show"]["proof"])
    state["show"]["proof"] = {"passed": False, "status": "running"}
    gate.put(project, state)
    result = run_command(plan["full_suite"], project, plan["timeout_seconds"],
                         Path(project, ".factory/fast/prove-suite.log"))
    result["candidate"] = evidence.candidate(project)
    result["passed"] = result["passed"] and result["candidate"] == state["show"]["report"]["candidate"]
    state["show"]["proof"] = result
    gate.put(project, state)
    gate.log("show.prove", key=state["key"], passed=result["passed"])
    print(Path(result["log"]).read_text(encoding="utf-8", errors="replace"))
    evidence.require(result["passed"], "Suite failed, timed out or source changed; inspect the log")


def run(args, gate):
    """Only the normal gate writes protected records; all input remains untrusted evidence."""
    try:
        project, state = gate.open_run(args.project)
        evidence.require(show.enabled(state) and not state.get("closed"), "Show needs an open UI run on current methods")
        if args.command == "prove":
            prove(project, state, gate)
            return
        if args.candidate:
            print(evidence.candidate(project))
            return
        action = next((name for name in ("plan", "prepare", "shared", "reply") if getattr(args, name)), None)
        if action is None:
            print(show.ready_for_prove(project, state))
            return
        data = evidence.read(evidence.local(project, getattr(args, action)))
        if action == "plan":
            evidence.require("plan" not in state["done"] and not state.get("show"), "Show plan is already frozen")
            state["show"] = {"plan": show.plan(data)}
        elif action == "prepare":
            evidence.require("build" in state["done"], "Finish Look with done build before preparing Show")
            report = show.prepare(project, state, data)
            path = Path(project, ".factory/fast/show.md")
            path.write_text(show.markdown(project, report), encoding="utf-8")
            invalidate(state)
            state["show"]["report"] = {**report, "path": ".factory/fast/show.md", "sha256": evidence.file_hash(path)}
            print(path.read_text(encoding="utf-8"))
            print("Prepared only. Share these pictures, check access, then record show --shared.")
        else:
            show.current(project, state)
            if action == "shared":
                evidence.require(not state["show"].get("shared"), "Delivery already recorded; preserve its original deadline")
                state["show"]["shared"] = {**show.publication(data), "at": gate.now()}
            else:
                evidence.require(state["show"].get("shared"), "Record actual delivery before an owner reply")
                state["show"]["reply"] = {**show.reply(data, state), "at": gate.now()}
        gate.put(project, state)
        gate.log(f"show.{action}", key=state["key"])
        if action in ("shared", "reply"):
            print(show.notice(project, state))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError) as error:
        gate.fail(f"Show: {error}")
