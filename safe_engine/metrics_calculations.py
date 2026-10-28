"""Pure duration and report calculations for local run metrics."""

from datetime import datetime


def stamp(value):
    """Convert an explicit UTC/offset timestamp to seconds for wall alignment."""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.timestamp() if parsed.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


def utc_delta_seconds(start, end):
    a, b = stamp(start), stamp(end)
    return b - a if a is not None and b is not None and b >= a else None


def duration_seconds(start, end):
    """Use monotonic stamps only inside one known process, else UTC."""
    a, b = start.get("mono_ns"), end.get("mono_ns")
    same_process = start.get("pid") == end.get("pid") or not (start.get("pid") and end.get("pid"))
    if same_process and isinstance(a, int) and isinstance(b, int) and b >= a:
        return (b - a) / 1e9
    return utc_delta_seconds(start.get("t"), end.get("t"))


def wall_interval(start, end):
    a, b = stamp(start.get("t")), stamp(end.get("t"))
    return (a, b) if a is not None and b is not None and b >= a else None


def record_activity(spans, key, event, action, gaps, label):
    """Accumulate only observed active task/phase segments across resume."""
    span = spans.setdefault(key, {"start": None, "end": None, "duration_seconds": None, "segments": []})
    if action == "declare":
        return span
    if action in ("start", "resume"):
        if span.get("_active"):
            if action == "resume":
                gaps.append({"gap": f"{label}_interrupted_segment_unknown", "detail": str(key), "t": event.get("t")})
                span["_unknown"] = True
                span["duration_seconds"] = None
                span.pop("_active")
            else:
                gaps.append({"gap": f"{label}_duplicate_start", "detail": str(key), "t": event.get("t")})
        if not span.get("_active"):
            span["_active"] = event
            span["start"] = span["start"] or event.get("t")
            span["start_mono"] = span.get("start_mono") or event.get("mono_ns")
            span["end"] = None
            if not span.get("_unknown") and span["duration_seconds"] is None:
                span["duration_seconds"] = 0.0
            if action == "resume":
                span["resumed"] = True
        return span
    if action not in ("finish", "fail", "cancel"):
        return span
    start = span.pop("_active", None)
    if start:
        seconds = duration_seconds(start, event)
        if seconds is not None:
            if not span.get("_unknown"):
                span["duration_seconds"] = round((span["duration_seconds"] or 0) + seconds, 3)
            span["segments"].append({"start": start.get("t"), "end": event.get("t"),
                                     "duration_seconds": round(seconds, 3)})
    else:
        seconds = None
    if seconds is None:
        gaps.append({"gap": f"{label}_duration_unknown", "detail": str(key), "t": event.get("t")})
        span["duration_seconds"] = None
        span["_unknown"] = True
    span.update(end=event.get("t"), status=action)
    return span


def elapsed_seconds(events, finished_intervals):
    stamps = [value for event in events if (value := stamp(event.get("t"))) is not None]
    if len(stamps) >= 2:
        return max(stamps) - min(stamps)
    if finished_intervals:
        return (max(b for _, b in finished_intervals) - min(a for a, _ in finished_intervals)) / 1e9
    return 0.0


def overlap_seconds(intervals):
    """Count depth above one once, not pairwise overlapping time."""
    points = sorted(point for start, end in intervals if end is not None and end >= start
                    for point in ((start, 1), (end, -1)))
    depth = 0
    last = None
    overlap = 0
    for instant, change in points:
        if last is not None and depth > 1:
            overlap += instant - last
        depth += change
        last = instant
    return overlap / 1e9


def uncovered_seconds(events, intervals):
    """Subtract the wall union of positioned commands and waits from run wall time."""
    stamps = [value for event in events if (value := stamp(event.get("t"))) is not None]
    if len(stamps) < 2:
        return None
    low, high = min(stamps), max(stamps)
    covered = 0.0
    cursor = low
    for start, end in sorted((max(low, a), min(high, b)) for a, b in intervals if b > low and a < high):
        if end > cursor:
            covered += end - max(start, cursor)
            cursor = end
    return round(max(0.0, high - low - covered), 3)


def clock(seconds):
    """Short wall duration; None remains unknown."""
    if seconds is None:
        return "unknown"
    seconds = float(seconds)
    if seconds < 60:
        text = f"{seconds:.1f}".rstrip("0").rstrip(".")
        return f"{text}s"
    minutes, sec = divmod(int(round(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {sec}s" if hours else f"{minutes}m {sec}s"


def share(part, whole):
    return f"{round(100 * float(part) / float(whole))}%" if whole else "n/a"


def ranked(elapsed, phases, waits, operations):
    """Rank observed slices without adding overlapping work to wall time."""
    rows = [{"kind": "phase", "name": name, "seconds": span["duration_seconds"]}
            for name, span in phases.items() if span.get("duration_seconds")]
    rows += [{"kind": "wait", "name": name, "seconds": duration}
             for name, duration in waits.items() if duration]
    commands = {}
    for row in operations:
        if row.get("container") or not row.get("duration_seconds"):
            continue
        name = row.get("name")
        commands[name] = max(commands.get(name, 0), row["duration_seconds"])
    rows += [{"kind": "command", "name": name, "seconds": duration} for name, duration in commands.items()]
    rows.sort(key=lambda row: -float(row["seconds"]))
    for row in rows:
        row.update(share=share(row["seconds"], elapsed), clock=clock(row["seconds"]))
    return rows[:8]


def repeated(operations):
    """Report command time beyond each command name's longest observed run."""
    groups = {}
    for row in operations:
        if not row.get("container") and row.get("duration_seconds") is not None:
            groups.setdefault(row.get("name") or "command", []).append(float(row["duration_seconds"]))
    rows = [{"name": name, "runs": len(values), "extra_seconds": round(sum(values) - max(values), 3),
             "each_seconds": values} for name, values in groups.items() if len(values) > 1]
    return sorted(rows, key=lambda row: -row["extra_seconds"])
