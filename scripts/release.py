"""Cut and check factory releases (docs/releasing.md). Standard library only.

python scripts/release.py cut X.Y.Z               bump every version copy, fold Unreleased into the version's
                                                  changelog section, require its upgrade notes, write the manifest
python scripts/release.py check vX.Y.Z [--out DIR]  the tag workflow's gate: the release check plus a dated changelog
                                                    section; writes notes.md, SHA256SUMS and the manifest to DIR
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from safe_engine import distribution as release  # noqa: E402 - the manifest and release check launchers carry

PLUGIN = ROOT / "skills/.claude-plugin/plugin.json"
MARKETPLACE = ROOT / ".claude-plugin/marketplace.json"
CHANGELOG = ROOT / "CHANGELOG.md"
UPGRADING = ROOT / "UPGRADING.md"
LINKS = "https://github.com/seifsg/ai-software-factory/"
SECTION = re.compile(r"^## \[([^\]]+)\](?: - (\d{4}-\d{2}-\d{2}))?[ \t]*$", re.M)
LINK = re.compile(r"^\[[^\]]+\]: \S+[ \t]*\n?", re.M)  # Keep a Changelog link references, rebuilt on every cut


def semver(text):
    """(MAJOR, MINOR, PATCH) of a plain SemVer core; exits on anything else."""
    match = release.TAG.fullmatch(f"v{text}")
    if not match:
        sys.exit(f"Not a release version (X.Y.Z, no pre-release): {text}")
    return tuple(map(int, match.groups()))


def sections(text):
    """{name: (heading start, body start, body end)} of each `## [name]` section of a changelog without links."""
    found = list(SECTION.finditer(text))
    return {match[1]: (match.start(), match.end(), end)
            for match, end in zip(found, [match.start() for match in found[1:]] + [len(text)])}


def links(names):
    """Link references for the sections `names`, newest first: Unreleased compares the newest release with HEAD, each
    release compares with the one before, the first release links its tag."""
    versions = [name for name in names if name != "Unreleased"]
    lines = [f"[Unreleased]: {LINKS}compare/v{versions[0]}...HEAD"] if versions else []
    lines += [f"[{name}]: {LINKS}" + (f"compare/v{older}...v{name}" if older else f"releases/tag/v{name}")
              for name, older in zip(versions, versions[1:] + [None])]
    return "\n".join(lines) + "\n"


def merge(*bodies):
    """Changelog section bodies joined: free text first, then each `### <type>` once with its entries in order."""
    leads, groups = [], {}
    for body in bodies:
        lead, *rest = re.split(r"^### ", body, flags=re.M)
        leads.append(lead.strip())
        for group in rest:
            name, _, entries = group.partition("\n")
            groups.setdefault(name.strip(), []).append(entries.strip())
    return "\n\n".join(filter(None, leads + [f"### {name}\n\n" + "\n".join(filter(None, entries))
                                             for name, entries in groups.items()]))


def fold(text, version, today):
    """The changelog with Unreleased moved into `## [version] - today`; an unpublished section of the same version
    keeps its own text first."""
    text = LINK.sub("", text).rstrip() + "\n"
    parts = sections(text)
    if "Unreleased" not in parts:
        sys.exit("CHANGELOG.md has no ## [Unreleased] section")
    _, body, end = parts["Unreleased"]
    notes = text[body:end].strip()
    if version in parts:  # always below Unreleased, so cutting it leaves `body` and `end` in place
        start, own, stop = parts[version]
        notes = merge(text[own:stop], notes)
        text = text[:start] + text[stop:]
    elif not notes:
        sys.exit("## [Unreleased] is empty: nothing to release")
    text = (text[:body] + f"\n\n## [{version}] - {today}\n\n{notes}\n\n" + text[end:].lstrip("\n")).rstrip()
    return text + "\n\n" + links(list(sections(text)))


def cut(version):
    """Prepare release `version` in a clean checkout: every copy bumped, changelog cut, manifest written."""
    current = release.read_version(ROOT)
    if semver(version) < semver(current):
        sys.exit(f"{version} is older than the current version {current}")
    if release.git("status", "--porcelain", "--untracked-files=all", cwd=ROOT):
        sys.exit("Commit or remove local changes first: the manifest covers committed files")
    if any(tag == f"v{version}" for tag, _ in release.releases(release.git("ls-remote", "--tags", "origin", cwd=ROOT))):
        sys.exit(f"v{version} is published; never re-publish a version: cut a new one")
    if not re.search(rf"^## {re.escape(version)}[ \t]*$", UPGRADING.read_text(encoding="utf-8"), re.M):
        sys.exit(f"Write the upgrade steps under '## {version}' in UPGRADING.md first")
    CHANGELOG.write_text(fold(CHANGELOG.read_text(encoding="utf-8"), version, date.today().isoformat()),
                         encoding="utf-8")
    (ROOT / release.VERSION_FILE).write_text(version + "\n", encoding="utf-8")
    for path, update in ((PLUGIN, lambda data: data.update(version=version)),
                         (MARKETPLACE, lambda data: data["plugins"][0]["source"].update(ref=f"v{version}"))):
        data = json.loads(path.read_text(encoding="utf-8"))
        update(data)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_manifest()
    print(f"Release {version} prepared. Next (docs/releasing.md): python tests/run.py, commit, open the release PR, "
          f"merge it, then tag the merge commit right away: git tag -a v{version} -m v{version} <commit> && "
          f"git push origin v{version}")


def write_manifest():
    """The manifest of the checkout as it stands (tracked files only)."""
    (ROOT / release.MANIFEST).write_text(json.dumps(release.build_manifest(ROOT), indent=1, sort_keys=True) + "\n",
                                         encoding="utf-8")


def check(tag, out):
    """The tag workflow's gate; writes the GitHub release's notes, SHA256SUMS and manifest to `out`."""
    if not release.TAG.fullmatch(tag):
        raise RuntimeError(f"{tag} is no release tag (vX.Y.Z)")
    release.check_release(ROOT, tag)
    text = LINK.sub("", CHANGELOG.read_text(encoding="utf-8"))
    parts = sections(text)
    if tag[1:] not in parts or not SECTION.match(text, parts[tag[1:]][0])[2]:
        raise RuntimeError(f"CHANGELOG.md has no dated ## [{tag[1:]}] section")
    out.mkdir(parents=True, exist_ok=True)
    manifest = release.read_manifest(ROOT)
    (out / "SHA256SUMS").write_text(release.sums(manifest["files"]), encoding="utf-8", newline="\n")
    shutil.copyfile(ROOT / release.MANIFEST, out / "release-manifest.json")
    _, body, end = parts[tag[1:]]
    (out / "notes.md").write_text(text[body:end].strip() + f"\n\nUpgrade steps: [UPGRADING.md]({LINKS}blob/{tag}/"
                                  f"UPGRADING.md). Tree digest: sha256:{manifest['tree']}.\n", encoding="utf-8")
    print(f"{tag} verified: on main, version {tag[1:]}, {len(manifest['files'])} files match the manifest; "
          f"release files in {out}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("cut", help="Prepare a release in a clean checkout").add_argument("version", help="X.Y.Z")
    checked = sub.add_parser("check", help="Verify a release tag and write its release files")
    checked.add_argument("tag", help="vX.Y.Z")
    checked.add_argument("--out", type=Path, help="Folder for the release files; default: a new temporary folder "
                                                  "(never inside the checkout, which must stay clean)")
    args = parser.parse_args()
    try:
        if args.command == "cut":
            cut(args.version)
        else:
            check(args.tag, args.out or Path(tempfile.mkdtemp(prefix=f"factory-{args.tag}-")))
    except RuntimeError as error:
        sys.exit(f"Release refused: {error}")


if __name__ == "__main__":
    main()
