---
name: how-to-review-a-pr
description: "Reviews a pull request end to end on a separate, fresh agent: intake, analysis, three solutions, the factory run audit, every review lens, synthesis, bounded fixes, gate and a detailed PR comment. Use for every factory-made draft PR and when asked to review any PR. Never marks ready or merges."
---

# How to review a PR

Contents: boundaries, 0 intake, 1 analysis, 1b three solutions, 1c run audit, 2 lenses, 3 synthesis, 4 question gate, 5 fixes, 6 gate, 7 push, 8 comment, own draft PR, safety, output contract.

Review a PR from a teammate, customer or agent, end to end. Every PR the factory opens gets this review from an agent that did not build it. Use the host's CLI or API; on GitHub, the commands in [github](references/github.md). No PR given: ask once for the URL or number.

## Boundaries

- Review-only or analysis-only request: stop after phase 4 with the report. Fixes, pushes and comments need the request or authorization to cover them.
- Run the review in a separate agent with fresh context, on a fresh checkout of the exact remote base and head; remote or cloud when the delivery requires it. Record provider/task identity, base/head, evidence and verdict.
- Asked to review a PR: you are the reviewer. When delivery requires a remote or cloud review, your local pass does not replace it; missing remote access blocks that review and merge, not independent local work.
- Clean checkout. Preserve dirty work in an isolated checkout; never silently stash or switch it.
- Discover the product, architecture, rules, checks and authority from the project. Use the existing toolchain; install nothing unrelated. Review the real system, including consumers outside the repository.

## 0. Intake and claim

1. Resolve the PR. Fetch metadata, diff, commits, comments, reviews and linked issues.
2. Check out the PR head. Record the branch you came from.
3. Detect touched areas from paths, imports and manifests. Flag separately shipped parts (client/server, scripts/binaries, plugins/host, schema/save formats) for change-guard.
4. Refresh the linked ticket: latest confirmed criteria, approved scope changes, owner source.
5. Emit the PR card and quote the claim:

```
PR #<n> <title>
author: <login> (bot? yes/no) | state: <state> | mergeable: <...>
base <- head: <base> <- <head> (<sha>) | fork: <yes/no>
size: +<add> / -<del> across <files> files | areas: <...>
linked: <issues/tickets> | url: <url>
CLAIM (verbatim, trimmed): "<what it does and why>"
```

A PR with no stated why is itself a finding.

## 1. Analysis (no code)

Run `analyze-start` on the PR. Read the real code, never only the diff.

1. Restate the purpose and why it is needed in 1-3 sentences. Define success.
2. ASCII flow of the real path, marking where the changes sit.
3. Cross-reference every touched symbol: callers, routes/commands, shared state, cache keys, schemas, events, tests. This seeds change-guard.
4. Claim vs diff: `| Claimed behavior | Where (file:line) | Delivered? YES / PARTIAL / NO | Note |`
   Proof: apply `how-to-make-a-pr`. Compare its view/journey inventory to the ticket and entire diff, including effects of shared logic; inspect every screenshot pair and play every journey video through its result. Check empty/seeded setup, changed failure/recovery paths, candidate identity, capture restart after fixes and explicit owner sources for scoped waivers. Missing outcomes, declarations, media, stale captures or inaccessible proof block evidence completion; a parser pass does not prove coverage or quality. Server-only and nonvisual outcomes retain matched input/output or command/diff proof, with explanatory diagrams when useful; no media waiver is needed without an affected interactive UI journey. Verify the claimed owner benefit. Keep proof near the top of the PR.
5. Hypotheses and open questions, kept apart from verified facts.

## 1b. Three solutions (no code)

Run `recommend` on the PR's approach: the implemented one against two credible alternatives. Keeping the approved design can be best; never manufacture a defect or a rewrite. A new substantive choice stays a recommendation for the owner.

## 1c. Run audit (factory PRs)

The PR came from a factory run: read its `.factory/run.md` and ticket. Check every block of steps 0–7 against its skill's output contract, the `Gate A` and `Gate B` lines (PASS or owner WAIVED; Gate C runs after this review), and that each Before file predates the first source commit. A missing step, contract line or gate is a HIGH finding: the run is incomplete even when the code is right.

## 2. Lenses

Run `deep-review`'s analysis categories and every applicable lens it lists: security, performance, journey, change-guard, compliance.

- Same candidate already passed a full local review: one reviewer covers all lenses on the delta plus a residual-risk check.
- Otherwise, or for security, release or public-exposure scope: one isolated reviewer per lens, in parallel when your agent has subagents (waves if capacity is short), otherwise one lens at a time. Synthesize only after all return. Never call sequential work parallel or drop a lens.
- Each reviewer gets: PR card and claim, phase 1 analysis, changed files on the checked-out branch, applicable rules, confirmed criteria, target workload/platforms, raw evidence and its limits. Mark each item verified or hypothesis. Reviewers verify hypotheses and correct you.
- Collect findings and lens verdicts. Fix nothing yet.

## 3. Synthesis

1. Merge and dedupe. Same line from two lenses: one row at the higher severity, both lenses noted.
2. Master table, severity-ranked: `deep-review`'s finding format plus a disposition column.
3. The fifth lens:
   - **Opportunities** nobody asked for: notes only, unless trivial and clearly aligned.
   - **Necessary complexity to KEEP**: platform branches, native quirks, concurrency/realtime constraints, defensive guards.
   - **The author's request**: harden and correct. Never redirect the feature, change its intent or bolt on scope.
4. Fix-set:
   - **Fix now** when all hold: clear correctness/security/build breaker or obvious low-risk improvement; small and local; inside the PR's intent; confidence HIGH, or MED with an obvious safe fix.
   - **Flag only** when any holds: changes intended behavior or scope; needs a product, team or external decision; large refactor; low confidence or touches necessary complexity; needs a platform, service or release change no authorized check can validate.
5. Verdict, one line with the single most important reason. A verdict that depends on unapplied fixes is conditional.

| Verdict | When |
|---|---|
| `APPROVE` | Delivers the claim; no blocking finding; nothing to fix. |
| `APPROVE-WITH-FIXES` | Delivers the claim; the fix-set clears every blocking finding; only flags remain. |
| `REQUEST-CHANGES` | HIGH remains that we cannot safely fix, or open questions block correctness. |
| `BLOCK` | CRITICAL unresolved: claim not delivered, existing behavior or supported runtime broken, secret shipped, or required gates cannot pass. |

6. Compile open questions.

## 4. Question gate

Before writing to the PR, ask the user the open questions in this session. Fold answers into fixes and report. Questions only a teammate can answer go into the PR comment. Nothing guessed silently. Zero questions: say so and continue. Fast factory run: hand them back; the coordinator decides how to fix within the agreed scope and records decision and reason on the ticket; the owner can reverse them at merge. A deferral or scope cut stays the owner's.

## 5. Fixes

Apply only the agreed fix-set, each through the `get-ready-to-code` 0-4 loop.

- Smallest change that removes the finding's cause; match the surrounding style. Harden, never replace the author's feature.
- Never weaken security handling (protected secrets, TLS, input/origin/permission checks) to make anything pass.
- No new circular dependencies.
- Keep a before/after note per fix.
- A fix that touches necessary complexity: stop and demote it to a flag.

## 6. Gate

1. Finish the whole fix-set.
2. Manually exercise the changed behavior through real actions.
3. Only then add or adapt tests and run the project's required checks: types/build, lint, affected tests, cycle check.
4. Failure: fix, recheck manually, rerun. Never push a red required gate.

Remote builds, paid services, signing or publishing without authority: report the gap. Never substitute an unrelated green check. Unknown applicability is UNKNOWN; justify real N/A.

A fresh independent reviewer then assesses the fixes; at most 6 failed rounds, then the owner decides.

## 7. Push (checkpoint)

Show the user the fix-set, before/after and gate result. Get a go-ahead unless pre-authorized.

- Stage only files you changed. Message: `fix(<area>): <what was hardened on PR #<n>>`.
- No AI or tool attribution in commits or comments.
- Never force-push, rewrite or delete the author's commits. Additive commits only.
- Push rejected (fork without maintainer edits, protected branch): skip to the comment and include the full patch.

## 8. Comment (checkpoint)

Show the draft before posting unless pre-authorized. The comment is the only author-visible output: professional, specific, self-contained, enough for a cold teammate or agent to take over. Facts, not verdicts about the author. Delete empty sections.

```markdown
## Review + fixes

**Review:** <remote provider/task, fresh context, exact base/head>
**Ticket:** <link, confirmed scope revision, refresh result or gap>
**Verdict:** <APPROVE | APPROVE-WITH-FIXES | REQUEST-CHANGES | BLOCK> - <one-line reason>
**Manual QA:** <actions, candidate, observed outcomes, limits>
**Gate:** <checks and pass/fail/unverified> | **Pushed:** <sha(s), or no push: see Handoff>

### What this PR claims
> <claim, quoted and trimmed>

**Delivers?** <YES / PARTIAL / NO> - <one sentence>

| Confirmed criterion | Actual change/journey | Proof | Gap/deviation |
|---|---|---|---|

### What we changed
| # | File | Change | Finding addressed |
|---|---|---|---|

**<file:line> - <title>**: Before `<old behavior>`. After `<new behavior>`.

### Review summary
<Lenses actually run and how; never claim reviewers that did not run.>

| # | Sev | Lens / layer | File:Line | Finding / impact | Evidence / action | Status |
|---|---|---|---|---|---|---|

### Open questions for the team
1. **<question>** - <what is blocked until answered>

### Handoff
- **Current state:** verified vs unverified; remaining human decisions
- **Done:** fixes pushed and verified
- **Pending:** flagged findings and why
- **Scope/history:** pending owner changes, dependencies
- **How to resume:** branch, gate commands that passed, where flagged items live
```

- Not pushed: label the actual state, "implemented locally, unpublished" or "proposed, not implemented", and put the patch in Handoff. Never imply applied work without evidence.
- No blame, no internal candor, no time estimates. Impact and next steps only.
- Save the full candid report outside the repository; tell the user where. Offer to switch back to the original branch.

## Own draft PR

For a draft PR your agent opened, the question gate, push and comment checkpoints are pre-authorized. Open questions go in the comment. Push only to that PR's branch, never force. Humans own ready, merge and release. Anyone else's PR keeps every checkpoint.

## Safety

- No code in phases 0-4. Reading only.
- Confirm before push and before comment; one combined checkpoint is fine if pre-authorized.
- Never notify, merge, release or deploy without explicit authority.

## Output contract

The block `## 8 Review` holds, and the PR comment carries:

- [ ] PR card and the quoted claim
- [ ] Analysis per `analyze-start`, with the claim-vs-code table
- [ ] Three solutions per `recommend`, with the verdict on the implemented approach
- [ ] Run audit (factory PRs): each step and gate met, or the findings
- [ ] Every applicable lens run, each with its findings table (possibly empty) and one-line verdict
- [ ] Synthesized master table and one verdict: APPROVE, APPROVE-WITH-FIXES, REQUEST-CHANGES or BLOCK
- [ ] Fixes through the 0–4 loop with their gate result, or "no fixes"
- [ ] The comment's link, read back; the PR still draft
