# Releasing

Humans release. Never move or delete a published tag, never re-publish a version: fix forward with a new version.

## Versions

- **One canonical version:** `version` in `.agents/.claude-plugin/plugin.json`; `.agents/.codex-plugin/plugin.json` and `.agents/.cursor-plugin/plugin.json` carry the same. Marketplace entry's tag `ref` in `.claude-plugin/marketplace.json` names same release.
- **Latest:** the update check reads the GitHub release marked Latest, never the highest tag. Deprecated 1.x tags stay; their releases say deprecated.
- **Public surface:** skill names, run file format, hook scripts and events. **Breaking** = an install, open run or caller must act (an `UPGRADING.md` step), or something that worked stops working.
- **Bump** from the release's highest entry ([SemVer 2.0.0](https://semver.org/spec/v2.0.0.html); 0.x rule as Cargo and npm `^`):

| Highest entry | From 1.0.0 | 0.y.z (now) |
|---|---|---|
| Breaking (incl. `Removed`) | MAJOR: X+1.0.0 | MINOR: 0.y+1.0 |
| `Added`, `Deprecated`, compatible `Changed` | MINOR: X.Y+1.0 | PATCH: 0.y.z+1 |
| `Fixed`, `Security` only | PATCH: X.Y.Z+1 | PATCH: 0.y.z+1 |
| Nothing a reader notices | no release | no release |

- One release carries every PR merged since the last; never one release per PR unless the owner asks.
- Risky release: test as `X.Y.Z-rc.1` (prerelease, never Latest) first.
- Leaving 0.x: `2.0.0`, never `1.0.0` (the deprecated 1.x tags hold it). When: public surface stable and every host run live.
- Wrong version published: never move or reuse it; fix forward with the next correct one. Pulled release: `## [X.Y.Z] - <date> [YANKED]`.

## Changelog

Written for the person who installs or runs the factory: what changed for them, never how it was built. [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) layout, [Common Changelog](https://common-changelog.org/) lines.

1. Each PR adds its lines under `## [Unreleased]`, in its group. Groups in this order, empty ones left out: `Changed`, `Added`, `Deprecated`, `Removed`, `Fixed`, `Security`.
2. One line per change, one sentence, under 30 words. Starts with an imperative verb (Add, Make, Let, Stop, Fix, Remove). Says the effect the reader sees, readable without its group heading.
3. Ends with its PR as `([#254])`, and `[#254]: <PR URL>` joins the link list at the file bottom.
4. Breaking line starts `**Breaking:**`, goes first in its group, and has its `UPGRADING.md` step.
5. Leave out what no reader notices: wording trims, byte counts, typos, CI, internal script structure, review rounds. Merge related lines; drop changes undone before the release.
6. No internal mechanics (file names inside skills, guard internals) unless the reader types or reads them.
7. Release header `## [X.Y.Z] - YYYY-MM-DD`; at most one notice under it, one italic sentence (first release, yanked, upgrade needed).

Example:

```markdown
### Changed

- **Breaking:** Make gate lines name their checker and commit, so old run files need a rerun ([#241])
- Let a gate pass after 3 rounds with no open critical finding, so runs never stall on nits ([#254])

### Fixed

- Fix steps waiting for "go" in Fast when the Stop hook is not loaded ([#254])
```

Bad: `- Continuous runs (#253): a gate or review loop with 3 failed rounds ... checks the guard loads.` (one paragraph for many changes, guard internals, ticket instead of PR).

## Steps

1. Pick `X.Y.Z` from the bump table and the Unreleased lines. Branch from up-to-date `main`: `git fetch origin`, then `git switch -c release/vX.Y.Z origin/main`.
2. Write upgrade steps under `## X.Y.Z` in `UPGRADING.md`.
3. Set `version` to `X.Y.Z` in all three plugin manifests. In `.claude-plugin/marketplace.json`, set the plugin's `source.ref` to `vX.Y.Z` and its `source.path` to plugin root at that tag (`.agents` from 0.1.0); refresh both descriptions to match that release.
4. In `CHANGELOG.md`, move `## [Unreleased]` into `## [X.Y.Z] - <today>`; keep an empty `## [Unreleased]` above it. At the bottom, point `[Unreleased]` at `vX.Y.Z...HEAD` and add `[X.Y.Z]`: `compare/<previous tag>...vX.Y.Z`.
5. Run repository checks in `AGENTS.md`, commit, open release PR, merge it.
6. Tag merge commit, push tag right away: Claude Code installs fetch the tag marketplace names; until it exists a new install fails.

   ```text
   git fetch origin && git switch --detach <merge commit>
   git tag -a vX.Y.Z -m vX.Y.Z <merge commit>
   git push origin vX.Y.Z
   ```

7. Publish as Latest: `gh release create vX.Y.Z --latest --notes-file <the CHANGELOG section>`. Until a 0.x release is Latest, installs see the deprecated 1.x one: 0.1.0 also retitles each 1.x release "(deprecated)" and adds a "Deprecated: use 0.1.0 or later" line to its notes, without `--latest`.

## What follows a release

Every install's update check sees it within a day and tells the owner. Claude Code installs take it at next plugin update (auto-update on: by itself). Codex: `codex plugin marketplace upgrade`. Cursor: reinstall from the marketplace. Copied skills: pull the clone, copy again.

## Owner settings

Tag protection rules, immutable releases, signed tags = repository settings.
