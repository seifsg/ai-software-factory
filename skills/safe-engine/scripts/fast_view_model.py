"""Optional owner-facing facts; missing evidence stays unknown, never estimated."""
import json
import re
from datetime import datetime
from urllib.parse import urlsplit

import fast_card as card
import fast_progress as facts


def lines(body, label):
    """Read exact metadata labels without interpreting ordinary prose."""
    return re.findall(r"^\*\*" + re.escape(label) + r":\*\*[ \t]*(.*)$", body, re.M)


def text(value, required=False, limit=500):
    """Reject malformed or oversized presentation text at its boundary."""
    if not isinstance(value, str) or len(value) > limit or "\n" in value:
        raise ValueError
    value = value.strip()
    if required and not value:
        raise ValueError
    return value


def object_line(raw):
    """One bounded JSON object, so accidental record content is never displayed as metadata."""
    if len(raw) > 100000:
        raise ValueError
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError
    return value


def goal(raw):
    """Only a declared milestone list supplies a goal denominator."""
    item = object_line(raw) if raw.startswith(("{", "[")) else {"title": raw}
    title = text(item.get("title"), True)
    identity = text(item["id"], True, 200) if "id" in item else None
    milestones, seen = item.get("milestones", []), set()
    if not isinstance(milestones, list):
        raise ValueError
    normalized = []
    for row in milestones:
        if not isinstance(row, dict) or type(row.get("done")) is not bool:
            raise ValueError
        key = text(row.get("id"), True, 200)
        if key in seen:
            raise ValueError
        seen.add(key)
        normalized.append({"id": key, "title": text(row.get("title"), True), "done": row["done"]})
    done, total = sum(row["done"] for row in normalized), len(normalized)
    return {"id": identity, "title": title, "milestones": normalized, "done": done, "total": total,
            "pct": round(100 * done / total) if total else None,
            "basis": "recorded-milestones" if total else "title-only"}


def next_test(raw):
    """An explicit next test, with optional expectation and feedback instructions."""
    item = object_line(raw)
    return {key: text(item.get(key, ""), key == "title") for key in ("title", "when", "estimate", "feedback")}


def timestamp(value):
    """Require an ISO timestamp with an offset; local times would imply false freshness."""
    parsed = datetime.fromisoformat(text(value, True, 80).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError
    return int(parsed.timestamp() * 1000)


def session(raw):
    """A coordinator report describes observed work, never process liveness."""
    item = object_line(raw)
    status = item.get("status")
    if status not in ("working", "finished", "blocked"):
        raise ValueError
    key = text(item.get("id"), True, 200)
    parent = text(item["parent"], True, 200) if item.get("parent") is not None else None
    if key == parent:
        raise ValueError
    return {"id": key, "title": text(item.get("title"), True), "task": text(item.get("task"), True),
            "status": status, "parent": parent, "updated": timestamp(item.get("updated")), "source": "record"}


def metadata(sections):
    """Last report wins; invalid reports become safe diagnostics instead of fabricated facts."""
    result = {"goal": None, "nextTest": None, "subsessions": [], "metadataErrors": []}
    errors = result["metadataErrors"]
    for label, key, parse in (("Goal", "goal", goal), ("Next test", "nextTest", next_test)):
        values = lines(sections.get("plan", ""), label)
        if values:
            try:
                result[key] = parse(values[-1].strip())
            except (ValueError, TypeError, OverflowError, RecursionError):
                errors.append(f"{label} report is invalid. Check its work-record format.")
    children = {}
    for raw in lines(sections.get("build log", ""), "Session"):
        try:
            row = session(raw.strip())
            children[row["id"]] = row
        except (ValueError, TypeError, OverflowError, RecursionError):
            message = "A session report is invalid. Check its work-record format."
            if message not in errors:
                errors.append(message)
    result["subsessions"] = list(children.values())
    return result


def subsessions(recorded, agents, observed):
    """Explicit reports override matching host IDs; retain every other reported child."""
    found = {row["id"]: row for row in recorded}
    for row in agents:
        if not isinstance(row, dict):
            continue
        key = str(row.get("id") or "")
        if not key or key in found:
            continue
        status = row.get("status")
        status = status if status in ("working", "finished", "blocked") else "unknown"
        found[key] = {"id": key, "title": str(row.get("desc") or "Reported subsession"),
                      "task": str(row.get("desc") or ""), "status": status, "parent": None,
                      "updated": observed, "source": "host"}
    return list(found.values())


def tickets(sections, view):
    """All referenced tickets with local task progress, never claimed tracker status."""
    rows, counts = {}, {}
    for url, rest in facts.TICKET_LINE.findall(sections.get("tickets", "")):
        try:
            parsed = urlsplit(url)
        except ValueError:
            continue
        match = re.search(r"(\d+)\D*$", parsed.path)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or not match:
            continue
        number = match.group(1)
        if url not in rows:
            rows[url] = {"id": url, "number": number, "title": rest.strip(" :()-"), "url": url}
            counts[number] = counts.get(number, 0) + 1
    assigned = {}
    for number in view.ids:
        assigned.setdefault(card.ticket_of(view, number), []).append(number)
    for row in rows.values():
        # Numeric references are ambiguous across trackers: do not assign work to either ticket.
        own = assigned.get(row["number"], []) if counts[row["number"]] == 1 else []
        done, total = sum(n in view.done for n in own), len(own)
        row.update(done=done, total=total, pct=round(100 * done / total) if total else None,
                   state="finished" if total and done == total else "working" if any(n in view.now for n in own)
                   else "next" if total else "unknown", tasks=[f"T{n}" for n in own], basis="local-tasks")
    return list(rows.values())
