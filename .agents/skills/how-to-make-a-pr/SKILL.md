---
name: how-to-make-a-pr
description: "Prepares and opens a draft pull request for human review, linked to its ticket and backed by before/after proof. Use when creating, updating or correcting a pull request."
---

# How to make a PR

Open a small, clear **draft PR** for human review. Humans decide ready, merge and release. This skill grants no merge, release or notification authority.

Analysis or review-only requests: do not open, push or comment.

## 1. Bind the project

Find the real repository, branches, release policy, PR template, signing rule, check commands, tracker and review owner from rules, manifests, CI and remote metadata. Copy no accounts, branches or tools from another project. Ask only consequential gaps. A missing binding blocks its dependent step; keep local work going.

## 2. Ticket first

- Every PR belongs to a ticket. None yet: run `ticketing`. Search by symptom, feature, area, files, PR title and branch slug first.
- No ticket only when the project defines an exemption and the whole diff falls under it, or for a trivial change the run kept without one: the PR body says why.
- Link both ways: PR URL in the ticket, clickable ticket link in the PR body.
- On open, add the PR link to the ticket's activity. A finished ticket waits in Ready for QA while the PR is open; the merge closes it as Done. Its status follows `ticketing`.
- Ticket with a confirmed contract: refresh it before opening or updating. Pending scope, drift or a failed refresh is an open dependent step. A draft or local pass never replaces the owner's current expectation.

## 3. Branch from the right base

- Work on your own branch. Never commit to the base.
- Base = the project's integration branch, else the default branch. Say so in the PR when it differs.
- **Dependent Safe ticket:** branch from the dependency's delivered commit and open the PR against the dependency's branch. Several dependencies: against the base, naming each dependency PR that merges first. After that branch merges, retarget the PR to the base (`references/github.md`).
- Check the remote, not the local list. Shallow and single-branch clones hide branches.

```text
git ls-remote --heads origin
git ls-remote --symref origin HEAD
git fetch origin
git switch -c <scope>/<short-name> origin/<base>
```

- Protect dirty and foreign work. New branch or isolated checkout.
- **Wrong base:** head already on the right ancestry: change the PR base (`references/github.md`). Diverged: new branch from the right base, cherry-pick the relevant commits, open a replacement PR, close the old one as replaced after approval. No force-push.
- **Hotfix**, only on explicit request. Separate production and integration branches mean a pair: the production PR plus a companion PR with the same change into integration. Branch the companion from integration and `git cherry-pick -x` only the fix commits. Never open a second PR from the production branch into integration: it drags in production-only commits. Link both; mirror every follow-up. One release branch: no pair.

## 4. Plan the proof before editing

Every PR is a demonstration to its stakeholders. Put Before & after immediately after a short purpose and ticket link, ahead of implementation detail (`references/pr-layout.md`). This proof is required in every mode unless the owner explicitly asks to omit the named media.

1. **Inventory the proof before editing:** map the ticket and diff to every changed or new view, distinct visual state and touched user journey. Name outcomes by their effect, never a file or folder. Include affected entry points and results, even when only shared logic changed. One outcome per journey; shared views may link the same screenshot pair. Reconcile the inventory again against the final diff.
2. **Capture each Before now**, before edits, with minimum safe navigation. If exercise or side effects are needed, use an isolated fixture or existing evidence and state its conditions. Missed it: capture from the base commit in a separate checkout and say so. Never fabricate it or reset dirty work to recreate it. New UI still needs the prior entry or empty-state screenshot, labeled "did not exist".
3. **Prepare the demonstration:** use a fresh isolated slot, profile or test workspace by default. When the journey needs data, seed only deterministic, non-sensitive fixtures and record their reset recipe. Preserve the owner's workspace and data. Match before/after viewport, state, sample data and workload; explain unavoidable differences.
4. **Capture each After during final manual QA:** screenshots cover every changed view/state; video shows every touched journey, including single-step flows, through real controls to its confirmed result. Record relevant changed validation, failure, edge and recovery paths too. A success toast alone does not prove an external result. Use authorized test destinations; recording grants no sending permission.

| Surface | Proof, Before and After |
|---|---|
| Screen, page, section | Before/after screenshot pair for every changed view and distinct visual state; no single hero image standing in for the rest |
| Any touched user journey, or motion | Final-candidate video from entry through actions to result for each journey, plus screenshot pairs for its changed visuals. A Before video is optional; GIFs are previews, never the required video |
| API | The same request: status and body as one `diff` block |
| CLI, script, gate | The same command: output as one `diff` block |
| Speed, size, cost | Measured numbers, same workload, in a fenced block |
| Internal module | Proof through the screen, endpoint or command whose behavior it changes |
| Method or prose | The behavior it changes (a fresh walkthrough's result), plus the key text as a `diff` |
| Something new | Before: the prior entry or empty state, labeled "did not exist"; visual work still needs both screenshots |

- **Bug during capture:** stop the demonstration, preserve a short sanitized failure note, fix the bug in scope, run affected checks, commit and push the checked fix when authorized, reset the fixture, then restart the entire planned demonstration from its beginning on that candidate. Replace failed or stale After media, never edit a failure out to imply success. A fix needing new authority blocks the demo with its cause and next action; no silent deferral or clean-pass claim.
- **Keep it fast:** plan shots and routes once, reuse one running build and fixture setup, capture screenshots while recording QA, share clips across outcomes with exact timestamps, batch uploads and body updates. Cover every distinct change without duplicate angles or repeated footage. Record setup/capture/upload durations and the slow stage; improve actual repeated work. Aim for the shortest complete demonstration, not a fixed time limit that drops coverage. Restart after a bug; retain valid base captures.
- Look at every screenshot and play every clip before using it: readable, correct result, no unexplained errors, no credentials or private data. Bind the inventory and After media to the demonstrated candidate; later code changes invalidate its After demonstration. Keep the base evidence and record any conditions you could not match. Passing a demo never proves the absence of all bugs.
- Upload media first (`references/github.md`); once the PR is open, verify each image renders and each video plays for reviewers. No localhost or local-path links. Broken or inaccessible media is missing proof.
- Under every outcome declare **Visual:** and **Journey:** using `references/pr-layout.md`; its **Video:** links its journey. A **Media waiver:** applies only to that outcome and named media, quoting the owner's explicit request with its source. Missing tools, upload access or time never implies consent. Keep the gap and recovery action visible and block evidence completion until supplied or explicitly waived. An incomplete draft may preserve progress but is not a completed handoff.

## 5. Make the change

- One thing per PR. Unrelated finds become follow-ups.
- Stage your own files by name. Never `git add .` or `git add -A`.
- Commit as `<type>(<scope>): <imperative subject>`. Body = why, not the lines changed.
- Branch name `<scope>/<short-name>` (`fix`, `feat`, `docs`, `chore`), or the project's convention.
- Honor required signing with the existing authorized identity. Never invent an identity or bypass signing, permissions or protected gates.
- **No AI or tool attribution lines** in commits. The PR body ends with the factory credit line in `references/credit.md`, in place of any line your agent adds by default.
- Find the real checks from rules, manifests and CI. Required gates pass before push. A check not run is **unverified**, not passed.
- Tests come last: finish implementation, manual QA on the real behavior, then write or adjust and run tests. A production fix found by tests goes back through manual QA, then tests rerun. No tests that restate the implementation.

## 6. Open the draft

1. Write the body to a file with `references/pr-layout.md`. Fill the project's PR template first, if it has one.
2. Push, then open as **draft** against the base. Commands: `references/github.md`.
3. Include: ticket links, attribution, before/after proof, criteria verification, what is unverified, history, remaining steps. A closing keyword goes only on each sub-issue or change ticket this PR finishes; the epic always gets a plain reference, and intake closes it when its in-scope sub-issues are Done and its checklist is ticked. A human or agent must continue cold from the PR.
4. Request review from the project's actual review owner through the supported mechanism, at draft time. Notify only the authorized recipient or channel. Reminders only when asked.
5. Link observation evidence (logs, traces, screenshots, measurements) only when authorized to share. State source and limits. No foreign session IDs, secrets or private data.

## 7. Review

- Own draft: run `deep-review` on it in Safe; in Fast and Lucky, the optional Safe check offer covers it. Skip it when this exact head already passed an independent review. Pushing fixes to that PR's own branch (never force) and posting its comments are pre-authorized; open questions go in a PR comment instead of a stop. Someone else's PR keeps every checkpoint.
- When the project has a remote or cloud review, request a fresh one: a separate agent, fresh context, the exact pushed head. Record where it ran, the run ID, base/head and verdict. Local review is separate and never a substitute; missing remote access leaves the review open.
- A reviewer that changes code needs a fresh independent assessment of the new head.
- The PR stays draft. Review is not merge or release approval.

## 8. Fast and Lucky PRs

Open one for every run, unasked. Before creating or updating it, offer once: **"Run a Safe check first? (optional)"** No answer: open the draft as is.

Variations requested: one branch and draft PR per variation, each following these rules with its own proof.

- A Safe check = final manual QA, relevant tests, one independent review of the finished work.
- Yes: run it, fix, then open the PR. No: open the draft as is.
- Never repeat the offer for the same PR.
- List missing tests, review and baseline as unverified. Fill Before & after for every outcome. Link the run's epic.

## Stops

- After a merge, start new work on a fresh branch from the current base.
- No force-push, history rewrite or unrequested merge, release or notification.
- No invented results, tests, authorship or accounts.
