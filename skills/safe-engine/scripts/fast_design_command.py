"""CLI ownership for a run's immutable reference inventory and independent review receipts."""
import json
from pathlib import Path

import fast_design as design


def parser(sub, common):
    """Keep all mutations behind the open run and normal gate persistence."""
    command = sub.add_parser("design", parents=[common], help=__doc__)
    action = command.add_mutually_exclusive_group()
    action.add_argument("--input", help="Coverage JSON to bind before plan; inventory is immutable")
    action.add_argument("--review", help="Independent review JSON for the current candidate")
    action.add_argument("--candidate", action="store_true", help="Print current source fingerprint for the reviewer")


def run(args, gate):
    """Record references/review or report measured coverage; never judge images automatically."""
    try:
        project, state = gate.open_run(args.project)
        design.require(state.get("design_port"), "Start a new UI run with --design-port")
        design.require(not state.get("closed"), "Closed design evidence cannot be changed")
        if args.candidate:
            print(design.candidate(project))
            return
        if args.input:
            design.require("plan" not in state["done"] and not state.get("design"),
                           "The reference inventory is already frozen or the plan has started")
            path = design.local(project, args.input)
            data = design.read(path)
            inventory = design.inventory(project, data)
            design.statuses(data)
            state["design"] = {"path": path.relative_to(Path(project).resolve()).as_posix(), "inventory": inventory}
            gate.put(project, state)
            gate.log("design.inventory", key=state["key"], elements=len(inventory["elements"]))
        elif args.review:
            design.require("build" in state["done"], "Finish the build before the likeness review")
            path = design.local(project, args.review)
            evidence = design.review_evidence(project, state, design.load(project, state), design.read(path))
            state["design"]["review"] = {"path": path.relative_to(Path(project).resolve()).as_posix(),
                                         "sha256": design.file_hash(path), "evidence": evidence, "at": gate.now()}
            gate.put(project, state)
            gate.log("design.review", key=state["key"], reviewer=evidence["reviewer"])
        print(json.dumps(design.summary(design.load(project, state)), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        gate.fail(f"Design coverage: {error}")
