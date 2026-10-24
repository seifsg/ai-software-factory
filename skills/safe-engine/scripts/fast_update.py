"""Daily self-update for installs without a plugin marketplace (docs/hosts.md#updates).

The session-start hook runs it (`run-gate.sh <host> update`) before the gate loads. At most once a day it moves the
factory clone that `install` recorded to its channel's newest revision: on stable (the default) the newest release
tag on main whose files match its manifest, on edge (or stable before the first release) main, fast-forwarded. Only a
clean clone of the factory repository, on main or detached at a release tag, and read by no open run, moves. It
records the previous revision, reruns the clone's own installer for each recorded install, restores the previous
revision when an install fails, and leaves a one-time notice for the gate. Fails open: any problem is logged and the
session goes on. Off with SAFE_ENGINE_NO_UPDATE=1 or `install --no-auto-update`. Pinned project bundles are never
touched.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))  # resolve_bundle and fast_install load inside update()

HOME = Path(os.environ.get("SAFE_ENGINE_HOME") or Path.home() / ".safe-engine")
RECORD = HOME / "install.json"  # written by fast_install.remember
STAMP = HOME / "update.stamp"  # its mtime is the last check
NOTICE = HOME / "update-notice.txt"  # shown once by the gate (fast_release.notice)
LOG = HOME / "logs" / "gate.log"
DAY = 24 * 3600
OFF = "SAFE_ENGINE_NO_UPDATE"
TAGS = "--format=%(if)%(*objectname)%(then)%(*objectname)%(else)%(objectname)%(end) %(refname)"  # tag -> commit


def due():
    """True once a day for a recorded install that has not opted out; claims the day at once, so failures wait too."""
    if os.environ.get(OFF) or not RECORD.is_file():
        return False
    try:
        if time.time() - STAMP.stat().st_mtime < DAY:
            return False
    except OSError:
        pass  # never checked
    try:
        STAMP.touch()
    except OSError:
        return False  # cannot claim the day: never run unthrottled
    return True


def git(clone, *args, timeout=15):
    """One git command in the clone, never prompting; raises on failure or timeout."""
    return subprocess.run(["git", "-C", str(clone), *args], capture_output=True, text=True, timeout=timeout,
                          check=True, stdin=subprocess.DEVNULL,
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}).stdout.strip()


def update(record):
    """Move the recorded clone to its channel's newest revision and reinstall; returns what happened."""
    import resolve_bundle as release  # here, not at import: a broken copy still reaches the log; idle starts load none
    from fast_install import write_json
    if not record.get("auto", True):
        return "off"
    if not record.get("installs"):
        return "nothing installed from a clone"
    clone = Path(record["clone"]).resolve()
    if (HOME / "bundles").resolve() in (clone, *clone.parents):
        return "pinned bundle: never updated"
    if not release.factory_origin(git(clone, "remote", "get-url", "origin")):
        return "skipped: clone origin is not the factory repository"
    if read_by_a_run(clone):
        return "skipped: an open run reads its methods from this clone"
    ref, head = git(clone, "rev-parse", "--abbrev-ref", "HEAD"), git(clone, "rev-parse", "HEAD")
    owned = (*dict(release.releases(git(clone, "for-each-ref", TAGS, "refs/tags"))).values(), record.get("revision"))
    if ref != "main" and (ref != "HEAD" or head not in owned):  # a release tag, or the install (or rollback) itself
        return "skipped: clone not on main or a release tag"  # a commit you checked out yourself stays put
    if git(clone, "status", "--porcelain"):
        return "skipped: clone has local changes"
    git(clone, "fetch", "--tags", "origin", timeout=20)  # a moved tag fails here (git names it): tags never move
    start = {"ref": ref, "revision": head, "version": release.read_version(clone)}
    # The way back is the last completed install; after an interrupted one, its commit, never a rewritten branch.
    old = start if record.get("revision") in (None, head) else {
        "ref": "HEAD", "revision": record["revision"], "version": record.get("version")}
    try:
        note = advance(clone, release.channel(record), release)
    except Exception:
        restore(clone, start)
        raise
    new = {"revision": git(clone, "rev-parse", "HEAD"), "version": release.read_version(clone)}
    if new["revision"] == record.get("revision"):  # the last completed install, so an interrupted one heals
        return "current" + note
    record["previous"] = old
    write_json(RECORD, record)  # before the new installer runs: a crash mid-install still names the way back
    try:
        reinstall(clone, record)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        tell(f"Factory update to {new['version']} failed; restoring {old['version'] or 'unversioned'}. "
             f"Check `fast_gate.py version` and {LOG}.")  # stays if the restore fails too
        restore(clone, old)
        reinstall(clone, record)
        tell(f"Factory update to {new['version']} failed and was rolled back to {old['version'] or 'unversioned'}; "
             f"see {LOG}.")
        return f"rolled back to {old['revision']}: install of {new['revision']} failed: {error}{note}"
    tell(f"Factory updated from {old['version'] or 'unversioned'} to {new['version']}. What changed: "
         f"{clone / 'CHANGELOG.md'}; what to do: {clone / 'UPGRADING.md'}.")
    return f"updated to {new['revision']}{note}"


def read_by_a_run(clone):
    """Whether an open Fast or Lucky run in this gate home uses the clone as its bundle; an unreadable run state
    counts, so a run is never changed under its feet."""
    for path in (HOME / "runs").glob("*.json"):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
            bundle = None if run.get("closed") else run.get("bundle")
            if bundle and Path(bundle["root"]).resolve() == clone:
                return True
        except (OSError, ValueError, AttributeError, KeyError, TypeError):
            return True
    return False


def advance(clone, channel, release):
    """Check out the channel's target: on stable the newest tag that passes the release check, trying older ones
    when it fails; on edge, or before any release, main fast-forwarded. Returns a note for the log."""
    tags = release.releases(git(clone, "for-each-ref", TAGS, "refs/tags")) if channel == "stable" else []
    skipped = []
    for tag, commit in tags:
        try:
            git(clone, "checkout", "--quiet", "--detach", commit)
            release.check_release(clone, tag)
            return f" ({tag}{'; skipped ' + '; '.join(skipped) if skipped else ''})"
        except RuntimeError as error:
            skipped.append(str(error))
        except subprocess.CalledProcessError as error:
            skipped.append(f"{tag} cannot be checked out: {(error.stderr or '').strip()}")
    if tags:
        raise RuntimeError("no release verifies: " + "; ".join(skipped))
    git(clone, "checkout", "--quiet", "main")
    git(clone, "merge", "--ff-only", "--quiet", "@{upstream}")
    return " (no release yet: following main)" if channel == "stable" else ""


def restore(clone, old):
    """Put the clone back on the branch or commit it had."""
    git(clone, "checkout", "--quiet", *(["-B", old["ref"]] if old["ref"] != "HEAD" else ["--detach"]), old["revision"])


def reinstall(clone, record):
    """Rerun the clone's installer for each recorded install; it rewrites the launchers, hook entries and record."""
    gate = clone / "skills" / "safe-engine" / "scripts" / "fast_gate.py"
    for item in record["installs"]:
        subprocess.run([sys.executable, str(gate), "install", "--host", item["host"],
                        *(["--project", item["project"]] if item.get("project") else [])],
                       capture_output=True, text=True, timeout=30, check=True, stdin=subprocess.DEVNULL)


def tell(text):
    """Leave the one-time notice the gate shows on its next start, status or version."""
    try:
        NOTICE.write_text(text + "\n", encoding="utf-8")
    except OSError:
        pass  # the log line still says it


def main():
    """Exit 0 always: the hook launcher reads non-zero as a missing Python and the session must never break."""
    if not due():
        return
    try:
        import resolve_bundle  # inside the try: a broken copy is logged, never fatal
        result = update(resolve_bundle.install_record())
    except subprocess.CalledProcessError as error:
        step = error.cmd[3] if error.cmd[0] == "git" else "install"
        result = f"error: {step} exit {error.returncode}: {(error.stderr or '').strip()}"
    except Exception as error:  # noqa: BLE001 - offline, missing git, a broken record: fail open
        result = f"error: {error!r}"
    try:
        import fast_gate  # the gate's own log; the new copy when the update just replaced it
        fast_gate.log("update", result=result)
    except Exception:  # noqa: BLE001 - a broken copy must not break the session either
        pass


if __name__ == "__main__":
    main()
