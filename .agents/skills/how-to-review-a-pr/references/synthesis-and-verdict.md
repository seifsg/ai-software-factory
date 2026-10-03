# Synthesis, verdict & fix-set selection

You now hold four themed reports (performance, security, user-journey, change-guard) plus your own
Phase-1 analysis. Turn them into one decision. This is the judgment layer the individual reviewers
can't reach — they each saw one facet; you see the whole.

## 1. Merge & dedupe

- Pool every finding. When two themes flag the same line, keep one entry at the **higher** severity
  and note both lenses (e.g. "perf + change-guard").
- Drop pure duplicates. Keep genuinely distinct findings even on the same file.

## 2. Master findings table (severity-ranked)

```
| # | Sev | Theme(s) | File:Line | Finding | Impact | Fix now? | Confidence |
|---|-----|----------|-----------|---------|--------|----------|------------|
```

Severity ladder: **CRITICAL > HIGH > MEDIUM > LOW.** Sort by it. Do **not** factor development
time — rank purely by impact on the product and its users.

## 3. The 5th lens — what the themes structurally can't judge

The four reviewers are specialists; none of them owns these cross-cutting calls. Make them
explicitly:

- **Opportunities** — improvements you noticed that nobody asked for. List them as notes. Don't
  act on them unless trivial and clearly aligned; they're gifts to the team, not scope creep.
- **Necessary complexity to KEEP** — call out anything a naive reviewer (or an over-eager fix pass)
  might "simplify" or delete that is actually load-bearing (platform branches, native quirks,
  Reanimated worklets, defensive guards). Protect it explicitly so we don't break it in Phase 4.
- **Compliance with the author's request** — are we staying in their lane? We harden and correct;
  we do not redirect their feature, change its intent, or bolt on things they didn't ask for. If a
  finding would require overstepping, it's a *flag for the team*, not a *fix now*.

## 4. Fix-set selection — "fix all that makes sense"

Decide per finding: **Fix now** or **Flag only**.

**Fix now** when ALL hold:
- It's a clear correctness / security / build-or-lint breaker, or an obvious low-risk improvement.
- The fix is small and localized.
- It stays inside the PR's intent (hardening, not redesign).
- Confidence is HIGH (or MED with an obvious, safe fix).

**Flag only** (note it, don't touch it) when ANY hold:
- Fixing it would change the author's intended behavior or scope.
- It needs a product / teammate / external decision.
- It's a large refactor or architectural change.
- It's low-confidence, or it touches necessary complexity you're not sure about.
- It requires a native change / new native build (can't be validated by the JS gate here).

Record the split so Phase 4 knows exactly what to do and Phase 7 knows exactly what to hand off.

## 5. Verdict

Pick one, judged **after** the Phase-4 fixes would be applied:

| Verdict | When |
|---|---|
| `APPROVE` | Delivers the claim; no CRITICAL/HIGH; nothing to fix. |
| `APPROVE-WITH-FIXES` | Delivers the claim; the issues we're fixing now clear the CRITICAL/HIGH set; only flags/notes remain. |
| `REQUEST-CHANGES` | HIGH issues remain that we can't safely fix (need the author/team), or open questions block correctness. |
| `BLOCK` | CRITICAL unresolved — doesn't do what it claims, breaks existing behavior, would crash on OTA'd older native, ships a secret, or the gate (typecheck/lint/tests/circular-dep) can't be made green. |

State the verdict in one line with the single most important reason.

## 6. Open questions

Collect everything ambiguous. These go through the **Phase 3.5 question gate** (ask the user first);
whatever survives unanswered goes into the PR comment as open questions for the team.
