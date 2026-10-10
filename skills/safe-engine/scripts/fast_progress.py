"""Run progress for the owner: work record parsing shared with the step checks, the run card and tick lines.

Hooks load this only after fast_gate.py's file-time check shows a change. Stdlib only, no network.
Method: .agents/skills/safe-engine/references/fast-run.md#progress.
"""
import os
import re
from datetime import datetime

TAGS = ("pre:", "do:", "post:")
LEAD = r"\s*(?:\|\s*)?(?:(?:[-*+]|\d+[.)])\s+)?(?:\[[ x]\]\s+)?[*`]*"  # bullet, number, [x], **, ` or a table cell
OWN = re.compile(LEAD + r"t(\d+)\b")  # a lowercased line that starts with its todo ID
TITLE = re.compile(LEAD + r"t(\d+)\b[\s:.)*`|-]*(.*?)[\s|*]*$", re.I)
MENTION = re.compile(r"\bt(\d+)\b")
SHOWN_TICKS = 6  # tick lines per message; the rest are counted


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


def todos(all_sections):
    return subsection(all_sections.get("plan", ""), "Todos") or ""


def todo_ids(all_sections):
    """Every todo ID the plan's Todos subsection names, in number order."""
    return sorted(set(re.findall(r"\bT(\d+)\b", todos(all_sections))), key=int)


def built_ids(build_log, strict):
    """Todo numbers with a 'pre: do: post:' line, in one pass. strict (coverage runs): the line starts with its
    ID, so a mention such as 'T23..T34' in another todo's line never counts."""
    found = set()
    for line in build_log.lower().splitlines():
        if not all(tag in line for tag in TAGS):
            continue
        if strict:
            own = OWN.match(line)
            if own:
                found.add(own.group(1))
        else:
            found.update(MENTION.findall(line))
    return found


def titles(all_sections):
    """Todo number -> short title, from the Todos lines that start with the ID."""
    found = {}
    for line in todos(all_sections).splitlines():
        match = TITLE.match(line)
        if match:
            found.setdefault(match.group(1), match.group(2)[:48].strip())
    return found


def read(record):
    """The work record's sections, or {} when it cannot be read."""
    try:
        return sections(record.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {}


def span(start, end):
    """'40s', '14m', '1h02m' or '2d3h' from one ISO time to another; '' when either is missing or invalid."""
    try:
        seconds = max(0, int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()))
    except (TypeError, ValueError):
        return ""
    hours = seconds // 3600
    if hours >= 24:
        return f"{hours // 24}d{hours % 24}h"
    if hours:
        return f"{hours}h{seconds // 60 % 60:02d}m"
    return f"{seconds // 60}m" if seconds >= 60 else f"{seconds}s"


def progress(run, all_sections):
    """(todo IDs, built IDs among them), counted exactly like the build check."""
    ids = todo_ids(all_sections)
    return ids, built_ids(all_sections.get("build log", ""), bool(run.get("coverage"))) & set(ids)


def todo_line(ids, built):
    left = [f"T{n}" for n in ids if n not in built]
    rest = f" +{len(left) - 3}" if len(left) > 3 else ""
    return f"todos {len(built)}/{len(ids)} · " + (f"open: {' '.join(left[:3])}{rest}" if left else "all built")


def steps_line(steps, done, current, created):
    """Done, current and left steps; once all are done, each step's duration."""
    if current is None:
        starts = [created] + [done[step].get("at") for step in steps]
        return "⏱️ " + " · ".join(f"{step} {span(starts[i], starts[i + 1])}".strip() for i, step in enumerate(steps))
    left = steps[steps.index(current) + 1:]
    parts = [f"✅ {' · '.join(s for s in steps if s in done)}" if steps.index(current) else "", f"▶️ {current}",
             f"⬜ {' · '.join(left)}" if left else ""]
    return "   ".join(part for part in parts if part)


def card(run, steps, all_sections, now, counted=None):
    """The owner's run card: where the run is, todo progress and what waits on the owner. 2 to 4 short lines.
    counted: progress() already computed by the caller."""
    done, created = run.get("done") or {}, run.get("created")
    current = next((step for step in steps if step not in done), None)
    head = [f"🏭 {run.get('mode')} {run.get('kind')} '{run.get('key')}'"]
    if current:
        began = max([entry.get("at") or "" for entry in done.values()] + [created or ""])
        head += [f"step {steps.index(current) + 1}/{len(steps)} {current}", f"{span(began, now)} in step"]
    head += [f"{span(created, now)} total", "abandoned" if run.get("abandoned") else "closed" if run.get("closed") else ""]
    lines = [" · ".join(part for part in head if part), steps_line(steps, done, current, created)]
    ids, built = counted or progress(run, all_sections)
    tickets = run.get("tickets") or []
    extra = [todo_line(ids, built)] if ids else []
    extra += [tickets[0] + (f" +{len(tickets) - 1}" if len(tickets) > 1 else "")] if tickets else []
    lines += [("☑️ " if ids else "🎫 ") + " · ".join(extra)] if extra else []
    paused = run.get("paused")
    return "\n".join(([f"⏸️ waiting on you: {paused.get('reason')}"] if paused else []) + lines)


def claim(path):
    """True for the first caller only (atomic create), so parallel hooks show each message once."""
    try:
        os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        return True
    except FileExistsError:
        return False


def news(run, steps, record, shown, ledger_ns, now):
    """Lines the owner has not seen: a tick per newly built todo, then the card after a ledger change
    (ledger_ns names it). Claims live in shown/."""
    shown.mkdir(exist_ok=True)
    all_sections = read(record)
    ids, built = progress(run, all_sections)
    taken = set(os.listdir(shown))  # one listing; claims only for unseen todos
    fresh = [n for n in ids if n in built and f"todo-{n}" not in taken and claim(shown / f"todo-{n}")]
    show_card = f"card-{ledger_ns}" not in taken and claim(shown / f"card-{ledger_ns}")
    names = titles(all_sections) if fresh else {}
    lines = [f"☑️ T{n} {names.get(n, '')}".rstrip() for n in fresh[:SHOWN_TICKS]]
    lines += [f"☑️ +{len(fresh) - SHOWN_TICKS} more"] if len(fresh) > SHOWN_TICKS else []
    if lines and not show_card:
        lines[-1] += " · " + todo_line(ids, built)
    lines += [card(run, steps, all_sections, now, (ids, built))] if show_card else []
    return lines
