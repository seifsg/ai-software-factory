"""Release identity for the gate: `version`, `verify`, the version line on start and status cards, and the one-time
update notice (docs/install.md#version-and-updates). Commands load it; hooks never do.
"""
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import resolve_bundle as release  # noqa: E402 - the version, manifest and release check every launcher carries

# This copy's root: the factory checkout it sits in, else its skills folder (plugin root or installed copy).
ROOT = HERE.parents[2] if (HERE.parents[2] / "safe_engine").is_dir() else HERE.parents[1]


def notice(home):
    """The pending update notice (fast_update.tell), claimed by rename so it shows once under parallel commands."""
    claimed = home / f"update-notice.{os.getpid()}.txt"
    try:
        os.replace(home / "update-notice.txt", claimed)
    except OSError:
        return None
    try:
        return claimed.read_text(encoding="utf-8").strip()
    finally:
        claimed.unlink(missing_ok=True)


def route(root):
    """How this copy got here."""
    if not release.layout(root):
        return f"checkout {root}"
    if (root / "safe-engine" / release.MARKER).exists():
        return f"installed copy {root}"
    return f"Claude Code plugin {root}" if (root / ".claude-plugin").is_dir() else f"copy {root}"


def digest(root):
    """The release manifest's tree digest and how the files under root compare with it."""
    try:
        manifest = release.read_manifest(root)
        problems = release.verify(root, manifest)
    except RuntimeError as error:
        return f"none ({error})"
    state = "all files match" if not problems else f"{len(problems)} differ (fast_gate.py verify lists them)"
    return f"sha256:{manifest['tree']} ({manifest['version']} manifest): {state}"


def version(home):
    """`fast_gate.py version`: version, commit, channel, install route and digest of this copy."""
    try:
        saved = release.install_record()
        channel = release.channel(saved)
    except RuntimeError as error:
        sys.exit(str(error))
    version = release.read_version(ROOT)
    if not release.layout(ROOT):
        try:
            commit = release.git("rev-parse", "HEAD", cwd=ROOT)
        except (RuntimeError, OSError):  # a downloaded copy of the repository
            commit = "unknown (not a Git checkout)"
    elif (ROOT / "safe-engine" / release.MARKER).exists() and saved.get("revision"):
        commit = f"{saved['revision']} (installed from {saved.get('clone')})"
    else:  # a plugin cache holds no Git: the release tag names the commit
        commit = f"the commit of tag v{version} (no Git here)" if version else "unknown (no Git here)"
    lines = [f"Factory {version or 'unversioned'}", f"Commit: {commit}",
             f"Channel: {channel}" + ("" if saved.get("auto", True) else " (auto-update off)"),
             f"Route: {route(ROOT)}", f"Digest: {digest(ROOT)}"]
    previous = saved.get("previous")
    if previous:
        lines.append(f"Before the last update: {previous.get('version') or 'unversioned'} at {previous.get('revision')}")
    print("\n".join(lines + list(filter(None, [notice(home)]))))


def verify(path):
    """`fast_gate.py verify`: every changed, missing or extra file against the release manifest; exit 1 on any."""
    root = Path(path).resolve() if path else ROOT
    try:
        manifest = release.read_manifest(root)
        problems = release.verify(root, manifest)
    except RuntimeError as error:
        sys.exit(f"{root}: {error}")
    print("\n".join(problems + [f"{root}: {len(problems)} differences from the {manifest['version']} manifest "
                                f"(sha256:{manifest['tree']})"]))
    sys.exit(1 if problems else 0)


def card(run, home):
    """The version line of the start and status cards, then any pending update notice."""
    bundle = run.get("bundle")
    try:
        channel = release.channel(release.install_record())
    except RuntimeError as error:  # named on the card; a broken record must not stop a run's start
        channel = f"channel unknown: {error}"
    line = f"Version: {release.read_version(ROOT) or 'unversioned'} ({channel})"
    if bundle:
        line += f"; run bundle {release.read_version(bundle['root']) or 'unversioned'}"
    return "\n".join(filter(None, [line, notice(home)]))


def parser(sub):
    """The `version` and `verify` subcommands (fast_gate.py)."""
    sub.add_parser("version", help="Print this factory's version, commit, channel, install route and digest")
    check = sub.add_parser("verify", help="Compare a bundle or install with its release manifest; lists every mismatch")
    check.add_argument("--path", help="A factory checkout or skills folder; default: this copy")
