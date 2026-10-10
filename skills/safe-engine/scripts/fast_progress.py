"""Work record facts shared by the step checks (fast_record.py) and the owner's dashboard (fast_card.py).

Pure parsing, stdlib only. Formats: .agents/skills/safe-engine/references/fast-run.md#work-record.
"""
import re

TAGS = ("pre:", "do:", "post:")
LEAD = r"\s*(?:\|\s*)?(?:(?:[-*+]|\d+[.)])\s+)?(?:\[[ x]\]\s+)?[*`]*"  # bullet, number, [x], **, ` or a table cell
OWN = re.compile(LEAD + r"t(\d+)\b")  # a lowercased line that starts with its todo ID
TODO_LINE = re.compile(r"^(?:[ \t]*#{1,6}[ \t]+)?" + LEAD.replace(r"\s", r"[ \t]") + r"t(\d+)\b[ \t:.)*`|-]*(.*)$",
                       re.M | re.I)  # ID and the rest of a todo line; a '#### T1' heading counts too
# "(#12, A2, deep)" closing a todo line (fullmatch): tickets, criteria or requested items, and the model tier
REFS = re.compile(r"\(((?:[ \t,]*(?:#\d+|[A-Za-z]{1,3}\d+|light|standard|deep))+)[ \t]*\)", re.I)
MENTION = re.compile(r"\bt(\d+)\b")
TICKET_NUMBER = re.compile(r"#(\d+)")
NEXT_H3 = re.compile(r"^###\s", re.M)
NOW = re.compile(r"\*\*Now:\*\*([^\n]*)", re.I)
TICKET_LINE = re.compile(r"\*\*(?:Epic|Ticket|Sub-issue):\*\*[ \t]*(\S+)[ \t]*([^\n]*)", re.I)


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
    """The text under the first '### ...<title>...' heading, up to the next one; None when absent. Two searches,
    linear in the body."""
    head = re.search(r"^###\s+[^\n]*" + re.escape(title) + r"[^\n]*\n", body, re.M | re.I)
    if not head:
        return None
    end = NEXT_H3.search(body, head.end())
    return body[head.end():end.start() if end else len(body)]


def todos(all_sections):
    """The plan's Todos subsection text: the one source of todo IDs, titles and results."""
    return subsection(all_sections.get("plan", ""), "Todos") or ""


def todo_ids(all_sections):
    """Every todo ID the plan's Todos subsection names, in number order."""
    return sorted(set(re.findall(r"\bT(\d+)\b", todos(all_sections))), key=int)


def built_ids(build_log, strict):
    """Todo numbers with a 'pre: do: post:' line, in log order (a dict used as an ordered set). strict (coverage
    runs): the line starts with its ID, so a mention such as 'T23..T34' in another todo's line never counts."""
    found = {}
    for line in build_log.lower().splitlines():
        if not all(tag in line for tag in TAGS):
            continue
        if strict:
            own = OWN.match(line)
            if own:
                found[own.group(1)] = None
        else:
            found.update(dict.fromkeys(MENTION.findall(line)))
    return found


def short(text, limit=48):
    """text cut at a word, with an ellipsis, when longer than limit."""
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def todo_items(all_sections):
    """Todo number -> (title, result, ticket number or None), in plan order, from the Todos lines that start with
    the ID: 'T4 Download button → click it and the PDF saves (#12, A2)'. A leading tag such as '(light)' drops."""
    found = {}
    for match in TODO_LINE.finditer(todos(all_sections)):  # one linear pass; string operations per line
        number, text = match.group(1), match.group(2).rstrip(" \t|*")
        if number in found and found[number][1]:
            continue  # a line with a result wins over an earlier mention such as 'T1 and T2 run first'
        if text.startswith("(") and ")" in text:
            text = text[text.find(")") + 1:].lstrip()
        cut = text.rfind("(")
        refs = REFS.fullmatch(text, cut) if cut >= 0 and text.endswith(")") else None
        ticket = TICKET_NUMBER.search(refs.group(1)) if refs else None
        name, gets = split_result(text[:cut] if refs else text)
        found[number] = (short(name), short(gets, 60), ticket.group(1) if ticket else None)
    return found


def split_result(text):
    """'Download button → click it' (or '->') into title and result; no arrow: no result."""
    for mark in ("→", "->"):
        at = text.find(mark)
        if at >= 0:
            return text[:at], text[at + len(mark):]
    return text, ""


def without_result(all_sections):
    """Plan todo IDs whose own line names no '→ result', or that have no line of their own."""
    items = todo_items(all_sections)
    return [n for n in todo_ids(all_sections) if not (items.get(n) or ("", "", None))[1]]


def ticket_titles(all_sections):
    """Ticket number -> short title, from Tickets lines such as '**Sub-issue:** <url> Download & SEO'."""
    found = {}
    for url, rest in TICKET_LINE.findall(all_sections.get("tickets", "")):
        number, title = re.search(r"(\d+)\D*$", url), rest.strip(" :()-")
        if number and title:
            found.setdefault(number.group(1), short(title, 40))
    return found


def now_ids(all_sections):
    """The todo IDs the Build log's last '**Now:**' line names: the todos in progress."""
    marks = NOW.findall(all_sections.get("build log", ""))
    return re.findall(r"\bT(\d+)\b", marks[-1]) if marks else []


def read(record):
    """The work record's sections, or {} when it cannot be read."""
    try:
        return sections(record.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {}
