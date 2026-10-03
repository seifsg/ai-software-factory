---
name: small-change
description: "Make a small, direct Safe Engine fix or adjustment through brief analysis, careful coding, focused checks and one narrow independent review. Default for bounded UI/input/copy/handler changes and successive small requests. No automatic regression or version-wide QA; new apps and cross-cutting features use the version workflow."
---

# Small Change

This is Seif's 3 October 2026 lightweight factory method. It replaces the full analysis, planning, coding-record, review, change-guard and compliance procedures **for the current bounded change**. Read this complete file; do not recursively load the full versions. Correct implementation remains required. A small request should lead to a small delivery cycle.

## Select the scope before starting work

Use automatically for a direct, bounded request whose affected behavior and consumers can be identified: an input that cannot accept typing, a label, a layout adjustment, or a localized handler defect. The user need not know a skill name. Explicit invocation: `Use small-change to fix [behavior] in [project].`

Inspect the actual project instructions, working changes, relevant source and existing session decisions. Reuse the established [session contract](../safe-engine/references/session-contract.md); do not restart intake. Record the symptom, intended result, narrow patch boundary and directly affected consumers in a few lines. Scope follows dependencies and user impact, not a maximum line/file/test count. Several files can form one small fix; a one-line authorization, shared-state or schema change may need more analysis.

If discovery reveals cross-cutting scope, explain the concrete dependency and refine the plan. Use the version workflow for substantial new features, architecture or migrations, but do not silently run broad tests because of that classification. Propose the affected-area checks and obtain the user's direction before additional broad validation. Do not split a risky change into fake small changes to evade necessary review. A real protected CI/security requirement remains binding: disclose an actual conflict instead of weakening it or calling an unrun gate passed. Older factory defaults and a convenient umbrella test script are not, by themselves, non-waivable requirements.

## The six lightweight routines

Run these in order, keeping one short change record rather than six reports. Headings below are the alternative entry points when a caller needs only that stage. Analysis and planning precede edits; review checks the resulting code.

### 1. Analyze lightly

Read the changed behavior's real implementation and trace the relevant callers/events/bindings. State the likely cause and supporting evidence; label uncertain causes. One short flow is enough if it clarifies the defect. No mandatory architecture chart, repository-wide reading, market research or three-alternative exercise for an obvious fix. Investigate a real unknown before coding; a file name or screenshot alone does not establish the cause.

For app changes, read [app diagnostics](../safe-engine/references/app-diagnostics.md), inspect existing facilities/event sites and keep its compact app-wide coverage inventory in this same record. Automatically include an absent minimum shared module and missing events for this journey/affected consumers in the small patch; implement and check them through the remaining routines. Record wider gaps/unknowns honestly without turning this fix into a full instrumentation sweep or QA cycle.

Apply [app efficiency](../safe-engine/references/app-efficiency.md) to the affected path: identify material repeated work/resource lifetime, choose useful safe reuse and record the smallest relevant evidence. Carry applicable cache validity, bounds, cancellation/ownership and cold/warm checks into preparation, code, this narrow review and handoff. A copy/input change with no resource impact needs only that supported conclusion; no automatic benchmark, new cache or app-wide optimization sweep.

### 2. Prepare lightly

State the files/behavior to change, the smallest complete solution and the exact verification needed. Critique that choice briefly. Preserve earlier decisions; do not invent alternatives to a user-selected repair. Reuse existing relevant checks where they exercise the actual failure. This replaces the five full planning artifacts.

### 3. Generate code carefully

Prepare context → inspect change site → implement → inspect the diff and user outcome → correct a supported defect. Keep this 0–4 discipline inside the small batch without a per-edit written transcript. Preserve necessary error handling, security, state and contracts. Avoid opportunistic cleanup or unrelated fixes; record unrelated discoveries separately and keep progressing on the requested change. Diagnosis may continue as long as necessary; there are no correction allowances or artificial exhaustion limits.

### 4. Review lightly

Use one narrow independent assessment of the final small batch, covering the changed lines plus enough surrounding code/consumers to judge correctness, relevant security/resource risks and the requested user interaction. Return actual findings and a brief verdict, not separate full security/performance/journey reports. No whole-project audit, alternative-design exercise or unrelated fixes. A clean result needs no edits.

Include the affected diagnostics coverage and module contract in that assessment when app code changes. Use the reference's focused evidence for new/changed logging, and include log discovery plus remaining coverage gaps in the concise handoff.

When the host supports delegation, prefer an available fast/light model for this bounded analysis or review as authorized by Seif. Discover the available model and tool capabilities, pass the original request, exact diff/base, relevant source paths, known dependencies and raw check evidence; do not prescribe its verdict. Keep implementation quality and the main coding configuration intact. If lightweight routing is unavailable, inherit the current model and continue with narrow scope; do not install a provider, buy access, or block merely because a preferred model is missing. Record the actual model when exposed. If the case exceeds its capability, use a capable reviewer for that affected scope. No automatic multi-agent fleet.

The reviewer can inspect existing evidence without rerunning passed checks. Repeat only an affected check when code, relevant runtime inputs, a failure or an unresolved concern warrants it. A reviewer that repairs code needs another independent assessment of that correction, not a restart of the entire factory. If no independent execution is available, report the limitation; do not claim independent approval.

### 5. Guard the change lightly

Map each proposed check to the changed behavior or a specific affected consumer. Run only those focused checks once after the small batch. The review may use their results, so verification can precede the independent assessment. A build/type check is appropriate when needed to run or validate this patch; a broad umbrella script is not automatically required. Inspect the script before running it. Use a supported filter, focused harness or direct interaction instead of accidentally invoking every test.

For an input defect, exercise real focus, typing and paste with a harmless dummy value through a permitted UI/input route; directly assigning a control property does not verify keyboard input. Check Save or another downstream action only when the patch affects it. Never use or log a real API key as fixture data. If the required interaction cannot be exercised, report exactly what remains unverified; do not substitute unrelated passing tests.

Do not add tests that mirror the implementation or ceremonial test files for reversible copy/layout edits. Verify the requested visible result directly when sufficient. Do not run automatic broad regression, full-suite QA, duplicate fresh-final QA or unrelated smoke tests. Previously unseen relevant failures require diagnosis and affected verification, not a full-suite reflex.

Keep a compact cumulative record of small changes and affected areas. At a useful boundary, if accumulated changes create interaction risk, offer a concrete **affected-area** validation batch and its purpose. The offer does not block the next authorized small fix and does not authorize execution. Run that additional batch only on the user's request/acceptance. No hidden threshold, automatic regression after N changes, repeated nagging or full suite unless the user explicitly requests it or an actual non-waivable gate requires it.

### 6. Check compliance lightly

Compare the original request with the implemented result and evidence. State delivered / incomplete / unverified, any meaningful deviation and any unrelated work deferred. One row per requested outcome suffices; do not expand the original feature backlog into this fix. Return a concise result with actual checks and remaining limits. Ready, merge, release and deployment remain owner decisions.

## Continuity with a version run

This is an **agent-operated small-change handoff**, not a new controller command or a full-version acceptance receipt. Keep a short append-only record in an already ignored `.factory/small-changes/` location or another established excluded session location: request, base/head or dirty-diff identity, source bundle identity, affected files/consumers, chosen checks/results, independent review and cumulative affected areas. Reuse one record across successive fixes; do not create a task/profile/report tree for each edit. Preserve unrelated dirty files and existing worktrees.

Inspect an existing controller run before app writes. Quiesce dependent operations and honor cancellation or owner checkpoints. Keep its original task/profile/bundle and state intact; never rewrite a phase/fingerprint, shrink protected acceptance or create a replacement run to hide a failure. In `build`, the existing supported `feature-check` may record focused feedback when useful. In later phases or after `ready`, a new authorized small fix can have its own clearly labeled handoff; historical full-version evidence no longer certifies changed inputs. Record that staleness explicitly without reopening or completing the full version pipeline automatically. Outstanding original defects/requirements remain outstanding; a narrow fix never erases a failed gate.

For a later owner-requested version checkpoint, use the original bundle's supported continuation/adoption procedure and disclose the actual configured checks before running a broader batch. Do not claim the current full-gate controller supports a selective version acceptance command. If the user's requested scope conflicts with an immutable profile, preserve it and resolve that conflict before dependent commands; do not alter acceptance to get green.

A pinned older bundle without this method must remain intact. An owner-authorized lightweight trial uses this complete reviewed candidate by explicit path as a separate method, records both identities and the stale/full-version evidence distinction, and leaves the older selection untouched. Do not silently upgrade another session or claim a local draft was released.

## PR delivery when requested or already authorized

Both [how-to-make-a-pr](../how-to-make-a-pr/SKILL.md) and [how-to-review-a-pr](../how-to-review-a-pr/SKILL.md) still run, using their small-change mode. Neither PR creation nor a remote push is a prerequisite for local owner testing. Preserve actual task links, draft state, truthful attribution and human handoff constraints.

For an update, inspect PR metadata, original purpose and prior review boundary; assess the new delta and affected consumers, not all previously accepted code from the original base. If the old broader PR never passed, preserve that status and limit the new verdict to this delta. Do not represent a scoped review as whole-PR approval. A separate reviewer may perform the small-change assessment and PR review together on the same final head, rather than duplicating the review before and after publishing. Existing relevant exact-candidate evidence may be reused with its limits stated.

## Example outcome

`Fixed focus on the key field. Verified dummy typing and paste in the running UI; one focused reviewer found no issues. Broader tests were not run. Ready for you to try.`

Use this wording only when those actions actually occurred. The objective is fast, precise delivery with evidence that directly supports the request.
