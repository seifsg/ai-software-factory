# Releasing

Humans release. Never move or delete a published tag, never re-publish a version: fix forward with a new version.

## Versions

- **One canonical version:** `version` in `.agents/.claude-plugin/plugin.json`; `.agents/.codex-plugin/plugin.json` and `.agents/.cursor-plugin/plugin.json` carry the same. Marketplace entry's tag `ref` in `.claude-plugin/marketplace.json` names same release.
- **Latest:** the update check reads the GitHub release marked Latest, never the highest tag. Deprecated 1.x tags stay; their releases say deprecated.
- **SemVer:** MAJOR = breaking change to public surface (skill names, run file format, hook scripts and events), MINOR = new capability, PATCH = fixes.
- **Every PR** adds a line under `## [Unreleased]` in `CHANGELOG.md`, and steps in `UPGRADING.md` when installs or open runs must act.

## Steps

1. Branch from up-to-date `main`: `git fetch origin`, then `git switch -c release/vX.Y.Z origin/main`.
2. Write upgrade steps under `## X.Y.Z` in `UPGRADING.md`.
3. Set `version` to `X.Y.Z` in all three plugin manifests. In `.claude-plugin/marketplace.json`, set the plugin's `source.ref` to `vX.Y.Z` and its `source.path` to plugin root at that tag (`.agents` from 0.1.0); refresh both descriptions to match that release.
4. In `CHANGELOG.md`, move `## [Unreleased]` into `## [X.Y.Z] - <today>`; keep an empty `## [Unreleased]` above it.
5. Run repository checks in `AGENTS.md`, commit, open release PR, merge it.
6. Tag merge commit, push tag right away: Claude Code installs fetch the tag marketplace names; until it exists a new install fails.

   ```text
   git fetch origin && git switch --detach <merge commit>
   git tag -a vX.Y.Z -m vX.Y.Z <merge commit>
   git push origin vX.Y.Z
   ```

7. Publish as Latest: `gh release create vX.Y.Z --latest --notes-file <the CHANGELOG section>`.

## What follows a release

Every install's update check sees it within a day and tells the owner. Claude Code installs take it at next plugin update (auto-update on: by itself). Codex: `codex plugin marketplace upgrade`. Cursor: reinstall from the marketplace. Copied skills: pull the clone, copy again.

## Owner settings

Tag protection rules, immutable releases, signed tags = repository settings.
