"""Run setup for fast_gate.py: keep run records out of Git, report which hosts call the gate."""
import json
from pathlib import Path

LINE = ".factory/"  # the exclude line that keeps run records out of Git


def ignore_factory(project):
    """Keep run records out of Git in the clone's own exclude file: no project file changes, and neither a reverted
    .gitignore nor `git clean -fd` can undo it (deletes inside .git are the guard's). A project that already tracks
    files in .factory/ keeps them in Git: excluding the folder would hide every new file there."""
    found = git(project, "rev-parse", "--git-path", "info/exclude")
    if found is None:
        return "not checked (git unavailable)"
    exclude = Path(project, found.stdout.strip())
    if found.returncode != 0 or not found.stdout.strip() or not exclude.parent.parent.is_dir():
        return "not a Git repository; keep .factory/ out of version control"
    tracked = git(project, "ls-files", "--", ".factory")
    if tracked is None or tracked.returncode != 0:
        return "not checked (git ls-files failed); keep .factory/ out of version control"
    if tracked.stdout.strip():
        return ".factory/ is tracked in this repository, so it stays in Git"
    try:
        text = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        if LINE in {line.strip() for line in text.splitlines()}:
            return f".factory/ already excluded in {exclude}"
        exclude.parent.mkdir(exist_ok=True)
        exclude.write_text(text + ("\n" if text and not text.endswith("\n") else "") + LINE + "\n", encoding="utf-8")
    except (OSError, ValueError) as error:  # unreadable or locked: never overwrite it
        return f"could not update {exclude} ({error}); keep .factory/ out of version control"
    return f"added .factory/ to {exclude}"


def git(project, *args):
    """A finished git command run in project, or None when git cannot run at all."""
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True, encoding="utf-8",
                              timeout=20)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


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
            if name not in found and ("fast_gate" in text or "run-gate" in text):
                found.append(name)
    return ", ".join(found) or "none detected: the gate records steps but nothing blocks; follow the order yourself"
