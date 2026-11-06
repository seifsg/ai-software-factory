# Changelog

Every notable change to the AI Software Factory, newest first. The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). This file and [UPGRADING.md](UPGRADING.md) are the only places for release history.

The public surface is the skill names, the run file format, and the hook scripts and events. How to write an entry and pick a version: [releasing](docs/releasing.md#changelog).

## [Unreleased]

### Changed

- Run the Stop check as two small hooks, one more model call per stop in a run; tested limits are in `docs/hosts.md` ([#302])
- Make a review's run audit check each gate line's backing, because the Stop check's small model can pass a forged one; with no records on the machine it notes that and does not block ([#302])

### Fixed

- Fix a looping agent running to the turn limit on Sonnet: a repeated step or todo number now ends it ([#302])
- Fix runs ending after a wait because the Stop check was already spent ([#302])

## [0.7.0] - 2026-11-05

### Changed

- **Breaking:** Move night tools, `pre-push` and Codex rules to `tools/night/`; update schedules and copied paths ([#295])
- Make Claude Code runs use a prompt Stop check instead of command hooks, so the plugin meets Anthropic's directory rules with no exception ([#295])
- Show the update notice at a run's first step on Claude Code, not at every session start ([#295])
- Re-arm the Stop check at every step on Claude Code through a new `stop-check` skill, because a stop removes it ([#297])

### Removed

- Remove the credit line from pull requests the factory writes in other repositories ([#295])

### Added

- Add a plugin README, `PRIVACY.md`, `SECURITY.md` and an icon for the directory listing ([#295])

### Security

- Cut how long a looping agent runs: the Stop check continues only after a new step block or todo line; a small model keeps this limit ([#297])
- Stop reading conversation files on Claude Code: gates are judged by a small model, and no script checks that blocks reached chat ([#295])

## [0.6.2] - 2026-11-04

### Added

- Add the MIT license ([#292])
- Add a `stable` branch that moves on every release, so a store listing follows released versions only ([#292])

### Fixed

- Fix the update notice telling Cursor users to reinstall, which Cursor staff advise against ([#292])
- Fix a second run in one session inheriting the first run's failed gate rounds, which offered a cap on a gate it never ran ([#292])

## [0.6.1] - 2026-11-04

### Added

- Let a run the owner keeps local finish with no PR ([#290])
- Add one clean format for run files, chat blocks and handbacks: short lines, tables, ASCII graphs, status marks, optional linked visuals ([#290])

### Changed

- Keep a run and its code in the project folder the owner names, even when the session cannot move there ([#290])

### Fixed

- Fix the guard doing nothing under the awk macOS ships: every stop passed silently, so no step or gate was enforced ([#290])
- Fix a misspelled or missing `Waiting:` line letting an agent stop silently: the guard drives the run and shows the exact header ([#290])
- Fix a skipped step going unnoticed: the guard names it, and a run cannot finish with one ([#290])
- Fix walls of text in the run file: the guard names any line over 300 characters ([#290])
- Fix a closed run asking for Gate C again after its checkout moved on ([#290])
- Fix a project with no remote never passing Gate C ([#290])
- Fix guard prompts on Windows naming Git Bash paths the agent could not open ([#290])

## [0.6.0] - 2026-11-04

_Upgrade needed: start a new session, and Codex trusts its hooks again; follow [UPGRADING.md](UPGRADING.md#060)._

### Changed

- **Breaking:** Make the Claude Code Stop guard load with the `safe-factory` skill, so other sessions start no guard process; a run's start may ask once to allow it ([#286])
- Move a run to a fresh session when its guard is not live on a host with hooks ([#286])

### Fixed

- Fix runs outside the session's folder getting no guard or warning: a session binds to the run its step block names, or the guard asks for the folder ([#286])

## [0.5.0] - 2026-11-03

_Upgrade needed only for night mode installs that copied the allow list; follow [UPGRADING.md](UPGRADING.md#050)._

### Changed

- **Breaking:** Move PR proof media to `refs/proof/<branch>` so clones stop downloading them; night mode that copied the allow list adds the new entry ([#283])
- Let a run check every gate line itself before it briefs the checker, so gates stop failing on form ([#283])

### Fixed

- Fix tickets staying open after their PR merged: Gate C now fails a PR without `Closes #<n>` for each ticket it finishes ([#283])
- Fix the update check leaving a hanging `gh` behind each session start: it stops after 20 s and the next start sweeps its leftovers ([#283])

## [0.4.4] - 2026-11-03

### Fixed

- Fix a Fast run hiding its step blocks: the Stop guard now asks the agent to post any finished step whose block never reached chat ([#280])
- Fix a run halting itself on an emoji in a message, and count a plugin install as a live guard so each step gets its own turn ([#280])
- Fix the session-start cleanup offering to move tracked files out of an old factory checkout; it now names the checkout and the command to update it ([#280])

## [0.4.3] - 2026-11-03

_Upgrade needed on Codex: re-add the marketplace sparse once; follow [UPGRADING.md](UPGRADING.md#043)._

### Fixed

- Fix the update notice missing new releases: the check now refreshes at every session start and retries after a failed fetch ([#277])
- Fix `codex plugin marketplace upgrade` timing out: the Codex install fetches only the plugin (`--sparse`), and the notice names the one-time re-add ([#277])

## [0.4.2] - 2026-11-03

_Upgrade needed: Codex trusts the changed hooks again, Cursor keeps one plugin; follow [UPGRADING.md](UPGRADING.md#042)._

### Changed

- Let Cursor run the plugin's own hooks; it also loads an installed Claude Code plugin, so install only one of the two ([#274])

### Fixed

- Fix the run guard never running in Cursor on Windows, and hanging outside a Git repo on a Windows drive path ([#274])

## [0.4.1] - 2026-11-03

_Upgrade needed on Codex for Windows: trust the changed hooks again; follow [UPGRADING.md](UPGRADING.md#041)._

### Fixed

- Fix step blocks (Recommend, Plan and the rest) missing from chat when steps chain in one turn or your own instructions ask for short replies ([#269])
- Fix Fast runs stopping after a step when the Stop hook never fires or starts outside the session's folder, as in desktop worktree sessions and Cursor ([#270])
- Fix Codex on Windows never sending the next step: hooks now run through Git Bash and say how to install it when missing ([#267])

## [0.4.0] - 2026-11-02

_Upgrade needed: run `doctor.sh --fix` once and add `Left running:` to open runs; follow [UPGRADING.md](UPGRADING.md#040)._

### Changed

- **Breaking:** Make every run stop what it started (servers, watchers, schedules, worktrees, hooks) before Gate C and list what stays in `Left running:` ([#262])

### Added

- Add `doctor.sh`, which lists leftovers of old factory versions at each session start and moves them to a backup with `--fix` ([#262])

## [0.3.0] - 2026-11-02

_Upgrade needed: the plugin is now `safe-factory`; follow [UPGRADING.md](UPGRADING.md#030)._

### Changed

- **Breaking:** Rename the plugin and its entry skill from `safe-engine` to `safe-factory`: run `/safe-factory`, or `$safe-factory` in Codex ([#260])
- Give the README one setup table per host: install, run, one skill alone, update and uninstall for Claude Code, Codex and Cursor ([#260])

### Fixed

- Fix the README version badge, which still showed 0.1.0 after the 0.2.0 release; it now reads the Latest release ([#258])
- Fix the update check staying silent without a signed-in GitHub CLI; it falls back to `curl` ([#258])

## [0.2.0] - 2026-11-02

_Renumbered: under the bump table adopted after this release it would be 0.1.1; published versions stay._

### Changed

- Let a gate or review loop pass after 3 rounds with no open critical finding, so runs never stall on nits; leftovers go to follow-ups ([#254])
- Make the checker list every miss, form included, in its first round, and recheck only that list after ([#254])
- Keep a live preview of the work in front of the owner from step 4 on, for every kind of project ([#254])

### Fixed

- Fix Fast runs waiting for `Say go` after every step when the Stop hook is not loaded; steps now chain, and step 0 says whether the guard is live ([#254])

## [0.1.0] - 2026-11-02

_Fresh start replacing the deprecated 1.x line; Claude Code installs reinstall once (see [UPGRADING.md](UPGRADING.md#010))._

### Changed

- **Breaking:** Run every task as ten visible steps (ticket, analyze, recommend, challenge, plan, Before proof, build, verify, PR, review), each posted to the owner, the ticket and `.factory/run.md` ([#232])
- **Breaking:** Count a gate or review line only when the named checker or reviewer's own transcript holds it on that commit ([#241])
- **Breaking:** Write `Gate C` under `## 8 Review` and run it once, after the review, on the final head ([#232])
- **Breaking:** Give every `Waiting: jobs:` line a deadline, `(max <n> min)` ([#241])
- **Breaking:** Build at the size the owner names, with no default; open runs drop an unnamed size label ([#244])
- **Breaking:** Move the plugin root to `.agents/` and the delegate roles to `.agents/agents/` ([#232])
- Run one step per turn: a Stop guard sends the next step's prompt and catches two steps ticked at once ([#232])
- Cap every review, gate and fix loop at 3 rounds, 5 with an open critical finding, then halt with one owner packet; resume with `run-guard.sh clear` ([#241])
- Hand a run to a fresh session after two compactions, and repeat the next step after each one ([#232], [#241])
- Make `recommend` show three solutions in one table with one pick, and pick one of three looks at step 2 ([#232], [#244])
- Add a UI pass at verify and polish the primary platform first, the secondary after the owner confirms it ([#244])
- Take screenshots from the host's built-in browser, never headless scripts unless asked ([#232])
- End a solo owner's run by asking them to verify and merge, with no review request ([#232])
- Make `how-to-review-a-pr` its own skill again ([#232])
- Rework the README with a run card, a three-point why and a 3-step quick start per host ([#251])

### Added

- Add plugins for Claude Code, Codex and Cursor from one `.agents/` root; Codex and Cursor not yet run live ([#248])
- Add an update check that tells the owner at step 0 when a newer release is out; off with `FACTORY_NO_UPDATE_CHECK=1` ([#248])
- Add step 2b Challenge, which rechecks the recommendation and posts `kept` or `changed` with the reason ([#232])
- Add overnight runs: `night.sh` starts only a run that can finish unattended, also with a CLI off PATH (`FACTORY_CLAUDE`, `FACTORY_CODEX`), and `watchdog.sh` resumes stalled ones ([#241], [#242])
- Add a `pre-push` hook that blocks pushes to the default branch, force pushes and token shapes ([#241])
- Add the checker role, which checks step outputs against their contracts at gates A, B and C; lens reviewers never count as review rounds ([#232], [#242])
- Let a new project start with no setup: folder, `git init` and a private GitHub repository are created for it ([#232])
- Let the owner waive a gate with `Gate <X>: WAIVED by owner` ([#232])

### Removed

- **Breaking:** Remove all Python: the `fast_gate.py` gate, Safe controller, installer, self-update, metrics and test suite ([#232])
- **Breaking:** Remove Lucky mode, the Show, Look, Prove and Ship phases, the product bar and the `ux-quality` skill ([#232])

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

[Unreleased]: https://github.com/seifsg/ai-software-factory/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/seifsg/ai-software-factory/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/seifsg/ai-software-factory/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/seifsg/ai-software-factory/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/seifsg/ai-software-factory/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/seifsg/ai-software-factory/compare/v0.4.4...v0.5.0
[0.4.4]: https://github.com/seifsg/ai-software-factory/compare/v0.4.3...v0.4.4
[0.4.3]: https://github.com/seifsg/ai-software-factory/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/seifsg/ai-software-factory/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/seifsg/ai-software-factory/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/seifsg/ai-software-factory/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/seifsg/ai-software-factory/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/seifsg/ai-software-factory/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/seifsg/ai-software-factory/releases/tag/v0.1.0
[1.3.0]: https://github.com/seifsg/ai-software-factory/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/seifsg/ai-software-factory/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/seifsg/ai-software-factory/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/seifsg/ai-software-factory/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/seifsg/ai-software-factory/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/seifsg/ai-software-factory/releases/tag/v1.0.0

[#297]: https://github.com/seifsg/ai-software-factory/pull/297
[#295]: https://github.com/seifsg/ai-software-factory/pull/295
[#292]: https://github.com/seifsg/ai-software-factory/pull/292
[#290]: https://github.com/seifsg/ai-software-factory/pull/290
[#232]: https://github.com/seifsg/ai-software-factory/pull/232
[#241]: https://github.com/seifsg/ai-software-factory/pull/241
[#242]: https://github.com/seifsg/ai-software-factory/pull/242
[#244]: https://github.com/seifsg/ai-software-factory/pull/244
[#248]: https://github.com/seifsg/ai-software-factory/pull/248
[#251]: https://github.com/seifsg/ai-software-factory/pull/251
[#254]: https://github.com/seifsg/ai-software-factory/pull/254
[#258]: https://github.com/seifsg/ai-software-factory/pull/258
[#260]: https://github.com/seifsg/ai-software-factory/pull/260
[#262]: https://github.com/seifsg/ai-software-factory/pull/262
[#267]: https://github.com/seifsg/ai-software-factory/pull/267
[#269]: https://github.com/seifsg/ai-software-factory/pull/269
[#270]: https://github.com/seifsg/ai-software-factory/pull/270
[#274]: https://github.com/seifsg/ai-software-factory/pull/274
[#277]: https://github.com/seifsg/ai-software-factory/pull/277
[#280]: https://github.com/seifsg/ai-software-factory/pull/280
[#283]: https://github.com/seifsg/ai-software-factory/pull/283
[#286]: https://github.com/seifsg/ai-software-factory/pull/286
[#302]: https://github.com/seifsg/ai-software-factory/pull/302
