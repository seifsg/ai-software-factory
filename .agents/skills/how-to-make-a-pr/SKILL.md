---
name: how-to-make-a-pr
description: "Prepares and opens a draft pull request for human review, linked to its ticket and backed by before/after proof. Use when creating, updating or correcting a pull request."
---

# How to make a PR

Open a **draft PR**. Humans decide ready, merge and release.

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

Every PR shows observed Before/After for each outcome; prose or illustrative diagrams never replace results. API proof shows one request's status and body in a `diff`; CLI/script/gate proof shows one command's output in a `diff`; method/prose proof shows a fresh walkthrough's changed result and key text in a `diff`. Speed/size/cost proof measures the same workload. An internal module proves its changed screen, endpoint or command. A new nonvisual result shows the prior output as "did not exist". Name `**Visual:**` and `**Journey:**` under each outcome (`references/pr-layout.md`), with a reason when no. Map shared backend effects to UI journeys. For changed views, states, motion, interactions or affected UI journeys, read [visual and journey proof](references/media-proof.md) before editing; its capture, preflight, freshness and waiver rules apply in full.

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

1. Write the body to a file with `references/pr-layout.md`. Fast/Lucky: preflight it with `fast_gate.py report --pr-body <file> --project <abs>` before publishing. Structure-only success never replaces observed proof or final handoff checks.
2. Push, then open as **draft** against the base. Commands: `references/github.md`.
3. Closing keyword only on each sub-issue or change ticket this PR finishes; the epic always gets a plain reference (intake closes it once its in-scope sub-issues are Done and its checklist is ticked).
4. Request review from the project's actual review owner through the supported mechanism, at draft time. Notify only the authorized recipient or channel. Reminders only when asked.
5. Link observation evidence (logs, traces, screenshots, measurements) only when authorized to share; state source and limits. No foreign session IDs, secrets or private data.

## 7. Review

- When independent review is required, review frozen source, manual use and affected checks before the complete suite; fix source findings first. Source-only review accepts nothing and advances no phase. The same reviewer checks author repairs and affected consumers; changed inputs need fresh affected proof. After the suite it inspects the exact-candidate receipt and log before its final verdict.
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
