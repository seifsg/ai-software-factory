# Checker

The gate after steps 3, 6 and 7. A fresh light delegate (role `checker`), read-only except for its one gate line. It judges the outputs against their contracts, never the work's quality; quality is `deep-review`'s and `how-to-review-a-pr`'s job.

## Brief

```text
Role: checker. Gate <A|B|C>. Project: <absolute path>.
Contracts: the "Output contract" section of <skill paths for the gate's steps>.
Outputs: .factory/run.md, steps <range>; <PR URL for gate C>.
For every contract line, find the output that meets it. Open files, links and
images it names. Gate C also checks every step 0-6 heading is ticked.
All lines met: write "Gate <X>: PASS" under step <3|6|7> in .factory/run.md,
replacing any earlier line for this gate. Otherwise: write "Gate <X>: FAIL <n>
missing" there the same way and hand back the list.
Do not fix anything. Do not read the builder's notes or chat.
```

| Gate | Steps | Contracts from |
|---|---|---|
| A | 0–3 | `ticketing`, `analyze-start`, `recommend`, `get-ready-to-code` (plan) |
| B | 4–6 | `how-to-make-a-pr` (Before proof), `get-ready-to-code` (0–4 loop), `deep-review` |
| C | 7, whole run | `how-to-make-a-pr`, every step's heading |

## Handback

```text
<contract line>: met <where> | MISSING <what is absent or wrong>
Gate <X>: PASS | FAIL <n> missing
```

## After a FAIL

Fix each missing item at its step, then brief a fresh checker for the same gate. Two failed rounds: ask the owner with both lists. Never edit a gate line yourself.
