---
name: ticketing
description: "Keep factory work in durable epics and tickets: preserve owner input, confirm scope, assign isolated sessions, track changes and bind final evidence to the latest expectation."
---

# Ticketing

Keep the request, decisions, work and evidence in the selected tracker. Read the [ticket contract](references/ticket-contract.md) when preparing, changing or reviewing a ticket. [Usage](../../../docs/ticketing.md) owns controller commands and limits.

Write tickets in Seif's words: shortest clear wording, complete intent. Use the contract's [writing recipe](references/ticket-contract.md#write-the-ticket): separate purpose/goal, context, change/reason, proof and progress; labeled emojis, bullets, tables and flow. No extra writing phase.

Default: build the ticket from the request, actual code and available context; keep execution moving within authority. The user need not supply/review a detailed ticket. Honor requested detail/checkpoints; ask only consequential reserved gaps. Give a fresh agent complete, visual context.

## Select the tracker

GitHub Issues is Seif's current choice. Reuse it; do not ask again. For another project, discover the preferred tracker and available authorized MCP tools first. Ask only an unresolved preference; without one, try GitHub Issues. Resolve the actual repository, access and privacy before writing.

Search existing epics/tickets by symptom, feature, area/files and PR title/branch. Reuse the same work. Record canonical provider, project, native ID and URL. Do not create a second ticket after an uncertain response: read the tracker and reconcile the effect first.

The remote ticket is canonical. Local snapshots preserve context and exact revisions; they grant no authority and cannot replace remote updates. Failed access, writes or conflicting versions stay explicit with the affected step and next action. Preserve a pending local record; no silent tracker switch, duplicate or success claim. Use only actual tools; installation, paid access and messaging need their own authority.

## Capture the work early

Order complete outcome tickets by user value. Each unlocks a visible/observable result. Dependencies: required now, useful later, unrelated. Explain required blockers; challenge them. Keep overall criteria and one integration owner. Deferrals need owner, destination ticket and acceptance/revisit condition. [Working iterations](../safe-engine/references/delivery-readiness.md#working-iterations).

1. Preserve the original owner input before compressing it into a plan. Include why, examples, supplied evidence, source/date and decision authority. Retain later corrections and superseded input.
2. State actual before behavior and consumers from source and existing evidence. Label facts, inference and unknowns. No early reproduction or walkthrough. PR baseline capture follows the existing [narrow exception](../../../docs/pr-workflow.md#beforeafter-proof).
3. Derive the expected after, acceptance criteria, applicable success/failure/recovery journeys, scope, exclusions, constraints and dependencies from the request/source. Record purpose, goal, approach, relevant code/consumers, required/optional wants and existing progress/PRs. Use the contract's visual recipe. For a new capability, say what does not exist yet; nonvisual work needs an observable consumer/result.
4. Confirm from actual owner instructions or recorded delegation; record the source and deciding actor. In-scope delegated choices need no new vote. Preserve approved, rejected and pending choices; label assumptions/unknowns. Ask only a consequential unresolved owner choice and continue independent work. Undelegated proposals stay pending; explicit stops persist.
5. Create/reuse the epic and complete delivery tickets. Keep the overall outcome and integration owner in the epic; give each ticket one accountable owner, deliverable and completion boundary. Do not split incomplete risky work to evade full methods or tests-last.

Version the confirmed contract. Keep the original input and what changed, why, who decided and what resulted. Record meaningful activity as work proceeds: decisions, assignment, implementation completion, QA/tests, review, blockers, PR updates and handoffs. Update the tracker and refresh the local snapshot; no per-edit diary or duplicated report.

## Assign a ticket session

Every implementation ticket uses the full factory cycle, including small fixes: original analysis and planning, each todo's 0–4 loop, completed implementation/improvements, final manual QA, final test authoring/execution and fresh independent review. This takes precedence over [Small Change](../small-change/SKILL.md)'s six replacement routines. Keep changes surgical, checks applicable and the original file-summary stop unless continuation is already authorized. Phase-only requests stay in phase.

Give each ticket a dedicated execution session with the [complete handoff](../safe-engine/references/method-handoff.md). Record the real session/agent, ticket revision, run, absolute checkout, bundle and base/head. Use available session tools; a ticket label is not a dispatched session. Missing capability stays explicit. Parent/coordinator owns scheduling, shared decisions and tracker reconciliation; one writer owns each file.

Choose one declared workspace arrangement:

- Separate ticket worktrees: parallel only with independent files, runtime effects, acceptance and decisions. Isolate or serialize shared ports, databases, caches and services too.
- Shared epic checkout: explicitly serial tickets, one active writer/runtime owner, dedicated ticket sessions and separately preserved ticket runs. Quiesce previous operations before handoff. Never overwrite another ticket's state or delete it to permit initialization.

A dependency is satisfied by its accepted contract/result at the recorded integrated commit, available in this ticket's base. Closed tracker status alone proves nothing. Record required dependency revisions and shared interfaces. Changed dependency scope or integration head needs affected analysis/evidence revalidation. Epic completion also needs its combined journey/integration evidence.

## Execute and keep the contract current

Use [Safe Engine](../safe-engine/SKILL.md) for delivery and [Improve Factory](../improve-factory/SKILL.md) for maintenance. Ticketing owns intake, durable scope and coordination; those methods own execution. No recursive ticketing runs, duplicate analysis or extra reviewer fleet.

Bind the run to a captured confirmed contract. Re-read canonical scope at intake/resume, before starting an affected batch and at final review/PR boundaries. Reuse an unchanged refresh within the batch; new input, conflict or handoff needs reconciliation. Compare semantic contract digests, not activity timestamps alone. A cached snapshot cannot establish current remote scope.

Later input: preserve it, resolve authority, confirm or leave pending, record reasons and refresh the versioned specification. Reassess affected plans/consumers. Legitimate version-2 contract changes use independently reviewed `amend` and ticket rebinding; preserve original request, revisions, protected inputs and failures. Never edit state, weaken acceptance or revive cancellation. A changed goal may need a linked replacement ticket/run; preserve lineage.

Follow [tests-last](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests) in every ticket, delegate, repair and resume. Source inspection, research and existing-log reading remain allowed. Finish the ticket's implementation before its final actions/tests. Combined epic QA waits until constituent implementation finishes. Fresh assessment is required after reviewer repairs; evidence cannot be copied as a new pass.

## Review and deliver

Refresh the canonical contract. In the existing Compliance/journey review, map every latest confirmed expectation to implementation and actual evidence. Compare actual before with delivered after; identify missing/partial results, unintended behavior and deviations. Approved deviations retain authority/reason; pending changes cannot redefine a pass. Unknown required scope or evidence blocks dependent acceptance.

Authorized PRs use both [creation](../how-to-make-a-pr/SKILL.md) and remote/cloud [review](../how-to-review-a-pr/SKILL.md), with the [adapter](../../../docs/pr-workflow.md). Include ticket/epic links, exact confirmed revision/digest, before/after proof, decisions/change history, evidence, unresolved findings and resume step. Check the latest confirmed expectation again for updates. Local review never replaces fresh-context cloud review of exact remote base/head.

Update the canonical ticket with the actual outcome and accessible sanitized evidence. Keep local reviewed, cloud reviewed, merged and released distinct. Complete only the recorded authorized boundary; preserve blocked/cancelled work and remaining human decisions. A completed child list does not certify an epic, and a draft PR does not imply merge/release.
