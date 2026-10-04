---
name: small-change
description: "Deliver a bounded fix through six light routines, focused checks and independent review. Analysis/planning/review requests keep their phase. New products and substantial features use the version workflow."
---

# Small Change

Read this whole file. Its six routines replace full analysis, planning, coding-record, review, change-guard and compliance for bounded changes. Do not load those procedures recursively.

## Check the scope

Use for requested direct fixes with identifiable behavior/consumers: input, copy, layout, local handlers or bounded non-UI defects.

Analysis, planning or review requests stay in that phase. Small scope never grants coding authority.

Read project rules, working changes, relevant source and decisions. Reuse the [session contract](../safe-engine/references/session-contract.md). Record symptom, intended result, patch boundary and consumers.

Judge scope by dependencies and impact, not file count. Permission/state/schema changes may need deeper work. Explain new dependencies and revise expanded plans. Substantial features, architecture and migrations use the version workflow; never split risky work into fake small fixes.

For a material data-model decision, use [Database Schema](../database-schema/SKILL.md) and revise scope as needed. A routine query/index correction reuses the selected design and assesses affected queries, write cost and migration risk; it does not reopen every product decision or trigger a whole-database rewrite.

Scope classification does not authorize broad testing. Offer affected-area checks; run them only when requested/accepted or required by a real protected gate. Preserve CI/security obligations; disclose conflicts, never weaken requirements or claim unrun gates passed. Old defaults and umbrella scripts are not automatically non-waivable.

## The six routines

Keep one short record. Surgical changes take precedence. Follow [tests-last order](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests): finish the fix → manual action QA → final automated tests → final review/PR. No test authoring, edits or execution during development. Stage-only requests use that stage only.

### 1. Analyze lightly

Read implementation, callers, events and bindings. State cause/evidence; label uncertainty. Investigate consequential unknowns before coding. A filename or screenshot alone is insufficient.

Use a short flow when helpful. Obvious fixes need no architecture chart, repository-wide reading, market survey or invented alternatives. Research unfamiliar behavior, stack or performance constraints in current primary sources only when they can change this fix; record answer, source and decision. Keep broader discoveries within scope/authority.

For product changes, read [mandatory app logging](../safe-engine/references/app-diagnostics.md). Reuse an adequate shared module or add the missing internal module, even for a small fix. Discover the owner's provider and request missing access securely; keep local logging working meanwhile. Wire detailed success/failure events through the affected journey, inspect broader coverage and record gaps. Logging is required scope; use shared hooks and surgical edits, not unrelated refactors. Read emitted logs while reproducing and fixing.

Apply [app efficiency](../safe-engine/references/app-efficiency.md) to the affected path: repeated work, resource lifetimes, safe useful reuse and focused evidence. Carry applicable validity, bounds, cancellation, ownership and cold/warm checks through all stages. If resources are unaffected, record supporting evidence; add no benchmark, cache or app-wide optimization.

### 2. Prepare lightly

For every UI/interaction change, apply [UX Quality](../ux-quality/SKILL.md) to the affected journey through manual QA and this skill's scoped reviewer. Preserve adequate patterns/assets; research uncertain choices and compare three credible options before selecting. Check actual visuals/audio when changed. Quality is required; unrelated redesign and a second review fleet are not.

List files, behavior, smallest complete fix, manual actions and final check scope. Reproduce through actual use; read existing tests when helpful, but do not write/run them yet. Critique correctness/impact; preserve settled choices without invented alternatives. This replaces the five full planning outputs.

### 3. Generate code carefully

Apply the 0–4 discipline within the batch:

0. Gather context.
1. Inspect the change site.
2. Apply the change.
3. Inspect diff and user outcome.
4. Correct supported defects; repeat affected steps.

Preserve error handling, security, state and contracts. Skip per-edit transcripts; record unrelated discoveries separately and continue. Diagnose without artificial correction/exhaustion limits.

### 4. Review lightly

Get one independent assessment of the final candidate after routine 5: changed lines, surrounding code, consumers, correctness, relevant security/resource risks and requested interaction. For product changes, include the working logging module, detailed emitted journey evidence, safe access and coverage gaps. Earlier source review is allowed; it cannot start automated testing.

Return findings and a brief verdict; no whole-project audit, alternative-design exercise, full theme reports or unrelated fixes. Clean reviews need no edits.

For available delegation, the user permits an available fast/light model for bounded analysis/review. Verify tools/capability; provide request, exact diff/base, paths, dependencies and raw evidence without prescribing a verdict. Preserve main coding configuration and implementation quality. If unavailable, inherit the current model; never install providers, buy access or block for preference. Record exposed model identity; escalate to a capable reviewer when needed, without an automatic fleet.

Reuse valid evidence; repeat checks only for changed code/runtime inputs, failures or unresolved concerns. Reviewer repairs need fresh independent assessment, not a factory restart. Report missing independent execution; never claim independent approval.

### 5. Guard the change lightly

Finish all implementation, then manually exercise changed behavior and affected consumers. Fix observed defects and repeat affected actions. Only after manual QA passes, add/adapt useful tests and run the final focused batch before PR preparation. Inspect umbrella scripts; use supported filters. Build/start for manual use must not trigger tests. Reviewer or final-test fixes repeat this order.

For input defects, exercise real focus, typing and paste through permitted controls with harmless dummy data; property assignment cannot prove keyboard input. Check Save/downstream actions only when affected. Never use/log real API keys as fixtures. Report missing interaction coverage; unrelated tests cannot replace it.

Avoid implementation-mirroring tests and ceremony for reversible copy/layout edits; inspect the visible result when sufficient. No automatic broad regression, full/duplicate QA or unrelated smoke tests. Diagnose relevant failures and check their affected area.

Track cumulative affected areas. When successive fixes risk interactions, offer a concrete validation batch and purpose without blocking authorized fixes or starting it. No hidden change-count threshold or repeated nagging. Full suites require the user's request or a real non-waivable gate.

### 6. Check compliance lightly

Compare request, result and evidence; mark outcomes delivered, incomplete or unverified. Note meaningful deviations/deferred unrelated work without reopening the feature backlog.

Return result, actual checks, limits, log discovery and coverage gaps. Ready/merge/release/deployment remain owner decisions.

## Continue alongside a version run

Reuse one append-only record across fixes in an already ignored `.factory/small-changes/` or established excluded session directory: request, base/head or dirty-diff identity, bundle, files/consumers, checks/results, independent review and cumulative areas. No per-edit task/profile/report tree. Preserve unrelated dirty files/worktrees. Records are neither controller commands nor full-version acceptance.

Before project writes, inspect any controller run. Quiesce dependent operations; honor cancellation/checkpoints. Preserve original task, profile, bundle and state. Never rewrite phases/fingerprints, shrink acceptance or replace a run to hide failure.

Do not use mid-build `feature-check`; it conflicts with tests-last order. Later or after `ready`, give a newly authorized fix its own labeled handoff. Mark old full-version evidence stale for changed inputs. Do not automatically reopen/complete full QA. Original defects, requirements and failed gates remain outstanding.

For a requested later version checkpoint, follow the original bundle's supported continuation/adoption procedure. Disclose configured checks before broader testing. No selective full-version acceptance command exists. Preserve immutable profiles; resolve scope conflicts before dependent commands.

If an old pin lacks this method, preserve it. An authorized local trial uses a complete reviewed candidate by explicit path, records both identities/evidence limits and leaves the old selection unchanged. Never silently upgrade another session or call a local draft released.

## Deliver a PR when authorized

Read [creation](../how-to-make-a-pr/SKILL.md), [review](../how-to-review-a-pr/SKILL.md) and the [adapter's small-change mode](../../../docs/pr-workflow.md). Preserve actual task links, draft status, truthful attribution and human handoff. Local owner testing needs no push/PR.

For updates, inspect PR metadata, original purpose and review boundary. Review the delta/consumers; preserve unresolved findings. Do not re-audit accepted code or claim whole-PR approval from scoped review.

One separate reviewer may cover this fix and PR review on the same final head. Reuse exact-candidate evidence with its limits; publication alone needs no duplicate review.
