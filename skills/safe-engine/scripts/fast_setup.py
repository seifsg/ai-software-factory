"""Run setup for fast_gate.py: keep run records out of Git, report which hosts call the gate."""
import json
from pathlib import Path

LINE = ".factory/"  # the exclude line that keeps run records out of Git


def ignore_factory(project):
    """Keep run records out of Git in the clone's own exclude file: no project file changes, and neither a reverted
    .gitignore nor `git clean -fd` can undo it (deletes inside .git are the guard's)."""
    import subprocess
    try:
        found = subprocess.run(["git", "-C", str(project), "rev-parse", "--git-path", "info/exclude"],
                               capture_output=True, text=True, encoding="utf-8", timeout=20)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return "not checked (git unavailable)"
    exclude = Path(project, found.stdout.strip())
    if found.returncode != 0 or not found.stdout.strip() or not exclude.parent.parent.is_dir():
        return "not a Git repository; keep .factory/ out of version control"
    try:
        text = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        if LINE in {line.strip() for line in text.splitlines()}:
            return f".factory/ already excluded in {exclude}"
        exclude.parent.mkdir(exist_ok=True)
        exclude.write_text(text + ("\n" if text and not text.endswith("\n") else "") + LINE + "\n", encoding="utf-8")
    except (OSError, ValueError) as error:  # unreadable or locked: never overwrite it
        return f"could not update {exclude} ({error}); keep .factory/ out of version control"
    return f"added .factory/ to {exclude}"


def hook_status(project):
    """Hosts wired to call this gate: an enabled Claude Code plugin, or factory entries in Codex/Cursor hook files."""
    home = Path.home()
    found = []
    try:
        plugins = json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8")).get("enabledPlugins", {})
        if any(name.startswith("safe-engine@") and value is True for name, value in plugins.items()):
            found.append("Claude Code")
    except (OSError, ValueError, AttributeError):
        pass
    for name, folder in (("Codex", ".codex"), ("Cursor", ".cursor")):
        for base in (home, Path(project)):
            try:
                text = (base / folder / "hooks.json").read_text(encoding="utf-8")
            except OSError:
                continue
            if "fast_gate" in text or "run-gate" in text or ('"factory_hook"' in text and '"safe_engine_' in text):
                scope = "user (legacy/global)" if base == home else "project"
                found.append(f"{name} {scope}: configured, loading/trust/connection/runtime version unverified")
    note = ", ".join(found) or "none detected: configure project hooks before relying on enforcement; the gate still records steps"
    return note + "; inline/plugin/managed sources may also apply; file discovery does not prove effective host trust"
