"""Validate and record Fast/Lucky repair selections without adding a tracker or replacing the build cycle."""
import hashlib
import json
from pathlib import Path

import fast_worth as worth


def parser(sub, common):
    """Register the explicit repair boundary; the selected report stays in the gate-owned receipt."""
    command = sub.add_parser("fix-round", parents=[common], help="Choose worthwhile fixes or an authorized finishing batch")
    command.add_argument("--file", required=True, help="JSON with scored findings; source and owner authority included")
    command.add_argument("--finding", action="append", required=True, help="Finding F1, F2 in report order; repeat")
    command.add_argument("--finishing-authority", help="Owner instruction and source authorizing this finishing batch")


def run(args, gate):
    """Refuse before changing state; accepted batches reopen build and invalidate completed proof steps."""
    try:
        project, state = gate.open_run(args.project)
        if state.get("closed") or state.get("paused") or gate.open_before_build(state):
            raise ValueError("Fix rounds need an open, unpaused run whose plan passed")
        report = gate.load(Path(args.file))
        decision = worth.select(report, args.finding, args.finishing_authority)
        encoded = json.dumps(report, sort_keys=True).encode()
        receipt = {"at": gate.now(), "report": report, "sha256": hashlib.sha256(encoded).hexdigest(), **decision}
        state.setdefault("fix_rounds", []).append(receipt)
        for step in ("build", "done-run", "handoff"):
            state["done"].pop(step, None)
        gate.put(project, state)
        gate.log("run.fix_round", key=state["key"], findings=args.finding, sha256=receipt["sha256"])
        try:
            import fast_metrics
            fast_metrics.safe(
                "emit",
                project,
                fast_metrics.identity(state),
                "invalidate",
                reason="fix_round",
                finding_ids=[str(item)[:32] for item in args.finding],
            )
        except Exception:
            pass
        print(json.dumps(decision, indent=2))
        for line in worth.parked_lines(report):
            print(line)
    except (OSError, ValueError, TypeError, KeyError) as error:
        gate.fail("Fix round refused: " + str(error))


def findings(body, project, marker, run):
    """A completed new run names its final finding report, or explicitly records a clean check."""
    value = marker(body, "Findings")
    rounds = run.get("fix_rounds", [])
    if value == "none" and not rounds:
        return []
    if not value or value == "none":
        return ["needs '**Findings:** none' for clean checks, or a JSON report path with every scored finding"]
    path = Path(value)
    try:
        report = json.loads((path if path.is_absolute() else Path(project) / path).read_text(encoding="utf-8-sig"))
        assessed = worth.rows(report)
        worth.reconcile(report, rounds)
        return [f"{row['id']}: resolve this finding or record an authorized accepted-deferral"
                for row in assessed if row["finding"]["disposition"] != "accepted-deferral"]
    except (OSError, ValueError, TypeError) as error:
        return ["Findings report: " + str(error)]
