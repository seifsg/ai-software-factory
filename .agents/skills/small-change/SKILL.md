---
name: small-change
description: "Make a bounded Safe Engine fix with brief analysis, careful coding, focused checks, and one narrow independent review. Use for requested small UI, input, copy, or handler fixes. Analysis-only requests stay analysis-only; new apps and substantial features use the version workflow."
---

# Small Change

Make the requested small fix. Understand it, fix it properly, check it, and return the result.

This is Seif's lightweight method selected on 3 October 2026. Its six routines replace the full analysis, planning, coding-record, review, change-guard, and compliance procedures for this bounded change. Read this whole file; do not load those full procedures recursively.

## Check the scope

Use this for a requested direct fix whose behavior and consumers can be identified: broken typing, a label, layout, or a local handler. The user need not name this skill. An explicit invocation is `Use small-change to fix [behavior] in [project].`

If the user asked only for analysis, planning, or review, do that phase and stop. Small scope is not permission to implement.

Read project instructions, working changes, relevant source, and existing decisions. Reuse the [session contract](../safe-engine/references/session-contract.md); do not restart intake. Record the symptom, intended result, patch boundary, and direct consumers in a few lines.

Judge scope by dependencies and user impact, not file or line count. Several files can form one small fix. A one-line permission, state, or schema change can require deeper work.

If the scope expands, explain the dependency and revise the plan. Substantial features, architecture, and migrations use the version workflow. That classification alone does not authorize broad testing. Propose affected-area checks and get the user's direction before additional broad validation. Do not split risky work into fake small fixes.

Real protected CI/security requirements still apply. Disclose a conflict; do not weaken the requirement or claim an unrun gate passed. Old factory defaults or a convenient umbrella script are not by themselves non-waivable gates.

## The six routines

Use one short change record. Analyze and prepare before edits; review the result. Checks may run before review so the reviewer can use their evidence. A caller requesting one stage uses that stage only.

### 1. Analyze lightly

Read the actual implementation and relevant callers, events, and bindings. State the likely cause and evidence. Label uncertain causes. Investigate real unknowns before coding; a filename or screenshot alone is insufficient.

Use a short flow when it helps. An obvious fix does not need an architecture chart, repository-wide reading, market research, or three invented alternatives.

For app changes, read [app diagnostics](../safe-engine/references/app-diagnostics.md). Inspect logging facilities and events. Keep the compact app-wide coverage inventory in this record. Include an absent minimum shared module and missing events for the changed journey and consumers in the patch, then implement and verify them through the following steps. Record wider gaps; do not turn this into an instrumentation sweep or full QA.

Apply [app efficiency](../safe-engine/references/app-efficiency.md) to the affected path. Identify material repeated work and resource lifetimes. Select useful safe reuse and the smallest relevant evidence. Carry applicable cache validity, bounds, cancellation, ownership, and cold/warm checks through preparation, code, review, and handoff. A copy/input fix with no resource impact needs only that supported conclusion, not a benchmark, new cache, or app-wide optimization.

### 2. Prepare lightly

State the files and behavior to change, the smallest complete solution, and exact checks. Criticize the choice briefly. Is it the right fix? What does it affect?

Keep earlier decisions. Do not invent alternatives to a selected repair. Reuse checks that exercise the actual failure. This replaces the five full planning outputs.

### 3. Generate code carefully

Use the 0–4 discipline inside the small batch:

0. Gather the context.
1. Inspect where the change belongs.
2. Apply it.
3. Inspect the diff and user outcome.
4. Correct supported defects and repeat the affected steps.

Keep necessary error handling, security, state, and contracts. No per-edit transcript is needed. Keep unrelated cleanup and fixes separate; record discoveries and continue the requested work. Diagnose as long as needed without artificial correction allowances or exhaustion limits.

### 4. Review lightly

Get one independent assessment of the final small batch. Cover changed lines and enough surrounding code and consumers to judge correctness, relevant security/resource risks, and the requested interaction.

Return findings and a brief verdict. Do not expand into a whole-project audit, alternative-design exercise, separate full theme reports, or unrelated fixes. A clean result needs no edits.

For app changes, include affected diagnostic coverage and the module contract. Use focused evidence for changed logging. Include log discovery and remaining gaps in the handoff.

When delegation is available, prefer an available fast/light model for this bounded analysis or review, as Seif authorized. Discover actual model and tool capabilities. Supply the request, exact diff/base, source paths, dependencies, and raw evidence. Do not prescribe the verdict. Keep implementation quality and the main coding configuration intact.

If a light model is unavailable, inherit the current model. Do not install a provider, buy access, or block for a preferred model. Record the actual model when exposed. Use a capable reviewer if the case exceeds the light model's capability. Do not launch a fleet automatically.

The reviewer may use existing evidence. Repeat a check only for changed code/runtime inputs, a failure, or an unresolved concern. If the reviewer repairs code, obtain a new independent assessment of that correction. Do not restart the factory. If independent execution is unavailable, report the limit and do not claim independent approval.

### 5. Guard the change lightly

Tie every check to changed behavior or an affected consumer. Run the focused batch once. Use a build/type check when the patch needs it. Inspect umbrella scripts before running them; prefer supported filters, a focused harness, or direct interaction.

For an input defect, test real focus, typing, and paste through a permitted input route with harmless dummy data. Assigning a control property does not test keyboard input. Test Save or another downstream action only when affected. Never use or log a real API key as fixture data. Report missing interaction coverage; unrelated passing tests cannot replace it.

Do not write tests that mirror the implementation or ceremonial tests for reversible copy/layout edits. Directly inspect the visible result when sufficient. Do not automatically run broad regression, full QA, duplicate final QA, or unrelated smoke tests. Diagnose new relevant failures and check their affected area.

Keep cumulative changed areas in the same record. If successive fixes create interaction risk, offer a concrete affected-area validation batch and explain its purpose. The offer neither blocks the next authorized fix nor authorizes running it. Run it only when requested or accepted. No hidden N-change threshold, automatic regression, or repeated nagging. A full suite needs the user's request or an actual non-waivable gate.

### 6. Check compliance lightly

Compare the request, result, and evidence. For each requested outcome, state delivered, incomplete, or unverified. Note meaningful deviations and deferred unrelated work. Do not expand this fix into the original feature backlog.

Return the result, actual checks, and remaining limits. Ready, merge, release, and deployment remain owner decisions.

## Continue alongside a version run

Keep a short append-only record in an already ignored `.factory/small-changes/` or another established excluded session directory. Record the request, base/head or dirty-diff identity, bundle identity, affected files/consumers, checks/results, independent review, and cumulative affected areas. Reuse it across successive fixes. Do not create a task/profile/report tree per edit. Preserve unrelated dirty files and worktrees.

This handoff is agent-operated. It is not a controller command or full-version acceptance receipt.

Inspect an existing controller run before app writes. Quiesce dependent operations and honor cancellation and owner checkpoints. Preserve its original task, profile, bundle, and state. Do not rewrite phases or fingerprints, shrink acceptance, or replace a run to hide failure.

During `build`, use supported `feature-check` feedback when useful. In later phases or after `ready`, a newly authorized small fix gets a separate labeled handoff. Old full-version evidence no longer certifies changed inputs: record it as stale. Do not automatically reopen or complete full-version QA. Original defects, requirements, and failed gates remain outstanding.

For a later requested version checkpoint, use the original bundle's supported continuation/adoption procedure. Disclose configured checks before the broader batch. The controller has no selective full-version acceptance command. If scope conflicts with an immutable profile, preserve it and resolve the conflict before dependent commands.

Keep an older pinned bundle intact if it lacks this method. An owner-authorized local trial uses the complete reviewed candidate by explicit path, records both identities and evidence limits, and leaves the older selection unchanged. Do not silently upgrade another session or call a local draft released.

## Deliver a PR when authorized

Read both [how-to-make-a-pr](../how-to-make-a-pr/SKILL.md) and [how-to-review-a-pr](../how-to-review-a-pr/SKILL.md). Use their originals through the [project adapter's small-change mode](../../../docs/pr-workflow.md). Preserve actual task links, draft status, truthful attribution, and human handoff rules. Local owner testing does not require a push or PR.

For updates, inspect PR metadata, original purpose, and prior review boundary. Review the new delta and affected consumers. Do not re-audit previously accepted code or claim whole-PR approval from this scoped review. If the old broader PR never passed, preserve that status.

One separate reviewer may cover the small change and PR review together on the same final head. Reuse relevant exact-candidate evidence with its limits; do not duplicate review merely because publishing happened.

Example, only when verified:

`Fixed focus on the key field. Verified dummy typing and paste in the running UI; one focused reviewer found no issues. Broader tests were not run. Ready for you to try.`