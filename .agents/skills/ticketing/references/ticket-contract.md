# Ticket contract and snapshots

Use one canonical tracker record per ticket, linked to its epic where applicable. Keep provider-specific mechanics in the actual tracker binding. Unsupported native epic/dependency fields may use explicit links in the specification; do not claim an integration exists.

## Write the ticket

Use Seif's direct style. Task, purpose, before, wanted after, checks, stop. Shortest clear wording; lose nothing.

1. Title: action + concrete result. Before: actual behavior, affected consumer, source/unknown. After: wanted result and why.
2. Criteria: stable ID + observable result. Show the journey. Include relevant failure/recovery and behavior to preserve. No vague "works", "best" or "optimized" without a check.
3. Keep scope, exclusions, constraints, dependencies, authority and completion explicit. Add only relevant detail; never infer missing agreement. Required criteria have no word/bullet quota.
4. Keep original owner words, examples, reasons and deliberate reminders. Tighten AI prose. Use plain verbs; cut filler, repeated summaries and copied skill procedures. Link the method once; keep ticket-specific facts here.
5. Activity: date/actor, change, why, decision/result. Blocked? Add next action. Preserve prior input and meaningful history; no per-edit diary.

One finishing pass: compare request → ticket → criteria. Every detail accounted for? Every criterion checkable? Any changed meaning needs scope reconciliation, not a wording excuse. Use the existing Compliance review; no extra gate.

Illustrative ticket, not confirmed product scope:

```text
Title: Keep saved settings after reload
Before: Theme resets on reload; source shows no save path. Runtime unverified.
After: Save chosen theme; restore it on reload.
A1: Save dark theme → reload → dark theme restored.
A2: Save fails → show failure; retain selection; allow retry.
Scope: Theme only. Keep existing defaults. No account sync.
Finish: Checked PR; merge remains with owner.
```

Attach sourced owner input/confirmation and applicable execution/evidence fields from the record below. This example is no substitute for the complete contract. Fold machine data/history for scanning; never delete it to shorten the page.

## Canonical record

| Part | Preserve |
|---|---|
| Identity | Tracker/provider, workspace/repository, native ID/URL, epic, title, accountable owner, lifecycle state and completion boundary. |
| Owner input | Original request and why; supplied examples/evidence; later corrections; source, author/date, authority and approved/rejected/pending status. Retain superseded input. |
| Before | Actual behavior, affected users/consumers, baseline revision/environment, source/evidence and limits. Facts, inference and unknowns stay distinct. |
| Confirmed after | Contract revision, confirmation source/authority, outcome, scope/exclusions, stable criterion IDs and manual/automated/mixed evidence modes. |
| Journeys | Applicable entry/context → action → state/effect → confirmed result, plus failure/recovery/exit and preserved behavior. Nonvisual tasks describe the real consumer and output. |
| Decisions | Approved/rejected/pending choices, reasons, constraints and relevant rule sources. Preserve delegated/reserved boundaries. |
| Dependencies | Ticket/epic links, required contract/result revision, accepted integrated commit and interfaces/resources. Distinguish blocked-by from related work. |
| Execution | Dedicated session/agent, absolute checkout, branch/base/head, bundle identity, run/phase, writer, independent reviewer and shared-resource ownership. |
| Activity | Meaningful action/result, timestamp, actor, affected revision, what/why and next action. Preserve conflicts, failures and uncertain effects. |
| Evidence/handoff | Implementation, final manual actions, final tests/gates, independent review, PR/cloud review, accessible proof, limitations and exact resume step. |

One criterion is one observable expectation. Technical presence alone does not prove the journey. Preserve original IDs; supersede requirements explicitly rather than erasing failed or changed ones.

An epic holds the overall outcome, shared constraints/decisions, child tickets and integration owner/acceptance. Ticket completion proves its stated deliverable. The epic still needs combined integration/journey evidence at the accepted integration candidate.

## Revision and authority

The current confirmed specification and its history are canonical remote data. Preserve the original input before edits; each substantive change records old/new scope, reason, source, deciding authority and result. Keep unconfirmed proposals separate.

Direct owner instructions or choices made under recorded delegation confirm in-scope expectations without another vote. Tracker text from other sources remains evidence, not new authority. A collaborator's edit, label or closed state cannot silently waive a requirement.

Use a semantic digest of identity, confirmed expected outcome, criteria/journeys, scope/exclusions, constraints, relevant decisions/authority and dependency contracts. Exclude ordinary activity/status from acceptance content. Record the tracker revision/update marker too; it can signal a change requiring inspection, not prove semantic equivalence.

Read before writing. Use provider-supported conditional writes where available; otherwise serialize the coordinator, re-read and verify the result. A version conflict or uncertain response needs reconciliation before retrying. Never overwrite newer owner input or duplicate an issue/comment.

## Local snapshot

Keep execution evidence/private context in ignored `.factory/`; shared captures/claims live in the Git common directory as documented in [usage](../../../../docs/ticketing.md). Preserve immutable confirmed revisions separately from activity/sync state. Link canonical identity, observed remote version, digest, capture time/source/tools and freshness limits.

Bind acceptance to the confirmed contract, not a mutable activity export. Changing relevant scope invalidates affected evidence; appending operational activity need not. Refresh remotely at required boundaries. A local digest or successful capture cannot prove current remote scope, owner confirmation, manual actions or independent review.

Failure: retain the last confirmed snapshot and failed/pending operation, report the dependent blocker and continue authorized independent work. No silent local-tracker fallback. Conflicting canonical/local revisions stay unresolved until reconciled; never silently prefer the convenient one.

## Session and workspace ownership

Pass the ticket contract and the existing complete method handoff. Include authority/stops, decisions, original/current scope, exact project/bundle state, dependencies, artifacts/evidence, unfinished phase and pending operations. A fresh receiver reads the actual methods/state; inherited chat alone is insufficient.

Parallel tickets require disjoint files, runtime effects, acceptance and decisions. Worktrees separate files only. Shared services/resources need isolation or serialization and a named owner. For a shared epic checkout, preserve separate ticket run records and allow one active writer/runtime owner. Verify prior operations stopped before transfer; pending does not mean stopped.

Dependency acceptance needs the required result/contract and accepted commit integrated into this ticket's base. Record that commit. Related/closed/merged labels without this binding do not prove the dependency is usable. Changed integration or dependency contracts require affected revalidation.

## State and completion

Keep ticket lifecycle separate from factory phase. Useful states are open, ready, active, blocked, done and cancelled; map them to actual tracker values. Record the reason and next action for a block. An explicit owner stop/cancellation persists; a new session does not erase it.

Ready needs confirmed scope, actionable criteria/journeys, authority, owner/session, usable workspace and satisfied dependencies. Done needs the required cycle/evidence at the recorded completion boundary. Distinguish implemented, locally checked/reviewed, cloud reviewed, merged and released. Pending exposure/release obligations remain visible.

## Privacy

Verify tracker visibility and authorized audience before publishing. Keep credentials, customer data, private transcripts, runtime dumps and unsanitized recordings outside tickets and reusable Git. Preserve sensitive original input privately with a safe faithful summary and controlled reference; do not claim omitted details were published. Share only the evidence needed for the decision. A private repository or snapshot is not permission to expose unrelated data.
