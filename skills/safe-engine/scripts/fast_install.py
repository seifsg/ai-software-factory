"""Per-host installer: put the factory's entry skills where the host finds them and wire the Fast gate hooks.

fast_gate.py install --host claude|codex|cursor|other [--project DIR]
- claude: declares this repository's marketplace and enables the safe-engine plugin in ~/.claude/settings.json;
  the plugin carries the skills and hooks.
- codex, cursor: copies skills/safe-engine and skills/improve-factory into ~/.agents/skills (the Agent Skills
  folder both read; <DIR>/.agents/skills with --project). New Codex user installs copy skills only; project
  installs wire scoped hooks. Existing user hooks stay installed until explicitly removed. Cursor keeps its route.
- other: the skills only, for agents wired by hand (docs/hosts.md).
"""
import json
import os
from pathlib import Path
import shutil


def ledger():
    """Load the existing state/path module beside the installer, including standalone module consumers."""
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("fast_ledger", Path(__file__).with_name("fast_ledger.py"))
    module = importlib.util.module_from_spec(spec)
    keep = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = keep
    return module

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
            if project:
                written.append(merge_codex(base / ".codex" / "hooks.json", gate, project))
            elif factory_hooks(home / ".codex" / "hooks.json"):
                log("retained existing user hook scope; migrate explicitly after closing unfinished runs")
            else:
                log("global skills installed; configure project hooks: fast_gate.py hooks --host codex --project <dir>")
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


# Python run as `python -c BOOT <gate folder> <host>`: imports the gate from its bytecode cache in the gate home.
# The stdlib it needs loads first, so only the gate's own cache lives there. run-gate.sh holds the same text.
HOME_PY = "import os,sys;h=os.environ.get('SAFE_ENGINE_HOME') or os.path.join(os.path.expanduser('~'),'.safe-engine');"
RUN_PY = ("import json,re,pathlib;d=sys.argv[1];sys.dont_write_bytecode=False;"
          "sys.pycache_prefix=os.path.join(h,'pycache');sys.path.insert(0,d);"
          "sys.argv=[os.path.join(d,'fast_gate.py'),'hook','--host',sys.argv[2]]+"
          "(['--scope',sys.argv[3]] if len(sys.argv)>3 and sys.argv[3] else []);import fast_gate;fast_gate.main()")
BOOT = HOME_PY + RUN_PY
# Windows hosts run no POSIX shell: Python itself leaves at once without a registered or open run, or a gate
GUARD_PY = ("d=sys.argv[1];any(n.endswith('.json') for s in ('active','runs') for n in (os.listdir(os.path.join(h,s)) "
            "if os.path.isdir(os.path.join(h,s)) else ())) and os.path.isfile(os.path.join(d,'fast_gate.py')) "
            "or sys.exit(0);")


def commands(gate, host):
    """(POSIX command, Windows command). Windows calls Python directly, guarded: no active run or no gate exits 0."""
    posix = f'sh "{(gate / "run-gate.sh").as_posix()}" {host}'
    python = "py -3" if shutil.which("py") else "python"
    return posix, f'{python} -c "{HOME_PY}{GUARD_PY}{RUN_PY}" "{gate.as_posix()}" {host}'


def ours(command):
    """Recognize this installer's complete legacy/new runtime paths, never a mention in someone else's command."""
    import re
    text = str(command).replace("\\", "/")
    runtime = r'[^"\r\n]+/safe-engine/scripts/'
    legacy = re.fullmatch(r'sh "' + runtime + r'run-gate\.sh" (codex|cursor)', text)
    native = re.fullmatch(r'cmd\.exe /d /v:off /c ""' + runtime + r'run-gate\.cmd" codex [0-9a-f]{16} (py|python)"', text)
    scoped = re.fullmatch(r'sh "' + runtime + r'run-gate\.sh" codex [0-9a-f]{16}', text)
    inline = re.fullmatch(re.escape(PS_HEAD) + r"[0-9a-f]{16}" + re.escape(PS_MIDDLE) +
                          r"[0-9a-f]{16}" + re.escape(PS_RUNTIME) + r"(?:[^'\r\n]|'')+/safe-engine/scripts/fast_gate\.py" +
                          re.escape(PS_DISPATCH) + r"(py -3|python) -c '" + re.escape(BOOT.replace("'", "''")) +
                          r"' '(?:[^'\r\n]|'')+/safe-engine/scripts' codex [0-9a-f]{16}" + re.escape(PS_END), text)
    legacy_run = RUN_PY.replace("+(['--scope',sys.argv[3]] if len(sys.argv)>3 and sys.argv[3] else [])", "")
    windows = any(re.fullmatch(r'(py -3|python) -c "' + re.escape(HOME_PY + GUARD_PY + boot) +
                              r'" "' + runtime.rstrip("/") + r'" (codex|cursor)', text)
                  for boot in (RUN_PY, legacy_run))
    return bool(legacy or native or scoped or inline or windows)


def merge_codex(path, gate, project=None):
    """Claude-style hooks.json: replace the factory's matcher groups per event, keep everything else."""
    posix, windows = scoped_commands(gate, project) if project else commands(gate, "codex")
    data = codex_data(path)
    events = data.setdefault("hooks", {})
    for event, matcher in CODEX_EVENTS.items():
        groups = without_factory(events.get(event, []))
        hook = {"type": "command", "command": posix, "commandWindows": windows, "timeout": 30}
        groups.append({**({"matcher": matcher} if matcher else {}), "hooks": [hook]})
        events[event] = groups
    write_json(path, data)
    return path


def without_factory(groups):
    """Keep unrelated handlers, even when they share a matcher group with the factory."""
    result = []
    for group in groups:
        kept = [hook for hook in group.get("hooks", []) if not owned_hook(hook)]
        if kept:
            result.append({**group, "hooks": kept})
    return result


def owned_hook(hook):
    """A recognized base command with no unknown platform override belongs to this installer."""
    return ours(hook.get("command", "")) and all(ours(hook[key]) for key in
        ("commandWindows", "command_windows") if key in hook)


def factory_hooks(path):
    return any(owned_hook(hook) for groups in codex_data(path).get("hooks", {}).values()
               for group in groups for hook in group.get("hooks", []))


def codex_data(path):
    """Validate the hook container before any setup/removal write, preserving unsupported or broken config."""
    data = read_json(path)
    events = data.get("hooks", {})
    if not isinstance(events, dict):
        raise SystemExit("Hook configuration has a non-object hooks field; fix it before setup. The file was preserved")
    for groups in events.values():
        if not isinstance(groups, list) or any(not isinstance(group, dict) or
                not isinstance(group.get("hooks"), list) or any(not isinstance(hook, dict) for hook in group["hooks"])
                for group in groups):
            raise SystemExit("Hook configuration has malformed event groups/handlers; fix it before setup. The file was preserved")
    return data


PS_HEAD = "try{$h=$env:SAFE_ENGINE_HOME;if(!$h){$h=$env:USERPROFILE;if(!$h){$h=$env:HOMEDRIVE+$env:HOMEPATH};$h+='/.safe-engine'};if([IO.File]::Exists([IO.Path]::Combine($h,'active/"
PS_MIDDLE = ".json')) -or [IO.File]::Exists([IO.Path]::Combine($h,'runs/"
PS_RUNTIME = ".json'))){if([IO.File]::Exists('"
PS_DISPATCH = "')){& "
PS_END = " 2>$null}}}catch{};exit 0"


def scoped_commands(gate, project):
    """Bind scope in the trusted definition; native shell only checks its two authoritative home files."""
    store = ledger()
    identity = store.registry_path(Path("active"), project).stem
    gate = Path(gate).resolve()
    # These characters cannot be represented safely in both host-shell and cmd command strings.
    # Other project/home paths are never put into the command: only the normalized hash is passed.
    if any(char in str(gate) for char in '%"$`\r\n'):
        raise SystemExit("Hook runtime path contains shell-expansion characters; use a runtime path without quotes, percent, dollar, backtick or newline")
    posix = f'sh "{(gate / "run-gate.sh").as_posix()}" codex {identity}'
    python = "py -3" if shutil.which("py") else "python"
    literal = lambda value: str(value).replace("'", "''")
    windows = (PS_HEAD + identity + PS_MIDDLE + identity + PS_RUNTIME + literal((gate / "fast_gate.py").as_posix()) +
               PS_DISPATCH + python + " -c '" + literal(BOOT) + "' '" + literal(gate.as_posix()) +
               "' codex " + identity + PS_END)
    return posix, windows


def configure(host, project=None, home=None, remove=False, user=False, log=print):
    """Configure/remove Codex hooks without copying skills or changing a project's pinned bundle."""
    store = ledger()
    if host != "codex" or (user and not remove) or (not user and not project):
        raise SystemExit("Use hooks --host codex --project <dir> [--remove], or hooks --host codex --remove --user")
    home = Path(home or Path.home())
    base = home if user else Path(project).resolve()
    if not base.is_dir():
        raise SystemExit("Project directory not found; create it before configuring hooks")
    gate_home = Path(os.environ.get("SAFE_ENGINE_HOME") or home / ".safe-engine")
    if not gate_home.is_absolute() or any(char in str(gate_home) for char in '"\r\n'):
        raise SystemExit("SAFE_ENGINE_HOME must be an absolute path without quotes or newlines; correct the environment before configuring hooks")
    identity = "user" if user else store.registry_path(gate_home / "active", base).stem
    runs = store.active_runs(gate_home / "active", lambda *_args, **_data: None, None if user else identity)
    if remove and runs:
        raise SystemExit("Unfinished runs still need these hooks. Close each run through fast_gate.py close (or an owner-authorized --abandon), then remove hooks")
    path = base / ".codex" / "hooks.json"
    data = codex_data(path)
    receipts = gate_home / "installations"
    receipt = receipts / f"codex-{identity}.json"
    backup = receipts / f"codex-{identity}.hooks-backup.json"
    if path.exists() and not backup.exists():
        write_json(backup, data)
    log("hooks.configure action=" + ("remove" if remove else "project") + " stage=configuration")
    if remove:
        events = data.get("hooks", {})
        for event in CODEX_EVENTS:
            if event in events:
                kept = without_factory(events[event])
                if kept:
                    events[event] = kept
                else:
                    del events[event]
        if path.exists():
            write_json(path, data)
    else:
        merge_codex(path, Path(__file__).resolve().parent, base)
    write_json(receipt, {"version": 1, "host": host, "scope": "user" if user else "project", "project": str(base),
                         "configuration": str(path), "removed": remove, "backup": str(backup) if backup.exists() else None})
    log("hooks.configured status=" + ("removed" if remove else "configured; review project and exact-hook trust, then load a fresh session"))
    return [path, receipt]


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
