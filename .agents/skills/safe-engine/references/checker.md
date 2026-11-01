# Checker

The gate after steps 3, 6 and 8. A fresh light read-only delegate (role `checker`, or any light read-only agent given this brief). The coordinator pastes its gate line verbatim with its agent id. It judges the outputs against their contracts, never the work's quality; quality is `deep-review`'s and `how-to-review-a-pr`'s job.

## Brief

```text
Role: checker. Gate <A|B|C>. Project: <absolute path>. Commit: <HEAD sha>.
Contracts: the "Output contract" checklist of <skill paths for the gate's steps>.
Outputs: .factory/run.md, steps <range>; <PR URL for gate C>.
Only those checklist lines (and Gate C's list below) count; any other concern is a "note:", never
MISSING. For every line, find the output that meets it; open what it names.
Read-only. Check every line in one pass. Hand back "Gate <X>: PASS @<commit>" when all are met, else "Gate <X>:
FAIL <n> missing" and the list. Do not fix anything. Do not read the builder's notes or chat.
```

| Gate | Steps | Contracts from |
|---|---|---|
| A | 0–3 | `ticketing`, `analyze-start`, `recommend`, `get-ready-to-code` (plan) |
| B | 4–6 | `how-to-make-a-pr` (Before proof), `get-ready-to-code` (0–4 loop), `deep-review` |
| C | 7–8, the PR | `how-to-make-a-pr` (`## 7 PR`), plus the list below |

Gate C's list, besides `## 7 PR`:

- [ ] Steps 0–8 ticked
- [ ] Gates A and B: PASS or WAIVED
- [ ] `## 8 Review` holds the reviewer's verdict on the PR's current head

## Handback

```text
<contract line>: met <where> | MISSING <what is absent or wrong>
note: <concern outside the contract lines, never counted>
Gate <X>: PASS @<commit> | FAIL <n> missing
```

## After a FAIL

Fix each missing item at its step, then brief a fresh checker for the same gate. Each FAIL is a round, capped like [review loops](run-cases.md#review-loops); the packet lists the repeated items.
