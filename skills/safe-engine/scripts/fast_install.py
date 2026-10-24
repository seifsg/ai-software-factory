"""Per-host installer: put the factory's entry skills where the host finds them and wire the Fast gate hooks.

fast_gate.py install --host claude|codex|cursor|other [--project DIR] [--no-auto-update] [--channel stable|edge]
- claude: declares this repository's marketplace and enables the safe-engine plugin in ~/.claude/settings.json;
  the plugin carries the skills and hooks and follows release tags.
- codex, cursor: copies skills/safe-engine and skills/improve-factory into ~/.agents/skills (the Agent Skills
  folder both read; <DIR>/.agents/skills with --project), then merges the gate hooks into ~/.codex/hooks.json or
  ~/.cursor/hooks.json (<DIR>/.codex, <DIR>/.cursor). Re-running replaces only the factory's own hook entries.
- other: the skills only, for agents wired by hand (docs/hosts.md).
Every host records the machine's update channel in the gate home (stable: release tags; edge: main), which new
projects and the self-update follow. Installed from a Git clone, codex, cursor and other also record the clone: their
session-start hook then updates them once a day (fast_update.py).
"""
import json
import os
from pathlib import Path
import shutil
import subprocess

CHANNELS = ("stable", "edge")  # the first is the default
MARKETPLACE = "ai-software-factory"
REPOSITORY = "https://github.com/seifsg/ai-software-factory.git"
ENTRIES = ("safe-engine", "improve-factory")
MARKER = ".safe-engine-install"  # marks copies this installer owns; anything else is never overwritten
CODEX_EVENTS = {"PreToolUse": "Bash|apply_patch", "Stop": None, "UserPromptSubmit": None, "SessionStart": None}
CURSOR_EVENTS = {"preToolUse": "Shell|Write|Delete|Edit|StrReplace|MultiEdit", "stop": None, "sessionStart": None}


def parser(sub):
    """The `install` subcommand (fast_gate.py)."""
    install = sub.add_parser("install", help="Install the entry skills and gate hooks for one host")
    install.add_argument("--host", required=True, choices=("claude", "codex", "cursor", "other"),
                         help="other: entry skills only, for agents you wire by hand")
    install.add_argument("--project", help="Install into this project instead of your user folders")
    install.add_argument("--no-auto-update", dest="auto", action="store_false",
                         help="No daily self-update at session start (also SAFE_ENGINE_NO_UPDATE=1)")
    install.add_argument("--channel", choices=CHANNELS, help="stable: the newest verified release (default); edge: "
                                                             "main. Kept for this machine until changed")


def install(host, project=None, home=None, log=print, auto=True, channel=None):
    """Install for one host; returns the files written. auto=False turns the daily self-update off; channel None
    keeps the recorded channel (stable when none)."""
    home = Path(home or Path.home())
    if host == "claude":
        written = [enable_plugin(home / ".claude" / "settings.json")]
    elif host in ("codex", "cursor", "other"):
        base = Path(project).resolve() if project else home
        skills = copy_entries(base / ".agents" / "skills")
        written = [skills / name for name in ENTRIES]
        gate = skills / "safe-engine" / "scripts"
        if host == "codex":
            written.append(merge_codex(base / ".codex" / "hooks.json", gate, auto))
        elif host == "cursor":
            written.append(merge_cursor(base / ".cursor" / "hooks.json", gate, auto))
    else:
        raise SystemExit(f"Unknown host '{host}': claude, codex, cursor or other (docs/hosts.md)")
    written.append(remember(host, project, home, auto, channel))
    for path in filter(None, written):
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
    """The two portable entries from this bundle, without caches, so each copy equals its release exactly (files a
    release dropped go too). Refuses folders it did not install (such as the factory's own .agents/skills methods)."""
    source = Path(__file__).resolve().parents[2]  # .../skills
    for name in ENTRIES:
        destination = target / name
        if (destination / "SKILL.md").exists() and not (destination / MARKER).exists():
            raise SystemExit(f"{destination} holds a skill this installer did not write; refusing to overwrite it")
    for name in ENTRIES:
        destination = target / name
        shutil.copytree(source / name, destination, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for path in sorted(destination.rglob("*"), reverse=True):  # deepest first, so emptied folders go too
            relative = path.relative_to(destination)
            if path.name == MARKER or "__pycache__" in relative.parts or (source / name / relative).exists():
                continue
            if not path.is_dir():
                path.unlink()
            elif not any(path.iterdir()):
                path.rmdir()
        (destination / MARKER).write_text(f"installed from {source / name}\n", encoding="utf-8")
    return target


def remember(host, project, home, auto, channel=None):
    """Record the machine's update channel and, for a host the clone updates, this install's clone, revision and
    targets for the session-start self-update. A copy that is no Git clone, or is a pinned project bundle, records
    only the channel and never updates. Other fields (the updater's previous revision) are kept."""
    root = Path(__file__).resolve().parents[3]
    gate_home = Path(os.environ.get("SAFE_ENGINE_HOME") or home / ".safe-engine")
    path = gate_home / "install.json"
    record = read_json(path)
    record["channel"] = channel or record.get("channel") or CHANNELS[0]
    if host != "claude" and (root / ".git").exists() and (gate_home / "bundles").resolve() not in root.parents:
        try:
            revision = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True,
                                      timeout=15, check=True, stdin=subprocess.DEVNULL).stdout.strip()
        except (OSError, subprocess.SubprocessError):  # no git here: the first daily check reinstalls
            revision = None
        item = {"host": host, "project": str(Path(project).resolve()) if project else None}
        installs = [old for old in record.get("installs", []) if old != item] + [item]
        record.update(clone=str(root), revision=revision, auto=auto, installs=installs)
    write_json(path, record)
    return path


# Python run as `python -c BOOT <gate folder> <host>`: imports the gate from its bytecode cache in the gate home.
# The stdlib it needs loads first, so only the gate's own cache lives there. run-gate.sh holds the same text.
HOME_PY = "import os,sys;h=os.environ.get('SAFE_ENGINE_HOME') or os.path.join(os.path.expanduser('~'),'.safe-engine');"
RUN_PY = ("import json,re,pathlib;d=sys.argv[1];sys.dont_write_bytecode=False;"
          "sys.pycache_prefix=os.path.join(h,'pycache');sys.path.insert(0,d);"
          "sys.argv=[os.path.join(d,'fast_gate.py'),'hook','--host',sys.argv[2]];import fast_gate;fast_gate.main()")
BOOT = HOME_PY + RUN_PY
# Session start only (an `update` argument): the daily self-update runs first, so the gate loads the new copy
UPDATE_PY = ("sys.argv[3:]==['update'] and not os.environ.get('SAFE_ENGINE_NO_UPDATE') and "
             "os.path.isfile(os.path.join(h,'install.json')) and __import__('subprocess').call("
             "[sys.executable,os.path.join(sys.argv[1],'fast_update.py')],stdin=-3,stdout=-3,stderr=-3);")  # -3: DEVNULL
# Windows hosts run no POSIX shell: Python itself leaves at once without a registered or open run, or a gate
GUARD_PY = ("d=sys.argv[1];any(n.endswith('.json') for s in ('active','runs') for n in (os.listdir(os.path.join(h,s)) "
            "if os.path.isdir(os.path.join(h,s)) else ())) and os.path.isfile(os.path.join(d,'fast_gate.py')) "
            "or sys.exit(0);")


def commands(gate, host, update=False):
    """(POSIX command, Windows command). Windows calls Python directly, guarded: no active run or no gate exits 0.
    update: the session-start entry, which first runs the daily self-update."""
    tail = f"{host} update" if update else host
    posix = f'sh "{(gate / "run-gate.sh").as_posix()}" {tail}'
    python = "py -3" if shutil.which("py") else "python"
    return posix, f'{python} -c "{HOME_PY}{UPDATE_PY if update else ""}{GUARD_PY}{RUN_PY}" "{gate.as_posix()}" {tail}'


def ours(command):
    return "fast_gate" in command or "run-gate" in command


def merge_codex(path, gate, auto=True):
    """Claude-style hooks.json: replace the factory's matcher groups per event, keep everything else."""
    data = read_json(path)
    events = data.setdefault("hooks", {})
    for event, matcher in CODEX_EVENTS.items():
        posix, windows = commands(gate, "codex", auto and event == "SessionStart")
        groups = [group for group in events.get(event, [])
                  if not any(ours(str(hook.get("command", ""))) for hook in group.get("hooks", []))]
        hook = {"type": "command", "command": posix, "commandWindows": windows, "timeout": 30}
        groups.append({**({"matcher": matcher} if matcher else {}), "hooks": [hook]})
        events[event] = groups
    write_json(path, data)
    return path


def merge_cursor(path, gate, auto=True):
    """Cursor hooks.json (version 1): replace the factory's entries per event, keep everything else."""
    data = read_json(path)
    data.setdefault("version", 1)
    events = data.setdefault("hooks", {})
    for event, matcher in CURSOR_EVENTS.items():
        command = commands(gate, "cursor", auto and event == "sessionStart")[os.name == "nt"]
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
