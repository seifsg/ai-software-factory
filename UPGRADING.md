# Upgrading

What installs and active runs must do for each release, newest first. What changed: [CHANGELOG.md](CHANGELOG.md).

## 0.4.1

1. **Codex on Windows:** `codex plugin marketplace upgrade ai-software-factory`, start a new chat and trust the changed hooks in `/hooks`. The plugin now finds Git Bash beside `git.exe` on `PATH`; no hook-trust bypass or PowerShell policy change is needed. Verify the ticket response is followed by an automatic analysis prompt and full response in a separate turn. Hand-copied hooks still need Git's `sh` on `PATH` as described in [install](docs/install.md#codex).

## 0.4.0

1. **Every install, once:** from each project that had factory hooks, run `sh <plugin root>/skills/safe-factory/scripts/doctor.sh --fix` ([clean up](docs/install.md#clean-up-and-uninstall)). It moves 1.x hooks and launchers, `~/.safe-engine`, old-path project hooks and stale `pre-push` and `codex.rules` copies to a backup, and names what needs a hand edit (the old `safe-engine@` id, hook files holding other settings). Not covered: `--codex-home <dir>` installs and a Codex `safe-engine@` plugin: clean those per 0.1.0 and 0.3.0.
2. **Open runs before Gate C:** add `Left running: <item, stop command>` or `Left running: none` to `## 8 Review` before Gate C.

## 0.3.0

The plugin and its entry skill are now `safe-factory`.

1. **Claude Code:** run `claude plugin marketplace update ai-software-factory`, then `/plugin install safe-factory@ai-software-factory` once, and start a new session. The marketplace maps `safe-engine` to `safe-factory`, so this replaces the old plugin and keeps its settings: nothing to uninstall.
2. **Codex:** `codex plugin marketplace upgrade ai-software-factory`, `codex plugin remove safe-engine@ai-software-factory`, `codex plugin add safe-factory@ai-software-factory`, then trust the hooks again in `/hooks`. Copied skills: `git -C <clone> pull`, `rm -rf ~/.agents/skills/safe-engine`, `cp -r <clone>/.agents/skills/* ~/.agents/skills/`, then step 4.
3. **Cursor:** in `/plugin`, uninstall `safe-engine` and install `safe-factory`.
4. **Hooks you copied by hand**, on any host: change `skills/safe-engine/` to `skills/safe-factory/` in every file that has it: `.claude/settings.json`, `.claude/settings.local.json`, `~/.claude/settings.json`, `~/.codex/hooks.json`, `<project>/.codex/hooks.json`, `~/.cursor/hooks.json`, `<project>/.cursor/hooks.json`. Until then the guard does not run; the night preflight reports it missing.
5. **Open runs and night jobs:** resume with `safe-factory Resume <dir>`; a `FACTORY_START`, `FACTORY_RESUME` or `FACTORY_FRESH` override or scheduled command that names `safe-engine` must name `safe-factory`.

## 0.2.0

Nothing to do: update the plugin. Open runs keep going; the guard applies round caps and step chaining from its next stop.

## 0.1.0

A fresh start: 0.1.0 replaces the deprecated 1.x line. The factory no longer runs any Python. Old runs cannot continue under 0.1.0.

1. **Finish or abandon open runs first** on 1.x (`fast_gate.py close`, or `close --abandon` with a reason). New runs start fresh with `.factory/run.md`; old `.factory/` run records are not read.
2. **Claude Code:** reinstall once, since 0.1.0 is a lower number than 1.3.0: `claude plugin marketplace update ai-software-factory`, `claude plugin uninstall safe-engine@ai-software-factory`, `claude plugin install safe-engine@ai-software-factory`. The old gate hooks go with the old version. Later releases update normally.
3. **Codex, Cursor and other copies:** delete the old launchers (`~/.agents/skills/safe-engine`, `~/.agents/skills/improve-factory`), remove every entry that runs `run-gate.sh` or `fast_gate` from `~/.codex/hooks.json` and `~/.cursor/hooks.json`, then install per [docs/install.md](docs/install.md). A leftover entry would call a script that no longer exists. Installs made with `--project <dir>` also wrote `<dir>/.agents/skills/` and `<dir>/.codex/hooks.json` or `<dir>/.cursor/hooks.json`; `--codex-home <dir>` wrote `<dir>/hooks.json`. Clean those the same way.
4. **Delete `~/.safe-engine`** once no 1.x run needs it. It held run state, bundles, caches and the self-update clone.
5. Runs opened on main before 0.1.0: the Gate C line now sits under `## 8 Review` and runs after the review; move an existing Gate C line there and rerun its checker once.
6. Factory clones: old commands (`python tests/run.py`, `scripts/release.py`, `python -m safe_engine`) are gone; checks are in `AGENTS.md`.
7. Runs opened on main before 0.1.0, and the guarded relay: a gate line now needs its commit (`Gate X: PASS (checker <id>) @<sha>`) and a checker brief that names it; a finished run also needs `Review: ready (reviewer <id>) @<sha>` on the pushed HEAD. Rerun the checker of each gate the run already passed, and the step 8 reviewer if step 8 is ticked. Give every `Waiting: jobs:` a `(max <n> min)`. The guard moves `.factory/run.md.ticks` and `.nudge` into `.factory/guard/` by itself.
8. Open runs with a size the owner never named (Fast's old "POC when unsure"): drop the label, and give logic a small test map entry.
9. Overnight runs are opt-in: [install](docs/install.md#overnight-runs). Nothing changes until you install the `pre-push` hook or start `night.sh`.

## 1.3.0

- Update launchers for `enroll-worktree`; use it only for a new Git worktree that inherited another run's files. The source run is untouched.
- Update launchers for `report --pr-body`; it validates local draft structure without completing a step or replacing final published-PR checks. Existing pins stay intact. Accepted `fix-round` output adds its stored `report_sha256`; no input or record migration is needed.
- A `start` without a selection now selects first, so offline starts need an existing selection or cache. Explicit and legacy pins skip the latest-release check. Active runs keep their recorded policies.

## 1.2.0

- After release, update launchers for `metrics` (`report`, `compare`, `export`, `delete`, `overhead`, `usage`, `task`). New Fast/Lucky/Safe runs write local analytics under `.factory/metrics/` (gitignored). Mark task boundaries only when observed; existing active pins stay unchanged and need no metrics migration. See [run metrics](https://github.com/seifsg/ai-software-factory/blob/v1.3.0/docs/run-metrics.md).

- Fast methods now bound delegation and proof work; no command, record schema or frozen plan migration is required. Existing runs retain their pinned methods, coverage and stops. Use the revised methods after a human release/update or explicit compatible adoption; this change never resumes a paused project or installs itself. Cross-candidate Show reuse remains unsupported.
- Selective CLI loading needs the updated bundle after release; no flags or schemas change. For local Windows factory tests, use `python tests/run.py` to select installed Git shells inside its processes. No global shell or host setting needs changing.
- New runs read detailed logging/security and visual proof cases through explicit pointers. Existing pins and frozen plans keep their methods; no record migration is required. `token_report.py` now labels phase/condition rows as non-additive file-text proxies.
- Release maintainers: replace the merged-commit `python tests/run.py` step with `python scripts/release.py prove vX.Y.Z`. Publication reuses its matching proof or runs the suite; normal installs and active pins need no migration.

## 1.1.2

- After release, update the factory for scoped Show plans. New input defaults to light desktop and Before/After; mobile apps select light phone, and required extra variants are explicit. Existing stored plans and active pins retain their coverage. Design ports select design comparison and keep every frozen reference. No active-run migration is required; see [Show](https://github.com/seifsg/ai-software-factory/blob/v1.3.0/docs/show-first.md).

## 1.1.1

- Update the full factory repository before eval runs. Ownership setup/resume failures now refuse execution, and unconfirmed cleanup reports an error. The isolated checker snapshots the canonical ownership helper; no saved-run or active-pin migration is needed. The immutable 1.1.0 tag remains, but its GitHub publication stopped on a cleanup regression; use this fix-forward release.

## 1.1.0

- Existing Claude Code installs: after release, update the factory and rerun `python skills/safe-engine/scripts/fast_gate.py install --host claude` if `claude plugin list --json` lacks the enabled `safe-engine@ai-software-factory` entry. The installer now installs and verifies the plugin, not only its settings. Start a new Claude Code session afterward. Keep active factory bundle pins unchanged.

- Record refusals now collect independent problems, and quoted FAIL text no longer overrides an explicit verdict. Existing runs keep their pins. See [record diagnostics](https://github.com/seifsg/ai-software-factory/blob/v1.3.0/docs/record-diagnostics.md).

After release, update launchers for `prove --plan` and `prove --suite --fresh`. New Fast plans declare their suite before plan completion; explicit `suite_inputs` enables reuse. New Safe states adopt the shared complete-suite queue automatically. Existing runs keep their saved policy and bundle. See [complete suites](https://github.com/seifsg/ai-software-factory/blob/v1.3.0/docs/suite-checks.md).

Journey checks should import the resolved bundle's fixed-clock helper, declare an explicit instant/timezone and list their files in the journey lint manifest. Update new plans with an affected-test command and mapping; complete suites still wait for Prove. Existing active pins stay unchanged. See [fixed browser time](https://github.com/seifsg/ai-software-factory/blob/v1.3.0/docs/journey-clock.md).

- New Fast/Lucky runs record `checks --plan` before plan and current check receipts before completion. Existing runs retain their prior checks. After release update launchers for `checks`; keep active bundles pinned. See [hidden checks](https://github.com/seifsg/ai-software-factory/blob/v1.3.0/docs/hidden-checks.md).
- New report publication checks picture content. Convert palette/interlaced/animated images to static 8-bit RGB/RGBA PNGs and inspect the result. Install updated launchers for `report`; supply honest per-ticket metrics or unavailable reasons. Existing saved reports are not fabricated from session totals.

- Worth-it rounds: update the installed launchers to obtain `fix-round`; new Fast/Lucky runs record `**Findings:** none` or their final scored report path. New complete-cycle Safe runs require worth fields and explicit repair selections. Existing saved runs keep their prior checks/schema. Do not upgrade an active run's pinned bundle. See [worth-it rounds](https://github.com/seifsg/ai-software-factory/blob/v1.3.0/docs/worth-it.md).

New UI runs on the resolved current bundle freeze a Show plan and share current pictures before proof. Existing runs keep their recorded sequence; do not rewrite active ledgers. See [Show first](https://github.com/seifsg/ai-software-factory/blob/v1.3.0/docs/show-first.md).

- New design-port runs use `start --design-port` and record reference coverage before plan. Existing runs keep their selected methods and obligations; do not add the flag or rewrite their ledger mid-run.

- Reinstall launchers/hooks for `wait` commands. New runs require explicit supported wait receipts; existing runs retain their prior host-list behavior until they register a wait. Completion callbacks must use the selected gate and the original gate home.

- Reinstall the launchers/hooks to enable new-run selection and selected-gate routing. Existing active runs retain their bundle and recorded behavior.
- New automatic receipts refresh at the next start, or with `resolve_bundle.py --project <dir> --new-run`. Resume omits `--new-run` and remains offline. Explicit selections and existing v1 receipts retain their pin; v1 has no trustworthy pin provenance and is never automatically migrated.
- Latest-check failures name the version retained. An unknown latest is not a successful check. Read a newly selected entrypoint before continuing the run. Bare-gate starts without a receipt remain legacy use.

## 1.0.0

From an install made before versioning:

- **Claude Code:** nothing to do. The plugin moves to 1.0.0 once tag `v1.0.0` is published and loads on `/reload-plugins` or a new session. Until that tag exists, a new install cannot fetch the plugin; an existing one keeps its copy.
- **Codex, Cursor and other, installed from a clone with auto-update:** nothing to do. The next daily update brings the new updater; from then on the clone follows release tags and stays detached at the newest verified one. To follow `main` instead: `fast_gate.py install --host <host> --channel edge`.
- **Installed by hand or with `--no-auto-update`:** in your clone run `git fetch --tags` and `git checkout v1.0.0`, then rerun `fast_gate.py install --host <host>`.
- **Active runs:** no action; each keeps its pinned bundle. Safe runs saved before 1.0.0 load on any 1.x bundle.
- **New projects:** pin the newest verified release instead of `main`; on the edge channel, `main`.
