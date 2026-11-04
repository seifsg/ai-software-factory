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
- `Waiting:` `none`, `owner: <question>` or `jobs: <what, who reports back> (max <minutes> min)`.
- A heading gets `✔` only when its block meets its skill's output contract. A gate line is separate: an open gate never unticks a step.
- `Gate A|B|C: PASS (checker <agent id>) @<sha>` lines carry a checker's handback (`Gate <X>: PASS @<sha>`), under steps 3, 6 and 8. An owner waiver is `Gate <X>: WAIVED by owner ("<their words>")`; night runs take none. A failed check leaves `Gate <X>: FAIL <missing items>`; each rerun replaces the earlier line for that gate.
- `Review: ready (reviewer <agent id>) @<sha>` under step 8: the reviewer's last verdict, on the pushed head (no remote: its head).
- `CRITICAL: <finding>` in the current step's block while a critical finding is open, `CRITICAL fixed: <finding>` once the reviewer confirms the fix: it opens loop rounds 4 and 5 ([run cases](run-cases.md#review-loops)).

## What the hooks do

Both use `scripts/run-guard.sh` on this session's run: its binding, nearest in its checkout, then its step block's `Workspace`. Ignored: untouched 12 hours (Stop), `Status: stopped`, finished (step 8 ticked, gates A, B, C and review proven). State: `.factory/guard/`, never edit.

| Hook | When | Does |
|---|---|---|
| Stop guard | turn ends | unless `Waiting: owner:`, `Waiting: jobs:` or reported background tasks: blocks, sends a step not ticked, a line over 300 characters, first unproven gate, else `Next:`'s prompt. A wait gets one block for a step not ticked. Past round 5, 6 idle turns or spent night budget: packet prompt, then halted. |
| Compact | compaction or resume | prints `Next:`, "load that skill fresh"; resume: load `safe-factory` |

A prompt Stop hook applies these through `check`; compaction's place comes at next stop.

Command guard: gate or review line counts only when the named id's subagent file holds that handback on that commit.
