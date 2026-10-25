# Changelog

Every notable change to the AI Software Factory, newest first. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). This file and [UPGRADING.md](UPGRADING.md) are the only places for release history.

The public surface is the `fast_gate.py` commands and flags, the work record format, the hook events and entries, and the skill names. A breaking change to any of them bumps MAJOR.

## [Unreleased]

### Added

- Release versioning (#139): one canonical version in `skills/safe-engine/VERSION`, `fast_gate.py version` and `fast_gate.py verify`, a sha256 release manifest, this changelog, `UPGRADING.md`, a release script and a `v*` tag workflow that publishes notes, manifest and `SHA256SUMS`.
- Update channels (#139): installs and new projects follow the newest verified release (stable, the default); `install --channel edge` follows `main`. The Claude Code plugin follows release tags.
- Model routing (#138): delegated jobs run on their role's tier (runner, analyst, maker, builder, reviewer; Claude Code `safe-engine:<role>` agents), with gates the coordinator re-runs, one job per agent, escalation one tier after two failed rounds, a compact handback per role and a per-host tier map with an owner override.

### Changed

- Leaner runs (#137): product, feature and change runs each read 24% less method text, every gate message is shorter with the same facts, `scripts/token_report.py` measures both, and tests hold every method file and the gate's fixture messages to a byte budget and the product and change loads to 80% of their earlier size.
- Self-update (#139): a clone install moves only to a release tag on `main` whose files match its manifest, records the previous revision, rolls back a failed install and shows a one-time notice naming both versions.

## [1.0.0] - 2026-10-24

### Added

- First versioned baseline: Fast, Lucky and Safe delivery, the Fast gate and its hooks, and installers for Claude Code, Codex, Cursor and other agents.

[Unreleased]: https://github.com/seifsg/ai-software-factory/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/seifsg/ai-software-factory/releases/tag/v1.0.0
