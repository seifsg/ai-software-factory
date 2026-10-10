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
    return {"body": FENCE.sub("", str(data.get("body") or "")), "stopped": cancelled or marked("blocked"),
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


UX_BRIEF = ("Map", "Hierarchy", "Labels")  # ux-quality step 1: structure, priority and words, planned before UI code
UX_RULES = tuple(f"U{n}" for n in range(1, 11))  # ux-quality step 3 rule IDs; each gets a done-run verdict
UX_AREAS = ("Map", "Navigation", "Hierarchy", "Disclosure", "Labels", "Interaction cost", "States and feedback",
            "Access and devices", "Look and consistency", "Performance")  # their area names, in ID order
# "- U3 PASS 04, 13: ...", "- **U3:** FAIL ...", "| U3 | Hierarchy | PASS | ... |": the ID, its area name or none, the
# verdict, then its text with any indented lines under it. Only a known area name may sit between the ID and the
# verdict, so "U3 FAIL schedule, PASS roster" stays a FAIL.
LEAD, SEP = r"^[ \t]*(?:\|[ \t]*)?(?:(?:[-*+]|\d+[.)])[ \t]+)?(?:\[[ xX]\][ \t]+)?[*`]*", r"[*` \t:|.,()-]*"
MORE = r"(?:\n[ \t]+(?!(?:[-*+]|\d+[.)])?[ \t]*[*`]*U\d+\b)\S.*)*"  # indented lines under it, never another rule's line
VERDICT = re.compile(rf"{LEAD}(U\d+)\b{SEP}(?:(?:{'|'.join(UX_AREAS)}){SEP})?(PASS|FAIL|UNKNOWN|N/A)\b(.*{MORE})$",
                     re.M | re.I)
RULE_LINE = re.compile(r"^.*(?:\bU\d+\b|\*\*UX judge:\*\*).*$", re.M | re.I)  # any line naming a rule or the judge
FAILED = re.compile(r"\bFAIL(?:S|ED)?\b")  # uppercase only: "failed booking with retry" is evidence, not a verdict
UI_FILE = re.compile(r"(?<!\.test)(?<!\.spec)(?<!\.stories)\.(?:tsx|jsx|vue|svelte|astro|html?|css|scss|sass|less|razor|"
                     r"cshtml|erb|hbs|ejs|pug|liquid|twig|njk|jinja2?|j2|mustache|haml|slim|xaml|axaml|storyboard|xib|qml|"
                     r"fxml|uxml|uss|tscn)$|\.blade\.php$", re.I)  # views and styles, not tests or stories; others use --ui
HEX = re.compile(r"[0-9a-f]{40,64}")


def block(body, label):
    """The label's value with the lines under it, up to a blank line, a heading or the next marker."""
    match = re.search(r"\*\*" + re.escape(label) + r":\*\*(.*?)(?=^[ \t]*(?:(?:[-*+]|\d+[.)])[ \t]+)?\*\*[^*\n]+:\*\*|"
                      r"^[ \t]*$|^#|\Z)", body, re.I | re.M | re.S)
    return match.group(1) if match else ""


def check_design(run, body, **_):
    problems = [] if len(set(re.findall(r"#[0-9a-fA-F]{6}\b", body))) >= 4 else ["needs >=4 hex palette colors"]
    brief = list(UX_BRIEF) if run.get("ux_rules") else []
    problems += missing_markers(body, ["UI kit", "Font", "Logo", "Icons", "Layout", "Theme", "Journeys", *brief])
    theme, journeys = marker(body, "Theme"), marker(body, "Journeys")
    if theme and "light" not in theme.lower():
        problems.append("Theme must name light mode as the default")
    if journeys and not re.search(r"\d.*\bmin\b\W*\d", journeys, re.I):
        problems.append("Journeys must give counts and a minimum: '<journey>: 2 actions, 1 load, min 2 actions'")
    if brief and marker(body, "Hierarchy") and "primary" not in block(body, "Hierarchy").lower():
        problems.append("Hierarchy must name each key screen's primary action: '<screen>: primary <action>; ...'")
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


def check_done_run(run, body, project, **_):
    touched = [] if run.get("ui") or not run.get("ux_rules") else ui_files(run, project)
    audited = run.get("ux_rules") and (run.get("ui") or touched)  # this run owes the UX audit
    used = RULE_LINE.sub("", VERDICT.sub("", body)) if audited else body  # rule lines never stand in for using it
    problems = [] if re.search(r"\bPASS\b", used) else ["needs >=1 PASS result from using it"]
    problems += missing_markers(body, ["Logs"])
    if run.get("ui") or touched:
        shots = [Path(shot) for shot in re.findall(r"[\w./\\:~-]+\.(?:png|jpe?g|webp|gif)\b", body, re.I)]
        missing = [] if any((shot if shot.is_absolute() else Path(project) / shot).is_file() for shot in shots) else [
            "needs >=1 existing screenshot path"]
        missing += ux_audit(body) if run.get("ux_rules") else []
        problems += ([f"this run changed UI files ({', '.join(touched[:3])}): record the UX audit"]
                     if missing and touched else []) + missing
    return problems


def ux_audit(body):
    """A fresh judge's verdict line per rule ID (ux-quality step 4), each with evidence or a reason. No FAIL is left
    about a rule: not as its verdict, in its text or the lines under it, or on any other line naming it. A contested
    FAIL is recorded as UNKNOWN with both reasons, so an UNKNOWN line may quote one."""
    verdicts = [(m.start(), m.group(1).upper(), m.group(2).upper(), m.group(3)) for m in VERDICT.finditer(body)]
    contested = {start for start, _, verdict, _ in verdicts if verdict == "UNKNOWN"}
    failed = {rule for _, rule, verdict, text in verdicts if verdict == "FAIL" or verdict != "UNKNOWN" and FAILED.search(text)}
    failed |= {rule.upper() for line in re.finditer(r"(?m)^.*$", body) if line.start() not in contested
               and FAILED.search(line.group()) for rule in re.findall(r"\bU\d+\b", line.group(), re.I)}
    named = {rule for _, rule, _, _ in verdicts}
    problems = [f"needs a '{rule} PASS|FAIL|UNKNOWN|N/A <screen>: <evidence or reason>' line"
                for rule in UX_RULES if rule not in named]
    problems += [f"{rule} FAIL is open: fix it, recheck, then keep one final verdict line and no other line naming {rule} "
                 "with FAIL; or record UNKNOWN with both reasons" for rule in sorted(failed, key=lambda r: int(r[1:]))]
    problems += [f"{rule} {verdict} needs its evidence or reason" for _, rule, verdict, text in verdicts
                 if rule not in failed and len(re.sub(r"\W", "", text)) < 3]
    return problems + missing_markers(body, ["UX judge"])


def ui_start(project):
    """The start commit and the UI files already changed then, so the done-run counts only this run's own edits."""
    base = (git(project, "rev-parse", "--verify", "-q", "HEAD") or "").strip() or None
    return {"base": base, "ui_seen": {name: digest(Path(project) / name)
                                      for names in ui_listings({"base": base}, project) for name in names}}


def ui_files(run, project):
    """UI files inside the project this run created, edited or deleted; none without Git."""
    seen = run.get("ui_seen") if isinstance(run.get("ui_seen"), dict) else {}
    touched = [name for name, mark in seen.items() if digest(Path(project) / name) != mark]  # changed at start, again
    for names in [] if touched else ui_listings(run, project):
        touched = [name for name in names if name not in seen]
        if touched:
            break  # the first listing with a new change spares the next git call
    return touched


def ui_listings(run, project):
    """UI paths under the project, one git call at a time: tracked files changed since the start commit (every tracked
    file when that commit is unknown or unreadable), then untracked files."""
    base = run.get("base")
    diff = git(project, "diff", "--name-only", "--relative", base) if isinstance(base, str) and HEX.fullmatch(base) else None
    tracked = diff if diff is not None else git(project, "ls-files")
    if tracked is None:
        return  # no Git here: nothing to check
    yield [name for name in tracked.splitlines() if UI_FILE.search(name)]
    untracked = git(project, "ls-files", "--others", "--exclude-standard") or ""
    yield [name for name in untracked.splitlines() if UI_FILE.search(name)]


def git(project, *args):
    """A git command's output in the project, or None when it fails."""
    import subprocess
    try:
        result = subprocess.run(["git", "-c", "core.quotePath=false", "-C", str(project), *args], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return None if result.returncode else result.stdout


def digest(path):
    """A file's content hash; None once it is gone."""
    import hashlib
    try:
        return hashlib.sha1(path.read_bytes()).hexdigest()
    except OSError:
        return None


def check_handoff(run, body, **kwargs):
    labels = ["Run", "Statuses", "Unverified", "Follow-ups"] + (["Dev sign-in"] if run.get("auth") else [])
    return missing_markers(body, labels) or held(run, kwargs, covered(run, needs_ticks))


CHECKS = {"research": check_research, "kickoff": check_kickoff, "tickets": check_tickets,
          "analysis": check_analysis, "plan": check_plan, "design": check_design, "schema": check_schema,
          "build": check_build, "done-run": check_done_run, "handoff": check_handoff}
