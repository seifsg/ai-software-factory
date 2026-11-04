---
name: how-to-make-a-pr
description: "Prepares and opens a draft pull request for human review, linked to its ticket and backed by before/after proof. Use when creating, updating or correcting a pull request."
---

# How to make a PR

Open a **draft PR**. Humans decide ready, merge, release. Analysis or review-only request: no open, push or comment.

## 1. Bind the project

Find real repository, branches, release policy, PR template, signing rule, check commands, tracker, review owner from rules, manifests, CI, remote metadata. Never copy accounts, branches or tools from another project. Ask only consequential gaps. Missing binding blocks its dependent step; keep local work going. Released app: changelog, version, note updates follow its existing format, timing, generators; handoff lists remaining release steps.

## 2. Ticket first

- Every PR belongs to a ticket. Search by symptom, area, files, title, branch; none found: run `ticketing`.
- No ticket only if a project exemption covers the whole diff, or the change is trivial and the run kept it without one: PR body says why.
- Link both ways: on open, PR link in ticket activity; clickable ticket link in PR body.
- Finished ticket = Ready for QA while PR open, Done on merge; status follows `ticketing`.
- Ticket with confirmed contract: refresh before opening or updating. Pending scope, drift or failed refresh leaves the dependent step open. Draft or local success never replaces owner's current expectation.

## 3. Branch from the right base

- Work on own branch, `<scope>/<short-name>` (`fix`, `feat`, `docs`, `chore`) or project convention; never commit to base. Protect dirty and foreign work: new branch or isolated checkout.
- Base = project integration branch, else default branch. Base differs from default branch: say so in PR.
- **Epic waves:** share one integration branch and draft PR. Finished lanes incorporate it, resolve/recheck, then integrate and push without force. Exception: independently complete UI ticket ships own draft after its verify; dependencies must be included and checked. Never wait on unrelated wave tickets.
- Dependent ticket, wrong base or hotfix: `references/pr-cases.md`.
- Check remote, not local list: shallow and single-branch clones hide branches.

```text
git ls-remote --heads origin
git ls-remote --symref origin HEAD
git fetch origin
git switch -c <scope>/<short-name> origin/<base>
```

## 4. Before proof, before the first edit

Every PR shows observed Before/After per outcome; prose or illustrative diagrams never replace results. Nonvisual proof, in a `diff`: API, one request's status and body; CLI or script, one command's output; method or prose, a fresh walkthrough's changed result and key text. Speed/size/cost proof measures same workload. Internal module proves its changed screen, endpoint or command. New nonvisual result: prior output is "did not exist". Name `**Visual:**` and `**Journey:**` under each outcome (`references/pr-layout.md`), with reason when no. Map shared backend effects to UI journeys.

1. Take plan's proof list. Changed views, states, motion, interactions or affected UI journeys: read [visual and journey proof](references/media-proof.md) now; its rules apply in full.
2. Brand-new surface: no Before capture, Before = "did not exist". Capture every other Before now, before any source edit, into `.factory/proof/<ticket>/before-<id>.png` (screens) or `before-<id>.txt` (commands, responses, text). Screens: capture from the preview owner watches, else host's built-in browser; keep that one server for After. No Playwright, headless browsers or capture scripts unless owner asks. Host cannot save screenshot as file: write what it shows into `before-<id>.txt` as `pane:` observation; valid proof, no waiver needed.
3. Inspect every capture: right screen, readable, no secrets.
4. Missed a Before after editing: text and command proof come from base (`git show <base>:<path>`, base build output); screenshot no longer takeable: state it as missing in PR. Never a second checkout or server just for a picture.
5. Capture After during verify's manual round, same server, same ids: `after-<id>.*`. Later fix recaptures only ids it affects.

## 5. Make the change

- One thing per PR. Unrelated finds = follow-ups.
- Stage own files by name. Never `git add .` or `git add -A`.
- Commit as `<type>(<scope>): <imperative subject>`; body = why, not lines changed.
- Honor required signing with existing identity; never invent one or bypass signing, permissions or protected gates.
- **No AI or tool attribution lines** in commits, even if your agent's defaults add one. PR body ends with factory credit line in `references/credit.md`.
- Required gates (step 1) go green locally before push; PR names their commands and results. A check not run is **unverified**. CI never required: never wait on or rerun it; a result that arrives = extra evidence.
- Tests last: implement, manually QA real behavior, then write and run tests. Fix found by tests repeats manual QA and tests. No tests that restate implementation.

## 6. Open the draft

1. Write body to a file with `references/pr-layout.md`. Upload Before/After media first (`references/github.md`), link with `https` URLs.
2. Push, then open as **draft** against base. Commands: `references/github.md`.
3. Closing keyword only on each sub-issue or change ticket this PR finishes; epic always gets plain reference.
4. Request review only from a review owner other than PR author, via supported mechanism, at draft time. Notify only authorized recipient or channel. Reminders only when asked.
5. Link observation evidence only if authorized to share; state source and limits. No foreign session IDs, secrets or private data.

## 7. Review

- Every PR gets `how-to-review-a-pr` from a fresh agent that did not build it, on exact pushed head. Give it PR, ticket, run file; never your reasoning or a desired verdict. Builder's self-check never replaces it.
- Pushing fixes to own draft's branch and posting its review comment: pre-authorized. Someone else's PR keeps every checkpoint.
- Every code update voids previous verdict: new head needs fresh review.
- Project has remote or cloud review: `references/pr-cases.md`.
- PR stays draft. Review is not merge or release approval.

## 8. Every run

Open one every run, unasked, unless its wave's draft PR is open: then push to that branch and update that PR: append run's outcomes, criteria verification, remaining steps; refresh summary.

- Variations requested: one branch and draft PR each, same rules, own proof.
- List missing tests, review, baseline as unverified. Link run's epic.

## Stops

- After merge, start new work on fresh branch from current base.
- No force-push, history rewrite, or unrequested merge, release, notification.

## Output contract

The block `## 4 Before` holds:

- [ ] Every proof-list id with its `before-<id>` file under `.factory/proof/<ticket>/`, or "did not exist" for a new surface
- [ ] Saved before the first source edit
- [ ] Each capture inspected, or none to inspect: every id "did not exist"

The block `## 7 PR` holds the draft PR URL, and the PR itself has:

- [ ] Title `<type>(<scope>): <subject>`; draft; the verified base
- [ ] A clickable ticket link in the body, and the PR link in the ticket's activity
- [ ] Purpose & goal, Before & after, Verification and Progress / next, in that order (other sections and their wording are never a FAIL)
- [ ] One heading per outcome under Before & after, each with `**Visual:**`, `**Journey:**` and either `**Before:**` and `**After:**`, each an `https` image, fenced output or `pane:` observation, or one `**Before → After:**` with a two-column image table (Visual yes) or a `diff` block (Visual no); a new surface or output's Before is `did not exist`
- [ ] Each After names the commit it was captured on
- [ ] Verification: criterion → change → proof → gap, with each command and its result; unverified items named
- [ ] Review requested from a review owner other than the author, or none (solo owner)
- [ ] The credit line from `references/credit.md` as the last line
