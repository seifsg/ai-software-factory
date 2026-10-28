# Upgrading

What installs and active runs must do for each release, newest first. What changed: [CHANGELOG.md](CHANGELOG.md).

For every release:

- **Active and explicit pins never change automatically.** Ask `improve-factory` for a compatible pin change; never edit a selected bundle or receipt.
- **Check what you run:** `fast_gate.py version` names the version, commit, channel and route; `fast_gate.py verify` lists every file that differs from the release manifest.

## Next release

- After updating, use `fast_gate.py enroll-worktree --project <new-worktree> --source <original-worktree> --bundle <reviewed-factory> --reason "<owner authority>"` only for an unregistered Git worktree inheriting unchanged tracked legacy run files. Read its archived lineage, then start a distinct run normally. The source must retain its registered open run. Enrollment keeps the source and inherited evidence intact; it does not resume, move or upgrade that run. Existing installs and pins need no migration.

## 1.2.0

- After release, update launchers for `metrics` (`report`, `compare`, `export`, `delete`, `overhead`, `usage`, `task`). New Fast/Lucky/Safe runs write local analytics under `.factory/metrics/` (gitignored). Mark task boundaries only when observed; existing active pins stay unchanged and need no metrics migration. See [run metrics](docs/run-metrics.md).

- Fast methods now bound delegation and proof work; no command, record schema or frozen plan migration is required. Existing runs retain their pinned methods, coverage and stops. Use the revised methods after a human release/update or explicit compatible adoption; this change never resumes a paused project or installs itself. Cross-candidate Show reuse remains unsupported.
- Selective CLI loading needs the updated bundle after release; no flags or schemas change. For local Windows factory tests, use `python tests/run.py` to select installed Git shells inside its processes. No global shell or host setting needs changing.
- New runs read detailed logging/security and visual proof cases through explicit pointers. Existing pins and frozen plans keep their methods; no record migration is required. `token_report.py` now labels phase/condition rows as non-additive file-text proxies.
- Release maintainers: replace the merged-commit `python tests/run.py` step with `python scripts/release.py prove vX.Y.Z`. Publication reuses its matching proof or runs the suite; normal installs and active pins need no migration.

## 1.1.2

- After release, update the factory for scoped Show plans. New input defaults to light desktop and Before/After; mobile apps select light phone, and required extra variants are explicit. Existing stored plans and active pins retain their coverage. Design ports select design comparison and keep every frozen reference. No active-run migration is required; see [Show](docs/show-first.md).

## 1.1.1

- Update the full factory repository before eval runs. Ownership setup/resume failures now refuse execution, and unconfirmed cleanup reports an error. The isolated checker snapshots the canonical ownership helper; no saved-run or active-pin migration is needed. The immutable 1.1.0 tag remains, but its GitHub publication stopped on a cleanup regression; use this fix-forward release.

## 1.1.0

- Existing Claude Code installs: after release, update the factory and rerun `python skills/safe-engine/scripts/fast_gate.py install --host claude` if `claude plugin list --json` lacks the enabled `safe-engine@ai-software-factory` entry. The installer now installs and verifies the plugin, not only its settings. Start a new Claude Code session afterward. Keep active factory bundle pins unchanged.

- Record refusals now collect independent problems, and quoted FAIL text no longer overrides an explicit verdict. Existing runs keep their pins. See [record diagnostics](docs/record-diagnostics.md).

After release, update launchers for `prove --plan` and `prove --suite --fresh`. New Fast plans declare their suite before plan completion; explicit `suite_inputs` enables reuse. New Safe states adopt the shared complete-suite queue automatically. Existing runs keep their saved policy and bundle. See [complete suites](docs/suite-checks.md).

Journey checks should import the resolved bundle's fixed-clock helper, declare an explicit instant/timezone and list their files in the journey lint manifest. Update new plans with an affected-test command and mapping; complete suites still wait for Prove. Existing active pins stay unchanged. See [fixed browser time](docs/journey-clock.md).

- New Fast/Lucky runs record `checks --plan` before plan and current check receipts before completion. Existing runs retain their prior checks. After release update launchers for `checks`; keep active bundles pinned. See [hidden checks](docs/hidden-checks.md).
- New report publication checks picture content. Convert palette/interlaced/animated images to static 8-bit RGB/RGBA PNGs and inspect the result. Install updated launchers for `report`; supply honest per-ticket metrics or unavailable reasons. Existing saved reports are not fabricated from session totals.

- Worth-it rounds: update the installed launchers to obtain `fix-round`; new Fast/Lucky runs record `**Findings:** none` or their final scored report path. New complete-cycle Safe runs require worth fields and explicit repair selections. Existing saved runs keep their prior checks/schema. Do not upgrade an active run's pinned bundle. See [worth-it rounds](docs/worth-it.md).

New UI runs on the resolved current bundle freeze a Show plan and share current pictures before proof. Existing runs keep their recorded sequence; do not rewrite active ledgers. See [Show first](docs/show-first.md).

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
