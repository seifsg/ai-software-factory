"""Per-host installer: put the factory's entry skills where the host finds them and wire the Fast gate hooks.

fast_gate.py install --host claude|codex|cursor|other [--project DIR]
- claude: declares this repository's marketplace and enables the safe-engine plugin in ~/.claude/settings.json;
  the plugin carries the skills and hooks.
- codex, cursor: copies skills/safe-engine and skills/improve-factory into ~/.agents/skills (the Agent Skills
  folder both read; <DIR>/.agents/skills with --project), then merges the gate hooks into ~/.codex/hooks.json or
  ~/.cursor/hooks.json (<DIR>/.codex, <DIR>/.cursor). Re-running replaces only the factory's own hook entries.
- other: the skills only, for agents wired by hand (docs/hosts.md#other-agents).
"""
import json
import os
from pathlib import Path
import shutil

MARKETPLACE = "ai-software-factory"
REPOSITORY = "https://github.com/seifsg/ai-software-factory.git"
ENTRIES = ("safe-engine", "improve-factory")
MARKER = ".safe-engine-install"  # marks copies this installer owns; anything else is never overwritten
CODEX_EVENTS = {"PreToolUse": "Bash|apply_patch", "Stop": None, "UserPromptSubmit": None, "SessionStart": None}
CURSOR_EVENTS = {"preToolUse": "Shell|Write|Delete|Edit|StrReplace|MultiEdit", "stop": None, "sessionStart": None}


def install(host, project=None, home=None, log=print):
    """Install for one host; returns the files written."""
    home = Path(home or Path.home())
    if host == "claude":
        written = [enable_plugin(home / ".claude" / "settings.json")]
    elif host in ("codex", "cursor", "other"):
        base = Path(project).resolve() if project else home
        skills = copy_entries(base / ".agents" / "skills")
        written = [skills / name for name in ENTRIES]
        gate = skills / "safe-engine" / "scripts"
        if host == "codex":
            written.append(merge_codex(base / ".codex" / "hooks.json", gate))
        elif host == "cursor":
            written.append(merge_cursor(base / ".cursor" / "hooks.json", gate))
    else:
        raise SystemExit(f"Unknown host '{host}': claude, codex, cursor or other (docs/hosts.md)")
    for path in written:
        log(f"wrote {path}")
    return written


def enable_plugin(settings):
    """Marketplace over HTTPS with your stored Git credentials (no SSH key needed), auto-update, plugin enabled."""
    data = read_json(settings)
    if settings.exists():
        backup = settings.with_name(settings.name + ".bak-before-safe-engine")
        if not backup.exists():
            shutil.copyfile(settings, backup)
    data.setdefault("extraKnownMarketplaces", {})[MARKETPLACE] = {
        "source": {"source": "git", "url": REPOSITORY}, "autoUpdate": True}
    data.setdefault("enabledPlugins", {})[f"safe-engine@{MARKETPLACE}"] = True
    write_json(settings, data)
    return settings


def copy_entries(target):
    """The two portable entries from this bundle, without caches. Refuses folders it did not install
    (such as the factory's own canonical .agents/skills methods)."""
    source = Path(__file__).resolve().parents[2]  # .../skills
    for name in ENTRIES:
        destination = target / name
        if (destination / "SKILL.md").exists() and not (destination / MARKER).exists():
            raise SystemExit(f"{destination} holds a skill this installer did not write; refusing to overwrite it")
    for name in ENTRIES:
        destination = target / name
        shutil.copytree(source / name, destination, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (destination / MARKER).write_text(f"installed from {source / name}\n", encoding="utf-8")
    return target


def commands(gate, host):
    """(POSIX command, Windows command). Windows calls Python directly, guarded: a missing gate exits 0."""
    posix = f'sh "{(gate / "run-gate.sh").as_posix()}" {host}'
    script = (gate / "fast_gate.py").as_posix()
    guarded = (f"import os,runpy,sys;p=r'{script}';sys.argv=[p,'hook','--host','{host}'];"
               "os.path.exists(p) and runpy.run_path(p,run_name='__main__')")
    python = "py -3" if shutil.which("py") else "python"
    return posix, f'{python} -c "{guarded}"'


def ours(command):
    return "fast_gate" in command or "run-gate" in command


def merge_codex(path, gate):
    """Claude-style hooks.json: replace the factory's matcher groups per event, keep everything else."""
    posix, windows = commands(gate, "codex")
    data = read_json(path)
    events = data.setdefault("hooks", {})
    for event, matcher in CODEX_EVENTS.items():
        groups = [group for group in events.get(event, [])
                  if not any(ours(str(hook.get("command", ""))) for hook in group.get("hooks", []))]
        hook = {"type": "command", "command": posix, "commandWindows": windows, "timeout": 30}
        groups.append({**({"matcher": matcher} if matcher else {}), "hooks": [hook]})
        events[event] = groups
    write_json(path, data)
    return path


def merge_cursor(path, gate):
    """Cursor hooks.json (version 1): replace the factory's entries per event, keep everything else."""
    posix, windows = commands(gate, "cursor")
    command = windows if os.name == "nt" else posix
    data = read_json(path)
    data.setdefault("version", 1)
    events = data.setdefault("hooks", {})
    for event, matcher in CURSOR_EVENTS.items():
        entries = [entry for entry in events.get(event, []) if not ours(str(entry.get("command", "")))]
        entries.append({"command": command, **({"matcher": matcher} if matcher else {})})
        events[event] = entries
    write_json(path, data)
    return path


def read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        raise SystemExit(f"{path} is not a JSON object; fix it before installing")
    return data


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)
