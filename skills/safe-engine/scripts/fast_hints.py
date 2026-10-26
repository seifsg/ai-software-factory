"""Work-record skeleton hints for fast_gate.py: each step's markers, for this run's kind, lane and flags only.

Loaded by `start` (fast_gate.skeleton), never by hooks. The checks themselves live in fast_record.py.
"""
import fast_briefs
import fast_record as record

HINTS = {  # record markers per step (fast-run.md#work-record); record_hints() adds what this run's kind and flags need
    "research": ">=3 '### <competitor>' each citing a source URL, a feature matrix table, an Opportunities line; "
                "product runs also '### Stack options' with a 3-row table",
    "kickoff": "Features, Approach, Answered by lines; product runs also Size and Stack",
    "tickets": "an Epic URL line, a Backlog line",
    "analysis": "a Success line and a fenced ASCII chart",
    "plan": "### Files, ### Critique, ### Phases, ### Todos (T1..), ### Whole plan, Logging and Efficiency lines",
    "design": ">=4 hex colors; UI kit, Font, Logo, Icons, Layout lines; Theme line naming light mode; Journeys line "
              "with counts and a minimum",
    "schema": "a 3-option table, a Chosen line, a fenced ERD or DDL",
    "build": "one line per plan todo: 'T1 pre: ... do: ... post: ...'",
    "show": "share every planned reference/current pair; record actual delivery and owner reply or elapsed deadline",
    "done-run": ">=1 PASS line from using it, a Logs line",
    "handoff": "Run, Statuses, Unverified, Follow-ups lines",
}


def ui_hint(run):
    """The done-run's UI markers: screenshots on UI runs; current methods add file-changing runs and the verdicts."""
    if not (run.get("ui") or run.get("ux_rules")):
        return ""
    if not run.get("ux_rules"):
        return "; UI runs >=1 existing screenshot path"
    return ("; UI runs, and runs that change UI files, >=1 existing screenshot path, a verdict line per U1..U10 "
            "(no open FAIL), a UX judge line")


def pr_hint(run):
    """The handoff's PR markers this run's methods turn on."""
    parts = []
    if run.get("pr_proof"):
        parts.append("a draft PR line: Before & after has a heading per outcome, each "
                     "Before and After with an image, recording or fenced block")
        if run.get("pr_demo"):
            parts.append("each outcome declares Visual and Journey (visual: screenshot pair, journey: Video; only a "
                         "scoped owner Media waiver)")
    if run.get("credit"):
        parts.append("PR ends with factory credit (how-to-make-a-pr credit.md)")
    return "".join("; " + part for part in parts)


def record_hints(run):
    """Each step's record markers for this run only: its kind, lane and the checks its methods turn on."""
    hints = dict(HINTS)
    if run.get("show_first"):
        hints["plan"] += "; UI phases: Look, Show, Prove, Ship; freeze show --plan before done plan"
    delivers, lane, coverage = run["kind"] != "change", record.light(run), run.get("coverage")  # delivers: product, feature
    online = "; online: "
    named = "; criteria name every requested item not owner-deferred" if delivers and coverage else ""
    if lane:
        hints["tickets"] = "a Ticket line (its URL, or 'none (why)'), a Backlog line"
        hints["plan"] = "a Success line, ### Todos ('T1 <title> → <result> (#ticket, A1)')"
    elif delivers:
        hints["tickets"] += ", >=1 Sub-issue URL line" + (", a Requested line (R1, R2, ...)" if coverage else "")
    if coverage and not lane:
        hints["plan"] = hints["plan"].replace("(T1..)", "('T1 <title> → <result> (#ticket, A1)')")
    if lane and run.get("show_first"):
        hints["plan"] += "; UI phases: Look, Show, Prove, Ship; freeze show --plan before done plan"
    if run.get("scans") and run["mode"] == "lucky" and delivers:  # Lucky has no kickoff to hold the Size line
        hints["tickets"] += ", a Size line"
    hints["tickets"] += online + ("each listed ticket is open with a Definition of done" if coverage else
                                  "each listed ticket has a Definition of done") + named
    hints["plan"] += online + ("checklist items name every criterion and hold every plan todo" if coverage else
                               "each listed ticket has checklist items") + named
    if coverage and run["kind"] == "feature":  # a feature's size, or 'none (<why>)' when small
        hints["kickoff"] += "; feature runs a Size line"
    if run.get("ux_rules"):
        hints["design"] += "; Map, Hierarchy (naming the primary action) and Labels lines"
    hints["done-run"] += ui_hint(run)
    if run.get("worth"):
        hints["done-run"] += "; Findings: clean none or scored JSON + resolutions"
    if run.get("scans"):  # Size starts with POC, MVP, production or none (<why>)
        hints["done-run"] += "; sized MVP or production: Secrets, Dependencies, Static lines"
    if record.hidden(run):
        hints["done-run"] += "; a Hidden checks block: '#<n> <ID>: PASS' per criterion of every listed ticket"
    ticked = "each listed ticket fully ticked, or Blocked, Backlog or not planned" + (
        "; items name every criterion and hold every plan todo" if coverage else "")
    hints = fast_briefs.hints(hints, run) if run.get("briefs") else hints  # Interface, Ports, UX rules, Deferred
    hints["handoff"] += (", a Dev sign-in line" if run.get("auth") else "") + pr_hint(run) + online + ticked + named
    return hints
