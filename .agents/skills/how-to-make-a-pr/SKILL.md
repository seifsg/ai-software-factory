---
name: how-to-make-a-pr
description: "Create, update, or retrospectively correct every factory-managed pull request, in any project. Requires a visual self-contained draft, the project's task and reviewer handoff, and automatic separate-instance how-to-review-a-pr execution."
---

# How to make a PR

## Small-change mode — select before the full chain

For a bounded small patch, execute both PR procedures using [small-change](../small-change/SKILL.md). Its six routines replace full analysis, three alternatives, five planning artifacts, separate deep-review reports and broad test batteries. Keep exact candidate identity, real project bindings, task/owner constraints, attribution, adjustment history and draft status. A concise body/comment can carry the requested result, affected scope, actual focused checks, findings and limits; do not manufacture empty tables.

Inspect the whole PR's metadata and previous assessment boundary, but review a follow-up delta plus its affected consumers. An unresolved earlier full-PR finding stays unresolved. State whether the verdict covers only the delta or the whole PR. Reuse valid exact-candidate focused evidence; a push alone is not grounds to rerun it. One separate instance may perform the final small-change and PR assessment together. If code changes afterward, reassess the affected delta and checks. Neither procedure automatically adds a full suite, duplicate local review, improvement loop or fresh-final gate. This is the owner's 3 October scope correction, not permission to bypass a real protected gate or human handoff. Read the remaining procedure for applicable delivery mechanics without re-executing superseded full-method stages.

Seif's mandatory PR procedure. Execute it for **every factory-managed PR**, including documentation, skills, fixes, and later updates. Do not replace it with a short summary, a template alone, or the local controller's review. A missing dependency blocks completion; it never makes the procedure optional.

Read the target project's instructions, PR template and recorded delivery settings. Use [project bindings](references/project-bindings.md) to resolve repository-specific facts without importing another company's people, accounts or tools. Read the entire procedure before acting. Preserve evidence of each completed step and every blocker in the PR body and review comment. A skill describes required behavior; it is not a host hook or protected GitHub gate.

## 1. Base and branch

- Never commit directly to the integration/production base. Use a focused branch.
- Discover branches **from the remote** with `git ls-remote --heads origin`; a shallow clone's `git branch -r` is not proof that a development branch does not exist.
- Default to the repository's actual development branch (`dev`, `develop`, `development`, or its documented equivalent). If none exists, verify the remote default and use it; state this fallback in the PR. Resolve ambiguous integration branches before choosing one.
- Fetch the current base before starting new work. Inspect existing work and branch divergence; do not reset, silently stash, or overwrite a branch. After a merged PR, start a fresh branch from the current integration base.
- Use `fix/`, `feat/`, `docs/`, or `chore/` plus a short descriptive slug. Existing published history is preserved when applying this skill retrospectively.
- Only an **explicitly requested hotfix** may bypass an existing development branch for production. It requires a production PR plus a companion carrying the **same fix** to development. Create the companion from development and cherry-pick only the fix commits; do not point the production branch at development and drag unrelated commits across. Cross-link the pair and mirror every follow-up. If no development branch exists, document that verified topology; do not invent one.

## 2. Focus, commits, and pre-push checks

- One coherent outcome. Preserve unrelated changes. Stage explicit paths, never `git add .` or `git add -A`.
- Use an imperative Conventional Commit subject, with an optional body explaining why. Sign when the repository requires verified signatures; do not bypass that requirement.
- Discover real checks from the project and CI: applicable tests, typecheck, lint, build and circular-dependency checks. Batch them after substantial work. Run the required gate **before pushing**; a missing or failing required check is a blocker.
- Add meaningful regression coverage for behavioral changes. Inspect worthwhile in-scope improvements before the final batch; no watch loops or tests after every edit.
- No force-push, history rewrite, fabricated checks, model/tool signatures or invented co-authors. Product names needed to explain the actual change are not attribution signatures.

## 3. Associated task — before the draft

The project must resolve its task-tracking binding. This procedure always runs; do not assume that an unavailable tracker means no task is required.

1. Search the configured tracker on **both axes**: change keywords (symptom, feature, endpoint, file) and PR title/branch slug.
2. Reuse a task covering the same work. Create one only after both searches find no match, using the project's real task-writing procedure and authorized account.
3. Put a clickable task link in the PR and the PR URL in the task's designated link field or supported equivalent. Verify both directions.
4. At draft creation, set the task to its exact **development finished / awaiting review** status. Discover supported values; do not invent one. This is not a shipped/closed status.
5. The original narrow exception is retained: a project explicitly designated as a skills/routines repository may exempt a PR changing **only** its routine paths. Any application/controller change restores the task requirement. Ordinary documentation is not automatically exempt. Record the resolved applicability and evidence; never silently skip it.

## 4. A visual, self-contained draft

Read the target repository's PR template. Preserve its required structure and place these contents within it; if none exists, use [the body template](references/pr-body-template.md).

- Keep truthful requested-by attribution first, then **Why**: the original problem and the decisions behind the change. Credit the actual human author/initiator by name; distinguish supplied methods from adaptation without tool/model signatures or false authorship.
- **Visual first:** before/after ASCII, lifecycle/data flow, comparison tables, file manifest and check results. Cover every relevant detail with minimal prose; use a single short sentence when a table or diagram would not help.
- Include the original request, decisions and reasons, relevant IDs/paths, current state, remaining work and blockers. A cold reader must be able to continue without reading this chat.
- Link actual originating threads/issues visibly, in addition to attribution. Link relevant observability sessions using the project's real system; if none informed the change, state that. Never invent links or expose private discussions to a wider audience.
- Keep an **Adjustment History** throughout the PR's lifetime: requester, date when known, what changed, why, and the resulting action. Rewrite the main description around the final implementation; keep this concise history as the requested audit trail.
- Open as **draft** with the verified base and Conventional Commit-style title. Use a saved body file with CLI `--body-file`; do not interpolate multiline prose into shell code. Attach the PR to the current chat when the host supports it.
- For an existing PR, inspect its full current diff and history before editing metadata. Correct omissions honestly; do not claim retrospective checks happened earlier. Preserve state/history; do not close or replace a PR without authority.

### Correct a PR opened against the wrong base

Fetch and verify the actual integration base before correcting the target. Inspect the candidate diff against it first.

- If the head already starts from the correct integration base and the resulting diff contains only the intended change, retarget the existing PR with the available GitHub tool (for example, `gh pr edit <number> --base <verified-base>`). Read back the new base and complete diff; obtain fresh checks/review as needed for the changed comparison.
- If the bases diverge and retargeting would pull unrelated production-only commits into the PR, create a **fresh branch from the current correct base** and cherry-pick only the intended change commits (`git cherry-pick -x <sha>`). Verify the resulting diff and actual gates. Open a replacement draft through this entire procedure, cross-link both PRs, and record which supersedes which. Close the old PR only with applicable authority; otherwise leave the closure explicitly pending.
- Never force-push or rewrite remote history to disguise the wrong base. A replacement is a new candidate and receives the full separate-instance review, task links and owner handoff. Preserve the old record and adjustment history.

## 5. Human handoff immediately at draft creation

Resolve the project's real human review owner and notification destination from its bindings.

1. Request the owner as GitHub reviewer at draft creation, where the platform permits it.
2. Send the review notification through the configured, authorized destination with the PR link. If the work originated in a thread, also update that thread when authorized. Read back the result.
3. Missing owner, missing access, author self-review restrictions or unavailable notifications are **explicit handoff blockers**, not completed actions. A platform limitation needs a user-approved alternative; do not pretend an assignee is a requested reviewer.
4. For important/urgent work, follow the project's authorized reminder cadence with severity-aware backoff and a stop on response/closure/merge. Use the host's scheduling tool when available. Do not silently create a new schedule, recipient or channel; unresolved scheduling authority stays pending. Nonurgent work may explicitly require no reminder.

These communications belong to the explicitly invoked PR workflow. They do not authorize unrelated messages, broad notifications or disclosure to a guessed recipient.

## 6. Mandatory separate-instance PR review

Immediately launch [how-to-review-a-pr](../how-to-review-a-pr/SKILL.md) on a **separate instance** after drafting. This is an explicit instruction to delegate that review. Pass the PR URL, exact head/base, original request, approved decisions, project bindings, gate evidence, diagnostic progress and actual constraints. Do not feed it a desired verdict. The builder's self-check does **not** satisfy this step. In version mode the controller's local review is also separate; small-change mode may combine the final independent assessment with this PR review on the same head.

If creation/handoff has a blocker, report it and still run independent inspection that is possible; the overall PR workflow remains incomplete. If independent execution is unavailable, record BLOCK, never substitute your own approval.

The reviewer runs the entire ordered chain, fixes only authorized findings, verifies the resulting candidate and posts its detailed report. Every code update invalidates the previous PR verdict; obtain fresh review of the new head. Reconcile uncertain pushes/comments before retrying to avoid duplicates. The PR **stays draft**; the human owns ready/merge/release.

## Completion record

| Required evidence | Completion condition |
|---|---|
| Base, branch, diff, commit | Verified remote topology; focused additive changes; signing rule met |
| Build gate | Actual applicable commands passed for the submitted candidate |
| Task | Both searches, linked task, both directions, exact awaiting-review status; or proven narrow routine-only applicability |
| Body | Attribution, Why, visuals, decisions, file manifest, evidence, gaps, context, adjustment history |
| Owner and notification | Verified request/delivery or explicit unresolved blocker |
| Separate review | Entire paired skill executed; detailed comment for current head; fresh assessment after repairs |
| Human boundary | Draft preserved; no automatic ready/merge/release |

No row disappears because this is a small change or a different project. Record a supported not-applicable result only where the procedure itself allows it. See [source provenance](../../../docs/skill-provenance.md) for the original and approved adaptations.
