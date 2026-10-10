"""Eval reports as JSON and Markdown, and the baseline compare that flags drops."""
import json
from pathlib import Path


def cell(text, limit=160):
    """Text safe for one Markdown table cell, cut at `limit` characters; report.json keeps it whole."""
    text = " ".join(str(text).split())
    return (text[:limit - 3] + "..." if len(text) > limit else text).replace("|", "\\|")


def markdown(report):
    """Per sample and arm: delivered/total, failing checks with reasons, minutes, agent end; then arm totals."""
    lines = ["| Sample | Arm | Delivered | Failing checks | Minutes | Agent |", "|---|---|---|---|---|---|"]
    totals = {}
    for run in report["runs"]:
        failing = "; ".join(cell(f"{item}: {why}") for item, why in run["failing"].items()) or "none"
        end = "timed out" if run["timed_out"] else f"exit {run['exit']}"
        lines.append(f"| {cell(run['sample'])} | {run['arm']} | {run['delivered']}/{run['total']} "
                     f"| {failing} | {run['minutes']} | {end} |")
        done, total, minutes = totals.get(run["arm"], (0, 0, 0.0))
        totals[run["arm"]] = (done + run["delivered"], total + run["total"], minutes + run["minutes"])
    lines += ["", "| Arm | Delivered | Minutes |", "|---|---|---|"]
    lines += [f"| {arm} | {done}/{total} | {round(minutes, 2)} |" for arm, (done, total, minutes) in totals.items()]
    return "# Eval report\n\n" + "\n".join(lines) + "\n"


def write(report, out):
    """Write report.json and report.md into `out`; returns their paths."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    paths = out / "report.json", out / "report.md"
    paths[0].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    paths[1].write_text(markdown(report), encoding="utf-8")
    return paths


def load(path):
    """A saved report; raises ValueError when it is missing, not JSON or has no valid runs."""
    try:
        report = json.loads(Path(path).read_text(encoding="utf-8"))
        runs = report["runs"]
        if not isinstance(runs, list) or not all(
                isinstance(run["sample"], str) and isinstance(run["arm"], str)
                and isinstance(run["delivered"], int) for run in runs):
            raise TypeError("runs need sample, arm and an integer delivered")
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f"{path}: not an eval report ({error})") from error
    return report


def drops(baseline, current):
    """Each sample/arm whose delivered count fell below the baseline's; a missing pair counts as a drop."""
    now = {(run["sample"], run["arm"]): run["delivered"] for run in current["runs"]}
    return [f"{run['sample']}/{run['arm']}: {run['delivered']} -> {now.get((run['sample'], run['arm']), 'missing')}"
            for run in baseline["runs"] if now.get((run["sample"], run["arm"]), -1) < run["delivered"]]
