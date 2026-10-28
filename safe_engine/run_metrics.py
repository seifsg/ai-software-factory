"""Local factory-run analytics: bounded events, reports and cross-run compare.

Failure-open: emit/finalize never raise into delivery callers. Corrupt or unwritable
storage becomes an explicit coverage gap. Durations are wall or monotonic process
intervals; never labelled CPU time unless CPU is measured.
"""

from __future__ import annotations

import json
import hashlib
import os
import platform
import re
import shutil
import sys
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path

from safe_engine.host_usage import detail as usage_detail
from safe_engine.metrics_calculations import (clock, share as _share, ranked as _ranked, repeated as _repeated,
                                              utc_delta_seconds as _utc_delta_seconds,
                                              elapsed_seconds as _elapsed_seconds,
                                              overlap_seconds as _overlap_seconds,
                                              uncovered_seconds, wall_interval, duration_seconds, record_activity,
                                              delivery_events)

_CURRENT = ContextVar("run_metrics_current", default=None)
_SEEN_IDS = {}
MAX_CACHED_RUNS = 8

METRICS_SCHEMA = 1
EVENTS_NAME = "events.jsonl"
REPORT_JSON = "report.json"
REPORT_MD = "report.md"
META_NAME = "meta.json"
MAX_EVENT_BYTES = 4096
MAX_EVENTS_PER_RUN = 50_000
MAX_RUNS_RETAINED = 64
MAX_FIELD_CHARS = 500
_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_DEVICE = frozenset({"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                     *(f"LPT{i}" for i in range(1, 10))})

# Overhead budget agreed in #175 plan (A8); publish measured values against these.
OVERHEAD_BUDGET = {
    # Paired start+finish append; 10 ms reflects measured Windows NTFS p99 after O(1) id dedupe.
    "event_append_p99_ms": 10.0,
    "report_generate_ms_at_10k": 200.0,
    "whole_run_fraction": 0.01,
    "whole_run_floor_seconds": 2.0,
    "whole_run_short_wall_seconds": 200.0,
}

EVENT_TYPES = frozenset({
    "run.start", "run.finish", "run.abort", "run.fail",
    "phase.start", "phase.finish", "phase.fail", "phase.cancel", "phase.resume",
    "task.declare", "task.start", "task.finish", "task.fail", "task.cancel", "task.resume",
    "operation.start", "operation.finish",
    "wait.start", "wait.finish",
    "reuse", "invalidate",
    "coverage_gap", "cost",
})

WAIT_CATEGORIES = frozenset({
    "helper", "owner", "approval", "suite_queue", "unknown",
})


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def metrics_root(project):
    return Path(project).resolve() / ".factory" / "metrics"


def run_dir(project, run_key):
    key = _safe_key(run_key)
    return metrics_root(project) / key


def _safe_key(run_key):
    text = str(run_key or "")
    root = text.split(".", 1)[0].upper()
    if (text != text.strip() or not _KEY.fullmatch(text)
            or text.endswith(".") or ".." in text or root in _DEVICE):
        raise ValueError("run_key must be a short path-safe slug")
    return text


def _clip(value):
    if isinstance(value, str) and len(value) > MAX_FIELD_CHARS:
        return value[:MAX_FIELD_CHARS]
    return value


def _fault(project, run_key, kind, detail):
    """Record a coverage gap without raising; best-effort only."""
    try:
        emit(
            project,
            run_key,
            "coverage_gap",
            gap=kind,
            detail=type(detail).__name__ if isinstance(detail, Exception) else kind,
            event_id=f"metrics-gap-{kind}-{_safe_key(run_key)}",
            _internal=True,
        )
    except Exception:
        try:
            sys.stderr.write(f"run_metrics: {kind}: {detail}\n")
        except Exception:
            pass


def ensure_run(project, run_key, *, factory_revision=None, mode=None, kind=None, extra=None):
    """Create the run folder and meta once. Returns the directory path or None on fault."""
    try:
        folder = run_dir(project, run_key)
        folder.mkdir(parents=True, exist_ok=True)
        meta_path = folder / META_NAME
        if not meta_path.is_file():
            meta = {
                "metrics_schema": METRICS_SCHEMA,
                "run_key": _safe_key(run_key),
                "created_at": utc_now(),
                "factory_revision": factory_revision,
                "mode": mode,
                "kind": kind,
                "platform": platform.platform(),
                "python": sys.version.split()[0],
                "runtime": {"os": os.name, "machine": platform.machine()},
            }
            if isinstance(extra, dict):
                meta["extra"] = {k: _clip(v) for k, v in extra.items()
                                 if isinstance(k, str) and k.isidentifier()}
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            emit(
                project,
                run_key,
                "run.start",
                event_id=f"run-start-{_safe_key(run_key)}",
                factory_revision=factory_revision,
                mode=mode,
                kind=kind,
            )
        _prune_retention(project)
        return folder
    except Exception as exc:
        _fault(project, run_key, "analytics_unwritable", exc)
        return None


def set_scope(project, run_key, tickets):
    """Store only a digest of observed ticket identity for matched comparisons."""
    if not tickets:
        return False
    try:
        path = run_dir(project, run_key) / META_NAME
        meta = json.loads(path.read_text(encoding="utf-8"))
        meta["scope"] = hashlib.sha256(json.dumps(sorted(tickets)).encode()).hexdigest()[:24]
        meta["scope_basis"] = "ticket_set"
        temporary = path.with_name(f".meta-{uuid.uuid4().hex}.tmp")
        temporary.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        return True
    except (OSError, ValueError, TypeError) as exc:
        _fault(project, run_key, "analytics_unwritable", exc)
        return False


def emit(project, run_key, event_type, **fields):
    """Append one structured event. Returns True on success, False on fault. Never raises."""
    internal = fields.pop("_internal", False)
    try:
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unknown event_type: {event_type}")
        folder = run_dir(project, run_key)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / EVENTS_NAME
        event_id = fields.pop("event_id", None) or str(uuid.uuid4())
        payload = {
            "metrics_schema": METRICS_SCHEMA,
            "event_id": event_id,
            "type": event_type,
            "t": utc_now(),
            "mono_ns": time.monotonic_ns(),
            "pid": os.getpid(),
            "run_key": _safe_key(run_key),
        }
        parent = fields.pop("parent_id", None)
        if parent:
            payload["parent_id"] = str(parent)[:128]
        for key, value in fields.items():
            if key.startswith("_"):
                continue
            if not isinstance(key, str) or not key.isidentifier():
                continue
            if key in ("prompt", "source", "credential", "password", "token", "secret", "env"):
                continue
            payload[key] = _clip(value)
        line = json.dumps(payload, ensure_ascii=False, default=str) + "\n"
        if len(line.encode("utf-8")) > MAX_EVENT_BYTES:
            raise OSError("event too large")
        with _event_lock(folder):
            index = _event_index(path)
            if event_id in index["ids"]:
                return True
            if index["count"] >= MAX_EVENTS_PER_RUN:
                raise OSError("event cap reached")
            data = (b"" if index["ends_newline"] else b"\n") + line.encode("utf-8")
            with path.open("ab") as out:
                out.write(data)
            index["ids"].add(event_id)
            index["count"] += 1
            stat = path.stat()
            index.update(size=stat.st_size, mtime_ns=stat.st_mtime_ns, inode=stat.st_ino,
                         tail=(index["tail"] + data)[-128:], ends_newline=True)
        return True
    except Exception as exc:
        if not internal:
            _fault(project, run_key, "analytics_unwritable", exc)
        else:
            try:
                sys.stderr.write(f"run_metrics emit failed: {exc}\n")
            except Exception:
                pass
        return False


def emit_phase(project, run_key, phase, action, **fields):
    """action: start|finish|fail|cancel|resume"""
    return emit(project, run_key, f"phase.{action}", phase=phase, **fields)


def emit_task(project, run_key, task_id, action, **fields):
    """Record only an explicitly observed task boundary or declaration."""
    if not isinstance(task_id, str) or not task_id or len(task_id) > 64:
        return False
    return emit(project, run_key, f"task.{action}", task_id=task_id, **fields)


def emit_operation(project, run_key, action, name, **fields):
    return emit(project, run_key, f"operation.{action}", name=name, **fields)


def emit_wait(project, run_key, action, category, **fields):
    if category not in WAIT_CATEGORIES:
        category = "unknown"
    return emit(project, run_key, f"wait.{action}", category=category, **fields)


def read_events(project, run_key):
    """Load events; skips corrupt lines and records a gap once."""
    path = run_dir(project, run_key) / EVENTS_NAME
    events, corrupt = [], 0
    if not path.is_file():
        return events
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        _fault(project, run_key, "analytics_corrupt", exc)
        return events
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict) and row.get("event_id"):
                events.append(row)
            else:
                corrupt += 1
        except ValueError:
            corrupt += 1
    if corrupt:
        gap_id = f"metrics-gap-analytics_corrupt-{_safe_key(run_key)}"
        stored = next((row for row in events if row["event_id"] == gap_id), None)
        if stored:
            stored["detail"] = f"{corrupt} bad lines"
        else:
            events.append({"event_id": gap_id, "type": "coverage_gap", "gap": "analytics_corrupt",
                           "detail": f"{corrupt} bad lines", "t": utc_now()})
        _fault(project, run_key, "analytics_corrupt", f"{corrupt} bad lines")
    return events


def aggregate(events, *, meta=None, outcome=None):
    """Derive report fields. Interrupted spans stay incomplete (no invented ends)."""
    by_id = {}
    for event in events:
        by_id[event["event_id"]] = event
    events = list(by_id.values())

    phase_spans, task_spans = {}, {}
    op_intervals = []  # (start_mono, end_mono or None)
    wall_intervals, command_wall_intervals = [], []
    placement_unknown = False
    open_ops = {}
    waits = {name: 0.0 for name in WAIT_CATEGORIES}
    open_waits = {}
    helpers = {}
    reuse_count = 0
    invalidate_reasons = {}
    gaps = []
    costs, snapshots = [], {}
    longest, failed = [], []

    for event in events:
        kind = event.get("type")
        mono = event.get("mono_ns")
        if kind and kind.startswith("phase."):
            record_activity(phase_spans, event.get("phase"), event, kind.split(".")[-1], gaps, "phase")
        elif kind and kind.startswith("task."):
            task_id = event.get("task_id")
            if task_id:
                span = record_activity(task_spans, task_id, event, kind.split(".")[-1], gaps, "task")
                if event.get("ticket_id"):
                    span["ticket_id"] = event["ticket_id"]
        elif kind == "operation.start":
            open_ops[event["event_id"]] = event
        elif kind == "operation.finish":
            parent = event.get("parent_id")
            start = by_id.get(parent) if parent else None
            if parent:
                open_ops.pop(parent, None)
            duration = event.get("duration_seconds")
            start_mono = start.get("mono_ns") if start else None
            end_mono = mono
            if duration is None and start:
                duration = duration_seconds(start, event)
            # Container ops (e.g. full_suite wrapping per-command ops) stay in longest; skip sum/overlap.
            container = bool(event.get("container") or (start or {}).get("container"))
            if start_mono is not None and end_mono is not None and not container and (
                    start.get("pid") == event.get("pid") or not (start.get("pid") and event.get("pid"))):
                op_intervals.append((start_mono, end_mono if end_mono is not None else start_mono))
            if not container:
                interval = wall_interval(start, event) if start else None
                if interval is None:
                    placement_unknown = True
                else:
                    wall_intervals.append(interval)
                    command_wall_intervals.append(interval)
            status = ("failed" if event.get("passed") is False or event.get("timed_out") is True else
                      "passed" if event.get("passed") is True else "unknown")
            operation = {
                "name": event.get("name") or (start or {}).get("name"),
                "task_id": event.get("task_id") or (start or {}).get("task_id"),
                "duration_seconds": round(duration, 3) if duration is not None else None,
                "reused": bool(event.get("reused")),
                "container": container,
                "status": status,
                "timed_out": bool(event.get("timed_out")),
            }
            longest.append(operation)
            if status == "failed":
                failed.append(operation)
        elif kind == "wait.start":
            open_waits[event["event_id"]] = event
            if event.get("category") == "helper" and event.get("helper_id"):
                helpers[event["helper_id"]] = {"helper_id": event["helper_id"],
                                               "wait_seconds": None, "status": "open"}
        elif kind == "wait.finish":
            parent = event.get("parent_id")
            start = by_id.get(parent) if parent else None
            if parent:
                open_waits.pop(parent, None)
            category = event.get("category") or (start or {}).get("category") or "unknown"
            if category not in waits:
                category = "unknown"
            duration = event.get("duration_seconds")
            if duration is None and start and start.get("t") and event.get("t"):
                duration = _utc_delta_seconds(start["t"], event["t"])
            # Never subtract mono_ns across processes; that yields near-zero/negative waits.
            if duration is not None and duration >= 0:
                waits[category] = round(waits[category] + float(duration), 3)
            elif start is not None:
                gaps.append({"gap": "wait_duration_unknown", "detail": category, "t": event.get("t")})
            interval = wall_interval(start, event) if start else None
            if interval is None:
                placement_unknown = True
            else:
                wall_intervals.append(interval)
            helper_id = event.get("helper_id") or (start or {}).get("helper_id")
            if category == "helper" and helper_id:
                helpers[helper_id] = {"helper_id": helper_id, "wait_seconds": duration,
                                      "status": event.get("status") or "unknown",
                                      "task_id": event.get("task_id") or (start or {}).get("task_id")}
        elif kind == "reuse":
            reuse_count += 1
        elif kind == "invalidate":
            reason = str(event.get("reason") or "unspecified")
            invalidate_reasons[reason] = invalidate_reasons.get(reason, 0) + 1
        elif kind == "coverage_gap":
            gaps.append({"gap": event.get("gap"), "detail": event.get("detail"), "t": event.get("t")})
        elif kind == "cost":
            if event.get("provenance") and event.get("units"):
                cost = {
                    "amount": event.get("amount"),
                    "units": event.get("units"),
                    "provenance": event.get("provenance"),
                    "scope": event.get("scope"),
                    "session_id": event.get("session_id"),
                    "model": event.get("model"),
                    "kind": event.get("kind"),
                    "detail": event.get("detail"),
                }
                if event.get("session_id") and event.get("snapshot_id"):
                    key = (event["session_id"], event["snapshot_id"])
                    group = snapshots.setdefault(key, {"rank": event.get("snapshot_total") or 0,
                                                       "order": len(snapshots), "expected": event.get("snapshot_rows"),
                                                       "costs": []})
                    group["costs"].append(cost)
                else:
                    costs.append(cost)

    latest = {}
    for (session_id, _), group in snapshots.items():
        if group["expected"] and len(group["costs"]) != group["expected"]:
            gaps.append({"gap": "usage_snapshot_incomplete", "detail": session_id, "t": utc_now()})
            continue
        if session_id not in latest or (group["rank"], group["order"]) > (latest[session_id]["rank"], latest[session_id]["order"]):
            latest[session_id] = group
    for group in latest.values():
        costs.extend(group["costs"])

    incomplete = []
    for event_id, start in open_ops.items():
        incomplete.append({"kind": "operation", "name": start.get("name"), "event_id": event_id})
        if start.get("mono_ns") is not None:
            op_intervals.append((start["mono_ns"], None))
    for event_id, start in open_waits.items():
        incomplete.append({"kind": "wait", "category": start.get("category"), "event_id": event_id})
    for phase, span in phase_spans.items():
        span.pop("_active", None)
        span.pop("_unknown", None)
        if span.get("end") is None:
            incomplete.append({"kind": "phase", "phase": phase})
    for task_id, span in task_spans.items():
        active = span.pop("_active", None)
        span.pop("_unknown", None)
        if active:
            incomplete.append({"kind": "task", "task_id": task_id, "event_id": active.get("event_id")})
        elif span.get("start") is None:
            gaps.append({"gap": "task_boundary_unobserved", "detail": task_id, "t": None})

    finished_intervals = [(a, b) for a, b in op_intervals if b is not None]
    summed = round(sum(row["duration_seconds"] for row in longest
                       if not row["container"] and row["duration_seconds"] is not None), 3)
    overlap = round(_overlap_seconds([(int(a * 1e9), int(b * 1e9)) for a, b in command_wall_intervals
                                      if a < b]), 3)
    clock_events = delivery_events(events)
    elapsed = round(_elapsed_seconds(clock_events, finished_intervals), 3)

    longest.sort(key=lambda row: (row.get("duration_seconds") is None, -(row.get("duration_seconds") or 0)))
    wait_total = round(sum(waits.values()), 3)
    if placement_unknown:
        gaps.append({"gap": "wall_placement_unknown", "detail": "operation_or_wait", "t": None})
    unaccounted = None if placement_unknown else uncovered_seconds(clock_events, wall_intervals)
    report = {
        "metrics_schema": METRICS_SCHEMA,
        "outcome": outcome or "partial",
        "generated_at": utc_now(),
        "elapsed_seconds": elapsed,
        "summed_operation_seconds": summed,
        "overlap_seconds": overlap,
        "phases": phase_spans,
        "tasks": task_spans,
        "helpers": list(helpers.values()),
        "waits": waits,
        "reuse_count": reuse_count,
        "invalidation_reasons": invalidate_reasons,
        "longest_operations": longest[:20],
        "failed_operation_count": len(failed),
        "failed_operations": failed[:20],
        "wait_total_seconds": wait_total,
        "unaccounted_seconds": unaccounted,
        "ranked": _ranked(elapsed, phase_spans, waits, longest),
        "repeated": _repeated(longest),
        "incomplete_spans": incomplete,
        "coverage_gaps": gaps,
        "event_count": len(events),
        "overhead_budget": OVERHEAD_BUDGET,
        "duration_notes": {
            "elapsed": "end-to-end wall from first to last event timestamp (UTC); not CPU time",
            "summed_operation_seconds": "sum of finished non-container operation intervals (monotonic when both ends known)",
            "overlap_seconds": "overlapping finished non-container command time aligned by UTC; do not add to elapsed for delivery time",
            "waits": "wall duration_seconds or UTC start/finish delta; mono_ns is not used across processes",
            "unaccounted_seconds": "UTC run wall outside the union of placed non-container commands and waits; unknown if placement fails",
            "tasks": "only explicitly observed boundaries; an active span can include waits and is not CPU or active effort",
            "cross_process_utc": "UTC alignment across processes may skew; prefer mono_ns within one process",
            "approval_waits": "approval category reserved; uncovered until an owner emits wait.approval events",
        },
    }
    if meta:
        report["meta"] = meta
    if costs:
        report["costs"] = costs
    return report


def within_budget(append_p99_ms, report_ms, collection_seconds, whole_cap_seconds):
    """True only when append, report, and whole-run caps all hold."""
    return (append_p99_ms <= OVERHEAD_BUDGET["event_append_p99_ms"]
            and report_ms <= OVERHEAD_BUDGET["report_generate_ms_at_10k"]
            and collection_seconds <= whole_cap_seconds)


def finalize(project, run_key, *, outcome=None, overhead=None):
    """Write report.json and report.md. outcome: finish|abort|fail|partial. Returns report or None.

    Only an explicit lifecycle terminal event completes a run.
    """
    try:
        folder = run_dir(project, run_key)
        meta = {}
        meta_path = folder / META_NAME
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        events = read_events(project, run_key)
        prior_terminal = next((event["type"].split(".")[1] for event in reversed(events)
                               if event.get("type") in ("run.finish", "run.abort", "run.fail")), None)
        if outcome not in (None, "finish", "abort", "fail", "partial"):
            raise ValueError("Invalid metrics outcome")
        chosen = outcome if outcome in ("finish", "abort", "fail") else prior_terminal or "partial"
        terminal = {"finish": "run.finish", "abort": "run.abort", "fail": "run.fail"}.get(chosen)
        if outcome and terminal:
            emit(project, run_key, terminal, event_id=f"run-{chosen}-{_safe_key(run_key)}")
            events = read_events(project, run_key)
        report = aggregate(events, meta=meta, outcome=chosen)
        if overhead:
            report["overhead"] = overhead
        (folder / REPORT_JSON).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (folder / REPORT_MD).write_text(markdown(report), encoding="utf-8")
        return report
    except Exception as exc:
        _fault(project, run_key, "analytics_unwritable", exc)
        return None


def _token_lines(costs):
    """One block. Host dollars and rate-card estimates stay labeled. Silence is unavailable."""
    token_rows = [row for row in costs if row.get("units") == "tokens"]
    usd_rows = [row for row in costs if row.get("units") == "usd"]
    if not token_rows and not usd_rows:
        return ["- unavailable: no host usage record was attached to this run"]
    lines = []
    for row in token_rows:
        scope = row.get("scope") or "unknown scope"
        session = row.get("session_id") or "unknown"
        lines.append(f"- {row.get('model')} [{scope}, session {session[:8]}, {row.get('provenance')}]: "
                     f"{row.get('detail')} ({row.get('amount')} tokens)")
    counted = sum(row.get("amount") or 0 for row in token_rows)
    if token_rows:
        lines.append(f"- tokens counted: {counted}")
    for row in usd_rows:
        kind = row.get("kind")
        if kind == "host":
            lines.append(f"- cost: ${row.get('amount')} host-reported")
        elif kind == "estimated":
            lines.append(f"- cost: about ${row.get('amount')} estimated from the rate card, not a bill")
        else:
            lines.append(f"- cost: {row.get('amount')} {row.get('units')} ({kind})")
    if token_rows and not usd_rows:
        lines.append("- cost: unavailable (tokens are known; no host price and no complete rate card)")
    return lines


def attach_usage(project, run_key, summary):
    """Record one already-parsed host summary. Does not read a session or call a model."""
    if not isinstance(summary, dict) or not summary.get("models"):
        return False
    provenance = summary.get("provenance") or "host-usage"
    session_id = summary.get("session_id")
    snapshot_id = hashlib.sha256(json.dumps(summary, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:24]
    has_usd = summary.get("cost_kind") in ("host", "estimated") and summary.get("cost_usd") is not None
    common = {"session_id": session_id, "snapshot_id": snapshot_id,
              "snapshot_total": summary.get("tokens"), "snapshot_rows": len(summary["models"]) + int(has_usd),
              "scope": summary.get("scope") or "shared_session"}
    ok = True
    for item in summary["models"]:
        ok = emit(
            project, run_key, "cost",
            amount=item.get("tokens"), units="tokens", provenance=provenance,
            model=item.get("model"), kind="host", **common,
            detail=usage_detail(item.get("counts") or {}, item.get("reasoning_output_tokens")),
            event_id=f"{run_key}-tokens-{snapshot_id}-{hashlib.sha256(str(item.get('model')).encode()).hexdigest()[:12]}",
        ) and ok
    if has_usd:
        ok = emit(
            project, run_key, "cost",
            amount=summary["cost_usd"], units="usd", provenance=provenance,
            kind=summary["cost_kind"], **common,
            event_id=f"{run_key}-usd-{snapshot_id}",
        ) and ok
    return ok


def markdown(report):
    elapsed = report.get("elapsed_seconds") or 0
    commands = report.get("summed_operation_seconds") or 0
    waits = report.get("wait_total_seconds") or 0
    lines = [
        f"# Where this run went ({report.get('outcome', 'partial')})",
        "",
        f"Wall clock: {clock(elapsed)}.",
        f"Recorded commands: {clock(commands)} ({_share(commands, elapsed)} of wall).",
        f"Recorded waits: {clock(waits)} ({_share(waits, elapsed)} of wall).",
        "Do not add commands and waits into the wall clock. Overlap is not delivery time.",
        f"Command overlap: {clock(report.get('overlap_seconds') or 0)}.",
        (f"{clock(report['unaccounted_seconds'])} of wall has neither a recorded command nor wait."
         if report.get("unaccounted_seconds") is not None else
         "Unaccounted wall is unknown because a command or wait could not be placed in UTC."),
        "",
        "## Largest measured slices",
        "Each share is versus wall clock. Slices overlap, so the shares are not a pie.",
    ]
    ranked = report.get("ranked") or []
    if not ranked:
        lines.append("- none")
    for index, row in enumerate(ranked, 1):
        lines.append(f"{index}. {row['kind']} {row['name']} — {row['clock']} — {row['share']} of wall")
    lines.extend(["", "## Tasks (observed boundary spans)"])
    tasks = report.get("tasks") or {}
    lines.extend(f"- {task_id}: {clock(span.get('duration_seconds'))}, "
                 f"{span.get('status') or 'boundary unknown'}"
                 for task_id, span in sorted(tasks.items()))
    if not tasks:
        lines.append("- no task boundary observed")
    lines.extend(["", "## Helper waits"])
    helpers = report.get("helpers") or []
    lines.extend(f"- {row['helper_id']}: {clock(row.get('wait_seconds'))}, {row['status']}"
                 for row in helpers)
    if not helpers:
        lines.append("- none observed")
    lines.extend(["", "## Failed commands"])
    failed = report.get("failed_operations") or []
    lines.extend(f"- {row.get('name')} [{row.get('task_id') or 'task unknown'}]: {clock(row.get('duration_seconds'))}"
                 for row in failed)
    if not failed:
        lines.append("- none observed")
    lines.extend(["", "## Repeated work"])
    repeated = report.get("repeated") or []
    reasons = report.get("invalidation_reasons") or {}
    if not repeated and not reasons:
        lines.append("- none")
    for row in repeated:
        lines.append(
            f"- {row['name']} ran {row['runs']} times; {clock(row['extra_seconds'])} is repeat work beyond the longest run"
        )
    for reason, count in sorted(reasons.items()):
        lines.append(f"- invalidated: {reason} × {count}")
    if report.get("reuse_count"):
        lines.append(f"- reused an earlier result {report['reuse_count']} time(s)")
    lines.extend(["", "## Tokens and cost"])
    lines.extend(_token_lines(report.get("costs") or []))
    lines.extend(["", "## Not measured"])
    gaps = report.get("coverage_gaps") or []
    if not gaps:
        lines.append("- none recorded")
    for gap in gaps:
        lines.append(f"- {gap.get('gap')}: {gap.get('detail')}")
    lines.extend(["", "## Incomplete spans"])
    incomplete = report.get("incomplete_spans") or []
    if not incomplete:
        lines.append("- none")
    for row in incomplete:
        lines.append(f"- {row}")
    lines.extend(["", "## Overhead budget", json.dumps(report.get("overhead_budget") or {}, indent=2)])
    if report.get("overhead"):
        lines.extend(["", "## Measured overhead", json.dumps(report["overhead"], indent=2)])
    lines.extend(["", "## Duration notes"])
    for key, note in (report.get("duration_notes") or {}).items():
        lines.append(f"- {key}: {note}")
    lines.append("")
    return "\n".join(lines)


def compare(project, run_keys):
    """Compare only completed runs inside matching observed context cohorts."""
    rows = []
    for key in run_keys:
        folder = run_dir(project, key)
        report_path = folder / REPORT_JSON
        meta_path = folder / META_NAME
        if not report_path.is_file():
            rows.append({"run_key": key, "status": "missing_report"})
            continue
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
        except (OSError, ValueError):
            rows.append({"run_key": key, "status": "invalid_report"})
            continue
        scope = meta.get("scope") or meta.get("kind")
        rows.append({
            "run_key": key,
            "status": report.get("outcome"),
            "factory_revision": meta.get("factory_revision"),
            "platform": meta.get("platform"),
            "kind": meta.get("kind"),
            "mode": meta.get("mode"),
            "scope": scope,
            "scope_basis": meta.get("scope_basis") or "kind_only_legacy",
            "elapsed_seconds": report.get("elapsed_seconds"),
            "summed_operation_seconds": report.get("summed_operation_seconds"),
            "overlap_seconds": report.get("overlap_seconds"),
            "reuse_count": report.get("reuse_count"),
            "failed_operation_count": report.get("failed_operation_count", 0),
            "invalidation_reasons": report.get("invalidation_reasons"),
            "coverage_gap_count": len(report.get("coverage_gaps") or []),
            "event_count": report.get("event_count"),
            "incomplete": len(report.get("incomplete_spans") or []),
        })
    cohorts = {}
    excluded = []
    for row in rows:
        context = tuple(row.get(name) for name in ("factory_revision", "platform", "kind", "mode", "scope"))
        if row.get("status") != "finish" or not all(context):
            excluded.append({"run_key": row["run_key"], "reason": "not_completed" if row.get("status") != "finish"
                             else "context_unknown"})
        else:
            cohorts.setdefault(context, []).append(row)
    groups = []
    for context, cohort in cohorts.items():
        if len(cohort) < 2:
            excluded.append({"run_key": cohort[0]["run_key"], "reason": "no_matching_run"})
            continue
        baseline = cohort[0]
        fields = ("elapsed_seconds", "summed_operation_seconds", "reuse_count",
                  "failed_operation_count", "coverage_gap_count", "incomplete")
        deltas = [{"run_key": row["run_key"], "against": baseline["run_key"],
                   **{name + "_delta": round(row[name] - baseline[name], 3)
                      if isinstance(row.get(name), (int, float)) and isinstance(baseline.get(name), (int, float))
                      else None for name in fields}} for row in cohort[1:]]
        groups.append({"context": dict(zip(("factory_revision", "platform", "kind", "mode", "scope"), context)),
                       "scope_basis": baseline["scope_basis"], "sample_size": len(cohort),
                       "pair_count": len(deltas), "baseline": baseline["run_key"], "deltas": deltas})
    return {
        "metrics_schema": METRICS_SCHEMA,
        "sample_size": sum(group["sample_size"] for group in groups),
        "requested": len(run_keys),
        "eligible_completed": sum(row.get("status") == "finish" for row in rows),
        "matching_context_groups": len(groups),
        "groups": groups,
        "excluded": excluded,
        "note": "Highlights timing/rework/quality deltas; does not claim causation; "
                "do not sum overlapping work into delivery time. Legacy kind-only scope is coarse.",
        "runs": rows,
    }


def export(project, run_key, destination):
    """Copy a run's metrics folder to destination. Returns path or None."""
    try:
        source = run_dir(project, run_key)
        if not source.is_dir():
            raise FileNotFoundError(source)
        dest = Path(destination)
        if dest.exists():
            raise FileExistsError(dest)
        shutil.copytree(source, dest)
        return str(dest)
    except Exception as exc:
        _fault(project, run_key, "analytics_unwritable", exc)
        return None


def delete(project, run_key):
    """Delete one run's metrics folder. Returns True on success."""
    try:
        folder = run_dir(project, run_key)
        root = metrics_root(project)
        junction = lambda path: getattr(path, "is_junction", lambda: False)()
        if (folder.parent != root or folder.resolve().parent != root.resolve()
                or root.is_symlink() or junction(root)
                or folder.is_symlink() or getattr(folder, "is_junction", lambda: False)()):
            raise ValueError("Metrics deletion needs one direct run folder")
        _SEEN_IDS.pop(str(folder / EVENTS_NAME), None)
        if folder.is_dir():
            shutil.rmtree(folder)
        return True
    except Exception as exc:
        _fault(project, run_key, "analytics_unwritable", exc)
        return False


def measure_overhead(project, run_key, event_count=200):
    """Publish fixture overhead numbers against OVERHEAD_BUDGET."""
    folder = ensure_run(project, run_key, factory_revision="overhead-fixture", mode="fast", kind="change")
    if folder is None:
        return None
    for index in range(20):  # warm filesystem and id cache before sampling
        emit(project, run_key, "operation.start", name="warmup", event_id=f"warm-s-{index}")
        emit(project, run_key, "operation.finish", name="warmup", event_id=f"warm-f-{index}",
             parent_id=f"warm-s-{index}", duration_seconds=0.0)
    samples = []
    for index in range(event_count):
        start = time.perf_counter()
        emit(project, run_key, "operation.start", name="overhead", event_id=f"oh-s-{index}")
        emit(
            project,
            run_key,
            "operation.finish",
            name="overhead",
            event_id=f"oh-f-{index}",
            parent_id=f"oh-s-{index}",
            duration_seconds=0.001,
        )
        samples.append((time.perf_counter() - start) * 1000.0)
    samples.sort()
    p99 = samples[min(len(samples) - 1, int(len(samples) * 0.99))]
    wall_start = time.perf_counter()
    report = finalize(project, run_key, outcome="finish")
    generate_ms = (time.perf_counter() - wall_start) * 1000.0
    wall_seconds = time.perf_counter() - wall_start + sum(s / 1000.0 for s in samples)
    whole_cap = max(
        OVERHEAD_BUDGET["whole_run_floor_seconds"],
        OVERHEAD_BUDGET["whole_run_fraction"] * max(wall_seconds, 0.001),
    )
    if wall_seconds < OVERHEAD_BUDGET["whole_run_short_wall_seconds"]:
        whole_cap = max(whole_cap, OVERHEAD_BUDGET["whole_run_floor_seconds"])
    collection_seconds = sum(s / 1000.0 for s in samples) + generate_ms / 1000.0
    result = {
        "workload": {
            "paired_operation_events": event_count * 2,
            "warmup_pairs": 20,
            "machine": platform.platform(),
            "single_shot": True,
        },
        "event_append_pair_p99_ms": round(p99, 3),
        "report_generate_ms": round(generate_ms, 3),
        "collection_seconds": round(collection_seconds, 3),
        "wall_seconds": round(wall_seconds, 3),
        "whole_run_cap_seconds": round(whole_cap, 3),
        "budget": OVERHEAD_BUDGET,
        "within_budget": within_budget(p99, generate_ms, collection_seconds, whole_cap),
        "event_count": report.get("event_count") if report else None,
    }
    if report is not None:
        report["overhead"] = result
        path = run_dir(project, run_key) / REPORT_JSON
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (run_dir(project, run_key) / REPORT_MD).write_text(markdown(report), encoding="utf-8")
    return result


@contextmanager
def _event_lock(folder):
    """Serialize event writers so an index refresh and append form one operation."""
    with (folder / "events.lock").open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _index_stamp(path, index):
    """Remember file identity and a short tail check for the next append."""
    if not path.is_file():
        index.update(size=0, mtime_ns=0, inode=None, tail=b"", ends_newline=True)
        return
    stat = path.stat()
    with path.open("rb") as handle:
        handle.seek(max(0, stat.st_size - 128))
        tail = handle.read()
    index.update(size=stat.st_size, mtime_ns=stat.st_mtime_ns, inode=stat.st_ino,
                 tail=tail, ends_newline=not tail or tail.endswith(b"\n"))


def _event_index(path):
    """Read only unseen bytes; rebuild after restart, truncate or external rewrite."""
    key = str(path)
    cached = _SEEN_IDS.get(key)
    if not path.is_file():
        index = {"ids": set(), "count": 0}
        _index_stamp(path, index)
        _cache_index(key, index)
        return index
    stat = path.stat()
    offset = cached["size"] if cached else 0
    reset = not cached or stat.st_ino != cached["inode"] or stat.st_size < offset
    if not reset and stat.st_size == offset and stat.st_mtime_ns != cached["mtime_ns"]:
        reset = True
    if not reset and stat.st_size == offset:
        _cache_index(key, cached)
        return cached
    if not reset and offset:
        with path.open("rb") as handle:
            handle.seek(max(0, offset - 128))
            reset = handle.read(len(cached["tail"])) != cached["tail"]
    if not reset and not cached["ends_newline"] and stat.st_size > offset:
        reset = True
    index = {"ids": set(), "count": 0} if reset else cached
    with path.open("rb") as handle:
        handle.seek(0 if reset else offset)
        for line in handle:
            index["count"] += 1
            try:
                row = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(row, dict) and row.get("event_id"):
                index["ids"].add(row["event_id"])
    _index_stamp(path, index)
    _cache_index(key, index)
    return index


def _cache_index(key, index):
    """Bound remembered IDs to active runs; evicted runs rebuild from JSONL."""
    _SEEN_IDS.pop(key, None)
    _SEEN_IDS[key] = index
    if len(_SEEN_IDS) > MAX_CACHED_RUNS:
        _SEEN_IDS.pop(next(iter(_SEEN_IDS)))


def _prune_retention(project):
    root = metrics_root(project)
    if not root.is_dir():
        return
    runs = sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
    for stale in runs[MAX_RUNS_RETAINED:]:
        shutil.rmtree(stale, ignore_errors=True)


def safe_call(fn, *args, **kwargs):
    """Wrap instrumentation sites so delivery never fails on analytics."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        try:
            sys.stderr.write(f"run_metrics: {exc}\n")
        except Exception:
            pass
        return None


@contextmanager
def bound(project, run_key, **meta):
    """Bind project/run for nested helpers (suite queue) without threading args through every API."""
    token = _CURRENT.set({"project": str(Path(project).resolve()), "run_key": run_key,
                          "task_id": meta.get("task_id"), "meta": meta})
    try:
        ensure_run(project, run_key, **{k: meta.get(k) for k in ("factory_revision", "mode", "kind") if k in meta})
        yield
    finally:
        _CURRENT.reset(token)


def current():
    return _CURRENT.get()


def emit_current(event_type, **fields):
    ctx = current()
    if not ctx:
        return False
    if ctx.get("task_id"):
        fields.setdefault("task_id", ctx["task_id"])
    return emit(ctx["project"], ctx["run_key"], event_type, **fields)
