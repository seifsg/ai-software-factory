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
4. `python tests/run.py` (local checks are the gate; CI is never required), commit, open the release PR and merge it with nothing else merged in between: the manifest describes this exact tree. If `main` moved, rebase and cut again.
5. Check the merged commit before tagging it. Pushing the tag is the release: Claude Code installs fetch the tag the marketplace names right away, with no check of their own, and clone installs adopt any tag that passes the release check.

   ```text
   git fetch origin && git switch --detach <merge commit>
   python scripts/release.py check vX.Y.Z
   python tests/run.py
   git tag -a vX.Y.Z -m vX.Y.Z <merge commit>
   git push origin vX.Y.Z
   ```

   `check` needs no tag yet and writes the release files to a new temporary folder, never into the checkout. Push the tag right after the merge: until it exists, a new Claude Code install fails (existing ones keep their copy).
6. Publish the GitHub release from the same checkout: `python scripts/release.py publish vX.Y.Z` runs the check and the full suite again, then `gh release create` with the changelog notes, `release-manifest.json` and `SHA256SUMS`. No CI is involved: the factory never needs GitHub Actions. If it fails after the tag is out, fix the cause and run it again; a release that shipped broken files is fixed forward with a new version.

## What follows a release

- Codex, Cursor and other installs on the stable channel move to the new tag at their next daily update, after the release check ([hosts](hosts.md#updates)). Claude Code installs take it at their next plugin update.
- New projects pin it, after the release check. Pinned projects and active runs keep their bundle.

## Owner settings

Tag protection rules, immutable releases and signed tags are repository settings outside the release script.
