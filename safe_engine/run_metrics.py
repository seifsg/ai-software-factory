"""Local factory-run analytics: bounded events, reports and cross-run compare.

Failure-open: emit/finalize never raise into delivery callers. Corrupt or unwritable
storage becomes an explicit coverage gap. Durations are wall or monotonic process
intervals; never labelled CPU time unless CPU is measured.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path

_CURRENT = ContextVar("run_metrics_current", default=None)
_SEEN_IDS = {}

METRICS_SCHEMA = 1
EVENTS_NAME = "events.jsonl"
REPORT_JSON = "report.json"
REPORT_MD = "report.md"
META_NAME = "meta.json"
MAX_EVENT_BYTES = 4096
MAX_EVENTS_PER_RUN = 50_000
MAX_RUNS_RETAINED = 64
MAX_FIELD_CHARS = 500

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
    "operation.start", "operation.finish",
    "wait.start", "wait.finish",
    "reuse", "invalidate",
    "coverage_gap", "cost",
})

WAIT_CATEGORIES = frozenset({
    "helper", "owner", "approval", "suite_queue", "unknown",
})


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def metrics_root(project):
    return Path(project).resolve() / ".factory" / "metrics"


def run_dir(project, run_key):
    key = _safe_key(run_key)
    return metrics_root(project) / key


def _safe_key(run_key):
    text = str(run_key or "").strip()
    if not text or len(text) > 64 or "/" in text or "\\" in text or ".." in text:
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
            detail=str(detail)[:MAX_FIELD_CHARS],
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


def emit(project, run_key, event_type, **fields):
    """Append one structured event. Returns True on success, False on fault. Never raises."""
    internal = fields.pop("_internal", False)
    try:
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unknown event_type: {event_type}")
        folder = run_dir(project, run_key)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / EVENTS_NAME
        if path.is_file() and _line_count(path) >= MAX_EVENTS_PER_RUN:
            raise OSError("event cap reached")
        event_id = fields.pop("event_id", None) or str(uuid.uuid4())
        seen = _seen_ids(path)
        if event_id in seen:
            return True  # duplicate: do not double-count
        payload = {
            "metrics_schema": METRICS_SCHEMA,
            "event_id": event_id,
            "type": event_type,
            "t": utc_now(),
            "mono_ns": time.monotonic_ns(),
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
        with path.open("a", encoding="utf-8") as out:
            out.write(line)
        seen.add(event_id)
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
        text = path.read_text(encoding="utf-8")
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
        _fault(project, run_key, "analytics_corrupt", f"{corrupt} bad lines")
    return events


def aggregate(events, *, meta=None, outcome=None):
    """Derive report fields. Interrupted spans stay incomplete (no invented ends)."""
    by_id = {}
    for event in events:
        by_id[event["event_id"]] = event

    phase_spans = {}
    op_intervals = []  # (start_mono, end_mono or None)
    open_ops = {}
    waits = {name: 0.0 for name in WAIT_CATEGORIES}
    open_waits = {}
    reuse_count = 0
    invalidate_reasons = {}
    gaps = []
    costs = []
    longest = []

    for event in events:
        kind = event.get("type")
        mono = event.get("mono_ns")
        if kind == "phase.start":
            phase_spans[event.get("phase")] = {"start": event.get("t"), "start_mono": mono, "end": None}
        elif kind in ("phase.finish", "phase.fail", "phase.cancel"):
            span = phase_spans.get(event.get("phase")) or {}
            span.update(end=event.get("t"), end_mono=mono, status=kind.split(".")[-1])
            if span.get("start_mono") is not None and mono is not None:
                span["duration_seconds"] = round((mono - span["start_mono"]) / 1e9, 3)
            phase_spans[event.get("phase")] = span
        elif kind == "phase.resume":
            phase_spans[event.get("phase")] = {
                "start": event.get("t"), "start_mono": mono, "end": None, "resumed": True,
            }
        elif kind == "operation.start":
            open_ops[event["event_id"]] = event
        elif kind == "operation.finish":
            parent = event.get("parent_id")
            start = by_id.get(parent) or open_ops.pop(parent, None)
            duration = event.get("duration_seconds")
            start_mono = start.get("mono_ns") if start else None
            end_mono = mono
            if duration is None and start_mono is not None and end_mono is not None:
                duration = round((end_mono - start_mono) / 1e9, 3)
            # Container ops (e.g. full_suite wrapping per-command ops) stay in longest; skip sum/overlap.
            container = bool(event.get("container") or (start or {}).get("container"))
            if start_mono is not None and not container:
                op_intervals.append((start_mono, end_mono if end_mono is not None else start_mono))
            longest.append({
                "name": event.get("name") or (start or {}).get("name"),
                "duration_seconds": duration,
                "reused": bool(event.get("reused")),
                "container": container,
            })
        elif kind == "wait.start":
            open_waits[event["event_id"]] = event
        elif kind == "wait.finish":
            parent = event.get("parent_id")
            start = by_id.get(parent) or open_waits.pop(parent, None)
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
        elif kind == "reuse":
            reuse_count += 1
        elif kind == "invalidate":
            reason = str(event.get("reason") or "unspecified")
            invalidate_reasons[reason] = invalidate_reasons.get(reason, 0) + 1
        elif kind == "coverage_gap":
            gaps.append({"gap": event.get("gap"), "detail": event.get("detail"), "t": event.get("t")})
        elif kind == "cost":
            if event.get("provenance") and event.get("units"):
                costs.append({
                    "amount": event.get("amount"),
                    "units": event.get("units"),
                    "provenance": event.get("provenance"),
                    "scope": event.get("scope"),
                })

    incomplete = []
    for event_id, start in open_ops.items():
        incomplete.append({"kind": "operation", "name": start.get("name"), "event_id": event_id})
        if start.get("mono_ns") is not None:
            op_intervals.append((start["mono_ns"], None))
    for event_id, start in open_waits.items():
        incomplete.append({"kind": "wait", "category": start.get("category"), "event_id": event_id})
    for phase, span in phase_spans.items():
        if span.get("end") is None:
            incomplete.append({"kind": "phase", "phase": phase})

    finished_intervals = [(a, b) for a, b in op_intervals if b is not None]
    summed = round(sum((b - a) / 1e9 for a, b in finished_intervals), 3)
    overlap = round(_overlap_seconds(finished_intervals), 3)
    elapsed = round(_elapsed_seconds(events, finished_intervals), 3)

    longest.sort(key=lambda row: (row.get("duration_seconds") is None, -(row.get("duration_seconds") or 0)))
    report = {
        "metrics_schema": METRICS_SCHEMA,
        "outcome": outcome or "partial",
        "generated_at": utc_now(),
        "elapsed_seconds": elapsed,
        "summed_operation_seconds": summed,
        "overlap_seconds": overlap,
        "phases": phase_spans,
        "waits": waits,
        "reuse_count": reuse_count,
        "invalidation_reasons": invalidate_reasons,
        "longest_operations": longest[:20],
        "incomplete_spans": incomplete,
        "coverage_gaps": gaps,
        "event_count": len(events),
        "overhead_budget": OVERHEAD_BUDGET,
        "duration_notes": {
            "elapsed": "end-to-end wall from first to last event timestamp (UTC); not CPU time",
            "summed_operation_seconds": "sum of finished non-container operation intervals (monotonic when both ends known)",
            "overlap_seconds": "overlapping finished non-container operation time; do not add to elapsed for delivery time",
            "waits": "wall duration_seconds or UTC start/finish delta; mono_ns is not used across processes",
            "cross_process_utc": "UTC alignment across processes may skew; prefer mono_ns within one process",
            "approval_waits": "approval category reserved; uncovered until an owner emits wait.approval events",
        },
    }
    if meta:
        report["meta"] = meta
    if costs:
        report["costs"] = costs
    return report


def _utc_delta_seconds(start, end):
    try:
        a = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        b = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
        return (b - a).total_seconds()
    except ValueError:
        return None


def _elapsed_seconds(events, finished_intervals):
    times = [e.get("t") for e in events if e.get("t")]
    if len(times) >= 2:
        try:
            start = datetime.fromisoformat(times[0].replace("Z", "+00:00"))
            end = datetime.fromisoformat(times[-1].replace("Z", "+00:00"))
            return max(0.0, (end - start).total_seconds())
        except ValueError:
            pass
    if finished_intervals:
        lows = [a for a, _ in finished_intervals]
        highs = [b for _, b in finished_intervals]
        return max(0.0, (max(highs) - min(lows)) / 1e9)
    return 0.0


def _overlap_seconds(intervals):
    """Sum of pairwise overlaps is wrong for delivery; return total overlapped coverage depth>1."""
    if not intervals:
        return 0.0
    points = []
    for start, end in intervals:
        if end is None or end < start:
            continue
        points.append((start, 1))
        points.append((end, -1))
    points.sort()
    depth = 0
    last = None
    overlapped = 0
    for stamp, delta in points:
        if last is not None and depth > 1:
            overlapped += stamp - last
        depth += delta
        last = stamp
    return overlapped / 1e9


def finalize(project, run_key, *, outcome=None, overhead=None):
    """Write report.json and report.md. outcome: finish|abort|fail|partial. Returns report or None.

    When outcome is omitted, keep a prior report's outcome if present; else finish.
    """
    try:
        folder = run_dir(project, run_key)
        meta = {}
        meta_path = folder / META_NAME
        report_path = folder / REPORT_JSON
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        prior_outcome = None
        if report_path.is_file():
            try:
                prior_outcome = json.loads(report_path.read_text(encoding="utf-8")).get("outcome")
            except (OSError, ValueError):
                prior_outcome = None
        chosen = outcome or prior_outcome or "finish"
        terminal = {"finish": "run.finish", "abort": "run.abort", "fail": "run.fail"}.get(chosen)
        if terminal:
            emit(project, run_key, terminal, event_id=f"run-{chosen}-{_safe_key(run_key)}")
        events = read_events(project, run_key)
        report = aggregate(events, meta=meta, outcome=chosen)
        if overhead:
            report["overhead"] = overhead
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (folder / REPORT_MD).write_text(markdown(report), encoding="utf-8")
        return report
    except Exception as exc:
        _fault(project, run_key, "analytics_unwritable", exc)
        return None


def markdown(report):
    lines = [
        f"# Factory run metrics ({report.get('outcome', 'partial')})",
        "",
        f"- Schema: {report.get('metrics_schema')}",
        f"- Events: {report.get('event_count')}",
        f"- Elapsed seconds (wall): {report.get('elapsed_seconds')}",
        f"- Summed operation seconds: {report.get('summed_operation_seconds')}",
        f"- Overlap seconds: {report.get('overlap_seconds')}",
        f"- Reuse count: {report.get('reuse_count')}",
        "",
        "## Waits",
    ]
    for name, value in sorted((report.get("waits") or {}).items()):
        lines.append(f"- {name}: {value}s")
    lines.extend(["", "## Invalidation"])
    reasons = report.get("invalidation_reasons") or {}
    if not reasons:
        lines.append("- none")
    for reason, count in sorted(reasons.items()):
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Longest operations"])
    for row in report.get("longest_operations") or []:
        lines.append(f"- {row.get('name')}: {row.get('duration_seconds')}s reused={row.get('reused')}")
    lines.extend(["", "## Coverage gaps"])
    gaps = report.get("coverage_gaps") or []
    if not gaps:
        lines.append("- none")
    for gap in gaps:
        lines.append(f"- {gap.get('gap')}: {gap.get('detail')}")
    lines.extend(["", "## Incomplete spans"])
    incomplete = report.get("incomplete_spans") or []
    if not incomplete:
        lines.append("- none")
    for row in incomplete:
        lines.append(f"- {row}")
    if report.get("costs"):
        lines.extend(["", "## Costs (host-attributed only)"])
        for cost in report["costs"]:
            lines.append(
                f"- {cost.get('amount')} {cost.get('units')} "
                f"provenance={cost.get('provenance')} scope={cost.get('scope')}"
            )
    lines.extend(["", "## Overhead budget", json.dumps(report.get("overhead_budget") or {}, indent=2)])
    if report.get("overhead"):
        lines.extend(["", "## Measured overhead", json.dumps(report["overhead"], indent=2)])
    lines.extend(["", "## Duration notes"])
    for key, note in (report.get("duration_notes") or {}).items():
        lines.append(f"- {key}: {note}")
    lines.append("")
    return "\n".join(lines)


def compare(project, run_keys):
    """Compare completed runs with matching meta context. No causation claims."""
    rows = []
    for key in run_keys:
        folder = run_dir(project, key)
        report_path = folder / REPORT_JSON
        meta_path = folder / META_NAME
        if not report_path.is_file():
            rows.append({"run_key": key, "status": "missing_report"})
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
        rows.append({
            "run_key": key,
            "status": report.get("outcome"),
            "factory_revision": meta.get("factory_revision"),
            "platform": meta.get("platform"),
            "kind": meta.get("kind"),
            "mode": meta.get("mode"),
            "elapsed_seconds": report.get("elapsed_seconds"),
            "summed_operation_seconds": report.get("summed_operation_seconds"),
            "overlap_seconds": report.get("overlap_seconds"),
            "reuse_count": report.get("reuse_count"),
            "invalidation_reasons": report.get("invalidation_reasons"),
            "coverage_gap_count": len(report.get("coverage_gaps") or []),
            "event_count": report.get("event_count"),
            "incomplete": len(report.get("incomplete_spans") or []),
        })
    contexts = {
        (row.get("factory_revision"), row.get("platform"), row.get("kind"), row.get("mode"))
        for row in rows if row.get("status") not in (None, "missing_report")
    }
    return {
        "metrics_schema": METRICS_SCHEMA,
        "sample_size": len([r for r in rows if r.get("status") != "missing_report"]),
        "requested": len(run_keys),
        "matching_context_groups": len(contexts),
        "note": "Highlights timing/rework/quality deltas; does not claim causation; "
                "do not sum overlapping work into delivery time.",
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
        "within_budget": p99 <= OVERHEAD_BUDGET["event_append_p99_ms"]
        and generate_ms <= OVERHEAD_BUDGET["report_generate_ms_at_10k"]
        and collection_seconds <= whole_cap,
        "event_count": report.get("event_count") if report else None,
    }
    if report is not None:
        report["overhead"] = result
        path = run_dir(project, run_key) / REPORT_JSON
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (run_dir(project, run_key) / REPORT_MD).write_text(markdown(report), encoding="utf-8")
    return result


def _seen_ids(path):
    key = str(path)
    cached = _SEEN_IDS.get(key)
    if cached is not None:
        return cached
    found = set()
    if path.is_file():
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(row, dict) and row.get("event_id"):
                        found.add(row["event_id"])
        except OSError:
            pass
    _SEEN_IDS[key] = found
    return found


def _has_event_id(path, event_id):
    return event_id in _seen_ids(path)


def _line_count(path):
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for _ in handle:
            count += 1
    return count


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
    token = _CURRENT.set({"project": str(Path(project).resolve()), "run_key": run_key, "meta": meta})
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
    return emit(ctx["project"], ctx["run_key"], event_type, **fields)
