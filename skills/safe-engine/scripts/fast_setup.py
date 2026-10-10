"""Start-time probes for fast_gate.py: keep run records out of Git, and report which hosts call the gate."""
import json
from pathlib import Path


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
    gitignore = Path(project) / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    gitignore.write_text(text + ("\n" if text and not text.endswith("\n") else "") + ".factory/\n", encoding="utf-8")
    return "added .factory/ to .gitignore"


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
