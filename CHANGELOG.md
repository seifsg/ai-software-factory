# Changelog

Every notable change to the AI Software Factory, newest first. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). This file and [UPGRADING.md](UPGRADING.md) are the only places for release history.

The public surface is the skill names, the run file format, and the hook scripts and events. A breaking change to any of them bumps MAJOR.

## [Unreleased]

### Changed

- After the first real run: the checker reports every missing item in one pass and only a repeated item counts as a failed round; no Before capture for a brand-new surface, no mandatory journey video, a fix recaptures only its ids; a small product gets one ticket and ticket comments only on status changes; change-guard only when existing code changed; size sets scope, never quality, and Fast never waits for it; every step prints its full block, and owner replies are folded in before the next step; the reviewer hands fixes back to the builder and Gate C reruns when the PR changed.
- **Breaking:** the factory is methods only. One pipeline of nine visible steps, ticket → analyze → recommend → plan → Before proof → build → verify → PR → review, each printing its block to the owner, the ticket and `.factory/run.md` (#231).
- `analyze-start` and `get-ready-to-code` are restored to their full original outputs; `how-to-review-a-pr` is its own skill again; every step skill ends with an output contract.
- Before proof is captured before the first edit with any host capture tool; After on the same server during verify. Builds run only tests mapped to changed files; the full suite runs once at verify.
- The plugin root is `.agents/`; the delegate roles live in `.agents/agents/`.
- `deep-review` opens with the owner's original method word for word; factory additions follow it. `ticketing` and the product bar are shorter: duplicate rules merged, rare cases (parallel tickets, speed checklist, external effects, release record) moved behind pointers. Read set 114,523 → 110,950 B (#233).

### Added

- New projects need no setup: with no folder named, the factory creates one beside the owner's other projects, runs `git init`, and with no remote creates a private GitHub repository and uses its Issues.
- `recommend`: three solutions in one table, one pick.
- Run guarantees: each step loads its skill fresh; a Stop guard re-prompts the next step until step 8 and three checker gates pass, and lets the stop through while the run waits on the owner or background jobs; a compact hook re-injects the next step after compaction. One `sh` script with one `awk` pass: about 0.07 s per turn end without a run, 0.15 s with one, nothing per tool call.
- The `checker` role: a fresh light delegate that checks step outputs against their contracts after steps 3, 6 and 7.

### Removed

- The product bar (`product-bar.md`, `cases.md`, `quality-cases.md`) and the `ux-quality` skill. Security stays in `deep-review`'s security lens; the owner's words decide look, copy and placeholders.
- All Python: the `fast_gate.py` gate and its per-tool-call hook (761 ms per call measured), the Safe controller, hidden checks, `shots`, metrics, the live view, bundle resolution, the installer and self-update, evals, release scripts and the 665-test suite.
- Lucky mode, `verify` and `promote` of a Fast run, the optional Safe check, Show/Look/Prove/Ship phases and the owner-reply timer.

## [1.3.0] - 2026-10-31

### Added

- Released apps keep their own changelog, version and release-note steps through every change and session; authorized releases run the app's tools, read back the result and reconcile partial effects (#221).
- `enroll-worktree` archives a new Git worktree's inherited run files and selects a factory for its own run, leaving the source run untouched (#209).

### Changed

- Preflight local PR draft structure through the real handoff validator, expose canonical repair identities, review source before the final suite, retain the independent reviewer for author repair deltas and keep bulky tool evidence outside model context.

### Fixed

- Every work-record value is read one way: trailing `.`, `;` or `,` is ignored and `none (<why>)` is recognised by one shared rule (Ports, Findings, Ticket), so its reason never counts as content.
- Valid record lines pass the first time: `Ports: none (<why>)` owns no port it mentions, a port ending a sentence counts, `min2` is a minimum, a trailing `.` or `;` after a proof declaration is accepted, and a Findings value that is not a report path says so (#218).
- Only delegated todos name a model tier, and a red full suite is diagnosed before a maker gets it (#219).
- Owner messages come first: answer or act with only the needed checks, let the latest request replace the objective, and resume only work that still fits (#216).
- Fast starts without a selection select one instead of starting with legacy defaults; explicit pins skip release discovery; eval exports are pinned local snapshots; startup hints are shorter (#213).
- Written facts (host, path, command, version, status) are claims to test before use or report; a stand-in proves only itself; unverified means the check cannot run here.
- Run metrics: Fast runs start their timeline at the first applicable step, Safe runs record the factory revision and never share a metrics folder, and analytics hooks are plain calls instead of repeated guards (#175).
- A host, URL or IP written in a ticket is tested by resolving the name and requesting that URL, never assumed linked or left unverified (#206).

## [1.2.0] - 2026-10-28

### Added

- Local factory-run metrics: versioned event store under `.factory/metrics/`, lifecycle instrumentation, JSON/Markdown reports, cross-run compare, export/delete, and `fast_gate.py metrics` (#175). `metrics usage --file` records tokens and dollars only from a host usage file already on disk.
- Correct cumulative usage imports per session, accept Codex token-count records, and replace per-append full-log counting with a locked incremental index (#175).
- Record observed task/helper identities and durations, resumed phase segments and failed commands; compare completed matching run cohorts with deltas, report uncovered wall from interval unions, and show Codex reasoning as a nonadditive output subset (#175).

### Changed

- Release publication reuses intact full-suite proof for the exact merged source and environment, retaining manifest checks and verifying the remote tag target.
- Bound Fast delegation and proof work: compact helper context, capability preflight, batched repairs and valid same-candidate evidence reuse. Required checks, conservative freshness, owner stops and active pins are unchanged.
- Load only requested CLI argument modules on ordinary commands, preserving full help, errors and bundle routing; isolate mocked review protocols and prefer installed Git shells in Windows test processes.
- Load detailed quality and visual proof methods only for their named situations; report method-file exposure as overlapping text proxies and retain complete preflight receipts.

### Fixed

- Preserve concurrent Fast check observations and owner control state when a long suite or check finishes, reject stale/conflicting run-state writes, and retain one log per suite execution so intact A→B→A proof can be reused (#195).
- Keep metrics separate when a Fast run key is reused; reject path aliases on local deletion and keep open reports partial and completed wall time stable after usage imports (#175).
- Carry Safe metrics into parallel check workers, measure Show owner-response waits without implying approval, and group repeated commands by opaque exact identity within each task (#175).

## [1.1.2] - 2026-10-28

### Changed

- POC/MVP visual work uses light mode on its target device by default. New Show plans freeze selected variants and ordinary Before/After comparisons; UX and PR proof focus on changed areas, while explicit requirements and frozen design coverage remain (#192).
- Clarify polished motion with respect for reduced-motion preferences; keep visual quality while narrowing optional device/theme scope (#192).

## [1.1.1] - 2026-10-27

Retains the delivery improvements listed under 1.1.0 below. That immutable tag passed its merged-tree checks, but GitHub publication stopped on the eval cleanup regression; this release fixes that path forward.

### Fixed

- Eval process cleanup requires ownership before execution and confirms descendant exit through the canonical job helper; isolated rubric checks receive its snapshotted source. Failed stops retain ownership for reconciliation without skipping other trees or losing partial reports (#186).

## [1.1.0] - 2026-10-27

### Fixed
- Journey clock lint accepts both documented direct fixed-clock helpers while retaining wall-time checks (#182).
- Claude Code install (#152): `install --host claude` now installs the plugin with Claude Code's CLI and checks `claude plugin list`, exiting 1 with the fix when it cannot; it used to only enable it in settings, which could leave no plugin. The run card's `Hooks:` line names an enabled but uninstalled plugin. Existing Claude Code installs: when `claude plugin list` lacks `safe-engine@ai-software-factory`, rerun `install --host claude`.

### Added
- Design ports (#155): immutable reference coverage, owner-recorded cuts, independent matched likeness receipts and measured element counts; stale or incomplete evidence blocks completion.
- Explicit verdict-field checks and accumulated record diagnostics (#163); approved-plan import remains outside this release pending manual acceptance (#184).

- Complete-suite input declarations, evidence reuse and a machine-wide queue; fixed browser-clock helpers, declared journey-time lint and affected-test feedback after manual use (#158).
- Reasoned hidden-check selection, pasted checker briefs, syntax/execution receipts and scoped browser trap helpers (#159).
- Plain owner reports with explicit per-ticket spend and estimates, body-code lint, latest pictures in the live view, and bounded PNG content checks before publication.
- UI Look/Show/Prove/Ship checkpoint with current paired pictures, recorded sharing and owner feedback/deadlines before the declared suite (#154).
- Quiet helper waits with immutable generation/completion receipts, named pending work and per-run Stop reconciliation.
- Owned lane start/stop/status, short browser profiles, explicit cache adapters and helper working-directory verification.

### Changed

- Intact matching complete-suite evidence returns before execution queue admission; misses retain FIFO admission and post-admission rechecks (#176).
- Accepted PNG checks reuse bounded, authenticated validation across gate processes; image Try accepts `.png`, explains unsupported formats, and thumbnails follow validated current bytes even when timestamps do not advance (#177).
- Factory maintenance separates the immutable gate runner from its editable candidate, allows an explicit approved unmerged base, and commits planned edits before final proof using the selected runner's capabilities (#178).
- Current helper receipts take priority over stale report directions; reports published after completion restore the next action.
- Combined factory commands retain selected-bundle routing, with lazy CLI registration split from the hook path to keep the gate small.
- Worth-it repairs (#157): bounded finding scores prioritize optional polish, Fast/Lucky and new Safe runs validate selected fixes, authorized Finishing touches batches reuse the epic's existing follow-ups, and parked reports explain what waits without weakening mandatory quality or owner authority.
- New runs (#160): automatic project selections refresh to the newest verified immutable bundle; active, explicit and legacy-unknown pins stay intact. Start reports selected/latest versions and failed newer releases, and project commands/hooks follow the selected gate.

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

[Unreleased]: https://github.com/seifsg/ai-software-factory/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/seifsg/ai-software-factory/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/seifsg/ai-software-factory/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/seifsg/ai-software-factory/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/seifsg/ai-software-factory/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/seifsg/ai-software-factory/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/seifsg/ai-software-factory/releases/tag/v1.0.0
