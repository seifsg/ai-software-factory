---
name: how-to-review-a-pr
description: >-
  End-to-end handling of an INCOMING pull request — from a
  teammate, a customer, or an agent. Fetches the PR, proves it does what it claims,
  runs remote/cloud themed deep reviews (performance, security, user journey,
  change-guard), synthesizes a verdict, fixes what
  makes sense within authorization, verifies the project's checks,
  pushes, and posts a handoff comment on the PR. Use this whenever the user shares a
  PR URL or number to look at, says "review / vet / analyze / audit this PR", or wants
  a pre-merge check of someone else's changes. Triggered by `/pr-review`.
---

# PR Review — incoming pull-request pipeline (`/pr-review`)

**Project adapter:** Read [project bindings](../how-to-make-a-pr/references/project-bindings.md) before acting. Discover actual rules, tools, checks and authority. An explicit analysis-only or review-only request stays read-only; later phases require authorization.

**Execution boundary:** PR review runs on a remote/cloud agent, in a fresh context and checkout of the exact remote base/head. Record actual remote task/provider identity and returned evidence. Local controller review stays separate; local workstation agents/subagents never count as PR review. Missing cloud access blocks this review, not independent local work. Use existing authorized routing; invent no completed cloud run.

**Choose scope first.** Selected [Small Change](../small-change/SKILL.md) uses its six routines instead of the full Analyze Start/Get Ready procedures referenced in Phases 1/4, and one scoped reviewer instead of Phase 2's four sessions. Preserve claims, prior findings, evidence, attribution and action checkpoints. Full mode follows every phase below.

**Remote capacity:** Keep four isolated themes on the remote/cloud review route. If four cannot run together, use capacity-bounded waves under the [PR adapter](../../../docs/pr-workflow.md); synthesize only after all four return. Record actual execution. The original parallel method below remains the preferred arrangement.

Triggered when the user message starts with **`/pr-review`**, shares a PR URL/number to
review, or asks to review/vet/analyze/audit an incoming (teammate-, customer-, or agent-authored) PR
against the selected project.

```
/pr-review <pr-url | pr-number>
```

If no PR is given → ask once for the URL/number, then continue.

This is not a review-only skill. It runs the review, then **fixes what makes sense, verifies
the build, pushes to the PR branch, and posts a handoff comment**. Writes to the PR sit behind an
explicit checkpoint (see [Safety gates](#safety-gates)).

Discover the product and architecture: game, client, server, service, tool or mixed system; supported platforms, trust boundaries, persistence and delivery model. Review the real system, including consumers outside this repository.

---

## Guiding principles (hold these through every phase)

We are judging *someone else's* work that we may ship to real users and systems. Optimize for:

1. **Highest quality & correctness** — does it actually work, end to end, in its target environment.
2. **Highest performance** — no jank, stalls, resource waste or avoidable latency at real load.
3. **Never blind to existing user scenarios** — what worked before must keep working.
4. **Never blind to necessary complexity** — some code is ugly *because it has to be* (native
   quirks, platform branches, concurrency or realtime constraints). Verify something is truly redundant before
   flagging or removing it. Load-bearing ≠ over-engineered.
5. **Never blind to opportunities** — note improvements we spot, even out of scope.
6. **Stay compliant with the author's request** — we fix and harden; we do **not** hijack their
   feature, silently change its intent, or scope-creep. Their PR, their goal.

These six pull against each other on purpose. Synthesis (Phase 3) is where we resolve the tension.

---

## Prerequisites

- Authorized repository-host access (`gh auth status` for GitHub CLI, or the available equivalent).
- Clean review checkout (`git status`). Preserve dirty work in an isolated checkout; never silently stash or switch it.
- Discover checks and dependencies from project rules, manifests and CI. Use the existing toolchain; do not invent commands or install unrelated tools.

---

## Phase 0 — Intake & claim capture

Goal: get the PR onto disk and pin down **what it claims and why**, because everything
downstream is measured against that claim.

1. **Resolve the PR ref**
   - URL → number from the last path segment (`/pull/<n>`).
   - Bare number → use as-is. Detect and verify the repo with `gh repo view --json nameWithOwner`.
2. **Fetch metadata** (one call):
   ```
   gh pr view <n> --json number,title,body,author,state,url,headRefName,baseRefName,\
     isCrossRepository,mergeable,mergeStateStatus,additions,deletions,changedFiles,\
     labels,commits,files,comments,reviews
   ```
3. **Fetch the diff**: `gh pr diff <n>` (keep it; the themed reviewers reference it).
4. **Read linked issues** referenced in the body (`#123`, `Closes …`, project tracker links).
5. **Check out the PR branch** so all later phases operate on the *actual* code:
   ```
   git status               # must be clean
   gh pr checkout <n>
   ```
   Record the branch you came from so you can offer to switch back at the end.
   > Cross-repo (fork) PRs: `gh pr checkout` tracks the fork. Pushing back needs "allow
   > maintainer edits". If push later fails, that's fine — everything lands in the PR comment
   > instead (Phase 7 degrades gracefully into a full handoff).
6. **Detect touched areas** from actual paths, imports, manifests and architecture. Map UI/input,
   domain logic, rendering/simulation, services, APIs, storage, queues, native/platform code,
   configuration and deployment where present. Record dependencies and relevant checks.

   Separately shipped components raise **version-compatibility** stakes: client/server,
   scripts/native binaries, plugins/host, schema/data or save formats. Flag these for change guard.
7. Emit the **PR Card** and quote the **Claim**:

   ```
   PR #<n> — <title>
   ├ author:     <login> (bot? <yes/no>)   ├ state:    <state>  mergeable:<…>
   ├ base←head:  <base> ← <head>           ├ fork?:    <isCrossRepository>
   ├ size:       +<add> / -<del>  across <changedFiles> files
   ├ areas:      <app|components|services|modules|native|…>
   ├ linked:     <issues/tickets>
   └ url:        <url>

   CLAIM (verbatim, trimmed): "<what the PR says it does + why>"
   ```

   If the body has no rationale, say so explicitly — a PR with no stated "why" is itself a finding.

---

## Phase 1 — Deep analysis  (inlines `analyze-start` + `dont-code` — NO CODE)

See [analyze-start.mdc](../analyze-start/SKILL.md) and
[dont-code.mdc](references/mobile-rules/dont-code.mdc). Understand the change end-to-end before
any judgment or edit. **Read the real code — never guess from the diff alone.**

1. **Restate** the PR's purpose and *why it's needed* in 1–3 sentences. Define what "success"
   looks like for it.
2. **Map the flow** with an ASCII diagram of the real path:
   `input/event → interface/API → domain logic → dependencies/storage → state/output`.
   Include relevant game loops, workers, notifications, navigation and failure paths.
   Show where the PR's changes sit.
3. **Cross-reference** every symbol the PR touches: callers, routes/commands, shared state,
   cache keys, platform bridges, schemas, events and tests. List everywhere
   else it's used — this seeds the change-guard theme.
4. **Claim-vs-diff check** — the heart of "does it actually do what it claims":

   | Claimed behavior | Where in the diff | Actually delivered? | Note |
   |---|---|---|---|
   | … | file:line | YES / PARTIAL / NO | … |

5. **Analysis findings** table (`Layer | File | What it does | OK/WARN/FAIL`).
6. **Hypotheses & open questions** — anything ambiguous, risky, or needing target-environment evidence. Keep
   hypotheses clearly separate from verified facts; a metric you only skimmed (grep counts, coverage
   %) is a hypothesis until you've read enough to know what it *means*, not just what it counts.

No code in this phase. Reading is fine.

---

## Phase 2 — Four parallel themed reviews (remote isolated subagents)

**Selected Small Change:** follow the [scoped adapter](../../../docs/pr-workflow.md#small-direct-changes): one independent reviewer covers the applicable themes together. Carry scoped findings into synthesis; do not claim four sessions. The full-mode method below retains four isolated reviews.

Run **four separate remote/cloud deep-review sessions**, one per theme, as **remote subagents spawned in a single
message when capacity permits**. Isolation is the point: each reviewer thinks about one thing
and can't dilute its focus.

For each theme, read its rubric file and pass it to the subagent along with the **Context Bundle**:

- The PR Card + Claim (Phase 0)
- The Phase-1 analysis (flow diagram, cross-refs, claim-vs-diff, open questions)
- The list of changed files (the PR branch is checked out — the subagent reads the working tree directly)
- Applicable project rules, selected requirements, target workload/platforms, and evidence limits.
  For factory delivery, read and pass applicable [diagnostics](../safe-engine/references/app-diagnostics.md)
  and [efficiency](../safe-engine/references/app-efficiency.md) requirements and evidence. Mark missing evidence; do not assume compliance.

Pass core methods and applicable references only; reviewers inspect scope and request missing evidence. Artistic/manual criteria need real candidate-bound observations; an unrelated green command cannot certify them.

> **Label what you pass.** Mark each item as **verified** (you read the code / ran the grep) or
> **hypothesis** (a hunch, a metric you eyeballed, an assumption). Subagents anchor hard on
> anything you assert as fact — a wrong "fact" in the bundle steers all four reviews off course.
> Tell them to verify hypotheses themselves and correct you. A raw count (e.g. "N of M files match
> X") is a hypothesis about *impact*, not a fact — the reviewer must interpret what it means before
> trusting it.

Themes and rubrics:

| Theme | Rubric file | The one question it obsesses over |
|---|---|---|
| Performance | [references/theme-performance.md](../deep-review/references/theme-performance.md) | Will real load cause stalls, latency or resource waste? |
| Security | [references/theme-security.md](../deep-review/references/theme-security.md) | Can untrusted input expose data, secrets or privileged actions? |
| User journey | [references/theme-user-journey.md](../deep-review/references/theme-user-journey.md) | Does the real user or consumer flow deliver the claim? |
| Change guard | [references/theme-change-guard.md](references/theme-change-guard.md) | Does this break existing behavior or supported version compatibility? |

Each subagent returns a structured findings table (schema defined in every rubric):

```
| # | Severity | File:Line | Finding | Impact | Recommendation | Confidence |
```

plus a one-line theme verdict. Collect all four. Do not fix anything yet.

> Why subagents and not one big pass: four clean contexts catch more than one crowded one, they
> run in parallel (fast), and a reviewer that only cares about security won't rationalize a
> security hole as "probably fine for perf reasons."

---

## Phase 3 — Synthesis, verdict & fix-set

Merge the four reports into one picture. Full method in
[references/synthesis-and-verdict.md](references/synthesis-and-verdict.md). In short:

1. **Merge & dedupe** findings; keep the highest severity when two themes overlap.
2. **Master table**, severity-ranked (`CRITICAL / HIGH / MEDIUM / LOW`).
3. **The 5th lens** (judgment the individual themes can't make):
   - **Opportunities** worth noting (even if out of scope).
   - **Necessary complexity to KEEP** — things that look like smell but are load-bearing.
   - **Compliance check** — are we about to overstep the author's request? Stay in their lane.
4. **Decide the fix-set** — *what makes sense to fix now* vs. *flag for the team*:
   - **Fix now**: clear correctness/security/build breakers, low-risk, within the PR's intent.
   - **Flag only**: anything that changes intended behavior, needs a product/teammate decision,
     is a large refactor, or is low-confidence. Note it; don't do it.
5. **Verdict**: `APPROVE` · `APPROVE-WITH-FIXES` · `REQUEST-CHANGES` · `BLOCK`
   (criteria in the reference file).
6. **Compile open questions.**

---

## Phase 3.5 — Question gate (ask HERE first)

Before writing anything to the PR, surface open questions **to the user in this session**:

> I have N questions before I fix + push. [list them]. Answer what you can; anything neither of
> us can resolve without a teammate, I'll put in the PR comment as an open question.

- Answers the user gives → fold into the fixes / report.
- Questions still unanswerable (need teammates, product calls, external context) → earmarked for
  the PR comment in Phase 7. Nothing about the PR is guessed silently.

If there are zero questions, say so and continue.

---

## Phase 4 — Fix what makes sense  (respect ALL project rules)

Apply only the agreed fix-set. Follow the repo's execution discipline from
[get-ready-to-code.mdc](../get-ready-to-code/SKILL.md): for each change →
**analyze → apply → review (no circular deps, no extra code, not over-engineered, more optimal?
gaps? does it still satisfy the user journey?) → loop if issues.** Obey
[coding-style.mdc](references/mobile-rules/coding-style.mdc) and every always-on repo rule:

- **[`no-ai-commit-attribution`](references/mobile-rules/no-ai-commit-attribution.mdc)** — never add AI/tool attribution to commits or PR content.
- **Never weaken security handling** — keep secrets in approved protected storage; never ship
  server secrets in client artifacts, disable TLS validation or weaken input/origin/permission checks.
- **No circular dependencies** — use the project's cycle checker or inspect affected dependency paths.

- Smallest change that fixes the finding. Match the surrounding code's style.
- **Do not** rewrite the author's feature or change its intent — you're hardening, not replacing.
- Keep a running **before/after** note per fix (feeds the PR comment).
- If a "fix" turns out to touch necessary complexity, stop and demote it to a flagged note instead.

---

## Phase 5 — Build gate (must pass before push)

Finish the entire permitted fix-set, then manually exercise its real behavior. Only after manual QA passes, write/adapt/polish tests and run the final gate. No earlier manual/user testing, reproduction runs, playtests, walkthroughs or automated test writing/execution, including by delegates. Source inspection and existing-log reading remain allowed. Read-only reviews inspect supplied evidence without running tests. Follow [tests-last order](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests); keep fixes surgical.

Discover the actual gate. Never push a red required gate. Use the project's commands and working directories:

| Check | Discover | Notes |
|---|---|---|
| Types / compile / build | Manifests, CI, toolchain | Run applicable required gates. |
| Lint / static analysis | Project configuration | Respect actual rules. |
| Tests | Affected suites and required CI | Cover changed behavior and consumers. |
| Circular deps | Available graph/checker | No new cycles. |

Remote builds, paid services, signing and publishing require actual authority. If unavailable,
report the affected verification gap and compatibility risk; never substitute an unrelated green check.
Unknown applicability is UNKNOWN, not N/A. Justify genuinely inapplicable checks.

If a check fails → back to Phase 4, fix, manually recheck changed behavior, then polish/re-run final tests. Report the final result (pass/fail per check) —
this line goes into the PR comment as proof.

---

## Phase 6 — Push  (checkpoint first)

**Checkpoint** — show the user: the fix-set applied, the before/after summary, and the green gate
result. Get a go-ahead (unless the user pre-authorized). Then:

- Stage only the files you changed. Commit with a clear conventional message:
  ```
  git add <changed files>
  git commit    # message: "fix(<area>): <what we hardened on PR #<n>>"
  git push
  ```
- **No AI attribution in the commit** — repo rule [`no-ai-commit-attribution`](references/mobile-rules/no-ai-commit-attribution.mdc) forbids AI/tool trailers such as `Co-Authored-By: AI`,
  `Made-with`, or any "generated by AI" trailer. If such text appears, rewrite before pushing.
- **Never force-push.** Only additive commits on top of the author's branch.
- If push is rejected (fork without maintainer-edits, protected branch) → don't fight it. Skip to
  Phase 7 and fold the full patch/context into the comment so a teammate or agent can apply it.

---

## Phase 7 — PR comment (the handoff context dump)

**Checkpoint** — show the drafted comment before posting (it's author-facing). Reuse explicit prior authorization; otherwise confirm.

Compose per [references/pr-comment-template.md](references/pr-comment-template.md). The comment is
deliberately a **rich context dump** so a fresh agent or teammate can take over cold:

- **What we contributed** — summary + commit sha(s), gate-passed proof.
- **Before / After** — per fix.
- **Review summary** — the verdict + the severity table (condensed).
- **Open questions for the team** — only the ones we couldn't resolve in Phase 3.5.
- **Handoff** — current state, what's done, what's pending, how to resume.

Post it:
```
gh pr comment <n> --body-file <file>
```

Then save the **full local report** to the scratchpad (working artifact, not committed) and tell
the user where it is. Offer to switch back to their original branch.

---

## Safety gates

- **No code** in Phases 0–3.5. Reading only.
- **Confirm before Phase 6 (push)** and **before Phase 7 (comment)** — both mutate the PR and are
  hard to undo. One combined checkpoint is fine if the user pre-authorized.
- **Never force-push, never rewrite their history, never delete their commits.**
- **Never weaken security handling** (protected secret storage, TLS, input/origin/permission checks,
  no hardcoded secrets) even to make a build pass.
- **Never add AI attribution** to commits or PR content ([`no-ai-commit-attribution`](references/mobile-rules/no-ai-commit-attribution.mdc)).
- Review checkout must be clean before `gh pr checkout`. Preserve dirty work; use an isolated checkout.
- The PR comment is the only author-visible output. Keep review candor for the local report;
  keep the comment professional, specific, and useful.

---

## Examples

| User message | Behavior |
|---|---|
| `/pr-review https://github.com/<owner>/<repo>/pull/240` | Authorized pipeline on #240. |
| `/pr-review 240` | Same, resolves repo via `gh`. |
| "a teammate opened a PR, can you vet it? <url>" | Triggers the pipeline. |
| "review this incoming PR before we merge" (+ url/number) | Triggers the pipeline. |
| `/pr-review` (no arg) | Ask once for the PR URL/number, then run. |
