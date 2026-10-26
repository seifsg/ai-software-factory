---
name: how-to-make-a-pr
description: "Prepares and opens a draft pull request for human review, linked to its ticket and backed by before/after proof. Use when creating, updating or correcting a pull request."
---

# How to make a PR

Open a small, clear **draft PR** for human review. Humans decide ready, merge and release.

Analysis or review-only requests: do not open, push or comment.

## 1. Bind the project

Find the real repository, branches, release policy, PR template, signing rule, check commands, tracker and review owner from rules, manifests, CI and remote metadata; never copy accounts, branches or tools from another project. Ask only consequential gaps. A missing binding blocks its dependent step; keep local work going.

## 2. Ticket first

- Every PR belongs to a ticket. Search by symptom, feature, area, files, PR title and branch slug; none found: run `ticketing`.
- No ticket only when a project exemption covers the whole diff, or for a trivial change the run kept without one: the PR body says why.
- Link both ways: on open, the PR link in the ticket's activity; a clickable ticket link in the PR body.
- A finished ticket is Ready for QA while the PR is open, Done on merge; status follows `ticketing`.
- Ticket with a confirmed contract: refresh it before opening or updating. Pending scope, drift or a failed refresh is an open dependent step. A draft or local pass never replaces the owner's current expectation.

## 3. Branch from the right base

- Work on your own branch; never commit to the base. Protect dirty and foreign work: new branch or isolated checkout.
- Base = the project's integration branch, else the default branch. Say so in the PR when it differs.
- **Epic waves:** share an integration branch and draft PR. Finished lanes incorporate it, resolve/recheck, then integrate and push without force. Exception: an independently complete UI ticket ships its own draft after Show and Prove; dependencies must be included and checked. Humans alone authorize merge; do not wait for unrelated wave tickets.
- Dependent Safe ticket, wrong base or hotfix: `references/pr-cases.md`.
- Check the remote, not the local list: shallow and single-branch clones hide branches.

```text
git ls-remote --heads origin
git ls-remote --symref origin HEAD
git fetch origin
git switch -c <scope>/<short-name> origin/<base>
```

## 4. Plan the proof before editing

Every PR shows a skeptical owner truthful before/after proof: what failed or was missing, what now works, the observed benefit. Required in every mode. A short schema, diagram, table or labeled emoji may explain nonvisual proof; prose or illustrative diagrams never replace observed results. Shared backend changes that affect a UI journey still demonstrate that journey.

1. **Inventory now:** map the ticket and diff to every changed or new view, distinct visual state and touched user journey, with affected entry points and results even when only shared logic changed. One outcome per journey; shared views may link the same screenshot pair. Reconcile it again against the final diff.
2. **Capture each Before now**, with minimum safe navigation. Exercise or side effects needed: an isolated fixture or existing evidence, conditions stated. Missed: capture from the base commit in a separate checkout and say so. Web views: the gate's `shots` serves base and head on their own ports and shoots the same views at one size. Never fabricate it or reset dirty work to recreate it.
3. **Prepare the demo:** a fresh isolated slot, profile or test workspace by default; data needed: seed only deterministic, non-sensitive fixtures and record their reset recipe. Preserve the owner's workspace and data. Match before/after viewport, state, sample data and workload; explain unavoidable differences.
4. **Capture each After during final manual QA**, per the table: each journey from entry, single-step flows included, through real controls to its confirmed result, plus relevant changed validation, failure, edge and recovery paths. A success toast alone does not prove an external result. Use authorized test destinations; recording grants no sending permission.

| Surface | Proof, Before and After |
|---|---|
| Screen, page, section | Screenshot pair per changed view and distinct visual state; no hero image standing in for the rest |
| Touched interactive journey, motion | Final-candidate video per journey, plus screenshot pairs for its changed visuals; Before video optional |
| API | Same request: status and body as one `diff` block |
| CLI, script, gate | Same command: output as one `diff` block |
| Speed, size, cost | Measured numbers, same workload, fenced |
| Internal module | Proof through the screen, endpoint or command it changes |
| Method or prose | A fresh walkthrough's changed result, plus the key text as a `diff` |
| Something new | Before: the prior entry or empty-state screenshot (nonvisual: output), labeled "did not exist"; visual work still needs both screenshots |

- **Bug during capture:** stop, keep a short sanitized failure note, fix it in scope, run affected checks, commit and push the checked fix when authorized, reset the fixture, then restart the whole planned demo on that candidate. Replace failed or stale After media; never edit a failure out to imply success. A fix needing new authority blocks the demo with its cause and next action; no silent deferral or clean-pass claim.
- **Keep it fast:** plan shots and routes once, reuse one running build and fixture setup, screenshot while recording QA, share clips across outcomes, batch uploads and body updates; no duplicate angles or footage. Record setup, capture and upload durations and the slow stage in the work record; summarize material delay in the PR; improve actual repeated work. Shortest complete demo, never a time limit that drops coverage.
- Look at every screenshot and play every clip before use: readable, correct result, no unexplained errors, credentials or private data. Bind the inventory and After media to the demonstrated candidate; later code changes invalidate its After. Keep the base evidence; record conditions you could not match. A passing demo never proves no bugs remain.
- Upload media first (`references/github.md`); once the PR is open, check each image renders and each video plays for reviewers. No localhost or local-path links. Broken or inaccessible media is missing proof.
- Under every outcome declare **Visual:** and **Journey:** (`references/pr-layout.md`). A **Media waiver:** needs the owner's explicit request; missing tools, upload access or time never implies consent. Until media is supplied or waived, keep the gap and recovery action visible and evidence completion blocked. An incomplete draft may preserve progress but is not a completed handoff.

## 5. Make the change

- One thing per PR. Unrelated finds become follow-ups.
- Stage your own files by name. Never `git add .` or `git add -A`.
- Commit as `<type>(<scope>): <imperative subject>`; body = why, not the lines changed.
- Branch `<scope>/<short-name>` (`fix`, `feat`, `docs`, `chore`), or the project's convention.
- Honor required signing with the existing authorized identity; never invent one or bypass signing, permissions or protected gates.
- **No AI or tool attribution lines** in commits. The PR body ends with the factory credit line in `references/credit.md`.
- Required gates (step 1) pass before push. A check not run is **unverified**, not passed.
- CI is never required: the local runs of the required checks are the gate, and the PR names their commands and results. Never wait on or rerun CI; a CI result that arrives is extra evidence.
- Tests come last: implementation, manual QA on the real behavior, then write or adjust and run tests. A production fix found by tests goes back through manual QA, then tests rerun. No tests that restate the implementation.

## 6. Open the draft

1. Write the body to a file with `references/pr-layout.md`.
2. Push, then open as **draft** against the base. Commands: `references/github.md`.
3. Closing keyword only on each sub-issue or change ticket this PR finishes; the epic always gets a plain reference (intake closes it once its in-scope sub-issues are Done and its checklist is ticked).
4. Request review from the project's actual review owner through the supported mechanism, at draft time. Notify only the authorized recipient or channel. Reminders only when asked.
5. Link observation evidence (logs, traces, screenshots, measurements) only when authorized to share; state source and limits. No foreign session IDs, secrets or private data.

## 7. Review

- Own draft: `deep-review` it in Safe; in Fast and Lucky, the optional Safe check covers it. Skip when this exact head already passed an independent review. Pushing fixes to that PR's own branch and posting its comments are pre-authorized; open questions go in a PR comment, not a stop. Someone else's PR keeps every checkpoint.
- Project has a remote or cloud review: `references/pr-cases.md`.
- A reviewer that changes code needs a fresh independent assessment of the new head.
- The PR stays draft. Review is not merge or release approval.

## 8. Fast and Lucky PRs

Open one for every run, unasked, unless its wave's draft PR is open: then push to that branch and update that PR, appending the run's outcomes, criteria verification and remaining steps and refreshing the summary. Before creating or updating it, offer once per PR (a wave's shared PR: its first run): **"Run a Safe check first? (optional)"** (final manual QA, relevant tests, one independent review of the finished work). Yes: run it, fix, then open. No or no answer: open the draft as is.

- Variations requested: one branch and draft PR per variation, each following these rules with its own proof.
- List missing tests, review and baseline as unverified. Link the run's epic.

## Stops

- After a merge, start new work on a fresh branch from the current base.
- No force-push, history rewrite or unrequested merge, release or notification.
- No invented results, tests, authorship or accounts.
