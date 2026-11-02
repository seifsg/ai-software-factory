---
name: ticketing
description: "Creates and maintains the project backlog, its epics and tickets in every mode. Use when work needs tickets or backlog upkeep, when starting a product, feature or fix, or when a PR or review must be checked against a ticket."
---

# Ticketing

Remote ticket = record; local notes = cache. Write tickets with `references/ticket-layout.md`. Analysis, planning or review-only requests grant no tracker writes; explicit ticket request does.

## Tracker

1. Use project's tracker, available tracker integration first.
2. New project without remote: create private repository on owner's account, push default branch, use its Issues (`references/github.md`). Otherwise, none set and not already answered: ask once, recommending Issues in a private GitHub repository.
3. Resolve real repository, access, visibility before writing. No credentials, customer data, private transcripts or runtime dumps in tickets. Sensitive original input stays private: ticket gets faithful safe summary, saying details were withheld.
4. Search before creating: symptom, feature, area, files, PR title, branch. Reuse same work: bug, enhancement, QA note or review finding on an existing ticket's outcome updates that ticket as change of intent, reopened if closed. New ticket only for new outcome or on owner's ask. No duplicates; after uncertain response, read tracker and reconcile before creating again.
5. Record provider, project, native ID, URL.
6. Access or write fails: name step and next action, keep pending local record. No silent tracker switch, duplicate or success claim. Use only tools that exist; installing, paid access, messaging need own authority.
7. No tracker reachable, or none chosen yet while run goes on: write ticket to `.factory/ticket.md`, same layout; `local: .factory/ticket.md` stands in for its link. Move to tracker once one is set.

## Backlog

Open tickets = backlog, kept current in every mode, autonomously unless owner asks for checkpoints. Other tracker or board states: map each status to nearest existing one, name factory status in activity entry. Never create, rename or delete workflow states.

| Status | Means | Carries on entry |
|---|---|---|
| Backlog | Known, not in a run | Request or source |
| To do | Picked for this run: active sprint | Epic or request link |
| In progress | Being built, assigned | Branch; progress screenshots or recordings when they help |
| Dev done | Every checklist item ticked; criteria proof or PR still open | Commit, screenshot or output of the result |
| Ready for QA | Finished, PR open: owner tests and approves by merging | How to check it, the PR link |
| Done | Its PR merged, which closes it | The merged PR |
| Blocked | Cannot move | Reason, next action, who unblocks |
| Cancelled | Dropped or deprecated by owner. Closed | Owner decision and source |

1. Intake first, at session start and after merges: bounded, never blocking the run. List closed PRs once (merged and unmerged).
   - Merged, any base: each open ticket it names with a closing keyword closes with merged PR link, only while at Dev done or Ready for QA (board status or label), ticking its epic checklist item. Moved or reopened by a person after merge (board or label): keeps its status. Any other status: stays open, on stale list. Merge was owner's acceptance; recording it decides nothing new.
   - Closed unmerged, naming an open ticket with a closing keyword: [unmerged PRs](references/unmerged-pr.md).
   - Close each open epic that meets Done (step 5).
   - In-app feedback owner shares or agent can read goes to its existing ticket, else epic's follow-ups ticket.
   - Stale or duplicate tickets and PRs go to owner as one short list, proposed fate each (close, merge into #n, keep). Apply after answer; kept item notes it in its activity, not proposed again until it changes.
   - After search, split open items in same epic, area, topic: owned by this run, affected, untouched. One held by another run, session or person (To do through Ready for QA, or Blocked) is affected: ask owner before taking it over. Run that asks nothing takes it over only when request names it, and reports itself Blocked on it only when it cannot finish without it.
2. Move run's tickets to To do. Sort by priority, then user value, then proven dependencies.
3. Priority: P0 broken or blocking, P1 next, P2 planned, P3 later. Every ticket run creates or owns has one; change it only on those, with reason.
4. Move at boundaries: build starts → In progress, every item ticked → Dev done, every criterion proven and PR open → Ready for QA, PR merged → Done, check failed → In progress. Agents never set Done; merge closes ticket, or intake records a merge that did not. Blocked any time; back to prior status once cleared.
5. Epic follows its sub-issues. In progress: first one starts. Ready for QA: all still in run are Ready for QA or Done, and no requested item outside run is open unless owner-deferred. A sub-issue Blocked, moved to a later iteration or going back: [epic cases](references/epic-cases.md). Done: every in-scope sub-issue (not follow-ups, owner-deferred or cancelled) Done and own checklist ticked; intake closes it, as PRs never use a closing keyword for an epic. A `change` run's single ticket moves like a sub-issue.
6. In progress needs actionable criteria, authority, assignee or session, usable workspace, met dependencies for items it starts; Safe also confirmed scope. Assign builder at In progress; unassign only on return to Backlog or To do.
7. Keep owned tickets' context, description, links, progress current; scope changes follow Refresh and drift.
8. Implemented, checked, independently reviewed, merged, released stay distinct. Owner stop or cancellation persists across sessions.

### Activity

- One entry per ticket change (status, priority, assignee, scope, description, links, blocks, deprecation): date, who, old → new, why, proof link. Changes made together share one.
- Progress without ticket change, ticks included, waits for next boundary; that entry lists items ticked since last one. No per-edit diary.
- Append only; never edit or delete past entries. Entries record; never mention or ping people.
- Proof reader can open, sanitized. Not openable yet: say so.

### Hands off

- Touch only run's tickets and those its work affects.
- Affected, not owned (duplicate, dependency, overlap, same recent topic): once effect is known, add activity note with what changed and link; update its context when work changed its facts, unless it carries a [Safe contract](references/safe-contract.md). Status, priority, assignee, scope stay.
- Never close, archive, cancel, deprecate, reprioritize, reassign or rewrite other items without owner's task. Only exceptions: recording merges and closed PRs at intake (closing or moving those tickets, closing finished epics, dropping status labels) and filing feedback. Future items stay as they are. Cancelling needs owner, own tickets included.

## Split the work

- Ticket = one complete, user-visible outcome; epic and sub-issue contents: the layout.
- One or more outcome sub-issues, plus follow-ups ticket. Small product (one page, one screen, one tool) or small change: one ticket, no epic; its `Deferred (pending owner)` section is the follow-ups ticket wherever a method names one. Never one per todo.
- Never split risky work to dodge full checks.
- Every requested item (feature, journey, integration, behavior) maps to an outcome ticket criterion. Only owner's recorded decision moves it to follow-ups ticket; unavailable capability keeps it Blocked in the run.
- One open low-priority Backlog follow-ups sub-issue per epic, never per item: owner, reason, revisit condition. Include findings left after round 3, owner-deferred ideas, declined/unanswered MVP suggestions, real version of owner-approved simplifications. Scored polish uses [Finishing touches](references/finishing-touches.md) in that same ticket.

## Definition of done and checklist

1. Write definition of done (criteria with IDs) at creation, checklist (plan's todos as task items) at plan time.
2. Each item runs `get-ready-to-code` 0–4 loop; tick only after its check passed (real effect used and seen working), proof beside the tick.
3. Independent items and tickets run in parallel as far as files, dependencies, capacity allow; each item ticked after own check, each ticket keeps own checklist loop. One writer per ticket body: coordinator ticks, delegates report. Parallel tickets, handoffs to other sessions, dependencies between tickets: [parallel work](references/parallel-work.md).
4. Finished: every item ticked and every criterion proven; otherwise loop on failing item until it passes. Blocked only when run cannot clear it (access, capability, owner decision): reason, next action, who unblocks; independent items continue.
5. Owner-deferred item is ticked as `Deferred by the owner: <decision link>`; its criteria leave ticket with it. Counts as resolved, never as delivered.
6. Item only owner or missing hardware can finish stays unticked, ending `DEFERRED (owner|hardware: <what is needed>)`. Not Blocked: rest finishes, ticket reaches Ready for QA naming it, owner ticks it once done.

## Fast

No contract or confirmation round. Same tracker, layout, backlog, authority rules.

Product and feature runs list every requested item and approved addition as R1, R2, ...; owner-deferred one stays listed as `R2 (owner-deferred: <decision link>)`, needs no criterion. Checker refuses gaps: at plan (gate A), a requested item no criterion names, and a criterion no checklist item names.

1. Product and feature runs: create epic after owner's kickoff answers with owner's words, answers, every layout section. Change runs update ticket they follow up, create one only for new outcome, none when trivial.
2. Create sub-issues in user-value order, linked as native sub-issues; optional ideas go to follow-ups ticket.
3. Write into step 0 block of run file (`.factory/run.md`): epic URL (a `change` run: ticket URL, or `none (<why>)`), each sub-issue URL in the run, R-ids (product and feature runs), owned, affected, untouched backlog items, follow-ups included. At PR step, add each owned ticket's final status: Ready for QA with its PR (naming items deferred to owner or hardware), Blocked, or Backlog when owner-deferred.

## Safe

Safe runs, or moving an epic to Safe: [the contract](references/safe-contract.md), confirmed before implementation.

## Refresh and drift

- Refresh at intake or resume, after implementation, after local review before handoff or PR.
- Cheap refresh: compare ticket's updated time with last read; read fully only when changed, then compare scope content, not timestamps.
- Read before every write; reuse unchanged reads within a batch.
- New owner input, conflict, failed refresh or changed dependencies need reconciliation before dependent work; cache never proves current scope. Failed refresh: keep last confirmed snapshot, report blocker, continue independent work.
- Later input: preserve it, resolve authority, confirm or leave pending, record reason, reassess affected plans and consumers.
- Ticket is the spec: code and ticket never disagree. Change of intent (owner or QA note, fix review requires, need found while building) updates definition of done and checklist before the code, with one activity entry. Safe: scope change = new revision, reviewed independently against the old one. Never edit state, weaken acceptance or revive a cancelled ticket; changed goal may need linked replacement ticket.

## Review and deliver

1. Refresh the ticket.
2. Map every latest confirmed expectation and original input item to its implementation and actual evidence. Compare actual before with delivered after. List missing or partial results, unintended behavior, deviations.
3. Approved deviations keep authority and reason. Pending changes cannot redefine a pass. Unresolved drift, unknown required scope, missing evidence block dependent acceptance.
4. PRs and reviews carry ticket and epic links, confirmed criteria, before/after proof, decisions, unresolved findings, resume step.
5. Update ticket with actual outcome and openable, sanitized proof. Preserve blocked and cancelled work and open human decisions.
6. Closed child list does not certify epic: it needs combined journey evidence; combined QA waits until its tickets finish implementation.

## Output contract

In a factory run this is step 0. Block `## 0 Ticket` holds:

- [ ] The ticket link, or `local: .factory/ticket.md` with the reason
- [ ] Reused or new, with the search terms used
- [ ] The definition of done as labelled criteria
- [ ] The checklist (filled from the plan's todos at step 3) and the status
