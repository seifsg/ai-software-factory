"""Keep a new run's selected methods and executing gate together; resumes never fetch."""
import json
import os
from pathlib import Path
import subprocess
import sys

def gate_path(bundle):
    """A selected bundle must supply its own gate; never substitute installed behavior."""
    path = Path(bundle["root"]) / "skills/safe-engine/scripts/fast_gate.py"
    if not path.is_file():
        raise RuntimeError(f"Selected factory has no gate at {path}; preserve the pin and resolve compatibility")
    return path.resolve()


def selected_command(gate, project):
    """Read the active run identity before the receipt; missing state keeps legacy gate handling."""
    entry = gate.registry_path(project)
    state = gate.store.state_path(entry)
    if entry.exists() and not state.exists():
        return None  # Lost run identity cannot be replaced by a receipt's gate.
    if state.exists():
        try:
            run = gate.store.current(gate.load(state))
        except (OSError, ValueError):
            return None  # The original gate owns lost-state diagnosis and owner-close recovery.
        bundle = run.get("bundle") if run else None
    else:
        bundle = gate.bundle_receipt(project)
    if not bundle:
        return None
    target = gate_path(bundle)
    return target if target != (gate.HERE / "fast_gate.py").resolve() else None


def route(args, gate):
    """Forward project commands to the pinned gate before installed argument validation."""
    commands = {"done", "status", "close", "try", "scratch", "pause", "resume", "shots", "lane", "wait", "cleanup-temp", "recover-baseline",
                "design", "show", "prove", "fix-round", "checks"}
    options = args[:args.index("--")] if "--" in args else args
    if not options or options[0] not in commands or {"-h", "--help"} & set(options):
        return None
    project = next((arg.split("=", 1)[1] for arg in options if arg.startswith("--project=")), None)
    if "--project" in options and options.index("--project") + 1 < len(options):
        project = options[options.index("--project") + 1]
    project = Path(gate.native(project)).resolve() if project else gate.find_project(None)
    target = selected_command(gate, project)
    return subprocess.call([sys.executable, str(target), *args]) if target else None


def hook(host, raw, event, runs, gate):
    """Route all affected/bound work; mixed factories require separate tool calls, never weaker rules."""
    cwd = gate.norm(event["cwd"] or os.getcwd())
    relevant = hook_runs(event, runs, cwd, gate)
    if not relevant:
        return None
    current = (gate.HERE / "fast_gate.py").resolve()
    targets = {gate_path(item[2]["bundle"]) if item[2].get("bundle") else current for item in relevant}
    if len(targets) > 1:
        hosts = gate.sibling("fast_hosts")
        reason = "This event spans runs using different factory versions; use a separate session and tool call per project."
        out, code = None, 0
        if event["kind"] == "pre_tool":
            out, code = hosts.deny(host, reason)
            if out is None:
                print(reason, file=sys.stderr)
        elif event["kind"] == "stop":
            if not event["again"]:
                if gate.sibling("fast_wait").blocked(event, relevant, event["session"], gate):
                    out = hosts.keep_going(host, reason)
                elif event.get("wait_message"):
                    out = hosts.with_message(None, event["wait_message"])
        else:
            out = hosts.context(host, event["name"], reason)
        if out:
            print(out)
        return code
    target = targets.pop()
    if target == (gate.HERE / "fast_gate.py").resolve():
        return None
    return subprocess.run([sys.executable, str(target), "hook", "--host", host],
                          input=json.dumps(raw).encode("utf-8")).returncode


def hook_runs(event, runs, cwd, gate):
    """Use the gate's ownership and shell-path rules, including work outside the event cwd."""
    relevant = gate.mine(runs, cwd, event["session"], bind_cwd=False)
    targets = [cwd]
    if event["tool"] == "edit":
        targets += [gate.norm(path, cwd) for path in event["paths"]]
    elif event["tool"] == "shell":
        targets += [gate.norm(path, gate.where(cds, cwd)) for cds, path in gate.sibling("fast_shell").writes(event["command"])]
        relevant += [item for item in runs if gate.mentioned([item], event["command"])]
    for path in targets:
        item = gate.owner(runs, path)
        if item and item not in relevant:
            relevant.append(item)
        elif any(gate.inside(path, gate.norm(folder)) for folder in (gate.ACTIVE, gate.HOME / "runs", gate.HOME / "pr-proof", gate.HOME / "waits")):
            if runs and not relevant:
                relevant.append(runs[0])
    return relevant


def summary(result):
    """Distinguish selected identity, advertised release, and a failed or skipped check."""
    latest = result.get("latest_release") or result.get("release") or "unknown (not checked or unavailable)"
    return (f"Factory selected: {result.get('version') or 'unversioned'} at {result['revision']}\n"
            f"Latest release: {latest}\n" + (result.get("notice", "") + "\n" if result.get("notice") else ""))


def start(args, gate):
    """Hold selection through state creation; the selected gate owns all subsequent steps."""
    import resolve_bundle as release
    project = Path(gate.native(args.project or os.getcwd())).resolve()
    if not project.is_dir() or not gate.KEY.fullmatch(args.key):
        return gate.cmd_start(args)  # Preserve the existing precise validation, without resolving anything.
    request = Path(args.request_file).read_text(encoding="utf-8") if args.request_file else args.request
    if not request or not request.strip():
        return gate.cmd_start(args)
    with release.selection_lock(project):
        if gate.registry_path(project).is_file():
            return gate.cmd_start(args)  # Keep the gate's precise recovery instructions for open/lost runs.
        held = release.active_selection(project)
        if held:
            raise RuntimeError(f"Run still open or unknown: {held}; resume or close it without changing its factory")
        receipt = project / ".factory/entry-bundle.json"
        local = project if project == gate.HERE.parents[2] and (project / "safe_engine/distribution.py").is_file() else None
        if local:
            release.inspect_bundle(local)  # Verify canonical source identity before treating this as maintenance.
        if not receipt.exists() and not local:
            return gate.cmd_start(args)  # Compatibility for older bare-gate callers, never a freshness claim.
        result = release.select_locked(project, local if not receipt.exists() else None, None,
                                       gate.HOME / "bundles", "safe-engine", new_run=True)
        print(summary(result), end="", flush=True)
        target = gate_path({"root": result["bundle_root"]})
        if target == (gate.HERE / "fast_gate.py").resolve():
            return gate.cmd_start(args)
        # A separate interpreter prevents installed helper modules leaking into the selected gate.
        code = ("import json,sys,types;sys.path.insert(0,sys.argv[1]);import fast_gate;"
                "fast_gate.cmd_start(types.SimpleNamespace(**json.loads(sys.argv[2])))")
        status = subprocess.call([sys.executable, "-X", "utf8", "-c", code, str(target.parent), json.dumps(vars(args))])
        if status:
            raise RuntimeError(f"Selected factory start failed (exit {status}); selection retained for diagnosis")
