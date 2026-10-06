# Use the Safe Engine pilot

## Small direct changes

This route is for requested implementation. An explicit analysis, planning or review request stays in that phase.

Seif selected [small-change](../.agents/skills/small-change/SKILL.md) on 3 October: six light routines, focused checks and one narrow assessment. Preserve that route for legacy unticketed work. New implementation uses [Ticketing](../.agents/skills/ticketing/SKILL.md) and the full cycle, even bugfixes; keep changes surgical and checks relevant. Existing pins, state and historical acceptance stay intact.

[Ticket usage](ticketing.md) owns exact capture, confirmation, session, dependency and proof commands. Prefer the owner's authorized tracker MCP; GitHub Issues is the default and Seif's current choice. Every ticket needs an actually dispatched dedicated builder session. Use `--ticket <key>` on its commands and `init ... --session <real-builder-session-id>`. State/output live under `.factory/runs/<key>/`; legacy `.factory/state.json` stays unchanged. Start ticket runs in fresh worktrees; shared epic checkouts serialize ticket writers. The controller provisions no sessions, worktrees or host automation.

Safe Engine 0.1.0 is a local, agent-operated delivery loop. The current Codex session builds the feature using Seif's methods. Python records stages and executes checks; a fresh read-only Codex CLI process reviews the final candidate. The controller creates a checked local handoff. It does not push, merge, deploy, or run as an unattended daemon.

## Start through Codex

Open this repository as the Codex project and ask:

> Use $safe-engine to implement this feature in [absolute target project path]: [request]. Follow analyze-start and get-ready-to-code. Work in substantial batches and stop at a checked handoff.

From another project, [install the portable Safe Engine skill](install-safe-engine.md) and invoke `$safe-engine`. You can also explicitly reference this bundle's `.agents/skills/safe-engine/SKILL.md` by absolute path. Repository skills are not automatically installed globally or into other repositories. Codex normally discovers `.agents/skills` within its repository scope. [Official skill documentation](https://learn.chatgpt.com/docs/build-skills).

Requirements: Python 3.9+, Git, authenticated Codex CLI, and the target project's actual check dependencies. Browser work additionally requires a working browser driver and a runnable test application. Use a suitable existing isolated worktree or the host's worktree tool. The demo uses an explicitly created disposable Git worktree.

Before dependent work, use `preflight --profile <profile.json>` to inspect available capabilities without launching an app or test. Record missing interaction/audio/device/integration evidence and the actual remote/cloud PR-review route; the local Codex CLI supplies controller review only. Follow [Delivery Readiness](../.agents/skills/safe-engine/references/delivery-readiness.md). Actual product tests, manual user QA and playtests all wait until implementation finishes. App/game/mobile pilots and simulations remain deferred until specifically requested.

## Configure a task

Run commands from this bundle's root. On Windows, use the full path of the real Python executable if `python` resolves to the Windows Store launcher.

```text
python -m safe_engine --project <absolute-project-root> discover
```

Discovery reads Git and package scripts without executing them. Review the proposed interface and supply real commands. Add `.factory/` to the target project's ignore rules, preserve existing work, and establish a clean committed baseline. Runtime artifacts belong in `.factory/` or an excluded external directory, not in the source candidate.

Version 2 is the new-run workflow. `init` accepts draft check definitions and empty `checks`/`protected_paths`; no early test creation. Declare `test_paths` for final test authoring and applicable `review_scopes` (`ui`, `assets`, `persistence`, `research`, `seo`, `security`, `integrations`, `release`). Set actual `exposure`: `local` (default), `public` or `production`. Core methods always apply; explain exclusions. Final `seal` validates complete reviewed task/profile and protected inputs. Review test-path exclusions; never hide production/configuration files there.

Choose checks before coding from changed effects/consumers, under Delivery Readiness. Guidance-only work needs real instruction use and fitting structural checks; runtime/config/policy or mixed work needs affected behavioral evidence. Every configured check runs. Saved/failed profiles cannot be narrowed to avoid checks; legitimate changes keep reviewed amendment rules.

Minimal draft shape; replace interface, scopes and paths with actual choices:

```json
{
  "version": 2, "interface": "cli", "exposure": "local",
  "checks": [], "protected_paths": [], "test_paths": ["tests"],
  "environment_inputs": [], "input_files": [], "review_scopes": []
}
```

Task keeps original `request` and `acceptance` entries with `id`, `text`, `mode`, `checks`. `manual` needs `checks: []`; `automated`/`mixed` may start empty but need real check IDs before sealing. No product testing is implied by writing a profile.

The following version-1 profile is a **legacy example**, retained for existing runs. Its fixed tests and two-check sequence are not the new-project default:

```json
{
  "version": 1,
  "interface": "web",
  "checks": [
    {"id": "unit", "kind": "unit", "argv": ["node", "tests/unit.mjs"], "timeout_seconds": 60},
    {"id": "browser", "kind": "browser", "argv": ["node", "tests/browser.cjs"], "timeout_seconds": 120,
     "artifacts": [".factory/outputs/browser/mobile.png", ".factory/outputs/browser/mobile-complete.png", ".factory/outputs/browser/desktop.png"]}
  ],
  "environment_inputs": ["NODE_ENV"],
  "input_files": [],
  "protected_paths": ["tests/unit.mjs", "tests/browser.cjs"]
}
```

Commands are argument arrays, not shell strings. `{python}`, `{project}`, and `{run}` expand to the current interpreter, target root, and local runtime directory. Explicitly use the right executable for the platform; npm shell wrappers may need a platform-specific command. Commands are trusted configuration reviewed by the operator, not a sandbox for untrusted test code.

Declare relevant environment variables and ignored/external inputs; content is hashed, not copied into records. Include dependency manifests, runtime configuration and test-data identity where applicable. Discovery cannot infer every mutable service/database/hidden input. Source equality alone proves no unchanged runtime. Legacy version-1 duplicate-gate reuse requires reviewed `reuse_unchanged_checks: true`, controlled declared identities and unchanged evidence; volatile backend/clock/hardware/permissions require fresh checks. Version 2 has one final gate, so no duplicate execution to optimize away.

`protected_paths` holds sealed accepted checks. Read them during development; testing waits until implementation and manual QA finish. Version 2 permits independent reviewed contract amendments rather than silent file/state changes: preserve old/new contract digests and protected hashes, reason, reviewer identity/verdict and actual authority. Amendment invalidates acceptance and returns through completed implementation and final manual QA. Never erase failures, revive cancellation or weaken expectations for green. Legacy version-1 contracts retain their original boundary. Same-user records remain workflow integrity, not hostile-user protection.

Optional per-check `artifacts` list generated evidence files under `.factory/outputs/` for unbound runs, or `.factory/runs/<key>/outputs/` for tickets. `{run}` selects that run's namespace. The runner removes only declared outputs before the command, requires fresh files afterwards, and verifies hashes before review/handoff. Configure actual paths; old screenshots cannot substitute for a new run.

Legacy task JSON; version 2 additionally declares criterion `mode` as `manual`, `automated` or `mixed`. Manual criteria need real structured receipts, not dummy executable checks:

```json
{
  "request": "The original requested outcome",
  "acceptance": [
    {"id": "A1", "text": "An observable required outcome", "checks": ["unit", "browser"]}
  ]
}
```

Resolve material unknowns before dependent choices. Prepared analysis/plans may be recorded in stage order. Version-2 acceptance stays draft until final sealing; legitimate later changes use `amend` with independent reviewed authority/history. A changed contract is no permission to hide failure or expand product scope.

Initialize with the completion boundary and authority recorded in the [session contract](../.agents/skills/safe-engine/references/session-contract.md). No numerical correction allowance or session deadline is required or invented. Keep actual owner stop/checkpoint and provider/access constraints. Individual check/review timeouts diagnose hung commands; they are not a whole-session limit:

```text
python -m safe_engine --project <project> init --task <task.json> --profile <profile.json>
python -m safe_engine --project <project> status
```

Those forms preserve unbound runs. New ticket initialization adds `--ticket <key>` before `init` and `--session <real-builder-session-id>` after its options; capture the confirmed canonical ticket first. Use the same key for all subsequent commands and the [recorded refresh/proof boundaries](ticketing.md).

## Follow the stages

Supported interfaces: `web`, `cli`, `library`, `desktop`, `mobile`, `game`, `service`. Choose by actual delivery: browser game may use `web`, headless game server `service`. Supported check kinds include `unit`, `integration`, `browser`, `interaction`, `api`, `build`, `security`, `performance`. Configure relevant commands and manual/mixed receipts; artistic or actual-use criteria need appropriate observed evidence. Legacy profiles retain interface-specific executable requirements. Labels install no tools and prove no behavior. Inspect mixed surfaces and applicable evidence.

Use the actual procedures, then record their outputs. Honor Get Ready to Code's file-summary stop unless existing user instructions explicitly authorize continuing. Read the Mobile-priority [source map](skill-provenance.md#current-source-map--3-october-2026). For new software, the existing `plan` phase contains original plan → [research-market](../.agents/skills/research-market/SKILL.md) → revised plan; retain and link all three before recording the final plan. Research covers product/UX, current stack/architecture and fitting patterns; inspect applicable resource costs and resolve material unknowns during delivery. Standalone research needs no run. No new CLI stage is introduced. Artifacts can be Markdown with diagrams and tables; the controller validates presence and integrity, while the fresh reviewer assesses substance.

New version-2 sequence:

```text
record analysis --file <analysis.md>
record plan --file <plan.md>
record implementation --file <improvement.md>
record manual --file <receipt.json>
seal --task <final-task.json> --profile <final-profile.json> --review <contract-review.json>
record batch --file <final.md>
check
review --timeout 600
handoff
```

`record implementation` declares the complete confirmed outcome iteration's implementation/improvements finished. Only then perform actual manual/user QA or instruction walkthroughs; record its candidate-bound receipt. Only after that receipt author/polish tests in declared test-only paths. `seal` freezes independently reviewed final acceptance; record the batch and run one complete final gate. Local read-only review follows. `amend --task ... --profile ... --review ... --reason ...` preserves history and invalidates acceptance for legitimate reviewed corrections.

### Final evidence records

Use `status.manual_candidate` after implementation completion. A receipt has the shape below; replace every description with actual observations and existing evidence paths. Never submit fictional PASS evidence. Cover every manual/mixed criterion; automated-only tasks still need relevant final actual-use observation.

```json
{
  "candidate": "<current manual_candidate>",
  "observations": [{
    "criterion": "A1", "device": "<actual environment/device>",
    "action": "<performed action>", "result": "<observed outcome and limits>",
    "status": "PASS", "evidence": [".factory/evidence/manual.md"]
  }]
}
```

Effect-scoped re-QA after `repair`: a criterion the repair cannot affect may be carried instead of re-observed, `{"criterion": "A2", "status": "PASS", "carried": {"receipt_sha256": "<prior receipt hash>", "reason": "unaffected by <change>"}}`. `status.prior_manual_receipts` lists this run's archived receipt hashes and their passed criteria. The controller accepts a carry only from such a receipt where that criterion passed, and rechecks its evidence hashes. At least one criterion must be freshly observed. Amendment clears the archive. Carrying is a claim the reviewer judges, not proof the change missed that behavior.

At final sealing, `contract-proposal --task <final-task.json> --profile <final-profile.json>` returns exact `old_digest`, `new_digest` and protected hashes for independent inspection. It grants no approval. The actual reviewer records `verdict: "PASS"`, `independent: true`, `reviewer`, `reason`, `authority` and matching digests in the review JSON. Original request cannot change. Seal preserves criterion IDs/text; changes to these through `amend` also need explicit `acceptance_change_authority`. Interface, test paths, declared inputs, scopes and exposure cannot silently change at seal. Amendment preserves snapshots and invalidates final evidence; a draft stays draft, a sealed contract stays sealed.

Legacy version-1 runs retain `analysis → plan → batch → check → improvement → check → review → handoff`. Their second check may reuse exact unchanged evidence only under their reviewed opt-in. No automatic migration.

Prefix every line with `python -m safe_engine --project <project>`, plus `--ticket <key>` when bound. Ticketed work also needs refreshed captures at its boundaries and `ticket-proof --file <proof.json>` after final checks, before review; `ticket-proof-draft --out <proof.json>` pre-fills it from recorded evidence. [Ticket usage](ticketing.md) owns that schema. A failed check or blocking finding requires `repair --reason "..."`, completed surgical correction, final manual QA, final test work, valid sealed acceptance, batch, configured gate and fresh review. Follow the saved version's sequence. Correction count is history, not a stop condition. `cancel --reason "..."` stops progression and preserves work. No operation deletes the worktree.

Optional reviewed profile field `parallel_checks: true` (default false) runs independent checks concurrently in `check`. Each keeps its own log and declared outputs; the batch passes only if every check passes and inputs stay unchanged. Leave it off when checks share ports, databases, files or caches.

Without a Codex CLI, `review-packet --out <packet.md>` writes the review prompt and binds current inputs and run state. Keep packets, reports and proof files in the run directory (`.factory` or `.factory/runs/<ticket>`, not its reserved files) or outside the project. The controller cannot detect one packet handed to several reviewers; hand each packet to one. The report's summary must start with the packet's review nonce; reissuing a packet before submitting a report counts as a failed round. Hand it to a fresh, read-only, separately spawned host subagent, then run `review --report <report.json> --reviewer "<host/agent id/model>"`. The report must match the review schema and pass the same validation; any input, record or packet-file change since the packet requires a new one. Status and handoff show "external reviewer; independence not verified by the controller". Failed external reviews count toward the 3-round cap. When Codex is present it stays the reviewer and `--report` is refused.

`handoff` writes a criterion → change → proof → gap table into `handoff.md` for the PR verification section, plus deferred review findings with their follow-up.

`status` is read-only: it takes no lock and creates no `.factory`. Commands other than `init` stop early when no saved run exists.

After interruption, use `status`. An incomplete check or review is not acceptance; rerun it on current inputs. A changed candidate after its batch record needs a repair cycle. File locks release when the process exits. To stop an active check or review, interrupt its foreground controller; it terminates its owned process tree. A concurrent cancel command does not bypass the active operation's lock.

## Records-only corrections

Optional reviewed v2 profile field: `reuse_record_evidence: true` (default absent/false). Choose only when declared runtime/context inputs are stable and complete enough for exact evidence reuse. Volatile external state, missing context or unresolved risk requires fresh ordinary repair.

`repair --records-only --reason "record defect, affected record and why raw proof remains valid"` keeps original manual/check evidence. Requires sealed v2 opt-in, fresh unchanged ticket scope, intact exact-input checks/manual/artifacts, reconciled operations and a current hash-bound review report. All criteria PASS, method followed; every finding evidence/report with `evidence_status: valid`, evidence and action. Unclassified findings, product defects, missing/challenged proof or FAIL/UNKNOWN criteria are ineligible.

Use before correction. It clears review and ticket proof, records original report/manual provenance and stays in review. Replace the cleared criterion-proof mapping or append an unhashed correction note in ignored storage. All original hashed records, review reports and raw evidence remain immutable, including ignored files. Regenerate proof; obtain fresh assessment. Retained actions are never freshly run. Corrections needing new raw proof/hashed records use ordinary repair, retaining originals. Tracked documentation/source/tests or profile/config/environment/contract/dependency/bundle changes also need ordinary repair and all configured checks. No per-check reuse across changed inputs. Old profiles/pins keep their behavior.

Prior classification is bound to the structured report hash. Execution metadata provides context, not authenticated reviewer/host identity; the existing same-user boundary remains.

New review findings include `layer: product|evidence|report`, `evidence_status: valid|missing|challenged`, raw `evidence` and clear `action`. Severity/disposition stays separate. Old reports remain readable; absent fields cannot grant reuse. Existing raw proof that the reviewer challenges needs fresh verification, not a label change.

## Feature feedback and version checkpoints

Current policy is [finish work → final manual/user QA → final test authoring/execution](current-decisions.md#finish-work-use-it-then-automate-tests), per complete confirmed outcome ticket. Intermediate pieces have no separate controller acceptance; full-product criteria remain open. No early playtests, manual reproduction or instruction walkthroughs. Source inspection/research/existing-log reading remain allowed. Version 2 records implementation completion and structured manual receipts before final test authoring; production changes invalidate manual evidence. Declared test-only changes do not. Receipts bind criterion/candidate/environment/actions/results/evidence; reviewers judge substance. The controller cannot prove the person acted or intercept arbitrary commands.

The legacy `feature-check --checks <IDs> --file <feature.md>` command still executes partial checks in `build`. Do not use it under current policy. Its availability is not permission; partial results never certify a version. Existing historical feedback remains evidence of its recorded candidate only.

Failed feature feedback is preserved and requires `repair --reason ...` before another feature or version batch. Repair from build is allowed only for actual failed feedback; diagnostic counters remain continuous. Interrupted operations remain incomplete, cannot be recorded as a finished version, and need reconciliation/rerun. Cancellation stays terminal.

After implementation, manual QA, final test authoring and sealing, version-2 `record batch` then `check` executes every configured final check once and enters review. The improvement assessment was already recorded at implementation completion. New production changes require repair and fresh affected manual evidence before final tests. Legacy version-1 final-check reuse validates exact source, contract, declared inputs/executable/guidance, logs and output hashes; volatile/runtime concerns require `check --fresh`. Missing/changed evidence prevents reuse. Partial subsets never certify a full version.

Greenfield version-2 initialization needs no existing tests. Draft acceptance preserves the original request and planned evidence; final independent sealing protects actual checks. No placeholder tests or invented completed stages. Existing version-1 runs retain their limitations and selected bundle; do not retrofit records or claim the new workflow was used historically.

The factory input owner is [bundle-inputs.json](../safe_engine/bundle-inputs.json). Required operative files cover controller/schema, rules, canonical methods, portable entries and current guidance. Missing required inputs block acceptance; operative changes invalidate QA. Historical audits, provenance and dated proposals stay available but are excluded from target-run procedural invalidation. Update the contract when adding required guidance. A target's explicitly declared inputs still count even when they are historical documents.

This procedural boundary excludes the factory's own tests, examples, preview and media. When such a resource is an input to a target's acceptance, declare it in that target's profile. An installed launcher outside the selected bundle, external tools/services and hidden runtime state are not inferred; preserve their identity and declare operative files/environment inputs or require fresh checks. The target project's own source fingerprint still includes its tracked and nonignored untracked files. A clean Git revision or portable completeness inspection alone is not QA.

Never edit saved profiles directly. Legacy version-1 reuse needs its original reviewed opt-in; version 2 uses reviewed amendments and one final gate. This is local workflow integrity, not an administered acceptance service or automatic dependency scheduler.

## What is enforced

- Original request/history are preserved. Version-2 draft, independent sealing and reviewed amendments validate criterion evidence modes and protected checks; legacy contracts remain fixed.
- Source changes during the analysis or planning phase prevent progression.
- Required acceptance files and recorded artifacts cannot change unnoticed through ordinary controller use.
- Evidence includes exact source contents, check definitions, declared inputs, executables, and the operative factory inputs defined above. A commit that only records unchanged contents does not itself invalidate evidence.
- Fitting manual/automated evidence, current logs, completed improvement assessment and a fresh local review are necessary for handoff. Blocking findings prevent acceptance; authorized lower-risk deferrals remain explicit. Under Seif's 6 Oct delegation, LOW findings, and MEDIUM at local exposure, may be `accepted-deferral` with owner `Seif`, authority `Seif 6 Oct delegation`, reason, scope, revisit trigger and a follow-up ticket; the controller blocks that authority on MEDIUM at public/production/release scope. HIGH/CRITICAL and unmet criteria still block.
- After 3 failed reviews, `review` refuses until Seif decides; record it with `extend-reviews --rounds <1-3> --reason ...`, or amend/cancel.
- Corrections continue with supported diagnosis and fresh acceptance; cancelled runs cannot continue. New init defaults to continuous; deprecated `--max-repairs` and old saved integers remain historical metadata, never active caps. `status` exposes `repair_policy: continuous`, `max_repairs: null`, `historical_max_repairs`, and preserved `repairs_used`. Compatible old post-QA runs use normal `repair --reason ...`; no manual state edit or acceptance carry-over.

## Remaining gaps

The controller does not intercept arbitrary agent actions, install host hooks, or protect GitHub merges. Its local records are not signed or isolated from the builder's OS identity. A fresh read-only reviewer supplies context and permission separation, but is not a separately administered acceptance service. Model judgments and tests can miss defects.

PR delivery uses [creation](../.agents/skills/how-to-make-a-pr/SKILL.md) and the complete [review](../.agents/skills/how-to-review-a-pr/SKILL.md) through the [adapter](pr-workflow.md). PR review must actually run remotely/in the cloud on a separate agent with fresh context, including docs/skills and updates. Local `handoff` or local subagents cannot satisfy it. Discover actual route, tracker, owner and authorized destinations; missing bindings block dependent completion, not independent local work. These remain instruction-level requirements, not remote enforcement.

The full architecture, UX research beyond the implemented [quality audit](../.agents/skills/ux-quality/SKILL.md), security, idea-assessment, test-quality review, skill-writing, and worktree-management modules are not implemented as independent specialist skills. General review lenses cover only part of those responsibilities. Planning and execution are separate controller phases but still share the original `get-ready-to-code` entrypoint; the selected modular split remains future packaging work.

The browser demo proves specified interactions, rendering checks, and a repair on one fixture. It does not demonstrate autonomous aesthetic judgment, broad project portability, remote state isolation, or production readiness. Python controller tests, skill structural validation, actual browser execution, and independent review are reported separately.

Fresh review uses `codex exec --sandbox read-only --ephemeral --output-schema ...`. Its completion and structured content are checked; a failed review blocks handoff, and an unavailable CLI blocks it unless the external review packet route is used. [Official non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode).
