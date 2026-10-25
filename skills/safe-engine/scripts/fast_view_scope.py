"""Local project identities and projections for the shared progress view."""
import hashlib
import os
import subprocess
from pathlib import Path

ALL = {"id": "all", "name": "All projects", "project": "", "kind": "all"}
VERSION = 2  # invalidate identities discovered under inherited repository overrides


def identity_stamp(project):
    """Invalidate a saved identity when its nearest Git marker or Git environment changes."""
    folder = Path(project).resolve()
    markers = []
    for parent in (folder, *folder.parents):
        marker = parent / ".git"
        try:
            info = marker.stat()
        except FileNotFoundError:
            continue
        markers = [str(marker), info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size]
        if marker.is_file():
            target = marker.read_text(encoding="utf-8").strip()
            if target.startswith("gitdir: "):
                common = (marker.parent / target[8:]).resolve() / "commondir"
                try:
                    entry = common.stat()
                    markers += [str(common), entry.st_ino, entry.st_mtime_ns, entry.st_size]
                except FileNotFoundError:
                    markers.append(None)
        break
    value = repr((VERSION, markers, sorted((k, v) for k, v in os.environ.items() if k.startswith("GIT_"))))
    key = hashlib.sha256(os.path.normcase(str(folder)).encode("utf-8")).hexdigest()[:24]
    return key, hashlib.sha256(value.encode("utf-8")).hexdigest()


def scope_for(project=None, all_projects=False):
    """Group local worktrees by Git common directory, otherwise use the exact folder."""
    if all_projects:
        return dict(ALL)
    try:
        if project is not None and not str(project).strip():
            raise ValueError("empty folder")
        folder = Path(project if project is not None else os.getcwd()).expanduser().resolve(strict=True)
        if not folder.is_dir():
            raise ValueError("not a folder")
    except (OSError, ValueError, RuntimeError) as error:
        raise ValueError("Project folder is unavailable; use view --project <existing-folder>.") from error
    kind, identity, root = "folder", folder, folder
    try:
        result = subprocess.run(["git", "-C", str(folder), "rev-parse", "--path-format=absolute",
                                 "--git-common-dir", "--show-toplevel"], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=5,
                                env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
        lines = result.stdout.splitlines()
        if result.returncode == 0 and len(lines) == 2:
            identity = Path(lines[0]).resolve()
            root = identity.parent if identity.name == ".git" else Path(lines[1]).resolve()
            kind = "repository"
        elif result.returncode and any((item / ".git").exists() for item in (folder, *folder.parents)):
            raise ValueError("Cannot resolve this Git repository; repair its Git metadata and retry view --project.")
    except FileNotFoundError:
        if any((item / ".git").exists() for item in (folder, *folder.parents)):
            raise ValueError("Git is unavailable; install Git or restore PATH, then retry view --project.")
    except (subprocess.TimeoutExpired, OSError) as error:
        raise ValueError("Cannot inspect this project; check folder access and Git, then retry view --project.") from error
    value = kind + ":" + os.path.normcase(str(identity))
    return {"id": hashlib.sha256(value.encode("utf-8")).hexdigest()[:24],
            "name": root.name or str(root), "project": str(root), "kind": kind}


def run_scope(run):
    """Resolve older stored runs once per changed state, without leaking invalid projects."""
    if run.get("scopeVersion") == VERSION and "scopeId" in run:
        return run["scopeId"]
    try:
        return scope_for(run["project"])["id"]
    except (KeyError, TypeError, ValueError):
        return None


def project_state(state, scope, ready_limit=20, event_limit=24):
    """Filter runs before deriving shared sections and their limits."""
    runs = [r for r in state.get("runs", []) if isinstance(r, dict)
            and (scope["kind"] == "all" or run_scope(r) == scope["id"])]
    ready = sorted((t for r in runs for t in r.get("ready") or []), key=lambda t: -t["at"])
    events = sorted((e for r in runs for e in r.get("events") or []), key=lambda e: e["id"])
    at = max([0, *(r.get("changed", 0) for r in runs), *(r.get("created", 0) for r in runs),
              *(r.get("closedAt") or 0 for r in runs), *(t["at"] for t in ready), *(e["t"] for e in events)])
    return {"at": at, "scope": scope, "runs": runs, "ready": ready[:ready_limit],
            "readyTotal": len(ready), "events": events[-event_limit:]}


def route(scope):
    """The URL namespace is the scope boundary for every resource."""
    return "/all/" if scope["kind"] == "all" else f"/projects/{scope['id']}/"
