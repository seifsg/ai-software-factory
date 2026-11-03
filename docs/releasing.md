# Releasing

Humans release. Never move or delete a published tag, never re-publish a version: fix forward with a new version.

## Versions

- **One canonical version:** `version` in `.agents/.claude-plugin/plugin.json`; `.agents/.codex-plugin/plugin.json` and `.agents/.cursor-plugin/plugin.json` carry the same. Marketplace entry's tag `ref` in `.claude-plugin/marketplace.json` names same release.
- **Latest:** the update check reads the GitHub release marked Latest, never the highest tag. Deprecated 1.x tags stay; their releases say deprecated.
- **Public surface:** skill names, run file format, hook scripts and events. **Breaking** = an install, open run or caller must act (an `UPGRADING.md` step), or something that worked stops working.
- **Renames and removals clean up after themselves:** a PR that renames or removes a skill, plugin id, script, hook or install path adds the old name to `.agents/skills/safe-factory/scripts/doctor.sh` in the same PR, so every install finds and moves it. The `UPGRADING.md` step then says `doctor.sh --fix` instead of listing files to delete by hand.
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

1. Each PR adds its lines under `## [Unreleased]`, in its group; a PR no reader notices (rule 5), such as a release-guide change, adds none. Groups in this order, empty ones left out: `Changed`, `Added`, `Deprecated`, `Removed`, `Fixed`, `Security` (Common Changelog order, plus Keep a Changelog's `Deprecated` before removals and `Security` last).
2. One line per change, one sentence, under 30 words. Starts with an imperative verb (Add, Make, Let, Rename, Fix, Remove, ...). Says the effect the reader sees, readable without its group heading.
3. Ends with its PR as `([#254])`, and `[#254]: https://github.com/seifsg/ai-software-factory/pull/254` joins the link list at the file bottom.
4. Breaking line starts `**Breaking:**`, goes first in its group, then the rest by importance. Each has a numbered `UPGRADING.md` step under `## X.Y.Z`: what to run or change, in order.
5. Leave out what no reader notices: wording trims, byte counts, typos, CI, internal script structure, review rounds. Merge related lines; drop changes undone before the release.
6. No internal mechanics (file names inside skills, guard internals) unless the reader types or reads them.
7. Release header `## [X.Y.Z] - YYYY-MM-DD`; at most one notice under it, one italic sentence (first release, yanked, upgrade needed, renumbered).

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

1. Pick `X.Y.Z` from the bump table and the Unreleased lines. Upgrade steps and changed marketplace descriptions land on `main` with their PRs; steps sit under `## Unreleased` in `UPGRADING.md`, and the script names that heading `## X.Y.Z`. A release candidate (`X.Y.Z-rc.1`) is cut by hand.
2. `sh scripts/release.sh prepare X.Y.Z`: refuses a dirty tree, a version not above `main`'s, an existing tag or an empty Unreleased section; branches `release/vX.Y.Z` from `origin/main`; sets `version` in the three plugin manifests and the marketplace `source.ref` to `vX.Y.Z` (`source.path` stays `.agents`); moves `## [Unreleased]` into `## [X.Y.Z] - <today>` with its compare links; runs `sh scripts/check.sh`; commits, pushes and opens the draft release PR.
3. The owner merges the release PR.
4. `sh scripts/release.sh publish X.Y.Z`: refuses until `main` carries `X.Y.Z` and while the tag exists; tags the commit that set the version (the release merge, even with later merges on top), pushes the tag right away (Claude Code installs fetch the tag the marketplace names; until it exists a new install fails), then `gh release create vX.Y.Z --latest` with the CHANGELOG section, links made absolute.

A step that fails says what is already done; finish it by hand from there. Never move a tag to retry.

## What follows a release

Every install's update check sees it at its next session start and tells the owner at the one after. Claude Code installs take it at next plugin update (auto-update on: by itself). Codex: `codex plugin marketplace upgrade`. Cursor: reinstall from the marketplace. Copied skills: pull the clone, copy again.

## Owner settings

Tag protection rules, immutable releases, signed tags = repository settings.
