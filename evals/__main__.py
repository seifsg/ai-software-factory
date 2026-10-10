"""`python -m evals run|compare|check` from the factory root. Python 3.9+, standard library only."""
import argparse
from datetime import datetime
import sys

from evals import catalog, isolation, report, runner


INTERRUPTED = 130  # the shell convention for a run stopped by Ctrl-C


def run(args):
    """Run the samples in both arms, write the report, and compare with a baseline when given."""
    if args.baseline:
        report.load(args.baseline)  # a bad baseline fails before any paid run
    out = args.out or isolation.FACTORY / ".factory/evals" / datetime.now().strftime("%Y%m%d-%H%M%S")
    result = runner.run_all(args.agent, out, args.sample, args.timeout, args.jobs, args.keep, args.factory_agent)
    paths = report.write(result, out)
    print(paths[1].read_text(encoding="utf-8"))
    print("Report:", *paths)
    if result["interrupted"]:
        print("Interrupted: partial report written; queued runs cancelled, running agents stopped.")
        return INTERRUPTED
    return compare(argparse.Namespace(baseline=args.baseline, report=paths[0])) if args.baseline else 0


def compare(args):
    """Exit 1 on any drop, missing pair or changed total against the baseline; new pairs are only noted."""
    problems, notes = report.compare(report.load(args.baseline), report.load(args.report))
    for line in problems + notes:
        print(line)
    print(f"{len(problems)} problem(s) against {args.baseline}" if problems else f"No drops against {args.baseline}")
    return 1 if problems else 0


def check(args):
    """Rubric self-check: every item fails on the untouched fixture and passes on the reference."""
    failed = 0
    sources = catalog.kit()
    for sample in catalog.load(args.sample):
        problems = catalog.self_check(sample, sources)
        failed += bool(problems)
        print(f"{'FAIL' if problems else 'PASS'} {sample.name}", *problems, sep="\n  ")
    return 1 if failed else 0


def parser():
    """The command line: run, compare and check."""
    root = argparse.ArgumentParser(prog="python -m evals", description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    go = commands.add_parser("run", help="run every sample in both arms with your agent command")
    go.add_argument("--agent", required=True, help="command template; see evals/README.md for placeholders")
    go.add_argument("--factory-agent", help="command template for the factory arm only (default: --agent)")
    go.add_argument("--timeout", type=float, default=30.0, help="minutes per run (default 30)")
    go.add_argument("--sample", action="append", help="only this sample; repeatable")
    go.add_argument("--jobs", type=int, default=1, help="runs at a time (default 1)")
    go.add_argument("--out", help="report folder (default .factory/evals/<timestamp>)")
    go.add_argument("--baseline", help="saved report.json to compare with; exit 1 on a drop")
    go.add_argument("--keep", action="store_true", help="keep each run's workspace for inspection")
    go.set_defaults(handler=run)
    diff = commands.add_parser("compare", help="compare a report with a saved baseline")
    diff.add_argument("baseline")
    diff.add_argument("report")
    diff.set_defaults(handler=compare)
    sanity = commands.add_parser("check", help="prove each rubric fails on its fixture and passes on its reference")
    sanity.add_argument("--sample", action="append", help="only this sample; repeatable")
    sanity.set_defaults(handler=check)
    return root


def main(argv=None):
    """Parse and dispatch; a bad input prints its reason and exits 2."""
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
