# Releasing

Humans release. Never move or delete a published tag and never re-publish a version: fix forward with a new version.

## Versions

- **One canonical version:** `skills/safe-engine/VERSION`. The release script writes it into every copy (the plugin manifest's `version`, the marketplace entry's tag `ref`); the controller and the gate read the file. `tests/test_release.py` fails when a copy, the release manifest or the newest released `CHANGELOG.md` heading differs.
- **SemVer:** MAJOR for a breaking change to the public surface (`fast_gate.py` commands and flags, the work record format, hook events and entries, skill names), MINOR for new capability, PATCH for fixes.
- **Every PR** adds a line under `## [Unreleased]` in `CHANGELOG.md`, and steps in `UPGRADING.md` when installs or active runs must act.
- **Release manifest:** `skills/safe-engine/release-manifest.json` holds the sha256 of every other tracked file (CRLF read as LF) and a tree digest, the sha256 of the same list in `SHA256SUMS` form. On `main` between releases it still describes the last release, so `fast_gate.py version` there reports files that differ.

## Steps

1. Branch from an up-to-date `main`: `git fetch origin`, then `git switch -c release/vX.Y.Z origin/main`.
2. Write the upgrade steps under `## X.Y.Z` in `UPGRADING.md` and commit them.
3. `python scripts/release.py cut X.Y.Z`. It refuses a dirty tree, an older version or a published tag, then bumps every version copy, moves `## [Unreleased]` into `## [X.Y.Z] - <today>` (an unpublished section of the same version keeps its text and merges), rebuilds the compare links and writes the release manifest.
4. `python tests/run.py`, commit, open the release PR and merge it with nothing else merged in between: the manifest describes this exact tree. If `main` moved, rebase and cut again.
5. Right after the merge, tag the merge commit and push the tag:

   ```text
   git tag -a vX.Y.Z -m vX.Y.Z <merge commit>
   git push origin vX.Y.Z
   ```

   Claude Code installs fetch the plugin from this tag: until it exists, a new install fails and existing ones keep their copy.
6. The `release` workflow (`.github/workflows/release.yml`) checks the tag (equal to the version, on `main`, a dated changelog section, every file matching the manifest), runs the tests and publishes the GitHub release with the changelog notes, `release-manifest.json` and `SHA256SUMS`. A failed check publishes nothing; fix forward with a new version.

Run the workflow's check locally: `python scripts/release.py check vX.Y.Z --out dist`.

## What follows a release

- Installs on the stable channel move to the new tag at their next daily update (Codex, Cursor, other) or Claude Code plugin update; each verifies it first ([hosts](hosts.md#updates)).
- New projects pin it. Pinned projects and active runs keep their bundle.

## Owner settings

Tag protection rules, immutable releases and signed tags are repository settings outside the release script.
