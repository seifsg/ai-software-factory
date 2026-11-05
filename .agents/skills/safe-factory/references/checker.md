# Checker

Fresh light read-only delegate (role `checker`, or any light read-only agent given this brief). Judges outputs against contracts, never work quality.

Before each brief, commit and check each contract line yourself, as strictly; a form FAIL costs a round.

## Brief

```text
Role: checker. Gate <A|B|C>. Project: <absolute path>. Commit: <HEAD sha>.
Contracts: the "Output contract" checklist of <skill paths for the gate's steps>.
Outputs: .factory/run.md, steps <range>; <PR URL for gate C>.
Only those checklist lines (and Gate C's list below) count; any other concern is a "note:", never
MISSING. For every line, find the output that meets it; open what it names; check its form too (layout,
URL vs bare number, table vs prose, commit, command). Strict: unsure is MISSING, with the reason.
`DEFERRED (owner|hardware: <what>)` meets a line only for work that needs the
owner (hands, approval, an install) or missing hardware; a stub or placeholder never does, and "unverified" only as that DEFERRED.
Read-only. Round 1 checks every line at once. Hand back "Gate <X>: PASS @<commit>" when all are met, else "Gate <X>:
FAIL <n> missing" and the list. Do not read the builder's notes or chat.
Round 2 on: recheck only MISSING lines of round 1's handback; the rest stay met.
```

| Gate | Steps | Contracts from |
|---|---|---|
| A | 0–3 | `ticketing`, `analyze-start`, `recommend`, `get-ready-to-code` (plan) |
| B | 4–6 | `how-to-make-a-pr` (Before proof), `get-ready-to-code` (0–4 loop), `deep-review` |
| C | 7–8, the PR | `how-to-make-a-pr` (`## 7 PR`), plus the list below |

`## 7 PR` `local only ("<owner's words>") @<sha>` with `git remote` empty: PR lines lapse. `Skipped by owner ("<their words>")` meets its step's lines. Not at night.

Gate C's list, besides `## 7 PR`:

- [ ] Steps 0–8 ticked
- [ ] Gates A and B: PASS or WAIVED
- [ ] PR body: a closing keyword per sub-issue or change ticket it finishes (`how-to-make-a-pr`); an epic only a plain reference
- [ ] `## 8 Review` holds the reviewer's verdict, or its cap line, on the PR's current head
- [ ] Each After file `## 8 Review` names as recaptured names a commit at or after its fix
- [ ] `## 8 Review` has `Left running:` as its last line before any Gate C line, with each item's stop command, or `none`

## Handback

```text
<contract line>: met <where> | MISSING <what is absent or wrong>
note: <concern outside the contract lines, never counted>
Gate <X>: PASS @<commit> | FAIL <n> missing
```

## After a FAIL

Fix each missing item at its step, then brief a fresh checker for the same gate with round 1's handback. Each FAIL is a round, capped like [review loops](run-cases.md#review-loops).
