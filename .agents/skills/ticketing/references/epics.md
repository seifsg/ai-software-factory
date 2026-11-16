# Epics

Product and feature runs, and every epic's upkeep.

## Status

Epic follows its sub-issues. In progress: first one starts. Ready for QA: all still in run are Ready for QA or Done, and no requested item outside run is open unless owner-deferred. Done: every in-scope sub-issue (not follow-ups, owner-deferred or cancelled) Done and own checklist ticked; intake closes it, as PRs never use a closing keyword for an epic.

- Blocked sub-issue, or in-scope sub-issues owner moved to later iteration (still in scope, unlike owner-deferred): epic Blocked once rest finished. Record reason, what waits, who decides.
- Sub-issue going back: unticks its epic item and integration checks, pulls epic back to In progress. None left in run: epic returns to Backlog.
- Closed child list does not certify epic: it needs combined journey evidence; combined QA waits until its tickets finish implementation.

## Fast

Product and feature runs list every requested item and approved addition as R1, R2, ...; owner-deferred one stays listed as `R2 (owner-deferred: <decision link>)`, needs no criterion. Checker refuses gaps: at plan (gate A), a requested item no criterion names, and a criterion no checklist item names.

1. Create epic after owner's kickoff answers with owner's words, answers, every layout section.
2. Create sub-issues in user-value order, linked as native sub-issues; optional ideas go to follow-ups ticket.
