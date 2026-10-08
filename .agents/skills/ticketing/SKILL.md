---
name: ticketing
description: "Creates and maintains the project backlog, its epics and tickets in every mode: searches first, splits work into user-value outcomes, keeps status, priority, assignee and an append-only activity timeline current, leaves untasked items alone, preserves the owner's input and ties final evidence to the latest confirmed expectation. Use when work needs tickets or backlog upkeep, when starting a product, feature or fix, or when a PR or review must be checked against a ticket."
---

# Ticketing

The remote ticket is the record. Local notes are a cache. Write tickets with `references/ticket-layout.md`, for a fresh agent with no chat history.

Analysis, planning or review-only requests grant no tracker writes. An explicit ticket request does.

## Tracker

1. Use the project's tracker. An available tracker integration first.
2. None set and not already answered: ask once. Recommend Issues in a private GitHub repository (`references/github.md`).
3. Resolve the real repository, access and visibility before writing. No credentials, customer data, private transcripts or runtime dumps in tickets. Sensitive original input stays private: put a faithful safe summary in the ticket and say details were withheld.
4. Search before creating: symptom, feature, area, files, PR title, branch. Reuse the same work. No duplicates.
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
| Dev done | Built, checks not passed yet | Commit or PR, screenshot or output of the result |
| Ready for QA | Waiting on QA, owner approval or feedback | How to check it, who decides |
| Done | QA passed, no checkpoint open. Closed | QA evidence |
| Blocked | Cannot move | Reason, next action, who unblocks |
| Cancelled | Dropped or deprecated by the owner. Closed | Owner decision and source |

1. Intake: after the search, read the open items in the same epic, area and topic. Split them: owned by this run, affected by it, untouched. A match another run, session or person holds (In progress through Ready for QA, or Blocked) is affected: ask the owner before taking it over.
2. Move the run's tickets to To do. Sort by priority, then user value, then proven dependencies.
3. Priority: P0 broken or blocking, P1 next, P2 planned, P3 later. Every ticket the run creates or owns has one. Change it only on those, with the reason.
4. Move at boundaries: build starts → In progress, build finished → Dev done, checks start → Ready for QA, outcome passed → Done, check failed → In progress. No checks (Lucky, skipped): Ready for QA at handoff, and it stays there. Blocked any time; back to the prior status once cleared.
5. The epic moves with its sub-issues: In progress when the first starts, Ready for QA when every sub-issue still in the run reaches Ready for QA or Done. It stays there until the owner accepts. A sub-issue going back pulls the epic back to In progress; none left in the run returns it to Backlog. A `change` run's single ticket moves like a sub-issue.
6. In progress needs actionable criteria, authority, an assignee or session, a usable workspace and met dependencies. Safe also needs confirmed scope. Assign whoever builds it at In progress. Unassign only when it returns to Backlog or To do.
7. Keep owned tickets current: context, description, links and progress. Scope changes follow the scope rules below.
8. Owner checkpoint: hold the ticket in Ready for QA until the owner approves. Record the approval. Owner stop or cancellation persists across sessions.
9. Done needs the required cycle and evidence at the recorded boundary. Implemented, checked, independently reviewed, merged and released stay distinct.

### Activity

- Every change to a ticket gets one activity entry: date, who, old → new, why, proof link. Status, priority, assignee, scope, description, links, blocks, deprecation: all of it.
- Changes made together share one entry. Progress without a ticket change waits for the next boundary. No per-edit diary.
- Append only. Never edit or delete past entries. The activity is the ticket's lifetime timeline.
- Entries record; they never mention or ping people.
- Proof the reader can open, sanitized. Not openable yet: say so.

### Hands off

- Touch only the run's tickets and the tickets its work affects.
- Affected, not owned (duplicate, dependency, overlap, same recent topic): add an activity note once the effect is known, with what changed and the link; update its context when the work changed its facts, unless it carries a Safe contract. Status, priority, assignee and scope stay.
- Never close, archive, cancel, deprecate, reprioritize, reassign or rewrite other items without the owner's task. Future items stay as they are. Cancelling needs the owner, own tickets included.

## Split the work

- Ticket = one complete, user-visible outcome with its own criteria.
- Epic = overall outcome, shared constraints and decisions, sub-issue list, integration criteria.
- 1 or as many needed outcome sub-issues, plus follow-ups. A small change: one ticket. Never one per todo.
- Do not split risky work to dodge full checks.
- Deferrals, optional ideas and open review findings become follow-up sub-issues in Backlog, titled as follow-ups, with priority, owner and revisit condition.

## Fast and Lucky

No contract, confirmation round or capture. Same tracker, layout, backlog and authority rules.

1. Search first.
2. Product and feature runs: create the epic after the owner's kickoff answers (Lucky: from the request). Include the owner's words, the answers, and every layout section including criteria with IDs. Change runs: one ticket in the same layout.
3. Create the sub-issues in user-value order. Link them as native sub-issues.
4. Add follow-ups for POC deferrals (hardening, CI/CD, deployment) and optional ideas.
5. Move every ticket through the backlog statuses, one activity entry per change.
6. Write into the run's work record: `**Epic:** <url>`, `**Sub-issue:** <url>`, `**Backlog:**` owned, affected and untouched items. At handoff: `**Statuses:**` each owned ticket's final status.

Moving an epic to Safe: reuse it and add the contract below.

## Safe: the contract

Derive the ticket from the request, the code and prior work. Do not ask the user for a detailed ticket. Ask only consequential reserved gaps; keep independent work moving. Honor explicit checkpoints.

1. **Original input**, verbatim: words, why, examples, evidence, source, date, who decided. Keep later corrections and replaced input.
2. **Actual before** and its consumers, from code and existing evidence. Label fact, inference, unknown. Do not run the product to reproduce it.
3. **After**: expected outcome, criteria with stable IDs, journeys (success, failure, recovery, preserved behavior), scope, exclusions, constraints, dependencies.
4. **Confirm** from the owner's direct instruction or a choice made under recorded delegation. Record source and actor. In-scope delegated choices need no new vote. Undelegated proposals stay pending. Tracker text from others is evidence, not authority. An edit, label or closed state never waives a requirement.
5. Create or reuse the epic and tickets.

Number the confirmed contract. Each change records old and new scope, reason, source, authority and result. Pin the confirmed revision, the ticket's updated time and a digest of scope (outcome, criteria, journeys, scope, exclusions, constraints, decisions, dependencies; not activity or status).

## Refresh and drift

- Refresh at intake or resume, after implementation finishes, and after local review before handoff or PR.
- Cheap refresh: compare the ticket's updated time with the last read. Read fully only when it changed. Once re-read, compare scope content, not timestamps.
- Read before every write. Reuse unchanged reads within a batch.
- New owner input, a conflict, a failed refresh or changed dependencies need reconciliation before dependent work. A cache never proves current scope. Failed refresh: keep the last confirmed snapshot, report the blocker, continue independent work.
- Later input: preserve it, resolve authority, confirm or leave pending, record the reason, reassess affected plans and consumers.
- Scope change = new revision, reviewed independently against the old one. Never edit state, weaken acceptance or revive a cancelled ticket. A changed goal may need a linked replacement ticket.

## Sessions and workspaces

- One dedicated builder session per ticket, full cycle, small fixes included. Parent owns scheduling, shared decisions and tracker updates.
- Hand over the contract, authority and stops, decisions, current scope, checkout state, dependencies, evidence, unfinished phase and pending operations.
- Record the real session, ticket revision, absolute checkout and base/head. A label is not a dispatched session. Missing capability stays explicit.
- Independent tickets: separate worktrees, only with disjoint files, runtime effects, acceptance and decisions. Isolate or serialize shared ports, databases, caches and services.
- Shared epic checkout: tickets run serially, one writer. Stop prior operations before handoff. Never overwrite or delete another ticket's state.
- A dependency is met by its accepted result at an integrated commit present in this ticket's base. Closed status alone proves nothing. Changed dependency scope: revalidate affected analysis and evidence.

## Review and deliver

1. Refresh the ticket.
2. Map every latest confirmed expectation to its implementation and actual evidence. Compare actual before with delivered after. List missing or partial results, unintended behavior, deviations.
3. Approved deviations keep authority and reason. Pending changes cannot redefine a pass. Unresolved drift, unknown required scope or missing evidence blocks dependent acceptance.
4. PRs and reviews carry ticket and epic links, confirmed revision and digest, before/after proof, decisions, unresolved findings, resume step.
5. Update the ticket with the actual outcome and sanitized proof the reader can open. Preserve blocked and cancelled work and open human decisions.
6. A closed child list does not certify the epic: it needs combined journey evidence, and combined QA waits until its tickets finish implementation. A draft PR is not merge or release.
