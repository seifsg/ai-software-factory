"""Show publication/reply commands and the declared, gated proof-suite entry point."""
from pathlib import Path
import sys
from uuid import uuid4

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
    proof = prove.add_mutually_exclusive_group(required=True)
    proof.add_argument("--suite", action="store_true")
    proof.add_argument("--plan", help="Declare a non-UI full suite and its effective inputs before plan")
    prove.add_argument('--fresh', action='store_true', help='Explicit diagnostic rerun; still uses the machine queue')


def invalidate(state):
    """New pictures replace the prior checkpoint, never borrow its owner response."""
    stopped = state["show"].get("reply", {}).get("action") == "stop"
    for name in ("shared", *([] if stopped else ["reply"])):
        state["show"].pop(name, None)
    for step in ("show", "done-run", "handoff"):
        state["done"].pop(step, None)


def prove(project, state, gate, fresh=False):
    """Current owner/manual gates remain authoritative even when command evidence is reused."""
    if show.enabled(state):
        print(show.ready_for_prove(project, state))
        evidence.require("show" in state["done"], "Record done show before running the suite")
    else:
        evidence.require('build' in state['done'], 'Record done build before the full suite')
    from resolve_bundle import inspect_bundle
    bundle = state.get("bundle") or {"root": Path(__file__).resolve().parents[3]}
    selected = inspect_bundle(bundle["root"], expected=bundle.get("revision"), entrypoint="safe-engine")
    sys.path.insert(0, selected["bundle_root"])
    from safe_engine.runner import run_command
    holder = state['show'] if show.enabled(state) else state.get('suite')
    evidence.require(isinstance(holder, dict) and holder.get('plan'), 'Declare prove --plan before running a non-UI suite')
    plan = holder['plan']
    candidate = evidence.candidate(project)
    if holder.get('proof') is not None:
        gate.log("show.proof_replaced", key=state["key"], proof=holder['proof'])
    receipt = uuid4().hex
    holder['proof'] = {"passed": False, "status": "running", "receipt": receipt}
    gate.put(project, state)
    import fast_metrics
    binder = fast_metrics.bind(project, state)
    from contextlib import nullcontext
    with binder if binder is not None else nullcontext():
        if state.get('suite_policy') or 'suite_inputs' in plan:
            from safe_engine.suites import describe, execute
            def identify():
                return describe(project, [plan['full_suite']], plan.get('suite_inputs'), plan)
            def launch(slot):
                return [run_command(plan['full_suite'], project, plan['timeout_seconds'],
                                    Path(project, '.factory/fast/prove', slot.generation + '.log'), owned_lease=slot.lease())]
            batch = execute(project, identify, launch, cache=not fresh)
            result = {**batch['results'][0], 'reused': batch['reused'], 'suite_execution': batch['execution'],
                      'suite_identity': batch['identity']}
            result['passed'] = result['passed'] and batch['unchanged']
        else:
            result = run_command(plan["full_suite"], project, plan["timeout_seconds"],
                                 Path(project, ".factory/fast/prove", uuid4().hex + ".log"))
    result["candidate"] = evidence.candidate(project)
    result["passed"] = result["passed"] and result["candidate"] == candidate
    def finish(current):
        """Keep unrelated check and owner writes, but refuse a changed proof owner or plan."""
        latest = current.get('show' if show.enabled(current) else 'suite')
        evidence.require(isinstance(latest, dict) and latest.get('plan') == plan
                         and isinstance(latest.get('proof'), dict) and latest['proof'].get('receipt') == receipt,
                         'Suite proof changed concurrently; rerun for the current plan')
        if ('build' not in current['done'] or (show.enabled(current) and 'show' not in current['done'])):
            result.update(passed=False, status='run-reopened')
        if show.enabled(current):
            try:
                show.ready_for_prove(project, current)
            except (ValueError, KeyError, TypeError):
                result.update(passed=False, status='owner-stopped')
        result['passed'] = result['passed'] and evidence.candidate(project) == candidate
        if 'suite_identity' in result:
            result['passed'] = result['passed'] and identify() == result['suite_identity']
        latest['proof'] = result
    gate.mutate(project, state, finish)
    gate.log("show.prove", key=state["key"], passed=result["passed"])
    print(Path(result["log"]).read_text(encoding="utf-8", errors="replace"))
    evidence.require(result["passed"], "Suite failed, timed out or source changed; inspect the log")


def run(args, gate):
    """Only the normal gate writes protected records; all input remains untrusted evidence."""
    try:
        project, state = gate.open_run(args.project)
        evidence.require(not state.get('closed'), 'Show/Prove needs an open run')
        if args.command == "prove":
            if getattr(args, 'plan', None):
                evidence.require(not args.fresh, '--fresh applies only to prove --suite')
                evidence.require(not state.get('ui') and 'plan' not in state['done'] and not state.get('suite'),
                                 'Declare the non-UI suite once before done plan; UI uses show --plan')
                data = evidence.read(evidence.local(project, args.plan))
                state['suite'] = {'plan': show.suite_plan(data)}
                gate.put(project, state)
                print('Full suite plan recorded')
                return
            prove(project, state, gate, getattr(args, 'fresh', False))
            return
        evidence.require(show.enabled(state), 'Show needs an open UI run on current methods')
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
    except Exception as error:
        gate.fail(f"Show: {error}")
