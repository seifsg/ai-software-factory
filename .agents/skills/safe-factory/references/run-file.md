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
- `Next:` `<step number> <step name> · <skill>`: the first unticked step, or, while an earlier step is blocked, the step you continue with; the blocked step's block names its blocker. Past step 3 that needs `Waiting: owner:`. Owner skips a step: tick it, block `Skipped by owner ("<their words>")`. A closed run: `none (closed)`.
- A heading gets `✔` only when its block meets its skill's output contract. A gate line is separate: an open gate never unticks a step. [Coded run](coded-run.md): the guard writes and ticks each posted block; never hand-edit block text.
- `Gate A|B|C: PASS (checker <agent id>) @<sha>` lines carry a checker's handback (`Gate <X>: PASS @<sha>`), under steps 3, 6 and 8. An owner waiver is `Gate <X>: WAIVED by owner ("<their words>")`; night runs take none. A failed check leaves `Gate <X>: FAIL <missing items>`; each rerun replaces the earlier line for that gate.
- `Review: ready (reviewer <agent id>) @<sha>` under step 8: the reviewer's last verdict, on the pushed head (no remote: its head).
- `CRITICAL: <finding>` in the current step's block while a critical finding is open, `CRITICAL fixed: <finding>` once the reviewer confirms the fix: it opens loop rounds 4 and 5 ([run cases](run-cases.md#review-loops)).

What the hooks do: [run cases](run-cases.md#hooks).
