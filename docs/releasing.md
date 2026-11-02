# Releasing

Humans release. Never move or delete a published tag, never re-publish a version: fix forward with a new version.

## Versions

- **One canonical version:** `version` in `.agents/.claude-plugin/plugin.json`. Marketplace entry's tag `ref` in `.claude-plugin/marketplace.json` names same release.
- **SemVer:** MAJOR = breaking change to public surface (skill names, run file format, hook scripts and events), MINOR = new capability, PATCH = fixes.
- **Every PR** adds a line under `## [Unreleased]` in `CHANGELOG.md`, and steps in `UPGRADING.md` when installs or open runs must act.

## Steps

1. Branch from up-to-date `main`: `git fetch origin`, then `git switch -c release/vX.Y.Z origin/main`.
2. Write upgrade steps under `## X.Y.Z` in `UPGRADING.md`.
3. Set `version` in `.agents/.claude-plugin/plugin.json` to `X.Y.Z`. In `.claude-plugin/marketplace.json`, set the plugin's `source.ref` to `vX.Y.Z` and its `source.path` to plugin root at that tag (`.agents` from 2.0.0); refresh both descriptions to match that release.
4. In `CHANGELOG.md`, move `## [Unreleased]` into `## [X.Y.Z] - <today>` keep an empty `## [Unreleased]` above it.
5. Run repository checks in `AGENTS.md`, commit, open release PR, merge it.
6. Tag merge commit, push tag right away: Claude Code installs fetch the tag marketplace names; until it exists a new install fails.

   ```text
   git fetch origin && git switch --detach <merge commit>
   git tag -a vX.Y.Z -m vX.Y.Z <merge commit>
   git push origin vX.Y.Z
   ```

7. Publish: `gh release create vX.Y.Z --notes-file <the CHANGELOG section>`.

## What follows a release

Claude Code installs take it at next plugin update. Codex and other installs take it when owner pulls the clone and copies the skills again.

## Owner settings

Tag protection rules, immutable releases, signed tags = repository settings.
