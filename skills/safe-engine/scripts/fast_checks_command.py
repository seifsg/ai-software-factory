"""Execute syntax and candidate checks with the existing bounded runner."""
from contextlib import nullcontext
import json
from pathlib import Path
import shutil
import sys
import uuid

import fast_checks as checks
import fast_design as evidence
import fast_show


def parser(sub, common):
    command = sub.add_parser("checks", parents=[common], help="Select proof, prepare syntax and run independent checks")
    action = command.add_mutually_exclusive_group(required=True)
    for name in ("plan", "prepare", "runtime", "observe"):
        action.add_argument(f"--{name}", help=f"{name} JSON inside the project")
    for name in ("run", "status", "brief"):
        action.add_argument(f"--{name}", action="store_true")


def runner(state):
    """Installed launchers load only the run's verified complete bundle."""
    from resolve_bundle import inspect_bundle
    bundle = state.get("bundle") or {"root": Path(__file__).resolve().parents[3]}
    selected = inspect_bundle(bundle["root"], expected=bundle.get("revision"), entrypoint="safe-engine")
    sys.path.insert(0, selected["bundle_root"])
    from safe_engine.runner import run_command
    return run_command


def parse_commands(project, prepared):
    """Native parsers read every declared source input; no caller-provided success command."""
    paths = dict.fromkeys(path for row in prepared["checks"].values() if not row.get("manual") for path in row["files"])
    for name in paths:
        path = evidence.local(project, name)
        if path.suffix == ".py":
            yield [sys.executable, "-c", "import ast,sys,tokenize; p=sys.argv[1]; ast.parse(tokenize.open(p).read(),filename=p)", str(path)]
        elif path.suffix == ".json":
            yield [sys.executable, "-c", "import json,sys; json.load(open(sys.argv[1],encoding='utf-8'))", str(path)]
        else:
            node = shutil.which("node")
            checks.require(node, "JavaScript syntax needs node on PATH")
            yield [node, "--check", str(path)]


def execute(project, state, gate, syntax_only=False):
    """A receipt starts failed, then passes only with unchanged inputs and all actual results."""
    saved = state["checks"]
    prepared = saved.get("prepared")
    checks.require(isinstance(prepared, dict), "Prepare a check set first")
    if not syntax_only:
        checks.require("build" in state["done"], "Finish build/manual use before running checks")
        if fast_show.enabled(state):
            fast_show.ready_for_prove(project, state)
            checks.require("show" in state["done"], "Record done show first")
        checks.runtime(project, state, saved.get("runtime", {}))
    before = checks.identity(project, prepared)
    candidate = evidence.candidate(project)
    target = "syntax" if syntax_only else "result"
    if saved.get(target):
        gate.log("checks.receipt_replaced", key=state["key"], receipt=saved[target])
        try:
            import fast_metrics
            fast_metrics.safe("emit", project, fast_metrics.identity(state), "invalidate",
                              reason="checks_receipt_replaced", receipt=target)
        except Exception:
            pass
    receipt = uuid.uuid4().hex
    result = {"passed": False, "status": "running", "receipt": receipt,
              "inputs": before, "candidate": candidate, "logs": []}
    saved[target] = result
    gate.put(project, state)
    run_command = runner(state)
    folder = Path(project, ".factory/fast/checks/logs", uuid.uuid4().hex)
    outcomes = []
    def run(command, timeout, kind):
        outcome = run_command(command, project, timeout, folder / f"{len(outcomes)}-{kind}.log")
        outcomes.append(outcome)
        result["logs"].append({"path": Path(outcome["log"]).relative_to(project).as_posix(),
                               "sha256": evidence.file_hash(Path(outcome["log"]))})
        if not outcome["passed"]:
            result["status"] = "harness-invalid" if kind == "syntax" else "failed-unclassified"
        return outcome["passed"]
    import fast_metrics
    binder = fast_metrics.bind(project, state)
    with binder if binder is not None else nullcontext():
        parsed = all(run(command, 60, "syntax") for command in parse_commands(project, prepared))
        passed = parsed
        if parsed and not syntax_only:
            observations = saved.get("observations", {})
            for key, row in prepared["checks"].items():
                if row.get("manual"):
                    observation = observations.get(key, {})
                    valid = observation.get("candidate") == candidate and observation.get("verdict") in ("PASS", "DEFERRED")
                    passed = passed and valid
                    if not valid:
                        result["status"] = "manual-observation-missing-or-failed"
                else:
                    passed = run(row["argv"], row["timeout_seconds"], "run") and passed
    result["outcomes"] = outcomes
    result["passed"] = passed and before == checks.identity(project, prepared) and candidate == evidence.candidate(project)
    if result["passed"]:
        result["status"] = "syntax-ready" if syntax_only else "executed"
    elif result["status"] == "running":
        result["status"] = "inputs-changed"
    def finish(current):
        """Save this execution only if no checker replaced or invalidated its receipt."""
        latest = current.get('checks', {})
        checks.require(isinstance(latest, dict) and latest.get('prepared') == prepared and
                       isinstance(latest.get(target), dict) and latest[target].get('receipt') == receipt,
                       'Check receipt changed concurrently; run checks again')
        result['passed'] = (result['passed'] and before == checks.identity(project, prepared)
                            and candidate == evidence.candidate(project))
        if not result['passed'] and result['status'] == 'executed':
            result['status'] = 'inputs-changed'
        latest[target] = result
    gate.mutate(project, state, finish)
    gate.log("checks.executed", key=state["key"], syntax_only=syntax_only, passed=result["passed"])
    print(json.dumps(result, indent=2))
    checks.require(result["passed"], "Checks did not pass; inspect retained logs, never relabel a failure")


def observe(project, state, data):
    """Manual proof names who observed what; owner/hardware deferral stays explicit."""
    key = checks.text(data.get("criterion"), "criterion")
    row = state["checks"].get("prepared", {}).get("checks", {}).get(key, {})
    checks.require(row.get("manual"), "Observation must name a prepared manual check")
    checks.require(data.get("candidate") == evidence.candidate(project), "Observation is stale")
    checks.text(data.get("source"), "observer/source")
    checks.text(data.get("observation"), "actual observation")
    checks.require(data.get("verdict") in ("PASS", "FAIL", "DEFERRED"), "Manual verdict must be PASS, FAIL or DEFERRED")
    if data["verdict"] == "DEFERRED":
        import fast_briefs
        checks.require(fast_briefs.DEFER.fullmatch(data.get("reason", "")), "Use DEFERRED (owner|hardware: reason)")
    state["checks"].setdefault("observations", {})[key] = data
    state["checks"].pop("result", None)


def run(args, gate):
    try:
        project, state = gate.open_run(args.project)
        checks.require(checks.enabled(state) and not state.get("closed"), "Checks selection needs an open run on current methods")
        if args.status:
            print(json.dumps({"problems": checks.problems(state, project, final=True), "checks": state.get("checks")}, indent=2))
            return
        if args.run:
            execute(project, state, gate)
            return
        if args.brief:
            saved = state.get("checks", {})
            print(json.dumps({"tickets": saved.get("plan"), "runtime": saved.get("runtime"),
                              "interface": saved.get("prepared", {}).get("interface"),
                              "ports": saved.get("prepared", {}).get("ports")}, indent=2))
            return
        action = next(name for name in ("plan", "prepare", "runtime", "observe") if getattr(args, name))
        data = evidence.read(evidence.local(project, getattr(args, action)))
        if action == "plan":
            checks.require("plan" not in state["done"] and not state.get("checks"), "Proof selection is frozen; revise through a new confirmed run")
            state["checks"] = {"plan": checks.selection(data, state)}
        elif action == "prepare":
            state.setdefault("checks", {})["prepared"] = checks.prepare(project, state, data)
            for key in ("result", "syntax", "observations"):
                state["checks"].pop(key, None)
        elif action == "runtime":
            checks.require("build" in state["done"], "Capture final runtime names after build")
            state["checks"]["runtime"] = checks.runtime(project, state, data)
            state["checks"].pop("result", None)
        else:
            observe(project, state, data)
        for step in ("done-run", "handoff"):
            state["done"].pop(step, None)
        gate.put(project, state)
        gate.log(f"checks.{action}", key=state["key"])
        if action == "prepare":
            execute(project, state, gate, syntax_only=True)
        else:
            print(f"Checks {action} recorded")
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError) as error:
        gate.fail(f"Checks: {error}")
