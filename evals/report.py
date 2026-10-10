"""Eval reports as JSON and Markdown, and the baseline compare that flags drops."""
import json
from pathlib import Path


def cell(text, limit=160):
    """Text safe for one Markdown table cell, cut at `limit` characters; report.json keeps it whole."""
    text = " ".join(str(text).split())
    return (text[:limit - 3] + "..." if len(text) > limit else text).replace("|", "\\|")


def ending(run):
    """How the run ended: void reason, timeout or exit code, plus any writes that escaped the run folder."""
    end = f"VOID: {run['void']}" if run.get("void") else "timed out" if run["timed_out"] else f"exit {run['exit']}"
    return end + (f"; escaped to temp: {', '.join(run['escapes'])}" if run.get("escapes") else "")


def markdown(report):
    """Per sample and arm: delivered/total, failing checks, minutes, how the agent ended; then arm totals."""
    lines = ["| Sample | Arm | Delivered | Failing checks | Minutes | Agent |", "|---|---|---|---|---|---|"]
    totals = {}
    for run in report["runs"]:
        failing = "; ".join(cell(f"{item}: {why}") for item, why in run["failing"].items()) or "none"
        lines.append(f"| {cell(run['sample'])} | {run['arm']} | {run['delivered']}/{run['total']} "
                     f"| {failing} | {run['minutes']} | {cell(ending(run))} |")
        done, total, minutes = totals.get(run["arm"], (0, 0, 0.0))
        totals[run["arm"]] = (done + run["delivered"], total + run["total"], minutes + run["minutes"])
    lines += ["", "| Arm | Delivered | Minutes |", "|---|---|---|"]
    lines += [f"| {arm} | {done}/{total} | {round(minutes, 2)} |" for arm, (done, total, minutes) in totals.items()]
    head = "**Interrupted:** partial report; queued runs never started.\n\n" if report.get("interrupted") else ""
    return "# Eval report\n\n" + head + "\n".join(lines) + "\n"


def write(report, out):
    """Write report.json and report.md into `out`; returns their paths."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    paths = out / "report.json", out / "report.md"
    paths[0].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    paths[1].write_text(markdown(report), encoding="utf-8")
    return paths


def count(value):
    """Whether `value` is a non-negative integer count (a boolean is not)."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def load(path):
    """A saved report; raises ValueError when it is missing, not JSON, or its runs are malformed or repeated."""
    try:
        runs = json.loads(Path(path).read_text(encoding="utf-8"))["runs"]
        keys = [(run["sample"], run["arm"]) for run in runs]
        if (not isinstance(runs, list) or len(set(keys)) != len(keys)
                or not all(isinstance(part, str) for key in keys for part in key)
                or not all(count(r["delivered"]) and count(r["total"]) and r["delivered"] <= r["total"] for r in runs)):
            raise TypeError("runs need unique sample/arm strings and counts with delivered <= total")
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f"{path}: not an eval report ({error})") from error
    return {"runs": runs}


def compare(baseline, current):
    """(problems, notes): a drop, a missing pair or a changed total is a problem; a new pair is a note."""
    then = {(r["sample"], r["arm"]): r for r in baseline["runs"]}
    now = {(r["sample"], r["arm"]): r for r in current["runs"]}
    problems = []
    for key, old in then.items():
        new, name = now.get(key), "/".join(key)
        if new is None:
            problems.append(f"DROP {name}: {old['delivered']} -> missing")
        elif new["total"] != old["total"]:
            problems.append(f"CHANGED {name}: total {old['total']} -> {new['total']}, not comparable")
        elif new["delivered"] < old["delivered"]:
            problems.append(f"DROP {name}: {old['delivered']} -> {new['delivered']}")
    return problems, [f"NEW {'/'.join(key)}: not in the baseline" for key in now if key not in then]
