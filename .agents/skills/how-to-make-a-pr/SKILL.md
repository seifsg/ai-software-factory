---
name: how-to-make-a-pr
description: "Prepares and opens a draft pull request for human review, linked to its ticket and backed by before/after proof. Use when creating, updating or correcting a pull request."
---

# How to make a PR

Open a **draft PR**. Humans decide ready, merge and release. Analysis or review-only requests: do not open, push or comment.

## 1. Bind the project

Find the real repository, branches, release policy, PR template, signing rule, check commands, tracker and review owner from rules, manifests, CI and remote metadata; never copy accounts, branches or tools from another project. Ask only consequential gaps. A missing binding blocks its dependent step; keep local work going. A released app: its changelog, version and note updates follow its existing format, timing and generators; the handoff lists remaining release steps.

## 2. Ticket first

- Every PR belongs to a ticket. Search by symptom, area, files, title and branch; none found: run `ticketing`.
- No ticket only when a project exemption covers the whole diff, or for a trivial change the run kept without one: the PR body says why.
- Link both ways: on open, the PR link in the ticket's activity; a clickable ticket link in the PR body.
- A finished ticket is Ready for QA while the PR is open, Done on merge; status follows `ticketing`.
- Ticket with a confirmed contract: refresh it before opening or updating. Pending scope, drift or a failed refresh is an open dependent step. A draft or local pass never replaces the owner's current expectation.

## 3. Branch from the right base

- Work on your own branch, `<scope>/<short-name>` (`fix`, `feat`, `docs`, `chore`) or the project's convention; never commit to the base. Protect dirty and foreign work: new branch or isolated checkout.
- Base = the project's integration branch, else the default branch. Say so in the PR when it differs.
- **Epic waves:** share an integration branch and draft PR. Finished lanes incorporate it, resolve/recheck, then integrate and push without force. Exception: an independently complete UI ticket ships its own draft after its verify; dependencies must be included and checked. Do not wait for unrelated wave tickets.
- Dependent ticket, wrong base or hotfix: `references/pr-cases.md`.
- Check the remote, not the local list: shallow and single-branch clones hide branches.

```text
git ls-remote --heads origin
git ls-remote --symref origin HEAD
git fetch origin
git switch -c <scope>/<short-name> origin/<base>
```

## 4. Before proof, before the first edit

Every PR shows observed Before/After for each outcome; prose or illustrative diagrams never replace results. In a `diff`, API proof shows one request's status and body; CLI/script proof, one command's output; method/prose proof, a fresh walkthrough's changed result and key text. Speed/size/cost proof measures the same workload. An internal module proves its changed screen, endpoint or command. A new nonvisual result shows the prior output as "did not exist". Name `**Visual:**` and `**Journey:**` under each outcome (`references/pr-layout.md`), with a reason when no. Map shared backend effects to UI journeys.

1. Take the plan's proof list. For changed views, states, motion, interactions or affected UI journeys, read [visual and journey proof](references/media-proof.md) now; its rules apply in full.
2. A brand-new surface needs no Before capture: its Before is "did not exist". Capture every other Before now, before any source edit, into `.factory/proof/<ticket>/before-<id>.png` (screens) or `before-<id>.txt` (commands, responses, text). Screens: capture with the host's built-in browser, the preview the owner watches, and keep that one server for After. No Playwright, headless browsers or capture scripts unless the owner asks. A screenshot the host cannot save as a file: write what it shows into `before-<id>.txt` as a `pane:` observation; that is valid proof, no waiver needed.
3. Inspect every capture: right screen, readable, no secrets.
4. Missed a Before after editing: text and command proof come from the base (`git show <base>:<path>`, the base build's output); a screenshot you can no longer take is stated as missing in the PR. Never a second checkout or server just for a picture.
5. After is captured during verify's manual pass, on the same server, with the same ids: `after-<id>.*`. A later fix recaptures only the ids it affects.

## 5. Make the change

- One thing per PR. Unrelated finds become follow-ups.
- Stage your own files by name. Never `git add .` or `git add -A`.
- Commit as `<type>(<scope>): <imperative subject>`; body = why, not the lines changed.
- Honor required signing with the existing identity; never invent one or bypass signing, permissions or protected gates.
- **No AI or tool attribution lines** in commits, even when your agent's defaults add one. The PR body ends with the factory credit line in `references/credit.md`.
- Required gates (step 1) pass locally before push; the PR names their commands and results. A check not run is **unverified**. CI is never required: never wait on or rerun it; a result that arrives is extra evidence.
- Tests come last: implement, manually QA the real behavior, then write and run tests. A fix found by tests repeats manual QA and tests. No tests that restate the implementation.

## 6. Open the draft

1. Write the body to a file with `references/pr-layout.md`. Upload Before/After media first (`references/github.md`) and link them with `https` URLs.
2. Push, then open as **draft** against the base. Commands: `references/github.md`.
3. Closing keyword only on each sub-issue or change ticket this PR finishes; the epic always gets a plain reference.
4. Request review only from a review owner other than the PR author, through the supported mechanism, at draft time. Notify only the authorized recipient or channel. Reminders only when asked.
5. Link observation evidence only when authorized to share; state source and limits. No foreign session IDs, secrets or private data.

## 7. Review

- Every PR gets `how-to-review-a-pr` from a fresh agent that did not build it, on the exact pushed head. Give it the PR, the ticket and the run file, never your reasoning or a desired verdict. The builder's self-check never replaces it.
- Pushing fixes to your own draft's branch and posting its review comment are pre-authorized. Someone else's PR keeps every checkpoint.
- Every code update invalidates the previous verdict: the new head needs a fresh review.
- Project has a remote or cloud review: `references/pr-cases.md`.
- The PR stays draft. Review is not merge or release approval.

## 8. Every run

Open one for every run, unasked, unless its wave's draft PR is open: then push to that branch and update that PR, appending the run's outcomes, criteria verification and remaining steps and refreshing the summary.

- Variations requested: one branch and draft PR per variation, each following these rules with its own proof.
- List missing tests, review and baseline as unverified. Link the run's epic.

## Stops

- After a merge, start new work on a fresh branch from the current base.
- No force-push, history rewrite or unrequested merge, release or notification.
- No invented results, tests, authorship or accounts.

## Output contract

The block `## 4 Before` holds:

- [ ] Every proof-list id with its `before-<id>` file under `.factory/proof/<ticket>/`, or "did not exist" for a new surface
- [ ] Saved before the first source edit
- [ ] Each capture inspected, or `no captures (new surfaces)`

The block `## 7 PR` holds the draft PR URL, and the PR itself has:

- [ ] Title `<type>(<scope>): <subject>`; draft; the verified base
- [ ] A clickable ticket link in the body, and the PR link in the ticket's activity
- [ ] Purpose & goal, Before & after, Verification and Progress / next, in that order (other sections and their wording are never a FAIL)
- [ ] One heading per outcome under Before & after, each with `**Visual:**`, `**Journey:**`, `**Before:**` and `**After:**`; Before and After are each an `https` image, fenced output or `pane:` observation; a new surface or output's Before is `did not exist`
- [ ] Each After names the commit it was captured on
- [ ] Verification: criterion → change → proof → gap, with each command and its result; unverified items named
- [ ] Review requested from a review owner other than the author, or none (solo owner)
- [ ] The credit line from `references/credit.md` as the last line
