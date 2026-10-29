"""The owner's mini dashboard: the run card, the todo-finished and NOW messages, and once-only claims.

Hooks load this only after fast_gate.py's file-time check shows a change. Stdlib only, no network.
Method: .agents/skills/safe-engine/references/fast-run.md#progress.
"""
import os
import sys
import zlib
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

HERE = str(Path(__file__).resolve().parent)
if HERE not in sys.path:
    sys.path.insert(0, HERE)  # loaded by file path (tests): find the sibling module
import fast_progress as facts  # noqa: E402 - record facts

ICONS = {"research": "🔎", "kickoff": "❓", "tickets": "🎫", "analysis": "🧠", "plan": "🗺️", "design": "🎨",
         "schema": "🗄️", "build": "🔨", "show": "🖼️", "done-run": "🧪", "handoff": "📦"}
SHOWN_DONE = 6  # finished-todo lines per message; the rest are counted


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


def bar(done, total, width=10):
    """'▰▰▱' with at most width cells."""
    cells = min(total, width)
    filled = int(cells * done / total + 0.5) if total else 0  # half up: 2.5 cells shows 3
    return "▰" * filled + "▱" * (cells - filled)


def view(run, all_sections):
    """The dashboard's facts, read once: todos, built (log order), NOW, the rest, ticket titles, focus ticket."""
    ids, items, tickets = facts.todo_ids(all_sections), facts.todo_items(all_sections), facts.ticket_titles(all_sections)
    known = set(ids)
    built = [n for n in facts.built_ids(all_sections.get("build log", ""), bool(run.get("coverage"))) if n in known]
    done = set(built)
    now = [n for n in facts.now_ids(all_sections) if n in known and n not in done]
    busy = set(now)
    sole = next(iter(tickets)) if len(tickets) == 1 else None  # a change run's one ticket owns every todo
    v = SimpleNamespace(ids=ids, items=items, tickets=tickets, built=built, done=done, now=now,
                        later=[n for n in ids if n not in done and n not in busy], sole=sole)
    first = (now or v.later or built[-1:] or [None])[0]
    v.focus = ticket_of(v, first) if first else None
    return v


def item(v, n):
    """Todo n's (title, result, ticket); empty for a todo the plan only mentions."""
    return v.items.get(n) or ("", "", None)


def ticket_of(v, n):
    """The ticket todo n belongs to: its own reference, else the run's one ticket."""
    return item(v, n)[2] or v.sole


def title(v, n):
    """Todo n's title in plain words, else its ID."""
    return item(v, n)[0] or f"T{n}"


def result(v, n):
    """What the owner can do once todo n is done; '' when the plan does not say."""
    return item(v, n)[1]


def ticket_line(v):
    """'🎫 #12 Download & SEO   ▰▰▱ 2/3 · run 7/9' for the ticket being worked on."""
    total = f"{len(v.built)}/{len(v.ids)}"
    if not v.focus:
        return f"🧩 todos   {bar(len(v.built), len(v.ids))} {total}"
    mine = [n for n in v.ids if ticket_of(v, n) == v.focus]
    done = sum(n in v.done for n in mine)
    whole = f" · run {total}" if len(mine) < len(v.ids) else ""
    return f"🎫 #{v.focus} {v.tickets.get(v.focus, '')}".rstrip() + f"   {bar(done, len(mine))} {done}/{len(mine)}{whole}"


def now_lines(v, paused=False):
    """What is being built now and what the owner gets from it, else what comes next."""
    if not v.now:
        return [f"⏭️ NEXT {title(v, v.later[0])}"] if v.later else []
    more = f" · +{len(v.now) - 1} in parallel" if len(v.now) > 1 else ""
    if paused:
        return [f"🔨 ON HOLD until you answer: {title(v, v.now[0])}{more}"]
    gets = result(v, v.now[0])
    return [f"🔨 NOW  {title(v, v.now[0])}{more}"] + ([f"     → {gets}"] if gets else [])


def work_lines(v, paused):
    """Ticket bar, the last finished todos, NOW and NEXT."""
    recent = [n for n in v.built if ticket_of(v, n) == v.focus][-2:] or v.built[-2:]
    lines = [ticket_line(v)] + [f"✅ {title(v, n)}" for n in recent] + now_lines(v, paused)
    following = v.later[:1] if v.now else []  # without NOW, now_lines already named the next todo
    return lines + [f"⏭️ NEXT {title(v, n)}" for n in following]


def steps_line(steps, done, current, created):
    """Done, current and left steps; once all are done, each step's duration."""
    if current is None:
        starts = [created] + [done[step].get("at") for step in steps]
        return "⏱️ " + " · ".join(f"{step} {span(starts[i], starts[i + 1])}".strip() for i, step in enumerate(steps))
    left = steps[steps.index(current) + 1:]
    parts = [f"✅ {' · '.join(s for s in steps if s in done)}" if steps.index(current) else "",
             f"{ICONS.get(current, '▶️')} {current}", f"⬜ {' · '.join(left)}" if left else ""]
    return "   ".join(part for part in parts if part)


def card(run, steps, all_sections, now, v=None, left=False, current=False):
    """The owner's mini dashboard: the question first when paused, the run line, then the work or the steps.
    left: mid-build, also the steps line, so the steps still to come stay named (status output)."""
    if run.get("owner_report"):
        import fast_report
        paused = run.get("paused")
        state = ([f"⏸️ WAITING ON YOU: {paused.get('reason')}"] if paused else [])
        if run.get("abandoned"):
            state.append("🏁 abandoned")
        elif run.get("closed"):
            state.append("🏁 closed")
        return "\n".join(state + ["Last published report:",
                                  fast_report.markdown(run["owner_report"], run.get("project"), bool(state) or current)])
    v = v or view(run, all_sections)
    done, created = run.get("done") or {}, run.get("created")
    current = next((step for step in steps if step not in done), None)
    head = [f"🏭 {run.get('key')!r}"]
    if current:
        began = max([entry.get("at") or "" for entry in done.values()] + [created or ""])
        head += [f"{ICONS.get(current, '▶️')} {current} · step {steps.index(current) + 1}/{len(steps)}",
                 f"⏱️ {span(created, now)} total, {span(began, now)} in step"]
    else:
        head.append(f"⏱️ {span(created, now)} total")
    head.append("🏁 abandoned" if run.get("abandoned") else "🏁 closed" if run.get("closed") else "")
    paused = run.get("paused")
    lines = ([f"⏸️ WAITING ON YOU: {paused.get('reason')}"] if paused else []) + [" · ".join(p for p in head if p)]
    if run.get("design_port"):
        import fast_design
        lines.append(fast_design.report(run))
    building = current in steps[steps.index("build"):] if "build" in steps else False
    if building and v.ids and (v.now or v.later):
        tail = [steps_line(steps, done, current, created)] if left else []
        return "\n".join(lines + work_lines(v, bool(paused)) + tail)
    if building and v.ids:
        lines.append(f"✅ all {len(v.ids)} todos built")
    return "\n".join(lines + [steps_line(steps, done, current, created)])


def claim(path):
    """True for the first caller only (atomic create), so parallel hooks show each message once. Names are short,
    so any other OSError is a real fault: it propagates, the gate logs it and the next hook retries."""
    try:
        os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        return True
    except FileExistsError:
        return False


def news(run, steps, record, shown, ledger_ns, now):
    """Lines the owner has not seen: each newly finished todo with what it gives, then the card after a ledger
    change, else the new NOW and the ticket bar. shown is this run's claims folder; each message is claimed once."""
    shown.mkdir(parents=True, exist_ok=True)
    all_sections = facts.read(record)
    v, taken = view(run, all_sections), set(os.listdir(shown))  # one listing; claims only for what is unseen
    fresh = [n for n in v.built if f"todo-{n}" not in taken and claim(shown / f"todo-{n}")]
    now_key = f"now-{zlib.crc32(' '.join(v.now).encode()):08x}"  # short and stable, however long the Now list
    show_now = bool(v.now) and now_key not in taken and claim(shown / now_key)
    show_card = f"card-{ledger_ns}" not in taken and claim(shown / f"card-{ledger_ns}")
    lines = [f"✅ {title(v, n)} done" + (f" → {result(v, n)}" if result(v, n) else "") for n in fresh[:SHOWN_DONE]]
    lines += [f"✅ +{len(fresh) - SHOWN_DONE} more done"] if len(fresh) > SHOWN_DONE else []
    if show_card:
        return lines + [card(run, steps, all_sections, now, v)]
    if (fresh or show_now) and v.ids:
        return lines + now_lines(v, bool(run.get("paused"))) + [ticket_line(v)]
    return lines
