"""Run setup for fast_gate.py: keep run records out of Git, report which hosts call the gate, and keep the run's
scratch folder for throwaway data."""
import json
import os
import re
import stat
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


KEY = re.compile(r"[a-z][a-z0-9-]{0,63}")  # fast_gate.py's run key rule, checked again: a state may come from a mirror
TEXT = ("Scratch: {} (the run's throwaway data: point TMPDIR, TEMP and TMP at it for tools and name it by this literal "
        "path in deletes; rm -r (Bash, / separators) or rd /s alone in its command pass inside it; close removes "
        "it)")


def scratch_path(home, run):
    """The run's own folder for throwaway data (test homes, browser profiles, spare servers), outside every project:
    <home>/scratch/<key>-<project tag>-<start stamp>. Derived, never stored, so no state can point it elsewhere; the
    tag keeps two projects' runs apart and the stamp keeps a new start from reusing an old folder. None when the key,
    start time or project does not hold."""
    key, stamp = str(run.get("key")), re.sub(r"\D", "", str(run.get("created")))[:14]
    if not KEY.fullmatch(key) or len(stamp) < 14 or not run.get("project"):
        return None
    return Path(home, "scratch", f"{key}-{tag(run['project'])}-{stamp}")


def tag(project):
    """Short hash of the project folder, as the gate home names its registration."""
    import hashlib
    from fast_ledger import norm
    return hashlib.sha1(norm(project).encode("utf-8")).hexdigest()[:8]


def lost_scratch(home, key, project):
    """Scratch folders of a project's run under key: for closing a run whose state, and so its start time, is gone."""
    return sorted(Path(home, "scratch").glob(f"{key}-{tag(project)}-*")) if KEY.fullmatch(str(key)) else []


def remove(path, left):
    """Delete path without following links: a symlink or junction goes as the link itself, a folder after its
    contents. What stays is appended to left as "path: error"."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return
    except OSError as error:
        left.append(f"{path}: {error}")
        return
    link = stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    folder = stat.S_ISDIR(info.st_mode) and not link
    try:
        if folder and os.name != "nt" and info.st_mode & stat.S_IRWXU != stat.S_IRWXU:
            os.chmod(path, info.st_mode | stat.S_IRWXU)  # a read-only folder (a module cache): its entries can go
        if folder:
            for entry in [entry.path for entry in os.scandir(path)]:
                remove(entry, left)
        unlinked(path, folder, link)
    except (OSError, RecursionError) as error:  # deeper than Python's stack: named, never half-silent
        left.append(f"{path}: {error!r}" if isinstance(error, RecursionError) else f"{path}: {error}")


def unlinked(path, folder, link):
    """Remove one emptied folder, file or link. A Windows directory link goes with rmdir; a read-only file or folder
    (never a link: chmod would follow it) is made writable and tried once more."""
    gone = os.rmdir if folder else os.unlink
    try:
        gone(path)
    except FileNotFoundError:
        pass
    except OSError:
        if link:
            os.rmdir(path)
        else:
            os.chmod(path, stat.S_IWRITE)
            gone(path)
