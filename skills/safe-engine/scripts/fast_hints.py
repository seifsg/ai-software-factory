"""Work-record skeleton hints for fast_gate.py: each step's markers, for this run's kind, lane and flags only.

Loaded by `start` (fast_gate.skeleton), never by hooks. The checks themselves live in fast_record.py.
"""
import fast_briefs
import fast_record as record

HINTS = {  # record markers per step (fast-run.md#work-record); record_hints() adds what this run's kind and flags need
    "research": ">=3 '### <competitor>' with source URLs; feature matrix; Opportunities; "
                "product: '### Stack options', 3-row table",
    "kickoff": "Features, Approach, Answered by; product: Size, Stack",
    "tickets": "Epic URL; Backlog",
    "analysis": "Success; fenced ASCII chart",
    "plan": "### Files, ### Critique, ### Phases, ### Todos (T1..), ### Whole plan; Logging; Efficiency",
    "design": ">=4 hex colors; UI kit, Font, Logo, Icons, Layout; Theme (light mode); Journeys (counts and minimum)",
    "schema": "3-option table; Chosen; fenced ERD or DDL",
    "build": "per todo: 'T1 pre: ... do: ... post: ...'",
    "show": "share all planned reference/current pairs; record actual delivery and owner reply or elapsed deadline",
    "done-run": ">=1 real-use PASS; Logs",
    "handoff": "Run, Statuses, Unverified, Follow-ups",
}


def ui_hint(run):
    """The done-run's UI markers: screenshots on UI runs; current methods add file-changing runs and the verdicts."""
    if not (run.get("ui") or run.get("ux_rules")):
        return ""
    if not run.get("ux_rules"):
        return "; UI runs >=1 existing screenshot path"
    return "; UI runs or UI file changes: >=1 existing screenshot path; U1..U10 verdicts (no open FAIL); UX judge"


def pr_hint(run):
    """The handoff's PR markers this run's methods turn on."""
    parts = []
    if run.get("pr_proof"):
        parts.append("draft PR: Before & after outcome headings; both states as image/recording/fenced output")
        if run.get("pr_demo"):
            parts.append("Visual, Journey per outcome (visual: screenshot pair; journey: Video; scoped owner Media waiver only)")
    if run.get("credit"):
        parts.append("end PR with factory credit (how-to-make-a-pr credit.md)")
    return "".join("; " + part for part in parts)


def record_hints(run):
    """Each step's record markers for this run only: its kind, lane and the checks its methods turn on."""
    hints = dict(HINTS)
    if run.get("show_first"):
        hints["plan"] += "; UI: Look, Show, Prove, Ship; freeze show --plan before done plan"
    delivers, lane, coverage = run["kind"] != "change", record.light(run), run.get("coverage")  # delivers: product, feature
    online = "; online: "
    named = "; criteria cover every non-owner-deferred requested item" if delivers and coverage else ""
    if lane:
        hints["tickets"] = "Ticket line: URL or 'none (why)'; Backlog"
        hints["plan"] = "Success; ### Todos ('T1 <title> → <result> (#ticket, A1)')"
    elif delivers:
        hints["tickets"] += "; >=1 Sub-issue URL" + ("; Requested (R1, R2, ...)" if coverage else "")
    if coverage and not lane:
        hints["plan"] = hints["plan"].replace("(T1..)", "('T1 <title> → <result> (#ticket, A1)')")
    if lane and run.get("show_first"):
        hints["plan"] += "; UI: Look, Show, Prove, Ship; freeze show --plan before done plan"
    if run.get("scans") and run["mode"] == "lucky" and delivers:  # Lucky has no kickoff to hold the Size line
        hints["tickets"] += "; Size"
    hints["tickets"] += online + ("listed tickets open, with Definition of done" if coverage else
                                  "listed tickets have Definition of done") + named
    hints["plan"] += online + ("checklist covers every criterion and plan todo" if coverage else
                               "listed tickets have checklists") + named
    if coverage and run["kind"] == "feature":  # a feature's size, or 'none (<why>)' when small
        hints["kickoff"] += "; feature: Size"
    if run.get("ux_rules"):
        hints["design"] += "; Map, Hierarchy (primary action), Labels"
    hints["done-run"] += ui_hint(run)
    if run.get("worth"):
        hints["done-run"] += "; Findings: none only if clean with no fix-rounds; otherwise scored JSON + resolutions"
    if run.get("scans"):  # Size starts with POC, MVP, production or none (<why>)
        hints["done-run"] += "; MVP/production: Secrets, Dependencies, Static"
    if record.hidden(run):
        hints["done-run"] += "; Hidden checks block: '#<n> <ID>: PASS' for every listed criterion"
    if run.get("check_selection"):
        hints["plan"] += "; checks --plan: ticket text, category, proof reason"
        hints["build"] += "; prepare selected checks' syntax before done build"
        hints["done-run"] += "; current executed check receipts/verdicts; visual ports: likeness + suite"
    ticked = "listed tickets fully ticked or Blocked/Backlog/not planned" + (
        "; items cover every criterion and todo" if coverage else "")
    hints = fast_briefs.hints(hints, run) if run.get("briefs") else hints  # Interface, Ports, UX rules, Deferred
    hints["handoff"] += ("; Dev sign-in" if run.get("auth") else "") + pr_hint(run) + online + ticked + named
    return hints
