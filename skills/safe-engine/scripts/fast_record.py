"""Work record parsing and step checks for fast_gate.py.

Each check returns a list of problems; empty means the step is recorded. Markers prove a step was
written down, not that it was good. Spec: .agents/skills/safe-engine/references/fast-run.md#work-record.
"""
import json
import re
from pathlib import Path

URL = re.compile(r"https?://[^\s)>\]|]+")
ISSUE = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/issues/(\d+)")
TASK = re.compile(r"^\s*[-*] \[([ xX])\]", re.M)
DEFINITION = re.compile(r"^#{2,4}[^\n]*definition of done", re.I | re.M)


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
    return problems or ([] if offline else verify_tickets(epic[0], subs) or ticket_problems(epic + subs, needs_definition))


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


def online(kwargs, check):
    """Run one ticket check on every ticket the record lists, unless the step is recorded offline."""
    if kwargs.get("offline"):
        return []
    epic, subs = ticket_urls(kwargs["all_sections"].get("tickets", ""))
    return ticket_problems(epic + subs, check)


def ticket_problems(urls, check):
    """Read each GitHub ticket once and collect check problems; an unreadable ticket stops the step."""
    import subprocess
    problems = []
    for url in dict.fromkeys(urls):
        if not ISSUE.match(url):
            return [f"cannot check non-GitHub ticket {url}; pass --offline '<tracker and reason>'"]
        try:
            ticket = read_ticket(url)
        except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as error:
            return [f"cannot read {url} with gh ({error}); fix access or pass --offline '<reason>'"]
        problem = check(ticket)
        if problem:
            problems.append(f"{url}: {problem}")
    return problems


def read_ticket(url):
    """Body, open state and Blocked mark (label or board status) of one issue."""
    data = json.loads(gh("issue", "view", url, "--json", "body,state,labels,projectItems"))
    if not isinstance(data, dict):
        raise ValueError("unexpected gh output")
    labels = {str((label or {}).get("name") or "").lower() for label in data.get("labels") or []}
    boards = {str(((item or {}).get("status") or {}).get("name") or "").lower() for item in data.get("projectItems") or []}
    return {"body": data.get("body") or "", "open": str(data.get("state", "")).lower() == "open",
            "blocked": "status: blocked" in labels or "blocked" in boards}


def needs_definition(ticket):
    return None if DEFINITION.search(ticket["body"]) else "needs a 'Definition of done' section (ticket layout)"


def needs_checklist(ticket):
    return None if TASK.search(ticket["body"]) else "needs checklist items ('- [ ] T1 <todo>') from the plan"


def needs_ticks(ticket):
    left = sum(1 for mark in TASK.findall(ticket["body"]) if mark == " ")
    if not left or not ticket["open"] or ticket["blocked"]:
        return None
    return f"{left} unticked checklist item(s): finish them, or mark the ticket Blocked with its reason"


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
    return problems + missing_markers(body, ["Logging", "Efficiency"]) or online(kwargs, needs_checklist)


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
    return missing_markers(body, labels) or online(kwargs, needs_ticks)


CHECKS = {"research": check_research, "kickoff": check_kickoff, "tickets": check_tickets,
          "analysis": check_analysis, "plan": check_plan, "design": check_design, "schema": check_schema,
          "build": check_build, "done-run": check_done_run, "handoff": check_handoff}
