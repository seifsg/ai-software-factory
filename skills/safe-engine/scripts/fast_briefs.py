"""What every brief carries, and what a run may leave to the owner: plan Interface, Ports and UX rules lines,
dev ports no other open run holds, and DEFERRED (owner|hardware) items. Spec: fast-run.md#briefs.
"""
import re

from fast_progress import is_none

PORT = re.compile(r"(?<![\w.-])([1-9]\d{3,4})(?![\w-]|\.\d)")  # '5180', 'localhost:5180.'; kept when 1024..65535
# 'DEFERRED (hardware: needs a macOS device)', 'DEFERRED (owner: sign-off on pricing copy)'
MARK = r"DEFERRED[ \t]+\((?:owner|hardware):[ \t]*[^()\n]*\S[^()\n]*\)"
DEFER = re.compile(MARK)


def ports(line):
    """The dev ports a Ports line names, in order; 'none (<why>)' owns none, even when <why> names one."""
    return [] if is_none(line) else list(dict.fromkeys(int(n) for n in PORT.findall(line or "") if 1024 <= int(n) <= 65535))


def plan_problems(run, body, marker, subsection, runs=None, light=False):
    """Briefs runs: a Ports line, an Interface subsection (full plans) and, on UI runs, a UX rules line naming U1 to
    U10; ports another open run already holds are refused, so parallel lanes never share a dev stack."""
    if not run.get("briefs"):
        return []
    problems = [] if light or (subsection(body, "Interface") or "").strip() else [
        "needs a '### Interface' subsection: public names, record shapes, labels, routes and commands the "
        "checker and builders use as written ('none (<why>)' when nothing is public)"]
    line = marker(body, "Ports")
    problems += [] if line else ["needs a '**Ports:**' line: this lane's dev ports per server, or 'none (<why>)'"]
    rules = marker(body, "UX rules") or ""
    if run.get("ui") and not (re.search(r"\bU1\b", rules) and re.search(r"\bU10\b", rules)):
        problems.append("needs a '**UX rules:**' line naming U1 to U10 (ux-quality) and the project's own rule "
                        "files, or 'none' for them: every UI builder brief carries it")
    return problems + clashes(run, ports(line), runs() if runs and line else [])


def clashes(run, mine, runs):
    """Ports this run names that another open run's plan holds."""
    problems = []
    for _, _, other in runs:
        if other.get("project") == run.get("project"):
            continue
        shared = sorted(set(mine) & set(other.get("ports") or []))
        if shared:
            problems.append(f"ports {', '.join(map(str, shared))} belong to open run '{other.get('key')}' at "
                            f"{other.get('project')}: give this lane its own block (fast-run.md#briefs)")
    return problems


def hints(hints, run):
    """The skeleton's gate hints for briefs runs."""
    ux = "; UI runs a UX rules line naming U1 to U10 and the project's rule files" if run.get("ui") else ""
    interface = "" if run.get("kind") == "change" and run.get("light") else "### Interface, "
    hints["plan"] += f"; {interface}a Ports line (no other open run's ports){ux}"
    hints["handoff"] += "; a Deferred line: 'none' or each owner or hardware item, every DEFERRED hidden check named"
    return hints


def handoff_problems(run, body, marker, hidden_checks):
    """Briefs runs: one '**Deferred:**' line ('none' or every deferred item), naming each DEFERRED hidden check
    (`hidden_checks`: the done-run's Hidden checks blocks, never its prose)."""
    if not run.get("briefs"):
        return []
    line = marker(body, "Deferred")
    if not line:
        return ["needs a '**Deferred:**' line: 'none', or each item left to the owner or hardware with its reason"]
    entries = re.findall(rf"#(\d+)[ \t]+([A-Z]{{1,3}}\d+):[ \t]*{MARK}", hidden_checks or "")
    named = set(re.findall(r"#(\d+)[ \t]+([A-Z]{1,3}\d+)\b", line))
    left = [f"#{n} {cid}" for n, cid in dict.fromkeys(entries) if (n, cid) not in named]
    return [f"'**Deferred:**' must name the deferred hidden checks: {', '.join(left)}"] if left else []
