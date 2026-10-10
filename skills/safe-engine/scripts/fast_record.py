"""Work record parsing and step checks for fast_gate.py.

Each check returns a list of problems; empty means the step is recorded. Markers prove a step was
written down, not that it was good. Spec: .agents/skills/safe-engine/references/fast-run.md#work-record.
"""
import json
import re
from pathlib import Path

URL = re.compile(r"https?://[^\s)>\]|]+")
ISSUE = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/issues/(\d+)")
TASK = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[([ xX])\].*(?:\n[ \t]+(?![-*+]\s|\d+[.)]\s)\S.*)*", re.M)  # marks; items
NEEDS = re.compile(r"\bneeds #\d+ T\d+")  # names another ticket's item, not one of this ticket's
CHECKLIST = re.compile(r"^(#{1,6})\s[^\n]*checklist[^\n]*$", re.I | re.M)
FENCE = re.compile(r"^\s*(```|~~~).*?^\s*\1", re.M | re.S)
DEFINITION = re.compile(r"^(#{2,4})[^\n]*(?:definition of done|done when)", re.I | re.M)  # older tickets: "Done when"
CRITERION = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*([A-Z]{1,3}\d+)\b", re.M)  # "- **A1:**", "1. **D3:**"
LABEL_ITEMS = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*[A-Z]{1,3}\d+\s*\(([^)\n]*)\)", re.M)  # "**A1 (R2):**" -> R2
ID = re.compile(r"\b[A-Z]{1,3}\d+\b")  # criterion, todo or requested item ID
REQUESTED = re.compile(r"\bR\d+\b")
# "R2 waitlist (owner-deferred: https://...)": the mark sits on its own item, before any other R-id
DEFERRED = re.compile(r"\b(R\d+)\b(?:(?!\bR\d+\b)[^()\n])*\((?i:owner-deferred):\s*"
                      r"(?:\[[^\]\n]*\]\(https?://[^\s)]+\)|https?://[^\s)]+)\)")  # bare URL or [text](URL)
# every '**Hidden checks:**' block, up to a blank line or the next line-start label; lists and tables included
HIDDEN = re.compile(r"\*\*Hidden checks:\*\*(.*?)(?=\n[ \t]*\n|\n[ \t]*\*\*[^*\n]+:\*\*|\Z)", re.I | re.S)
# one entry: an ID, then on its line before any other ID the first verdict: 'A1 PASS', '- A2: failed', '| A3 | ✅ |'
VERDICT = re.compile(r"\b([A-Z]{1,3}\d+)\b(?:\s*\([^)\n]*\))?(?:(?!\b[A-Z]{1,3}\d+\b)[^\n])*?"
                     r"(\b(?i:pass|fail)(?i:ed|es|ing)?\b|✅|❌)")


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
    """The label's value: on its line, or on the next line unless that line is another marker."""
    match = re.search(r"\*\*" + re.escape(label) + r":\*\*[ \t]*(?:\n[ \t]*(?!\*\*[^*\n]+:\*\*))?(\S[^\n]*)", body, re.I)
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
    sized = run["kind"] == "feature" and run.get("coverage")  # a feature's size, or 'none (<why>)' when small
    labels = ["Features", "Approach", "Answered by"] + (["Size", "Stack"] if run["kind"] == "product" else []) + (
        ["Size"] if sized else [])
    return missing_markers(body, labels)


def ticket_urls(body):
    """Epic URL (a change: its one ticket), zero or one, and sub-issue URLs listed in a Tickets section."""
    epic = [url.rstrip(".,;") for url in URL.findall(marker(body, "Epic") or marker(body, "Ticket") or "")[:1]]
    subs = [url.rstrip(".,;") for line in re.findall(r"\*\*Sub-issue:\*\*(.*)", body, re.I) for url in URL.findall(line)]
    return epic, subs


def requested(body, deferred=False):
    """Requested item IDs (R1..) listed after the '**Requested:**' label, up to the next label. An item carrying
    the mark '(owner-deferred: <url>)' left scope by the owner's decision and needs no criterion, unless
    `deferred` asks for every ID."""
    match = re.search(r"\*\*Requested:\*\*(.*?)(?=^\s*(?:[-*+]\s+)?\*\*(?!R\d+\b)[^*\n]+:\*\*|\Z)",
                      body, re.I | re.M | re.S)
    text = match.group(1) if match else ""
    skip = set() if deferred else set(DEFERRED.findall(text))
    return [rid for rid in dict.fromkeys(REQUESTED.findall(text)) if rid not in skip]


def check_tickets(run, body, offline=None, **_):
    epic, subs = ticket_urls(body)
    change, coverage, lane = run["kind"] == "change", run.get("coverage"), light(run)
    trivial = lane and not epic and (marker(body, "Ticket") or "").lower().startswith("none")
    problems = [] if epic or trivial else [
        "needs an '**Epic:** <url>' line" + (" or '**Ticket:** <url, or none (why)>'" if lane else "")]
    if lane and marker(body, "Epic") and marker(body, "Ticket"):
        problems.append("a change lists its one ticket once: keep only the '**Ticket:**' line")
    problems += missing_markers(body, ["Backlog"])
    wanted = [] if change or not coverage else requested(body)
    if not change and not subs:
        problems.append("needs >=1 '**Sub-issue:** <url>' line")
    if coverage and not change and not requested(body, deferred=True):
        problems.append("needs a '**Requested:**' line numbering every requested item: R1, R2, ...")
    if problems or trivial:
        return problems
    if offline:
        return readable(run, epic + subs)
    if not run.get("ticket_checks"):
        return verify_tickets(epic[0], subs)
    named = []  # requested items each listed ticket's criterion labels name, kept from its one read

    def read(ticket):
        named.extend(labelled(ticket["body"]))
        if run.get("light") and ticket["closed"]:  # a follow-up reopens the ticket it updates
            return "is closed: reopen the ticket this run updates, or list the right one"
        return needs_definition(ticket)
    return verify_tickets(epic[0], subs) or ticket_problems(epic + subs, read) or unnamed(wanted, named)


def labelled(body):
    """Requested item IDs the definition of done's criterion labels name: '**A1 (R2):**'."""
    return REQUESTED.findall(" ".join(LABEL_ITEMS.findall(under(body, DEFINITION))))


def unnamed(wanted, named):
    """The gap when a requested item has no criterion naming it."""
    gaps = [rid for rid in wanted if rid not in set(named)]
    return [f"requested items no listed ticket's criteria name: {', '.join(gaps)}"] if gaps else []


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
    if not run.get("ticket_checks"):
        return []
    epic, subs = ticket_urls(kwargs["all_sections"].get("tickets", ""))
    if kwargs.get("offline"):
        return readable(run, run.get("tickets", []) + epic + subs)
    return ticket_problems(run.get("tickets", []) + epic + subs, check)  # tickets pinned at `done tickets` stay checked


def readable(run, urls):
    """On coverage runs, --offline is refused when gh can read the first listed GitHub ticket after all."""
    import subprocess
    url = next((url for url in urls if ISSUE.match(url)), None)
    if not run.get("coverage") or not url:
        return []
    try:
        read_ticket(url)
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError, TypeError, AttributeError):
        return []  # not readable here: offline is the honest record
    return [f"{url} is readable through gh: record this step online, without --offline"]


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
    """Body without fenced examples, and its marks: closed as not planned, Blocked, Backlog (label or board)."""
    data = json.loads(gh("issue", "view", url, "--json", "body,state,stateReason,labels,projectItems"))
    if not isinstance(data, dict):
        raise ValueError("unexpected gh output")
    labels = {name(label) for label in listed(data, "labels")}
    boards = {name(item.get("status")) for item in listed(data, "projectItems") if isinstance(item, dict)} - {""}
    marked = lambda status: f"status: {status}" in labels or status in boards
    cancelled = str(data.get("stateReason") or "").upper() == "NOT_PLANNED"
    return {"url": url, "body": FENCE.sub("", str(data.get("body") or "")), "stopped": cancelled or marked("blocked"),
            "backlog": marked("backlog"), "closed": str(data.get("state") or "").upper() == "CLOSED"}


def under(body, heading):
    """Text under the first heading `heading` matches, up to the next heading of the same or higher level."""
    found = heading.search(body)
    if not found:
        return ""
    end = re.compile(rf"^#{{1,{len(found.group(1))}}}\s", re.M).search(body, found.end())
    return body[found.end():end.start() if end else len(body)]


def checklist(body):
    """Text under the ticket's Checklist heading."""
    return under(body, CHECKLIST)


def items(body):
    """The ticket's checklist task items with their wrapped lines; prose and `needs` markers name nothing."""
    return NEEDS.sub("", "\n".join(item.group(0) for item in TASK.finditer(checklist(body))))


def uncovered(body):
    """Criterion IDs in the definition of done that no checklist item names (no spec drift)."""
    named = set(ID.findall(items(body)))
    return [cid for cid in dict.fromkeys(CRITERION.findall(under(body, DEFINITION))) if cid not in named]


def covered(run, check):
    """`check`, then on coverage runs: every criterion of a ticket still in play is named by an item."""
    def both(ticket):
        gaps = [] if not run.get("coverage") or ticket["stopped"] or ticket["backlog"] else uncovered(ticket["body"])
        return check(ticket) or (f"criteria no checklist item names: {', '.join(gaps)}" if gaps else None)
    return both


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
    """Plan step: every listed ticket that is not Blocked or cancelled carries its checklist."""
    return None if ticket["stopped"] or TASK.search(checklist(ticket["body"])) else (
        "needs a Checklist section with task items ('- [ ] T1 <todo>') from the plan")


def needs_ticks(ticket):
    """Handoff: a listed ticket is finished (every item ticked) unless Blocked, cancelled or deferred to Backlog."""
    if ticket["stopped"] or ticket["backlog"]:
        return None
    marks = TASK.findall(checklist(ticket["body"]))
    if not marks:
        return needs_checklist(ticket)
    left = marks.count(" ")
    if not left:
        return None
    return (f"{left} unticked checklist item(s): finish them, mark the ticket Blocked with its reason, "
            "or Backlog only when the owner deferred it")


def gh(*args):
    import subprocess
    result = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "gh failed")
    return result.stdout


def check_analysis(run, body, **_):
    return missing_markers(body, ["Success"]) + ([] if fenced(body) else ["needs a fenced ASCII chart"])


def light(run):
    """A light-lane change: a Success line and todos replace the analysis step and the full plan."""
    return run.get("kind") == "change" and bool(run.get("light"))


def check_plan(run, body, **kwargs):
    titles = ("Todos",) if light(run) else ("Files", "Critique", "Phases", "Todos", "Whole plan")
    problems = [f"needs a '### {title}' subsection" for title in titles if subsection(body, title) is None]
    if not todo_ids(kwargs["all_sections"]):
        problems.append("needs todo IDs (T1, T2, ...) under ### Todos")
    labels = ["Success"] if light(run) else ["Logging", "Efficiency"]
    return problems + missing_markers(body, labels) or held(run, kwargs, covered(run, needs_checklist))


def held(run, kwargs, check):
    """`check` on every listed ticket; on coverage runs also: each plan todo is an item there and each
    requested item is still named by a criterion (no drift after the tickets step)."""
    lists, named = [], []  # each listed ticket's items and labelled requested items, kept from its one read

    def read(ticket):
        lists.append(items(ticket["body"]))
        named.extend(labelled(ticket["body"]))
        return check(ticket)
    problems = online(run, kwargs, read)
    if problems or not run.get("coverage") or not lists:
        return problems
    ids = set(ID.findall("\n".join(lists)))
    loose = [f"T{n}" for n in todo_ids(kwargs["all_sections"]) if f"T{n}" not in ids]
    wanted = [] if run.get("kind") == "change" else requested(kwargs["all_sections"].get("tickets", ""))
    todos = [f"plan todos no listed ticket's checklist holds: {', '.join(loose)}"] if loose else []
    return todos + unnamed(wanted, named)


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
    """Each plan todo has one line with pre:, do: and post:; on coverage runs the line starts with its ID, so a
    mention such as 'T23..T34' in another todo's line never counts."""
    lines = [line.lower() for line in body.splitlines()]
    lead = r"\s*(?:\|\s*)?(?:(?:[-*+]|\d+[.)])\s+)?(?:\[[ x]\]\s+)?[*`]*"  # bullet, number, [x], **, ` or a table cell
    owns = (lambda n, line: re.match(rf"{lead}t{n}\b", line)) if run.get("coverage") else (
        lambda n, line: re.search(rf"\bt{n}\b", line))
    return [f"T{number} needs its own 'T{number} pre: ... do: ... post: ...' line"
            for number in todo_ids(kwargs["all_sections"])
            if not any(owns(number, line) and all(tag in line for tag in ("pre:", "do:", "post:")) for line in lines)]


def check_done_run(run, body, project, **kwargs):
    problems = [] if re.search(r"\bPASS\b", body) else ["needs >=1 PASS result"]
    problems += missing_markers(body, ["Logs"])
    if run.get("ui"):
        shots = [Path(shot) for shot in re.findall(r"[\w./\\:~-]+\.(?:png|jpe?g|webp|gif)\b", body, re.I)]
        if not any((shot if shot.is_absolute() else Path(project) / shot).is_file() for shot in shots):
            problems.append("needs >=1 existing screenshot path")
    return problems + (hidden_checks(body, kwargs, run) if hidden(run) else [])


def hidden(run):
    """Product and feature runs whose methods define hidden checks; change runs and older runs never."""
    return bool(run.get("hidden_checks")) and run.get("kind") != "change"


def verdicts(body):
    """Hidden checks entries by scope: '#2 A1 PASS' scopes to issue 2, unscoped entries to '' (every ticket)."""
    found = {}
    for block in HIDDEN.findall(body):
        parts = re.split(r"#(\d+)\b", block)
        for scope, text in zip([""] + parts[1::2], parts[::2]):
            found.setdefault(scope, []).extend((cid, mark[:4].lower() == "pass" or mark == "✅")
                                               for cid, mark in VERDICT.findall(text))
    return found


def hidden_checks(body, kwargs, run):
    """Any FAIL entry refuses; online, every in-play listed ticket's criterion needs a PASS; offline, >=1 entry."""
    found = verdicts(body)
    entries = [entry for scoped in found.values() for entry in scoped]
    failed = [cid for cid, passed in entries if not passed]
    if failed:
        return [f"hidden checks FAIL ({', '.join(dict.fromkeys(failed))}): back to build, then the checker runs them again"]
    if not entries:
        return ["needs a '**Hidden checks:**' line or list from the checker: every criterion ID with PASS or FAIL"]
    gaps = []

    def read(ticket):
        if not (ticket["stopped"] or ticket["backlog"]):
            number = ISSUE.match(ticket["url"]).group(2)
            passed = {cid for cid, _ in found.get(number, []) + found.get("", [])}
            criteria = dict.fromkeys(CRITERION.findall(under(ticket["body"], DEFINITION)))
            gaps.extend(f"#{number} {cid}" for cid in criteria if cid not in passed)
    problems = online(run, kwargs, read)
    return problems or ([f"criteria without a hidden-check PASS: {', '.join(gaps)}"] if gaps else [])


def check_handoff(run, body, **kwargs):
    labels = ["Run", "Statuses", "Unverified", "Follow-ups"] + (["Dev sign-in"] if run.get("auth") else [])
    return missing_markers(body, labels) or held(run, kwargs, covered(run, needs_ticks))


CHECKS = {"research": check_research, "kickoff": check_kickoff, "tickets": check_tickets,
          "analysis": check_analysis, "plan": check_plan, "design": check_design, "schema": check_schema,
          "build": check_build, "done-run": check_done_run, "handoff": check_handoff}
