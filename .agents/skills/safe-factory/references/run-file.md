# Run file

`.factory/run.md`, one per checkout. Hooks read only the four header lines, step headings and gate lines: keep exact spelling.

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
Gate A: PASS (checker <agent id>) @<sha>

## 4 Before ✔
<block>

## 5 Build
T1 pre: <before> do: <change> post: <check> ✔

## 6 Verify

## 7 PR

## 8 Review
```

- `Status:` `open`, `closed`, or `stopped (<owner's reason>)`.
- `Next:` `<step number> <step name> · <skill>`: the first unticked step, or, while an earlier step is blocked, the step you continue with; the blocked step's block names its blocker. A closed run: `none (closed)`.
- `Waiting:` `none`, `owner: <question>` or `jobs: <what runs and who reports back> (max <minutes> min)`.
- A heading gets `✔` only when its block meets its skill's output contract. A gate line is separate: an open gate never unticks a step.
- `Gate A|B|C: PASS (checker <agent id>) @<sha>` lines carry a checker's handback (`Gate <X>: PASS @<sha>`), under steps 3, 6 and 8. An owner waiver is `Gate <X>: WAIVED by owner ("<their words>")`; night runs take none. A failed check leaves `Gate <X>: FAIL <missing items>`; each rerun replaces the earlier line for that gate.
- `Review: ready (reviewer <agent id>) @<sha>` under step 8: the reviewer's last verdict, on the pushed head.
- `CRITICAL: <finding>` in the current step's block while a critical finding is open, `CRITICAL fixed: <finding>` once the reviewer confirms the fix: it opens loop rounds 4 and 5 ([run cases](run-cases.md#review-loops)).
- Long blocks may live on the ticket: write the comment link and a one-line summary instead of the full text.

## What the hooks do

Both run `scripts/run-guard.sh` (`stop` or `compact`) on nearest run file inside current checkout. Product checkouts get that script and host hook files from step 0's `wire-product-hooks.sh`. The Stop guard ignores a run file untouched for 12 hours; both ignore `Status: stopped` and a finished run (step 8 ticked, gates A, B and C and the review proven). Run-guard state lives in `.factory/guard/`: never edit it. No live guard: Fast self-resumes `Next:` in the same turn.

| Hook | When | Does |
|---|---|---|
| Stop guard | your turn ends | with `Waiting: none` and no background tasks reported by the host: blocks the stop and sends the first unproven gate, else the fixed prompt for `Next:`'s step. Two headings ticked in one turn: asks to redo the later one as its own pass. A second stop with no run-file change since the last block passes. A jobs wait past its deadline: asks to check the job. Round 3, no `CRITICAL:`: asks for its cap line. Past round 5, 6 turns without progress or a spent night budget: one packet prompt, then the run is halted. Two compactions, or a night phase boundary: one relay prompt, then a fresh session drives the run. |
| Compact hook | after compaction or a resume | prints `Next:` with "load that skill fresh"; counts compactions |

Proof comes from the host: a gate or review line counts only when the subagent file of the id it names holds that handback on that commit. Only a well-formed `Next:` value (`<step> <name> · <skill>`) reaches the agent; no other run-file text does.
