---
name: ticketing
description: "Creates and maintains the project backlog, its epics and tickets in every mode. Use when work needs tickets or backlog upkeep, when starting a product, feature or fix, or when a PR or review must be checked against a ticket."
---

# Ticketing

The remote ticket is the record; local notes are a cache. Write tickets with `references/ticket-layout.md`. Analysis, planning or review-only requests grant no tracker writes; an explicit ticket request does.

## Tracker

1. Use the project's tracker, an available tracker integration first.
2. A new project without a remote: create a private repository on the owner's account, push the default branch and use its Issues (`references/github.md`). Otherwise, none set and not already answered: ask once, recommending Issues in a private GitHub repository.
3. Resolve the real repository, access and visibility before writing. No credentials, customer data, private transcripts or runtime dumps in tickets. Sensitive original input stays private: the ticket gets a faithful safe summary, saying details were withheld.
4. Search before creating: symptom, feature, area, files, PR title, branch. Reuse the same work: a bug, enhancement, QA note or review finding on an existing ticket's outcome updates that ticket as a change of intent, reopened if closed. A new ticket only for a new outcome or on the owner's ask. No duplicates; after an uncertain response, read the tracker and reconcile before creating again.
5. Record provider, project, native ID and URL.
6. Access or a write fails: name the step and next action, keep a pending local record. No silent tracker switch, duplicate or success claim. Use only tools that exist; installing, paid access and messaging need their own authority.
7. No tracker reachable, or none chosen yet while the run goes on: write the ticket to `.factory/ticket.md` in the same layout; `local: .factory/ticket.md` stands in for its link. Move it to the tracker once one is set.

## Backlog

Open tickets are the backlog, kept current in every mode, autonomously unless the owner asks for checkpoints. Other tracker or board states: map each status to the nearest existing one, naming the factory status in the activity entry. Never create, rename or delete workflow states.

| Status | Means | Carries on entry |
|---|---|---|
| Backlog | Known, not in a run | Request or source |
| To do | Picked for this run: the active sprint | Epic or request link |
| In progress | Being built, assigned | Branch; progress screenshots or recordings when they help |
| Dev done | Every checklist item ticked; criteria proof or PR still open | Commit, screenshot or output of the result |
| Ready for QA | Finished, PR open: the owner tests and approves by merging | How to check it, the PR link |
| Done | Its PR merged, which closes it | The merged PR |
| Blocked | Cannot move | Reason, next action, who unblocks |
| Cancelled | Dropped or deprecated by the owner. Closed | Owner decision and source |

1. Intake first, at session start and after merges: bounded, never blocking the run. List the closed PRs once (merged and unmerged).
   - Merged, any base: each open ticket it names with a closing keyword closes with the merged PR link, only while at Dev done or Ready for QA (board status or label), ticking its epic checklist item. Moved or reopened by a person after the merge (board or label): keeps its status. Any other status: stays open, on the stale list. The merge was the owner's acceptance; recording it decides nothing new.
   - Closed unmerged, naming an open ticket with a closing keyword: [unmerged PRs](references/unmerged-pr.md).
   - Close each open epic that meets Done (step 5).
   - In-app feedback the owner shares or the agent can read goes to its existing ticket, else the epic's follow-ups ticket.
   - Stale or duplicate tickets and PRs go to the owner as one short list, a proposed fate each (close, merge into #n, keep). Apply after the answer; a kept item notes it in its activity and is not proposed again until it changes.
   - After the search, split open items in the same epic, area and topic: owned by this run, affected, untouched. One held by another run, session or person (To do through Ready for QA, or Blocked) is affected: ask the owner before taking it over. A run that asks nothing takes it over only when the request names it, and reports itself Blocked on it only when it cannot finish without it.
2. Move the run's tickets to To do. Sort by priority, then user value, then proven dependencies.
3. Priority: P0 broken or blocking, P1 next, P2 planned, P3 later. Every ticket the run creates or owns has one; change it only on those, with the reason.
4. Move at boundaries: build starts → In progress, every item ticked → Dev done, every criterion proven and the PR open → Ready for QA, PR merged → Done, check failed → In progress. Agents never set Done; the merge closes the ticket, or intake records a merge that did not. Blocked any time; back to the prior status once cleared.
5. The epic follows its sub-issues. In progress: the first starts. Ready for QA: all still in the run are Ready for QA or Done, and no requested item outside the run is open unless owner-deferred. A sub-issue Blocked, moved to a later iteration or going back: [epic cases](references/epic-cases.md). Done: every in-scope sub-issue (not follow-ups, owner-deferred or cancelled) Done and its own checklist ticked; intake closes it, as PRs never use a closing keyword for an epic. A `change` run's single ticket moves like a sub-issue.
6. In progress needs actionable criteria, authority, an assignee or session, a usable workspace and met dependencies for the items it starts; Safe also confirmed scope. Assign the builder at In progress; unassign only on return to Backlog or To do.
7. Keep owned tickets' context, description, links and progress current; scope changes follow Refresh and drift.
8. Implemented, checked, independently reviewed, merged and released stay distinct. Owner stop or cancellation persists across sessions.

### Activity

- One entry per ticket change (status, priority, assignee, scope, description, links, blocks, deprecation): date, who, old → new, why, proof link. Changes made together share one.
- Progress without a ticket change, ticks included, waits for the next boundary; that entry lists the items ticked since the last one. No per-edit diary.
- Append only; never edit or delete past entries. Entries record; they never mention or ping people.
- Proof the reader can open, sanitized. Not openable yet: say so.

### Hands off

- Touch only the run's tickets and those its work affects.
- Affected, not owned (duplicate, dependency, overlap, same recent topic): once the effect is known, add an activity note with what changed and the link; update its context when the work changed its facts, unless it carries a [Safe contract](references/safe-contract.md). Status, priority, assignee and scope stay.
- Never close, archive, cancel, deprecate, reprioritize, reassign or rewrite other items without the owner's task. Only exceptions: recording merges and closed PRs at intake (closing or moving those tickets, closing finished epics, dropping status labels) and filing feedback. Future items stay as they are. Cancelling needs the owner, own tickets included.

## Split the work

- Ticket = one complete, user-visible outcome; epic and sub-issue contents: the layout.
- One or more outcome sub-issues, plus the follow-ups ticket. A small product (one page, one screen, one tool) or a small change: one ticket, no epic; its follow-ups go to a `Deferred (pending owner)` section in that ticket. Never one per todo.
- Ticket comments only on status changes, each linking the run file's blocks; no comment per step.
- Do not split risky work to dodge full checks.
- Every requested item (feature, journey, integration, behavior) maps to an outcome ticket criterion. Only the owner's recorded decision moves it to the follow-ups ticket; unavailable capability keeps it Blocked in the run.
- One open low-priority Backlog follow-ups sub-issue per epic, never per item: owner, reason and revisit condition. Include findings left after round 3, owner-deferred ideas, declined/unanswered MVP suggestions and the real version of owner-approved simplifications. Scored polish uses [Finishing touches](references/finishing-touches.md) in that same ticket.

## Definition of done and checklist

Every ticket, every mode: unfinished until both are complete.

1. Write the definition of done (criteria with IDs) at creation, the checklist (the plan's todos as task items) at plan time.
2. Each item runs the `get-ready-to-code` 0–4 loop; tick it only after its check passed (its real effect used and seen working), proof beside the tick.
3. Independent items and tickets run in parallel as far as files, dependencies and capacity allow; each item is ticked after its own check, each ticket keeps its own checklist loop. One writer per ticket body: the coordinator ticks, delegates report. Parallel tickets, handoffs to other sessions and dependencies between tickets: [parallel work](references/parallel-work.md).
4. Finished: every item ticked and every criterion proven; otherwise loop on the failing item until it passes. Blocked only when the run cannot clear it (access, capability, owner decision): reason, next action, who unblocks; its independent items continue.
5. An owner-deferred item is ticked as `Deferred by the owner: <decision link>`; its criteria leave the ticket with it. It counts as resolved, never as delivered.
6. An item only the owner or missing hardware can finish stays unticked, ending `DEFERRED (owner|hardware: <what is needed>)`. Not Blocked: the rest finishes, the ticket reaches Ready for QA naming it, the owner ticks it once done.

## Fast

No contract or confirmation round. Same tracker, layout, backlog and authority rules.

Product and feature runs list every requested item and approved addition as R1, R2, ...; an owner-deferred one stays listed as `R2 (owner-deferred: <decision link>)` and needs no criterion. The checker refuses gaps: at plan (gate A), a requested item no criterion names, and a criterion no checklist item names.

1. Product and feature runs: create the epic after the owner's kickoff answers with the owner's words, the answers and every layout section. Change runs update the ticket they follow up, create one only for a new outcome, none when trivial.
2. Create the sub-issues in user-value order, linked as native sub-issues; optional ideas go to the follow-ups ticket.
3. Write into the step 0 block of the run file (`.factory/run.md`): the epic URL (a `change` run: the ticket URL, or `none (<why>)`), each sub-issue URL in the run, the R-ids (product and feature runs), the owned, affected and untouched backlog items, follow-ups included. At the PR step, add each owned ticket's final status: Ready for QA with its PR (naming items deferred to the owner or hardware), Blocked, or Backlog when owner-deferred.

## Safe

Safe runs, or moving an epic to Safe: [the contract](references/safe-contract.md), confirmed before implementation.

## Refresh and drift

- Refresh at intake or resume, after implementation, and after local review before handoff or PR.
- Cheap refresh: compare the ticket's updated time with the last read; read fully only when it changed, then compare scope content, not timestamps.
- Read before every write; reuse unchanged reads within a batch.
- New owner input, a conflict, a failed refresh or changed dependencies need reconciliation before dependent work; a cache never proves current scope. Failed refresh: keep the last confirmed snapshot, report the blocker, continue independent work.
- Later input: preserve it, resolve authority, confirm or leave pending, record the reason, reassess affected plans and consumers.
- The ticket is the spec: code and ticket never disagree. A change of intent (an owner or QA note, a fix the review requires, a need found while building) updates the definition of done and checklist before the code, with one activity entry. Safe: a scope change is a new revision, reviewed independently against the old one. Never edit state, weaken acceptance or revive a cancelled ticket; a changed goal may need a linked replacement ticket.

## Review and deliver

1. Refresh the ticket.
2. Map every latest confirmed expectation and original input item to its implementation and actual evidence. Compare actual before with delivered after. List missing or partial results, unintended behavior, deviations.
3. Approved deviations keep authority and reason. Pending changes cannot redefine a pass. Unresolved drift, unknown required scope or missing evidence blocks dependent acceptance.
4. PRs and reviews carry ticket and epic links, confirmed criteria, before/after proof, decisions, unresolved findings, resume step.
5. Update the ticket with the actual outcome and openable, sanitized proof. Preserve blocked and cancelled work and open human decisions.
6. A closed child list does not certify the epic: it needs combined journey evidence, and combined QA waits until its tickets finish implementation.

## Output contract

In a factory run this is step 0. The block `## 0 Ticket` holds:

- [ ] The ticket link, or `local: .factory/ticket.md` with the reason
- [ ] Reused or new, with the search terms used
- [ ] The definition of done as labelled criteria
- [ ] The checklist (filled from the plan's todos at step 3) and the status
