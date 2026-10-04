# PR comment template — the handoff context dump

This is the **only author-visible artifact**, so it must be professional, specific, and self-
contained. Its job is twofold: (1) tell the author what we changed and why, and (2) carry enough
context that **a fresh agent or teammate with zero prior knowledge can take over the job**.

Keep the local report candid; keep this comment constructive. State facts, not verdicts about the
author. Fill every placeholder — an empty section is better deleted than left as a stub.

```markdown
## Review + fixes

**Verdict:** <APPROVE | APPROVE-WITH-FIXES | REQUEST-CHANGES | BLOCK> — <one-line reason>
**Manual QA:** <actual actions, candidate and observed outcomes/limits before test work>
**Final tests:** <tests added/adapted, execution results and remaining gaps>
**Gate:** <actual checks and pass/fail/unverified results> &nbsp;|&nbsp; **Pushed:** <commit sha(s)> _(or: no push — see Handoff)_

### What this PR claims
> <the claim, quoted/trimmed from the PR body>

**Does it deliver?** <YES / PARTIAL / NO> — <one sentence, from the user-journey review>

---

### What we changed
<Only if we pushed fixes. One row per fix.>

| # | Area | What we did | Why |
|---|------|-------------|-----|
| 1 | <file> | <change> | <finding it addresses> |

#### Before / After
<Per non-trivial fix — short, readable. Code fences or prose.>

**<file:line> — <title>**
- Before: `<old behavior / snippet>`
- After:  `<new behavior / snippet>`

---

### Review summary
<Actual review scope and reviewers: performance · security · user journey · change-guard.
State focused Small Change scope when selected; never claim four sessions that did not run.>

| # | Sev | Theme | File:Line | Finding | Status |
|---|-----|-------|-----------|---------|--------|
| <n> | <actual severity> | <theme> | <file:line> | <finding> | <verified status> |

<Include actual findings only; a clean review has no finding rows. Full detail lives in our local report.>

---

### ❓ Open questions for the team
<Only the ones neither the reviewer nor the maintainer could resolve without you.
Omit this whole section if there are none.>

1. **<question>** — <why it matters / what's blocked until answered>

---

### 🔁 Handoff (for whoever picks this up next)
- **Current state:** <what's verified, what isn't; draft and remaining human decisions>
- **Done:** <fixes pushed / verified>
- **Pending:** <flagged findings not fixed, and why (out of scope / needs decision / missing platform or release evidence)>
- **How to resume:** <branch, the gate commands that passed, where the flagged items live>
<If push failed (fork/protected branch), include the full patch here so it can be applied manually.>
```

## Rules
- Post with `gh pr comment <n> --body-file <file>` (write the body to a temp file first — avoids
  shell-escaping pain with the markdown).
- **Confirm with the user before posting** unless explicit prior authorization covers it — it's author-facing and hard to unsend.
- **No AI attribution** in the comment (repo rule `no-ai-commit-attribution` applies to PR content too).
- If we didn't push, label actual state: *implemented locally, unpublished* or *proposed, not implemented*. Put the available patch/diff in **Handoff**; never imply applied or published work without evidence.
- No internal-only candor, no blame, no dev-time estimates. Impact and next steps only.
