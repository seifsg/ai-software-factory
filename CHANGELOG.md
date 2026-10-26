# Changelog

Every notable change to the AI Software Factory, newest first. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). This file and [UPGRADING.md](UPGRADING.md) are the only places for release history.

The public surface is the `fast_gate.py` commands and flags, the work record format, the hook events and entries, and the skill names. A breaking change to any of them bumps MAJOR.

## [Unreleased]

### Added
- UI Look/Show/Prove/Ship checkpoint with current paired pictures, recorded sharing and owner feedback/deadlines before the declared suite (#154).

### Changed

- Synced docs (#150): the README covers every install host and flag, what each host gets, orchestrators, the live view, model routing, local releases and the full layout; `tests/test_docs_sync.py` fails when a command, flag, host, release step, doc page, skill or folder goes undocumented.
- No GitHub CI/CD (#148): the release workflow is gone; `python scripts/release.py publish vX.Y.Z` checks the tag, runs the suite and publishes the GitHub release locally, and methods treat local checks as the gate in every project, never waiting on CI.

## [1.0.0] - 2026-10-26

### Added

- First versioned baseline: Fast, Lucky and Safe delivery, the Fast gate and its hooks, and installers for Claude Code, Codex, Cursor and other agents.
- Project preview (#129): `fast_gate.py view --project` scopes the live view to one project (worktrees included), `--all-projects` opens the machine-wide view, and the page leads with the session's goal, next test and reported child sessions.
- Orchestrators (#128): `fast_gate.py orchestrate` sets up an orchestrator (Paperclip first) to start factory sessions that run unattended through the orchestrated-run binding; `install --codex-home` targets an agent's own Codex home.
- No-guess briefs (#145): plans fix an Interface, this checkout's Ports and, for UI work, the UX rules every agent's brief carries; items only the owner or missing hardware can finish are marked DEFERRED and listed at handoff; an epic's wave shares one integration branch and draft PR; `fast_gate.py shots` captures a PR's Before and After screenshots in one go.
- Stale baselines (#135): `fast_gate.py recover-baseline` corrects a run's start baseline on the owner's authority after a preview, keeping owned UI work under proof; runs fetch their upstream before starting.
- Release versioning (#139): one canonical version in `skills/safe-engine/VERSION`, `fast_gate.py version` and `fast_gate.py verify`, a sha256 release manifest, this changelog, `UPGRADING.md`, a release script and a `v*` tag workflow that publishes notes, manifest and `SHA256SUMS`.
- Update channels (#139): installs and new projects follow the newest verified release (stable, the default); `install --channel edge` follows `main`. The Claude Code plugin follows release tags.
- Model routing (#138): delegated jobs run on their role's tier (runner, analyst, maker, builder, reviewer; Claude Code `safe-engine:<role>` agents), with gates the coordinator re-runs, one job per agent, escalation one tier after two failed rounds, a compact handback per role and a per-host tier map with an owner override.

### Changed

- Leaner runs (#137): product, feature and change runs each read 24% less method text, every gate message is shorter with the same facts, `scripts/token_report.py` measures both, and tests hold every method file and the gate's fixture messages to a byte budget and the product and change loads to 80% of their earlier size.
- Self-update (#139): a clone install moves only to a release tag on `main` whose files match its manifest, records the previous revision, rolls back a failed install and shows a one-time notice naming both versions.

[Unreleased]: https://github.com/seifsg/ai-software-factory/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/seifsg/ai-software-factory/releases/tag/v1.0.0
- Design ports (#155): immutable reference coverage, owner-recorded cuts, independent matched likeness receipts and measured element counts; stale or incomplete evidence blocks completion.
