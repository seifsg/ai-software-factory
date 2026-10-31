# Run file

`.factory/run.md`, one per checkout. The hooks read only the four header lines, the step headings and the gate lines, so keep their exact spelling.

```text
# Run: <ticket link> · <mode> · <kind>
Status: open
Next: 5 Build · get-ready-to-code
Waiting: none

## 0 Ticket ✔
<block>

## 1 Analyze ✔
<block>

## 2 Recommend ✔
<block>

## 3 Plan ✔
<block>
Gate A: PASS

## 4 Before ✔
<block>

## 5 Build
T1 pre: <before> do: <change> post: <check> ✔

## 6 Verify

## 7 PR

## 8 Review
```

- `Status:` `open`, `closed`, or `stopped (<owner's reason>)`.
- `Next:` `<step number> <step name> · <skill>`: the first unticked step, or, while an earlier step is blocked, the step you continue with; the blocked step's block names its blocker.
- `Waiting:` `none`, `owner: <question>` or `jobs: <what runs and who reports back>`.
- A heading gets `✔` only when its block meets its skill's output contract.
- `Gate A|B|C: PASS` lines come only from the checker, under steps 3, 6 and 7. A failed check leaves `Gate <X>: FAIL <missing items>`; each rerun replaces the earlier line for that gate.
- Long blocks may live on the ticket: write the comment link and a one-line summary instead of the full text.

## What the hooks do

| Hook | When | Reads | Does |
|---|---|---|---|
| Stop guard | your turn ends | `Status`, `Waiting`, `Next`, step 8 tick, gate lines | open run, `Waiting: none`, not finished: blocks the stop and says `Next:`. A second stop with no run-file change since the last block passes. |
| Compact hook | after compaction or a resume | header lines | prints them with "reload the `Next:` skill" |

`Status: closed` without step 8 ticked and three PASS lines gets blocked like an open run.
