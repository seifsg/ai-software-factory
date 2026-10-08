"""Work record parsing and step checks for fast_gate.py.

Each check returns a list of problems; empty means the step is recorded. Markers prove a step was
written down, not that it was good. Spec: .agents/skills/safe-engine/references/fast-run.md#work-record.
"""
import json
import re
from pathlib import Path

URL = re.compile(r"https?://[^\s)>\]|]+")
ISSUE = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/issues/(\d+)")
TASK = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[([ xX])\]", re.M)
CHECKLIST = re.compile(r"^(#{1,6})\s[^\n]*checklist[^\n]*$", re.I | re.M)
FENCE = re.compile(r"^\s*(```|~~~).*?^\s*\1", re.M | re.S)
DEFINITION = re.compile(r"^#{2,4}[^\n]*(?:definition of done|done when)", re.I | re.M)  # older tickets: "Done when"


def sections(text):
    """Level-2 sections by lowercase title; HTML comments (skeleton hints) never count."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    found, name = {}, None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            name = heading.group(1).lower()
            found.setdefault(name, [])
        elif name is not None:
            found[name].append(line)
    return {key: "\n".join(lines) for key, lines in found.items()}


def subsection(body, title):
    match = re.search(r"^###\s+[^\n]*" + re.escape(title) + r"[^\n]*\n(.*?)(?=^###\s|\Z)", body, re.M | re.S | re.I)
    return match.group(1) if match else None


def marker(body, label):
    match = re.search(r"\*\*" + re.escape(label) + r":\*\*[ \t]*\n?[ \t]*(\S[^\n]*)", body, re.I)
    return match.group(1).strip() if match else None


def table_rows(body):
    return [line for line in body.splitlines()
            if line.strip().startswith("|") and not re.fullmatch(r"\s*\|[\s:|-]+\|\s*", line)]


def fenced(body):
    return len(re.findall(r"^\s*```", body, re.M)) >= 2


def missing_markers(body, labels):
    return [f"needs a '**{label}:**' line" for label in labels if not marker(body, label)]


def todo_ids(all_sections):
    todos = subsection(all_sections.get("plan", ""), "Todos") or ""
    return sorted(set(re.findall(r"\bT(\d+)\b", todos)), key=int)


def check_research(run, body, **_):
    problems = []
    others = re.sub(r"^###\s+[^\n]*stack options[^\n]*\n.*?(?=^###\s|\Z)", "", body, flags=re.M | re.S | re.I)
    cited = [title for title, text in re.findall(r"^###\s+([^\n]+)\n(.*?)(?=^###\s|\Z)", others, re.M | re.S)
             if URL.search(text)]
    if len(cited) < 3:
        problems.append("needs >=3 '### <competitor>' subsections, each citing a source URL")
    if len(table_rows(others)) < 4:
        problems.append("needs a feature matrix table outside '### Stack options'")
    problems += missing_markers(body, ["Opportunities"])
    if run["kind"] == "product" and len(table_rows(subsection(body, "Stack options") or "")) < 4:
        problems.append("needs '### Stack options' with a 3-row table")
    return problems


def check_kickoff(run, body, **_):
    labels = ["Features", "Approach", "Answered by"] + (["Size", "Stack"] if run["kind"] == "product" else [])
    return missing_markers(body, labels)


def ticket_urls(body):
    """Epic URL (zero or one) and sub-issue URLs listed in a Tickets section."""
    epic = [url.rstrip(".,;") for url in URL.findall(marker(body, "Epic") or "")[:1]]
    subs = [url.rstrip(".,;") for line in re.findall(r"\*\*Sub-issue:\*\*(.*)", body, re.I) for url in URL.findall(line)]
    return epic, subs


def check_tickets(run, body, offline=None, **_):
    epic, subs = ticket_urls(body)
    problems = ([] if epic else ["needs an '**Epic:** <url>' line"]) + missing_markers(body, ["Backlog"])
    if run["kind"] != "change" and not subs:
        problems.append("needs >=1 '**Sub-issue:** <url>' line")
    if problems or offline:
        return problems
    return verify_tickets(epic[0], subs) or (ticket_problems(epic + subs, needs_definition) if run.get("ticket_checks") else [])


def verify_tickets(epic, subs):
    """Confirm the epic exists and every listed sub-issue is linked to it, through gh."""
    import subprocess
    match = ISSUE.match(epic)
    if not match:
        return [f"cannot check non-GitHub ticket {epic}; pass --offline '<tracker and reason>'"]
    repo, number = match.groups()
    try:
        gh("api", f"repos/{repo}/issues/{number}", "--jq", ".number")
        if subs:
            linked = set(gh("api", f"repos/{repo}/issues/{number}/sub_issues", "--paginate", "--jq", ".[].html_url").split())
            stray = [url for url in subs if url not in linked]
            if stray:
                return ["not linked as sub-issues of the epic: " + ", ".join(stray)]
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        return [f"cannot verify tickets with gh ({error}); fix access or pass --offline '<reason>'"]
    return []


def online(run, kwargs, check):
    """Run one ticket check on every listed ticket, unless the run predates ticket checks or the step is offline."""
    if kwargs.get("offline") or not run.get("ticket_checks"):
        return []
    epic, subs = ticket_urls(kwargs["all_sections"].get("tickets", ""))
    return ticket_problems(run.get("tickets", []) + epic + subs, check)  # tickets pinned at `done tickets` stay checked


def ticket_problems(urls, check):
    """Read each GitHub ticket once and collect check problems; an unreadable ticket stops the step."""
    import subprocess
    problems = []
    for url in dict.fromkeys(urls):
        if not ISSUE.match(url):
            return [f"cannot check non-GitHub ticket {url}; pass --offline '<tracker and reason>'"]
        try:
            ticket = read_ticket(url)
        except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError, TypeError, AttributeError) as error:
            return [f"cannot read {url} with gh ({error}); fix access or pass --offline '<reason>'"]
        problem = check(ticket)
        if problem:
            problems.append(f"{url}: {problem}")
    return problems


def read_ticket(url):
    """Body without fenced examples, and whether the issue is exempt: Blocked, Backlog or closed as not planned."""
    data = json.loads(gh("issue", "view", url, "--json", "body,stateReason,labels,projectItems"))
    if not isinstance(data, dict):
        raise ValueError("unexpected gh output")
    labels = {name(label) for label in listed(data, "labels")}
    boards = {name(item.get("status")) for item in listed(data, "projectItems") if isinstance(item, dict)} - {""}
    marked = lambda status: f"status: {status}" in labels or status in boards
    cancelled = str(data.get("stateReason") or "").upper() == "NOT_PLANNED"
    return {"body": FENCE.sub("", str(data.get("body") or "")),
            "exempt": cancelled or marked("blocked") or marked("backlog")}


def checklist(body):
    """Text under the ticket's Checklist heading, up to the next heading of the same or higher level."""
    heading = CHECKLIST.search(body)
    if not heading:
        return ""
    end = re.compile(rf"^#{{1,{len(heading.group(1))}}}\s", re.M).search(body, heading.end())
    return body[heading.end():end.start() if end else len(body)]


def listed(data, key):
    """A list field of gh output; anything else reads as empty."""
    value = data.get(key)
    return value if isinstance(value, list) else []


def name(value):
    """Lower-case name of a label or board status; anything else has none."""
    return str(value.get("name") or "").lower() if isinstance(value, dict) else ""


def needs_definition(ticket):
    """Tickets step: every listed ticket states its definition of done."""
    return None if DEFINITION.search(ticket["body"]) else "needs a 'Definition of done' section (ticket layout)"


def needs_checklist(ticket):
    """Plan step: every listed ticket in the run carries its checklist."""
    return None if ticket["exempt"] or TASK.search(checklist(ticket["body"])) else (
        "needs a Checklist section with task items ('- [ ] T1 <todo>') from the plan")


def needs_ticks(ticket):
    """Handoff: a ticket in the run is finished (every item ticked) unless Blocked, Backlog or cancelled."""
    if ticket["exempt"]:
        return None
    marks = TASK.findall(checklist(ticket["body"]))
    if not marks:
        return needs_checklist(ticket)
    left = marks.count(" ")
    if not left:
        return None
    return f"{left} unticked checklist item(s): finish them, or mark the ticket Blocked or Backlog with its reason"


def gh(*args):
    import subprocess
    result = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "gh failed")
    return result.stdout


def check_analysis(run, body, **_):
    return missing_markers(body, ["Success"]) + ([] if fenced(body) else ["needs a fenced ASCII chart"])


def check_plan(run, body, **kwargs):
    problems = [f"needs a '### {title}' subsection" for title in ("Files", "Critique", "Phases", "Todos", "Whole plan")
                if subsection(body, title) is None]
    if not todo_ids(kwargs["all_sections"]):
        problems.append("needs todo IDs (T1, T2, ...) under ### Todos")
    return problems + missing_markers(body, ["Logging", "Efficiency"]) or online(run, kwargs, needs_checklist)


def check_design(run, body, **_):
    problems = [] if len(set(re.findall(r"#[0-9a-fA-F]{6}\b", body))) >= 4 else ["needs >=4 hex palette colors"]
    problems += missing_markers(body, ["UI kit", "Font", "Logo", "Icons", "Layout", "Theme", "Journeys"])
    theme, journeys = marker(body, "Theme"), marker(body, "Journeys")
    if theme and "light" not in theme.lower():
        problems.append("Theme must name light mode as the default")
    if journeys and not re.search(r"\d.*\bmin\b\W*\d", journeys, re.I):
        problems.append("Journeys must give counts and a minimum: '<journey>: 2 actions, 1 load, min 2 actions'")
    return problems


def check_schema(run, body, **_):
    problems = [] if len(table_rows(body)) >= 4 else ["needs a 3-option comparison table"]
    return problems + missing_markers(body, ["Chosen"]) + ([] if fenced(body) else ["needs a fenced ERD or DDL"])


def check_build(run, body, **kwargs):
    lines = [line.lower() for line in body.splitlines()]
    return [f"T{number} needs a 'pre: ... do: ... post: ...' line" for number in todo_ids(kwargs["all_sections"])
            if not any(re.search(rf"\bt{number}\b", line) and all(tag in line for tag in ("pre:", "do:", "post:"))
                       for line in lines)]


def check_done_run(run, body, project, **_):
    problems = [] if re.search(r"\bPASS\b", body) else ["needs >=1 PASS result"]
    problems += missing_markers(body, ["Logs"])
    if run.get("ui"):
        shots = [Path(shot) for shot in re.findall(r"[\w./\\:~-]+\.(?:png|jpe?g|webp|gif)\b", body, re.I)]
        if not any((shot if shot.is_absolute() else Path(project) / shot).is_file() for shot in shots):
            problems.append("needs >=1 existing screenshot path")
    return problems


def check_handoff(run, body, **kwargs):
    labels = ["Run", "Statuses", "Unverified", "Follow-ups"] + (["Dev sign-in"] if run.get("auth") else [])
    return missing_markers(body, labels) or online(run, kwargs, needs_ticks)


CHECKS = {"research": check_research, "kickoff": check_kickoff, "tickets": check_tickets,
          "analysis": check_analysis, "plan": check_plan, "design": check_design, "schema": check_schema,
          "build": check_build, "done-run": check_done_run, "handoff": check_handoff}
