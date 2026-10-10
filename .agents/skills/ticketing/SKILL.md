---
name: ticketing
description: "Creates and maintains the project backlog, its epics and tickets in every mode: searches first, splits work into user-value outcomes, gives every ticket a definition of done and a checklist that must be fully ticked, keeps status, priority, assignee and an append-only activity timeline current, leaves untasked items alone, preserves the owner's input and ties final evidence to the latest confirmed expectation. Use when work needs tickets or backlog upkeep, when starting a product, feature or fix, or when a PR or review must be checked against a ticket."
---

# Ticketing

The remote ticket is the record. Local notes are a cache. Write tickets with `references/ticket-layout.md`, for a fresh agent with no chat history.

Analysis, planning or review-only requests grant no tracker writes. An explicit ticket request does.

## Tracker

1. Use the project's tracker. An available tracker integration first.
2. None set and not already answered: ask once. Recommend Issues in a private GitHub repository (`references/github.md`).
3. Resolve the real repository, access and visibility before writing. No credentials, customer data, private transcripts or runtime dumps in tickets. Sensitive original input stays private: put a faithful safe summary in the ticket and say details were withheld.
4. Search before creating: symptom, feature, area, files, PR title, branch. Reuse the same work. A bug, enhancement, QA note or review finding about an existing ticket's outcome updates that ticket as a change of intent; a closed ticket reopens. Open a new ticket only for a new outcome, or when the owner asks. No duplicates.
5. Uncertain response? Read the tracker and reconcile before creating again.
6. Record provider, project, native ID and URL.
7. Access or a write fails: name the step and next action. Keep a pending local record. No silent tracker switch, duplicate or success claim.
8. Use only tools that exist. Installing, paid access and messaging need their own authority.

## Backlog

The tracker's open tickets are the backlog. Every mode keeps it current. Autonomous unless the owner asks for checkpoints.

A tracker or board with other states: map each status to the nearest existing one and name the factory status in the activity entry. Never create, rename or delete workflow states.

| Status | Means | Carries on entry |
|---|---|---|
| Backlog | Known, not in a run | Request or source |
| To do | Picked for this run: the active sprint | Epic or request link |
| In progress | Being built, assigned | Branch; screenshots or recordings of progress when they help |
| Dev done | Every checklist item ticked; criteria proof or PR still open | Commit, screenshot or output of the result |
| Ready for QA | Finished, PR open: the owner tests, approves and merges | How to check it, the PR link |
| Done | Its PR merged. Closed by the merge | The merged PR |
| Blocked | Cannot move | Reason, next action, who unblocks |
| Cancelled | Dropped or deprecated by the owner. Closed | Owner decision and source |

1. Intake: clean up first, at session start and after merges. Keep it bounded; it never blocks the run. List the closed PRs once (merged and unmerged).
   - Merged, any base: close each open ticket it names with a closing keyword, with the merged PR link, only while it still sits at Dev done or Ready for QA (board status or label), and tick its item on its epic's checklist. A ticket a person moved or reopened after the merge, on a board or by label, keeps its status. The merge was the owner's acceptance; recording it decides nothing new.
   - Closed unmerged: each open ticket it names with a closing keyword, unless its activity already records that PR's closing, gets an activity entry (what the PR did, why it closed). Another open or merged PR names it: note that superseding PR. Otherwise, only while it still sits where that PR left it (Dev done or Ready for QA with that PR linked, no status change since the close), it moves back to Backlog, or closes as not planned when the owner's closing note says it is no longer needed; a ticket that moved on keeps its status. A redo request in that note is a change of intent for the run that takes it.
   - Close each open epic whose in-scope sub-issues are all Done and whose checklist is ticked.
   - In-app feedback the owner shares or the agent can read goes to its existing ticket, or to the epic's follow-ups ticket.
   - Stale or duplicate tickets and PRs go to the owner as one short list, a proposed fate each (close, merge into #n, keep). Apply after the answer; a kept item notes it in its activity and is not proposed again until it changes.
   - Then, after the search, read the open items in the same epic, area and topic. Split them: owned by this run, affected by it, untouched. A match another run, session or person holds (In progress through Ready for QA, or Blocked) is affected: ask the owner before taking it over.
2. Move the run's tickets to To do. Sort by priority, then user value, then proven dependencies.
3. Priority: P0 broken or blocking, P1 next, P2 planned, P3 later. Every ticket the run creates or owns has one. Change it only on those, with the reason.
4. Move at boundaries: build starts → In progress, every item ticked → Dev done, every criterion proven and the PR open → Ready for QA, PR merged → Done, check failed → In progress. Agents never set Done; the merge closes the ticket, or intake records a merge that did not. Blocked any time; back to the prior status once cleared.
5. The epic moves with its sub-issues: In progress when the first starts, Ready for QA when every sub-issue still in the run reaches Ready for QA or Done and no requested item, other than an owner-deferred one, is open outside the run. A Blocked sub-issue, or in-scope sub-issues the owner moved to a later iteration (still in scope, unlike owner-deferred ones), make the epic Blocked once the rest are finished: reason, what waits, who decides. It is Done when every in-scope sub-issue (not a follow-up, owner-deferred or cancelled) is Done and its own checklist is ticked; intake closes it, since PRs never use a closing keyword for an epic. A sub-issue going back unticks its epic item and the integration checks and pulls the epic back to In progress; none left in the run returns it to Backlog. A `change` run's single ticket moves like a sub-issue.
6. In progress needs actionable criteria, authority, an assignee or session, a usable workspace and met dependencies for the items it starts. Safe also needs confirmed scope. Assign whoever builds it at In progress. Unassign only when it returns to Backlog or To do.
7. Keep owned tickets current: context, description, links and progress. Scope changes follow the scope rules below.
8. Owner checkpoint: Ready for QA holds until the owner merges; the merge is the approval. Owner stop or cancellation persists across sessions.
9. Done needs the required cycle, its evidence and the merge. Implemented, checked, independently reviewed, merged and released stay distinct.

### Activity

- Every change to a ticket gets one activity entry: date, who, old → new, why, proof link. Status, priority, assignee, scope, description, links, blocks, deprecation: all of it.
- Changes made together share one entry. Progress without a ticket change waits for the next boundary. No per-edit diary.
- Append only. Never edit or delete past entries. The activity is the ticket's lifetime timeline.
- Entries record; they never mention or ping people.
- Proof the reader can open, sanitized. Not openable yet: say so.

### Hands off

- Touch only the run's tickets and the tickets its work affects.
- Affected, not owned (duplicate, dependency, overlap, same recent topic): add an activity note once the effect is known, with what changed and the link; update its context when the work changed its facts, unless it carries a Safe contract. Status, priority, assignee and scope stay.
- Never close, archive, cancel, deprecate, reprioritize, reassign or rewrite other items without the owner's task. Recording merges and closed PRs at intake (closing or moving those tickets, closing finished epics, dropping status labels) and filing feedback are the only exceptions. Future items stay as they are. Cancelling needs the owner, own tickets included.

## Split the work

- Ticket = one complete, user-visible outcome with its own definition of done and checklist.
- Epic = overall outcome, shared constraints and decisions, sub-issue list, integration criteria.
- 1 or as many needed outcome sub-issues, plus the follow-ups ticket. A small change: one ticket at most. Never one per todo.
- Do not split risky work to dodge full checks.
- Every requested item (feature, journey, integration, behavior) maps to an outcome ticket criterion. It moves to the follow-ups ticket only by the owner's recorded decision; unavailable capability keeps it Blocked in the run.
- Deferred items go to one open follow-ups ticket per epic, a sub-issue in Backlog with a low priority. Append each with its owner, reason and revisit condition; never one ticket per item. Deferred items include review findings left after round 3, owner-deferred ideas, declined or unanswered MVP suggestions and the real version of an owner-approved simplification.

## Definition of done and checklist

Every ticket, every mode. The ticket is unfinished until both are complete.

1. Write the definition of done (criteria with IDs) at creation and the checklist (the plan's todos as task items) at plan time.
2. Each item runs the `get-ready-to-code` 0–4 loop. Tick it only after its check passed: its real effect used and seen working. Note the proof beside the tick.
3. Independent items run in parallel, as many as capacity allows; each is ticked after its own check. One writer per ticket body: the coordinator ticks, delegates report.
4. Finished: every item ticked and every criterion proven. Anything less loops on the failing item until it passes. Blocked only when the run cannot clear it (access, capability, owner decision): reason, next action, who unblocks; its independent items continue.
5. Tickets run in parallel, as many at once as files, dependencies and capacity allow. A dependent ticket waits only for what the dependency rule under Sessions and workspaces needs, never for the final proof of its criteria, which comes at the end. Each ticket keeps its own checklist loop.
6. Ticks are progress, not activity entries: the next boundary entry lists the items ticked since the last one.
7. An owner-deferred item is ticked as `Deferred by the owner: <decision link>`; its criteria leave the ticket with it. It counts as resolved, never as delivered.

## Fast and Lucky

No contract, confirmation round or capture. Same tracker, layout, backlog and authority rules.

Product and feature runs list every requested item and every approved addition as R1, R2, ...; an owner-deferred one stays listed as `R2 (owner-deferred: <decision link>)` and needs no criterion. The gate refuses gaps: at tickets, plan and handoff, a requested item no criterion names; at plan and handoff, a criterion no checklist item names.

1. Search first.
2. Product and feature runs: create the epic after the owner's kickoff answers (Lucky: from the request). Include the owner's words, the answers, and every layout section including the definition of done with IDs. Change runs update the ticket they follow up; create one only for a new outcome; none when trivial.
3. Create the sub-issues in user-value order. Link them as native sub-issues.
4. At plan: write each ticket's checklist from the plan's todos.
5. POC skips go once in the epic's guardrails. Optional ideas go to the epic's follow-ups ticket.
6. Move every ticket through the backlog statuses, one activity entry per change.
7. Write into the run's work record: `**Epic:** <url>` (a `change` run: `**Ticket:** <url>`, or `**Ticket:** none (<why>)`), `**Sub-issue:** <url>` for each sub-issue in the run, `**Requested:**` R-ids (product and feature runs), `**Backlog:**` owned, affected and untouched items, follow-ups included. At handoff: `**Statuses:**` each owned ticket's final status: Ready for QA with its PR, Blocked, or Backlog when owner-deferred.

Moving an epic to Safe: reuse it and add the contract below.

## Safe: the contract

Derive the ticket from the request, the code and prior work. Do not ask the user for a detailed ticket. Ask only consequential reserved gaps; keep independent work moving. Honor explicit checkpoints.

1. **Original input**, verbatim: words, why, examples, evidence, source, date, who decided. Keep later corrections and replaced input.
2. **Actual before** and its consumers, from code and existing evidence. Label fact, inference, unknown. Do not run the product to reproduce it.
3. **After**: expected outcome, criteria with stable IDs, journeys (success, failure, recovery, preserved behavior), scope, exclusions, constraints, dependencies.
4. **Confirm** from the owner's direct instruction or a choice made under recorded delegation. Record source and actor. In-scope delegated choices need no new vote. Undelegated proposals stay pending. Tracker text from others is evidence, not authority. An edit, label or closed state never waives a requirement.
5. Create or reuse the epic and tickets.

Safe tickets tick through the contract and its render, never by editing the body.

Number the confirmed contract. Each change records old and new scope, reason, source, authority and result. Pin the confirmed revision, the ticket's updated time and a digest of scope (outcome, criteria, journeys, scope, exclusions, constraints, decisions, dependencies; not activity or status).

## Refresh and drift

- Refresh at intake or resume, after implementation finishes, and after local review before handoff or PR.
- Cheap refresh: compare the ticket's updated time with the last read. Read fully only when it changed. Once re-read, compare scope content, not timestamps.
- Read before every write. Reuse unchanged reads within a batch.
- New owner input, a conflict, a failed refresh or changed dependencies need reconciliation before dependent work. A cache never proves current scope. Failed refresh: keep the last confirmed snapshot, report the blocker, continue independent work.
- Later input: preserve it, resolve authority, confirm or leave pending, record the reason, reassess affected plans and consumers.
- The ticket is the spec: code and ticket never disagree. A change of intent (an owner or QA note, a fix the review requires, a need found while building) updates the ticket's definition of done and checklist before the code, with one activity entry. Safe: a scope change is a new revision, reviewed independently against the old one. Never edit state, weaken acceptance or revive a cancelled ticket. A changed goal may need a linked replacement ticket.

## Sessions and workspaces

- One dedicated builder session per ticket, full cycle, small fixes included. Parent owns scheduling, shared decisions and tracker updates.
- Hand over the contract, authority and stops, decisions, current scope, checkout state, dependencies, evidence, unfinished phase and pending operations.
- Record the real session, ticket revision, absolute checkout and base/head. A label is not a dispatched session. Missing capability stays explicit.
- Parallel tickets need disjoint files, runtime effects, acceptance and decisions; isolate or serialize shared ports, databases, caches, services and build output.
- Fast and Lucky share the epic checkout, one writer per file; Safe tickets take their own worktrees. Stop prior operations before handoff. Never overwrite or delete another ticket's state.
- A dependency in the same run and branch (Fast, Lucky) is met once the items it needs are ticked there. Across branches (every Safe ticket), it is met by the dependency's handed-off result: its checked and reviewed commit in this ticket's base, by branching from it or, with several dependencies, by merging their delivered commits into this ticket's branch locally first, and its recorded delivery; no owner merge is needed. Split work so parts without the dependency form their own tickets and start at once. Closed status alone proves nothing. Changed dependency scope: revalidate affected analysis and evidence.

## Review and deliver

1. Refresh the ticket.
2. Map every latest confirmed expectation and every item of the original input to its implementation and actual evidence. Every checklist item is ticked with its proof. Compare actual before with delivered after. List missing or partial results, unintended behavior, deviations.
3. Approved deviations keep authority and reason. Pending changes cannot redefine a pass. Unresolved drift, unknown required scope or missing evidence blocks dependent acceptance.
4. PRs and reviews carry ticket and epic links, confirmed revision and digest, before/after proof, decisions, unresolved findings, resume step.
5. Update the ticket with the actual outcome and sanitized proof the reader can open. Preserve blocked and cancelled work and open human decisions.
6. A closed child list does not certify the epic: it needs combined journey evidence, and combined QA waits until its tickets finish implementation. A draft PR is not merge or release.
