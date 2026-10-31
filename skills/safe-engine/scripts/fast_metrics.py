"""Bridge Fast gate lifecycle to safe_engine.run_metrics (failure-open)."""
from contextlib import nullcontext
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


def identity(run):
    """Separate repeated gate keys by their immutable run instance."""
    instance = run.get("pr_instance")
    if isinstance(instance, str) and len(instance) == 32 and all(char in "0123456789abcdef" for char in instance):
        return f"{run['key'][:31]}-{instance}"
    return run["key"]  # legacy run without an instance


def on_start(project, run, steps):
    key = identity(run)
    revision = (run.get("bundle") or {}).get("revision")
    safe(
        "ensure_run",
        project,
        key,
        factory_revision=revision,
        mode=run.get("mode"),
        kind=run.get("kind"),
        extra={"gate_key": run["key"]},
    )
    first = steps[0] if steps else "tickets"  # research/kickoff come first on product and feature runs
    safe("emit_phase", project, key, first, "start", event_id=f"{key}-phase-{first}-start")


def on_done(project, run, step, steps):
    key = identity(run)
    if step == "tickets":
        safe("set_scope", project, key, run.get("tickets"))
    elif step == "plan":
        for task_id in run.get("todos", []):
            safe("emit_task", project, key, task_id, "declare",
                 event_id=f"{key}-task-{task_id}-declare")
    safe(
        "emit_phase",
        project,
        key,
        step,
        "finish",
        event_id=f"{key}-phase-{step}-finish",
    )
    remaining = [name for name in steps if name not in run.get("done", {}) and name != step]
    if remaining:
        nxt = remaining[0]
        safe(
            "emit_phase",
            project,
            key,
            nxt,
            "start",
            event_id=f"{key}-phase-{nxt}-start",
        )


def on_pause(project, run, reason, prior_pause=None):
    key = identity(run)
    if reason:
        stamp = (run.get("paused") or {}).get("at") or "open"
        wait_id = f"{key}-owner-wait-{stamp}"
        safe(
            "emit_wait",
            project,
            key,
            "start",
            "owner",
            event_id=wait_id,
        )
        return
    stamp = (prior_pause or {}).get("at") or "unknown"
    wait_id = f"{key}-owner-wait-{stamp}"
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
    safe("emit_wait", project, key, "finish", "owner", **fields)


def on_show(project, run, action, shared=None, status=None):
    """Measure the observed owner response window without implying approval."""
    shared = shared or (run.get("show") or {}).get("shared")
    if not isinstance(shared, dict) or not shared.get("at"):
        return
    key = identity(run)
    wait_id = f"{key}-show-wait-{shared['at']}"
    fields = {"event_id": wait_id if action == "start" else wait_id + "-end"}
    if action != "start":
        fields.update(parent_id=wait_id, status=status or action)
    safe("emit_wait", project, key, action, "approval", **fields)


def on_close(project, run, abandoned):
    outcome = "abort" if abandoned else "finish"
    safe("finalize", project, identity(run), outcome=outcome)


def bind(project, run, task_id=None):
    revision = (run.get("bundle") or {}).get("revision")
    return safe(
        "bound",
        project,
        identity(run),
        factory_revision=revision,
        mode=run.get("mode"),
        kind=run.get("kind"),
        task_id=task_id,
    ) or nullcontext()  # analytics down: the command still runs
