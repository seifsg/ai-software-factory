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

## 2b Challenge ✔
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
- A heading gets `✔` only when its block meets its skill's output contract. A gate line is separate: an open gate never unticks a step.
- `Gate A|B|C: PASS (checker <agent id>)` lines are a checker's handback pasted verbatim, under steps 3, 6 and 8. An owner waiver is `Gate <X>: WAIVED by owner ("<their words>")`. A failed check leaves `Gate <X>: FAIL <missing items>`; each rerun replaces the earlier line for that gate.
- Long blocks may live on the ticket: write the comment link and a one-line summary instead of the full text.

## What the hooks do

Both run `scripts/run-guard.sh` (`stop` or `compact`) on the nearest run file inside the current checkout. The Stop guard ignores a run file untouched for 12 hours; both ignore `Status: stopped` and a finished run (step 8 ticked, gates A, B and C PASS or WAIVED).

| Hook | When | Does |
|---|---|---|
| Stop guard | your turn ends | with `Waiting: none` and no background tasks reported by the host: blocks the stop and names the first missing gate, else `Next:`. A second stop with no run-file change since the last block passes. |
| Compact hook | after compaction or a resume | prints `Next:` with "load that skill fresh" |

Only a well-formed `Next:` value (`<step> <name> · <skill>`) reaches the agent; no other run-file text does.
