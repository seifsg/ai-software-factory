"""Work record parsing and step checks for fast_gate.py.

Each check returns a list of problems; empty means the step is recorded. Markers prove a step was
written down, not that it was good. Spec: .agents/skills/safe-engine/references/fast-run.md#work-record.
"""
import json
import re
import sys
from pathlib import Path

HERE = str(Path(__file__).resolve().parent)
if HERE not in sys.path:
    sys.path.insert(0, HERE)  # loaded by file path (tests, older gates): find the sibling module
from fast_progress import built_ids, sections, subsection, todo_ids, without_result  # noqa: E402,F401 - shared parsers
import fast_proof  # noqa: E402 - the PR body's Before & after check

URL = re.compile(r"https?://[^\s)>\]|]+")
ISSUE = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/issues/(\d+)")
PULL = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/pull/\d+")
TASK = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[([ xX])\].*(?:\n[ \t]+(?![-*+]\s|\d+[.)]\s)\S.*)*", re.M)  # marks; items
NEEDS = re.compile(r"\bneeds #\d+ T\d+")  # names another ticket's item, not one of this ticket's
CHECKLIST = re.compile(r"^(#{1,6})\s[^\n]*checklist[^\n]*$", re.I | re.M)
FENCE = re.compile(r"^\s*(```|~~~).*?^\s*\1", re.M | re.S)
DEFINITION = re.compile(r"^(#{2,4})[^\n]*(?:definition of done|done when)", re.I | re.M)  # older tickets: "Done when"
TODO_RANGE = re.compile(r"\bT(\d+)\s*(?:to|-|–)\s*T(\d+)\b")  # "T63 to T65", "T63-T65"
OTHERS = re.compile(r"#(\d+)\s+[A-Z]{1,3}\d+(?:\s+to\s+[A-Z]{1,3}\d+)?")  # a ticket's IDs: "#4 A1 to A8"
CRITERION = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*([A-Z]{1,3}\d+)\b", re.M)  # "- **A1:**", "1. **D3:**"
LABEL_ITEMS = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*[A-Z]{1,3}\d+\s*\(([^)\n]*)\)", re.M)  # "**A1 (R2):**" -> R2
ID = re.compile(r"\b[A-Z]{1,3}\d+\b")  # criterion, todo or requested item ID
REQUESTED = re.compile(r"\bR\d+\b")
# "R2 waitlist (owner-deferred: https://...)": the mark sits on its own item, before any other R-id
DEFERRED = re.compile(r"\b(R\d+)\b(?:(?!\bR\d+\b)[^()\n])*\((?i:owner-deferred):\s*"
                      r"(?:\[[^\]\n]*\]\(https?://[^\s)]+\)|https?://[^\s)]+)\)")  # bare URL or [text](URL)
BULLET = r"(?:(?:[-*+]|\d+[.)])[ \t]+(?:\[[ xX]\][ \t]+)?)?"  # '- ', '1. ', '- [x] ' or none
# every '**Hidden checks:**' block, blank lines included, up to the next label (bulleted or not) or heading
HIDDEN = re.compile(rf"\*\*Hidden checks:\*\*(.*?)(?=^[ \t]*{BULLET}\*\*[^*\n]+:\*\*|^#{{1,6}}\s|\Z)", re.M | re.S)
# one entry, nothing guessed: '#2 A1: PASS' or '#2 A1: FAIL', an optional '(note)' only after the verdict
ENTRY = r"#(\d+)[ \t]+([A-Z]{1,3}\d+):[ \t]*(PASS|FAIL)(?:[ \t]+\([^()\n]*\))?"
ENTRIES = re.compile(rf"{BULLET}{ENTRY}(?:[ \t]*,[ \t]*{ENTRY})*[ \t]*")  # one line: entries, commas


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


# a size: POC, MVP or production as the first word; a small feature may give none (<why>) instead
SIZE = re.compile(r"[\s`*_]*(?:poc|mvp|production)(?![\w-])", re.I)
SMALL = re.compile(r"[\s`*_]*none\s*\(", re.I)
LAUNCH = re.compile(r"\b(?:mvp|production)\b", re.I)  # any mention of a launch size scans: fail closed
PLACEHOLDER = re.compile(r"\W*(?:(?:skip(?:ped)?|n/?a|todo|tbd)\b.*|none\W*)?", re.I)  # whole value, or a skip note


def run_size(sections):
    """The run's one Size value: the kickoff's, else the Tickets section's (Lucky runs have no kickoff)."""
    return marker(sections.get("kickoff", ""), "Size") or marker(sections.get("tickets", ""), "Size")


def size_problems(run, value):
    """Flagged runs: the Size value must be one the done-run scans can read. Guessing a size is the bug."""
    small = run.get("kind") == "feature"
    if not run.get("scans") or value is None or SIZE.match(value) or (small and SMALL.match(value)):
        return []
    named = "POC, MVP, production" + (" or 'none (<why>)'" if small else "")
    return [f"Size must start with {named}, not '{value[:40]}'"]


def check_kickoff(run, body, **_):
    sized = run["kind"] == "feature" and run.get("coverage")  # a feature's size, or 'none (<why>)' when small
    labels = ["Features", "Approach", "Answered by"] + (["Size", "Stack"] if run["kind"] == "product" else []) + (
        ["Size"] if sized else [])
    return missing_markers(body, labels) + size_problems(run, marker(body, "Size"))


def lucky_size(run, body):
    """A flagged Lucky product or feature run has no kickoff: its size sits in Tickets."""
    if not run.get("scans") or run.get("mode") != "lucky" or run.get("kind") == "change":
        return []
    return missing_markers(body, ["Size"]) + size_problems(run, marker(body, "Size"))


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
    problems += missing_markers(body, ["Backlog"]) + lucky_size(run, body)
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


def online(run, kwargs, check, finish=False):
    """Run one ticket check on every listed ticket, unless the run predates ticket checks or the step is offline.
    `finish` (done-run, handoff): an epic (a change: its ticket) whose integration todos are all another run's is
    marked `later` with this run's todo IDs (pinned at `done plan`, plus the current plan), the only items of it
    this run owes."""
    if not run.get("ticket_checks"):
        return []
    epic, subs = ticket_urls(kwargs["all_sections"].get("tickets", ""))
    if kwargs.get("offline"):
        return readable(run, run.get("tickets", []) + epic + subs)
    if finish and epic:
        own = set(run.get("todos", [])) | {f"T{n}" for n in todo_ids(kwargs["all_sections"])}
        whole = check
        check = lambda ticket: whole({**ticket, "later": own} if ticket["url"] == epic[0] and handed(ticket, own)
                                     else ticket)
    return ticket_problems(run.get("tickets", []) + epic + subs, check)  # tickets pinned at `done tickets` stay checked


def item_todos(item):
    """Every todo ID a checklist item names outside `needs` references, ranges expanded; reading more never owes
    less, so decoration and lists ('🤝 **T63**', 'T63 / T64', 'T63 to T65') fail closed."""
    text = NEEDS.sub("", item)
    spans = {f"T{n}" for a, b in TODO_RANGE.findall(text) for n in range(int(a), min(int(b), int(a) + 50) + 1)}
    return set(re.findall(r"\bT\d+\b", text)) | spans


def handed(ticket, own):
    """True when the ticket's checklist holds integration todos (items naming any of its criterion IDs; `needs`
    and '#4 A1' references to other tickets do not count) and none is one of this run's todos `own`. Fails closed:
    an item naming its criteria without naming a todo ID keeps the ticket owed whole."""
    criteria = set(CRITERION.findall(under(ticket["body"], DEFINITION)))
    number = (ISSUE.match(ticket.get("url", "")) or [None, None, None])[2]
    todos = set()
    for item in TASK.finditer(checklist(ticket["body"])):
        text = OTHERS.sub(lambda ref: ref.group(0) if ref.group(1) == number else "", NEEDS.sub("", item.group(0)))
        if criteria & set(ID.findall(text)):
            ids = item_todos(item.group(0))
            if not ids:
                return False
            todos |= ids
    return bool(todos) and not todos & own


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
    """Handoff: a listed ticket is finished (every item ticked) unless Blocked, cancelled or deferred to Backlog.
    An epic other runs finish later (`later`) owes only the items that are this run's todos ('- [ ] T75 ...')."""
    if ticket["stopped"] or ticket["backlog"]:
        return None
    marks = TASK.findall(checklist(ticket["body"]))
    if not marks:
        return needs_checklist(ticket)
    own = ticket.get("later")
    left = marks.count(" ") if own is None else sum(
        1 for item in TASK.finditer(checklist(ticket["body"]))
        if item.group(1) == " " and item_todos(item.group(0)) & own)
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
    if run.get("outcomes"):  # the owner's dashboard shows each todo's result
        problems += [f"T{n} needs its own line with its result: 'T{n} <title> → <what the owner can do once it is "
                     f"done> (#<ticket>, <criteria>)'" for n in without_result(kwargs["all_sections"])]
    labels = ["Success"] if light(run) else ["Logging", "Efficiency"]
    return problems + missing_markers(body, labels) or held(run, kwargs, covered(run, needs_checklist))


def held(run, kwargs, check, finish=False):
    """`check` on every listed ticket; on coverage runs also: each plan todo is an item there and each
    requested item is still named by a criterion (no drift after the tickets step)."""
    lists, named = [], []  # each listed ticket's items and labelled requested items, kept from its one read

    def read(ticket):
        lists.append(items(ticket["body"]))
        named.extend(labelled(ticket["body"]))
        return check(ticket)
    problems = online(run, kwargs, read, finish)
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
RULE_ID = r"(?-i:U(?:10|[1-9]))"  # the ten rule IDs, capitals only in every pattern: test user "u1" is no rule
# "- U3 PASS 04, 13: ...", "- **U3:** FAIL ...", "| U3 | Hierarchy | PASS | ... |": a rule ID, its area name or
# none, the verdict, its text. Only a known area name may sit between, so "U3 FAIL a, PASS b" stays a FAIL.
LEAD, SEP = r"[ \t]*(?:\|[ \t]*)?(?:(?:[-*+]|\d+[.)])[ \t]+)?(?:\[[ xX]\][ \t]+)?[*`]*", r"[*` \t:|.,()-]*"
VERDICT = re.compile(rf"{LEAD}({RULE_ID})\b{SEP}(?:(?:{'|'.join(UX_AREAS)}){SEP})?(PASS|FAIL|UNKNOWN|N/A)\b(.*)",
                     re.I)
JUDGE = re.compile(r"[ \t]*(?:\|[ \t]*)?(?:(?:[-*+]|\d+[.)])[ \t]*)?(?:\[[ xX]\][ \t]*)?[*`]*\*\*UX judge:\*\*",
                   re.I)  # as LEAD, but no space needed after the bullet or the checkbox
# A line under a verdict or the judge line belongs to it: indented text, or plain text that starts no bullet, table,
# heading, quote, rule line or the done-run's own markers. A blank line ends it.
DONE_MARKS = ("Logs", "UX judge", "Secrets", "Dependencies", "Static", "Hidden checks")  # done-run labels
MARK = rf"\*\*(?:{'|'.join(DONE_MARKS)}):\*\*"
CONTINUES = re.compile(rf"(?:[ \t]+(?![ \t])(?!(?:[-*+]|\d+[.)])?[ \t]*(?:[*`]*{RULE_ID}\b|{MARK}))"
                       rf"|(?!(?:[-*+]|\d+[.)])[ \t]|[|#>]|{MARK}|[*`]*{RULE_ID}\b))\S", re.I)
FAILED = re.compile(r"\bFAIL(?:S|ED)?\b")  # capitals only: "failed booking with retry" is evidence, not a verdict
# views and styles, not tests or stories; mixed-code languages use --ui
UI_FILE = re.compile(r"(?<!\.test)(?<!\.spec)(?<!\.stories)\.(?:tsx|jsx|vue|svelte|astro|html?|css|scss|sass|less|"
                     r"razor|cshtml|erb|hbs|ejs|pug|liquid|twig|njk|jinja2?|j2|mustache|haml|slim|xaml|axaml|"
                     r"storyboard|xib|qml|fxml|uxml|uss|tscn)$|\.blade\.php$", re.I)
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
    """Each plan todo has its own 'pre: do: post:' line (fast_progress.built_ids)."""
    built = built_ids(body, strict=bool(run.get("coverage")))
    return [f"T{number} needs its own 'T{number} pre: ... do: ... post: ...' line"
            for number in todo_ids(kwargs["all_sections"]) if number not in built]


def scans(run, all_sections):
    """Scan markers a flagged run sized MVP or production records in its done-run (product-bar.md#security)."""
    sizes = f"{run.get('size') or ''} {run_size(all_sections) or ''}"  # the frozen size and the record's
    return ["Secrets", "Dependencies", "Static"] if run.get("scans") and LAUNCH.search(sizes) else []


def scan_cause(run, all_sections):
    """Why the scans are required, so a run whose record was edited later understands the refusal."""
    frozen = LAUNCH.search(run.get("size") or "")
    found = frozen or LAUNCH.search(run_size(all_sections) or "")
    where = ("frozen at " + run["size_at"] if run.get("size_at") else "frozen in the ledger") if frozen else "in the record"
    return f"Size {found.group(0).upper()}, {where}"


def placeholder_problems(body, labels):
    """A scan marker names the tool, the command and the result; a placeholder records nothing."""
    values = {label: marker(body, label) for label in labels}
    return [f"'**{label}:**' needs the tool, the command and the result, not '{value[:20]}'"
            for label, value in values.items() if value and PLACEHOLDER.fullmatch(value)]


def check_done_run(run, body, project, **kwargs):
    sections = kwargs.get("all_sections") or {}
    own = HIDDEN.sub("", body) if hidden(run) else body  # the builder's own done-run, apart from the checker's
    touched = touched_ui(run, project)
    audited = run.get("ux_rules") and (run.get("ui") or touched)  # this run owes the UX audit
    parsed = audit_lines(own) if audited else None
    used = parsed[2] if parsed else own  # rule and judge lines never stand in for using it
    problems = [] if re.search(r"\bPASS\b", used) else ["needs >=1 PASS result"]
    labels = scans(run, sections)
    cause = f" ({scan_cause(run, sections)})" if labels else ""
    problems += missing_markers(body, ["Logs"]) + [problem + cause for problem in missing_markers(body, labels)]
    problems += placeholder_problems(body, labels)
    problems += size_problems(run, run.get("size") or run_size(sections))
    if run.get("ui") or touched:
        shots = [Path(shot) for shot in re.findall(r"[\w./\\:~-]+\.(?:png|jpe?g|webp|gif)\b", body, re.I)]
        missing = [] if any((shot if shot.is_absolute() else Path(project) / shot).is_file() for shot in shots) else [
            "needs >=1 existing screenshot path"]
        missing += ux_audit(own, parsed) if run.get("ux_rules") else []
        problems += ([f"this run changed UI files ({', '.join(touched[:3])}): record the UX audit"]
                     if missing and touched else []) + missing
    return problems + (hidden_checks(body, kwargs, run) if hidden(run) else [])

def hidden(run):
    """Product and feature runs whose methods define hidden checks; change runs and older runs never."""
    return bool(run.get("hidden_checks")) and run.get("kind") != "change"


def verdicts(body):
    """Hidden checks entries (issue number, criterion ID, passed) and the lines that are not entries."""
    entries, unreadable = [], []
    for line in "\n".join(HIDDEN.findall(body)).splitlines():
        if not line.strip():
            continue
        if not ENTRIES.fullmatch(line.strip()):
            unreadable.append(line.strip())
            continue
        found = re.findall(ENTRY, line)
        entries += [(number, cid, verdict == "PASS") for number, cid, verdict in found]
    return entries, unreadable


def hidden_checks(body, kwargs, run):
    """Unreadable entries and any FAIL refuse; online, every in-play listed ticket's criterion, the epic's
    included unless another run owes it (`handed`), needs its own '#<n> <ID>: PASS'; offline, >=1 entry."""
    entries, unreadable = verdicts(body)
    if unreadable:
        return [f"unreadable hidden-check entry: {line}" for line in unreadable] + [
            "write each as '#<n> <ID>: PASS' or '#<n> <ID>: FAIL', a note only after it in parentheses; "
            "the block ends at the next '**Label:**'"]
    failed = [f"#{number} {cid}" for number, cid, passed in entries if not passed]
    if failed:
        return [f"hidden checks FAIL ({', '.join(dict.fromkeys(failed))}): back to build, then the checker runs them again"]
    if not entries:
        return ["needs a '**Hidden checks:**' block from the checker: '#<n> <ID>: PASS' for every criterion"]
    gaps, passed = [], {(number, cid) for number, cid, _ in entries}

    def read(ticket):
        if not (ticket["stopped"] or ticket["backlog"] or "later" in ticket):
            number = ISSUE.match(ticket["url"]).group(2)
            criteria = dict.fromkeys(CRITERION.findall(under(ticket["body"], DEFINITION)))
            gaps.extend(f"#{number} {cid}" for cid in criteria if (number, cid) not in passed)
    problems = online(run, kwargs, read, finish=True)
    return problems or ([f"criteria without a hidden-check PASS: {', '.join(gaps)}"] if gaps else [])


def audit_lines(body):
    """One pass over a done-run: each rule's verdicts with the word characters of their text, the rules a FAIL is
    left about, and the lines about no rule and not the judge (only those can show the product was used). A contested
    FAIL is an UNKNOWN, which may quote its own rule's FAIL in or under its line; a FAIL about another rule counts."""
    # owner: (rule or "judge", verdict) the line belongs to; top: that owner's indent; gap: a blank line came before
    verdicts, failed, used, owner, gap, top = {}, set(), [], None, False, 0
    for line in body.splitlines():
        if not line.strip():
            gap = True  # as in Markdown, indented lines after a blank line still belong to the item above
            continue
        depth = len(line[:len(line) - len(line.lstrip(" \t"))].expandtabs(4))  # tabs and spaces measured alike
        head = VERDICT.match(line)
        quote = head and depth > top and owner == (head.group(1), "UNKNOWN")  # deeper than its UNKNOWN: a reason
        if head and not quote:
            owner, top = (head.group(1), head.group(2).upper()), depth
            verdicts.setdefault(owner[0], []).append([owner[1], len(re.sub(r"\W", "", head.group(3)))])
        elif JUDGE.match(line):
            owner, top = ("judge", ""), depth
        elif quote or owner and CONTINUES.match(line) and (line[0] in " \t" or not gap):
            if owner[0] in verdicts:
                verdicts[owner[0]][-1][1] += len(re.sub(r"\W", "", head.group(3) if quote else line))
        else:
            owner = None
        gap = False
        named = set(re.findall(rf"\b{RULE_ID}\b", line)) | ({owner[0]} if owner and owner[0] != "judge" else set())
        if owner and owner[1] == "FAIL":
            failed.add(owner[0])
        if FAILED.search(line):
            failed |= {rule for rule in named if owner != (rule, "UNKNOWN")}
        if not owner and not named:
            used.append(line)
    return verdicts, failed, "\n".join(used)


def ux_audit(body, parsed=None):
    """A fresh judge's verdict per rule ID (ux-quality step 4), each with evidence or a reason; no FAIL left."""
    verdicts, failed, _ = parsed or audit_lines(body)
    problems = [f"needs a '{rule} PASS|FAIL|UNKNOWN|N/A <screen>: <evidence or reason>' line"
                for rule in UX_RULES if rule not in verdicts]
    problems += [f"{rule} FAIL is open: fix it, recheck, then keep one final verdict line with no FAIL, FAILS or "
                 f"FAILED in or under it and no other line naming {rule} with them; or record UNKNOWN with both reasons"
                 for rule in sorted(failed, key=lambda rule: int(rule[1:]))]
    problems += [f"{rule} {verdict} needs its evidence or reason" for rule, found in verdicts.items()
                 if rule not in failed for verdict, words in found if words < 3]
    return problems + missing_markers(body, ["UX judge"])


def ui_start(project):
    """The start commit and the UI files already changed then, so the done-run counts only this run's own edits."""
    base = (git(project, "rev-parse", "--verify", "-q", "HEAD") or "").strip() or None
    return {"base": base, "ui_seen": {name: digest(Path(project) / name)
                                      for names in ui_listings({"base": base}, project) for name in names}}


def touched_ui(run, project):
    """UI files a run not started as UI changed, when its methods count them; [] otherwise."""
    return [] if run.get("ui") or not run.get("ux_rules") else ui_files(run, project)


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
    labels = ["Run", "Statuses", "Unverified", "Follow-ups"] + (["Dev sign-in"] if run.get("auth") else []) + (
        ["PR"] if run.get("pr_proof") else [])
    return missing_markers(body, labels) or held(run, kwargs, covered(run, needs_ticks), finish=True) + pr_proof(run, body, **kwargs)


def pr_proof(run, body, project=None, offline=None, **_):
    """Runs on current methods: the PR named on the '**PR:**' line shows Before & after per outcome (fast_proof.py)."""
    import subprocess
    if not run.get("pr_proof"):
        return []
    value = marker(body, "PR") or ""
    try:
        text = pr_body(value, project, offline)
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as error:
        return [str(error)]
    ui = bool(run.get("ui") or touched_ui(run, project))
    found = fast_proof.problems(text, ui) + (fast_proof.credit(text) if run.get("credit") else [])
    return [f"PR body: {problem}" for problem in found]


def pr_body(value, project, offline):
    """The PR body: read through gh, or offline from the body file named on the PR line."""
    if offline:
        named = re.search(r"\(body:[ \t]*([^)]+?)[ \t]*\)", value, re.I)  # paths may hold spaces
        try:
            return Path(project, named.group(1).strip("`'\" ")).read_text(encoding="utf-8", errors="replace")
        except (AttributeError, OSError) as error:  # no '(body: ...)', or the file is not readable
            raise ValueError("offline: name the PR body file on the PR line: '**PR:** <url> (body: <file>)'") from error
    url = PULL.search(value)
    if not url:
        raise ValueError("needs '**PR:** <GitHub PR URL>'; another host: pass --offline '<reason>' and name the "
                         "PR body file on that line")
    try:
        return gh("pr", "view", url.group(0), "--json", "body", "--jq", ".body")
    except RuntimeError as error:
        raise RuntimeError(f"cannot read {url.group(0)} with gh ({error}); fix access or pass --offline '<reason>' "
                           "and name the PR body file") from error


CHECKS = {"research": check_research, "kickoff": check_kickoff, "tickets": check_tickets,
          "analysis": check_analysis, "plan": check_plan, "design": check_design, "schema": check_schema,
          "build": check_build, "done-run": check_done_run, "handoff": check_handoff}
