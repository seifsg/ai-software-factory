"""Run setup for fast_gate.py: keep run records out of Git (and the ignore line in place), report which hosts call
the gate."""
import json
from pathlib import Path

LINE = ".factory/"  # the .gitignore line that keeps run records out of Git


def ignore_factory(project):
    """Keep run records out of Git: add .factory/ to .gitignore when Git would track it."""
    import subprocess
    try:
        probe = subprocess.run(["git", "-C", str(project), "check-ignore", "-q", ".factory/fast/run.json"],
                               capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return "not checked (git unavailable)"
    if probe.returncode == 0:
        return ".factory/ already ignored"
    if probe.returncode != 1:
        return "not a Git repository; keep .factory/ out of version control"
    if restore_line(project):
        return "added .factory/ to .gitignore"
    return "Git tracks .factory/ although .gitignore names it, or .gitignore is unreadable; keep it out of Git"


def gitignore_text(project):
    """The project's .gitignore ("" when missing), or None when it cannot be read: it is never overwritten then."""
    try:
        return (Path(project) / ".gitignore").read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except (OSError, ValueError):
        return None


def named(text):
    return text is not None and LINE in {line.strip() for line in text.splitlines()}


def has_line(project):
    return named(gitignore_text(project))


def restore_line(project):
    """Append the .factory/ line when a readable .gitignore lacks it; True when it did. Write errors are the caller's."""
    text = gitignore_text(project)
    if text is None or named(text):
        return False
    (Path(project) / ".gitignore").write_text(text + ("\n" if text and not text.endswith("\n") else "") + LINE + "\n",
                                              encoding="utf-8")
    return True


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
