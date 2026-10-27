"""Bridge Fast gate lifecycle to safe_engine.run_metrics (failure-open)."""
from pathlib import Path
import sys


def module():
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import safe_engine.run_metrics as metrics
    return metrics


def safe(name, *args, **kwargs):
    try:
        return getattr(module(), name)(*args, **kwargs)
    except Exception as exc:
        try:
            sys.stderr.write(f"fast_metrics: {exc}\n")
        except Exception:
            pass
        return None


def on_start(project, run):
    revision = (run.get("bundle") or {}).get("revision")
    safe(
        "ensure_run",
        project,
        run["key"],
        factory_revision=revision,
        mode=run.get("mode"),
        kind=run.get("kind"),
    )
    safe("emit_phase", project, run["key"], "tickets", "start", event_id=f"{run['key']}-phase-tickets-start")


def on_done(project, run, step, steps):
    safe(
        "emit_phase",
        project,
        run["key"],
        step,
        "finish",
        event_id=f"{run['key']}-phase-{step}-finish",
    )
    remaining = [name for name in steps if name not in run.get("done", {}) and name != step]
    if remaining:
        nxt = remaining[0]
        safe(
            "emit_phase",
            project,
            run["key"],
            nxt,
            "start",
            event_id=f"{run['key']}-phase-{nxt}-start",
        )


def on_pause(project, run, reason, prior_pause=None):
    if reason:
        stamp = (run.get("paused") or {}).get("at") or "open"
        wait_id = f"{run['key']}-owner-wait-{stamp}"
        safe(
            "emit_wait",
            project,
            run["key"],
            "start",
            "owner",
            event_id=wait_id,
            detail=str(reason)[:200],
        )
        return
    stamp = (prior_pause or {}).get("at") or "unknown"
    wait_id = f"{run['key']}-owner-wait-{stamp}"
    duration = None
    try:
        from datetime import datetime
        start = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        end = datetime.fromisoformat(module().utc_now().replace("Z", "+00:00"))
        duration = max(0.0, (end - start).total_seconds())
    except Exception:
        duration = None
    fields = {"event_id": f"{wait_id}-end", "parent_id": wait_id}
    if duration is not None:
        fields["duration_seconds"] = round(duration, 3)
    safe("emit_wait", project, run["key"], "finish", "owner", **fields)


def on_close(project, run, abandoned):
    outcome = "abort" if abandoned else "finish"
    safe("finalize", project, run["key"], outcome=outcome)


def bind(project, run):
    revision = (run.get("bundle") or {}).get("revision")
    return safe(
        "bound",
        project,
        run["key"],
        factory_revision=revision,
        mode=run.get("mode"),
        kind=run.get("kind"),
    )
