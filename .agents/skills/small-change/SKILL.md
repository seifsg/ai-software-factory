---
name: small-change
description: "Deliver bounded fixes through six light routines, focused checks and independent review. Analysis/planning/review stays in phase. New products and substantial features use the version workflow."
---

# Small Change

Read this whole file. These six routines replace full analysis, planning, coding-record, review, change-guard and compliance for bounded changes. Do not load them recursively.

## Check the scope

Requested direct fix, identifiable behavior/consumers: input, copy, layout, local handlers or bounded non-UI defects. Analysis/planning/review stays in phase; small scope grants no coding authority.

Read project rules, working changes, relevant source/decisions; reuse the [session contract](../safe-engine/references/session-contract.md). Record symptom, intended result, patch boundary, consumers.

Judge dependencies/impact, not file count. Permission/state/schema changes may need depth. Explain new dependencies; revise expanded plans. Substantial features, architecture and migrations use version workflow. Never split risky work into fake small fixes.

Material data-model decision: use [Database Schema](../database-schema/SKILL.md), revise scope as needed. Routine query/index fix: retain selected design; assess affected queries, write cost, migration risk. No whole-database rewrite or reopened product decisions.

Scope grants no broad testing. Offer useful affected-area checks; run only when requested/accepted or required by a real protected gate. Preserve CI/security obligations; disclose conflicts, never weaken requirements or claim unrun gates passed. Old defaults/umbrella scripts are not automatically non-waivable.

## The six routines

One short record. Surgical changes first. [Tests last](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests): finish fix → manual action QA → final automated tests → final review/PR. No test authoring, edits or execution during development. Stage-only requests use only that stage.

### 1. Analyze lightly

Read implementation, callers, events, bindings. State cause/evidence; label uncertainty. Resolve consequential unknowns before coding. Filename/screenshot alone proves too little.

Use short flow when helpful. Obvious fixes need no architecture chart, repository-wide reading, market survey or invented alternatives. Research unfamiliar behavior, stack/performance constraints in current primary sources only when it can change this fix. Record answer, source, decision. Broader discoveries stay within scope/authority.

Product changes require [logging](../safe-engine/references/app-diagnostics.md): reuse adequate shared module or add missing internal module, even for small fixes. Discover owner's provider, request missing access securely, keep local logging working meanwhile. Wire detailed success/failure events through affected journey; inspect broader coverage, record gaps. Use shared hooks/surgical edits, no unrelated refactors. Read emitted logs while reproducing/fixing.

Apply [efficiency](../safe-engine/references/app-efficiency.md) to affected path: repeated work, resource lifetimes, safe useful reuse, focused evidence. Carry applicable validity, bounds, cancellation, ownership, cold/warm checks through stages. Unaffected resources: record evidence; add no benchmark, cache or app-wide optimization.

### 2. Prepare lightly

Apply [Application Security](../safe-engine/references/app-security.md) to affected trust boundaries; preserve cheap protections and record unrelated risks. No automatic app-wide hardening or early scans.

Human-facing prose uses [Clear Writing](../safe-engine/references/clear-writing.md); one finishing pass, same scoped reviewer.

Public-page fixes apply affected [SEO checks](../ux-quality/references/web-seo.md), including shared templates. No whole-site rebuild or publication authority implied.

Every UI/interaction change uses [UX Quality](../ux-quality/SKILL.md) on the affected journey through manual QA and this scoped reviewer. Preserve adequate patterns/assets; research uncertain choices, compare three credible options, then select. Inspect changed visuals/audio. No unrelated redesign or second review fleet.

List files, behavior, smallest complete fix, manual actions, final checks. Reproduce through actual use; read existing tests if helpful, never write/run yet. Critique correctness/impact; preserve settled choices, invent no alternatives. This replaces five full planning outputs.

### 3. Generate code carefully

Apply 0–4 within the batch:

0. Gather context.
1. Inspect change site.
2. Apply change.
3. Inspect diff and user outcome.
4. Correct supported defects; repeat affected steps.

Preserve error handling, security, state, contracts. No per-edit transcripts. Record unrelated discoveries separately; continue. Diagnose without artificial correction/exhaustion limits.

### 4. Review lightly

After routine 5, get one independent final-candidate assessment: changed lines, surrounding code, consumers, correctness, relevant security/resource risks, requested interaction. Product changes include working logging module, detailed emitted journey evidence, safe access, coverage gaps. Earlier source review cannot start automated testing.

Brief findings/verdict. No whole-project audit, alternative-design exercise, full theme reports or unrelated fixes. Clean review needs no edits.

For bounded delegated analysis/review, user permits an available capable fast/light model. Verify tools/capability; provide request, exact diff/base, paths, dependencies, raw evidence, no prescribed verdict. Preserve main coding configuration/quality. If unavailable, inherit current model; no provider install, purchase or preference blocker. Record exposed model identity; escalate capability when needed, no automatic fleet.

Reuse valid evidence. Repeat only for changed code/runtime inputs, failures or unresolved concerns. Reviewer repairs need fresh independent assessment, no factory restart. Disclose missing independent execution; never claim independent approval.

### 5. Guard the change lightly

Finish implementation → manually exercise changed behavior/consumers → fix defects and repeat affected actions → after manual QA passes, add/adapt useful tests and run final focused batch before PR preparation. Reviewer/final-test fixes follow this order. Inspect umbrella scripts; use supported filters. Build/start for manual use must not trigger tests.

Input defects: real focus, typing, paste through permitted controls using harmless dummy data. Property assignment cannot prove keyboard input. Check Save/downstream only when affected. Never use/log real API keys as fixtures. Disclose missing interaction coverage; unrelated tests cannot replace it.

Avoid implementation-mirroring tests and ceremony for reversible copy/layout edits; inspect visible result when sufficient. No automatic broad regression, full/duplicate QA or unrelated smoke tests. Diagnose relevant failures; check affected area.

Track cumulative affected areas. Successive fixes risking interaction: offer a concrete validation batch/purpose without blocking authorized fixes or starting it. No hidden change-count trigger or repeated nagging. Full suites need user request or real non-waivable gate.

### 6. Check compliance lightly

Compare request, result, evidence. Mark delivered/incomplete/unverified; note meaningful deviations/deferred unrelated work without reopening backlog.

Return result, actual checks, limits, log discovery/coverage gaps. Ready/merge/release/deployment remain owner decisions.

## Continue alongside a version run

Reuse one append-only record in already ignored `.factory/small-changes/` or established excluded session directory: request, base/head or dirty-diff identity, bundle, files/consumers, checks/results, independent review, cumulative areas. No per-edit task/profile/report tree. Preserve unrelated dirty files/worktrees. Records are neither controller commands nor full-version acceptance.

Before project writes, inspect any controller run. Quiesce dependent operations; honor cancellation/checkpoints. Preserve original task, profile, bundle, state. Never rewrite phases/fingerprints, shrink acceptance or replace a run to hide failure.

No mid-build `feature-check`; tests wait. Later/after `ready`, newly authorized fixes get labeled handoffs. Mark old full-version evidence stale for changed inputs. No automatic full QA reopening/completion. Original defects, requirements, failed gates remain outstanding.

Requested later version checkpoint: follow original bundle's supported continuation/adoption. Disclose configured checks before broad testing. No selective full-version acceptance command exists. Preserve immutable profiles; resolve scope conflicts before dependent commands.

Old pin lacking this method stays selected. Authorized local trial: complete reviewed candidate by explicit path, both identities/evidence limits recorded, old selection unchanged. Never silently upgrade another session or call local draft released.

## Deliver a PR when authorized

Read [creation](../how-to-make-a-pr/SKILL.md), [review](../how-to-review-a-pr/SKILL.md), [adapter small-change mode](../../../docs/pr-workflow.md). Preserve actual task links, draft status, truthful attribution, human handoff. Local owner testing needs no push/PR.

Updates: inspect PR metadata, original purpose, review boundary. Review delta/consumers; preserve unresolved findings. Do not re-audit accepted code or claim whole-PR approval from scoped review.

One separate reviewer may cover fix and PR review on same final head. Reuse exact-candidate evidence with limits; publication alone needs no duplicate review.
