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
- `Review: ready (reviewer <agent id>) @<sha>` under step 8: the reviewer's last verdict, on the pushed head (no remote: its head).
- `CRITICAL: <finding>` in the current step's block while a critical finding is open, `CRITICAL fixed: <finding>` once the reviewer confirms the fix: it opens loop rounds 4 and 5 ([run cases](run-cases.md#review-loops)).

## What the hooks do

Both run `scripts/run-guard.sh` (`stop` or `compact`) on this session's run: its binding, nearest in its checkout, then its step block's `Workspace`. The Stop guard ignores a run file untouched for 12 hours; both ignore `Status: stopped` and a finished run (step 8 ticked, gates A, B and C and the review proven). Run-guard state lives in `.factory/guard/`: never edit it.

| Hook | When | Does |
|---|---|---|
| Stop guard | your turn ends | unless `Waiting: owner:`, `Waiting: jobs:` or background tasks the host reports: blocks the stop, sends a step not ticked, a line over 300 characters, first unproven gate, else fixed prompt for `Next:`'s step. A wait gets one block for a step not ticked. Past round 5, 6 turns without progress or a spent night budget: one packet prompt, then halted. |
| Compact hook | after compaction or a resume | prints `Next:` with "load that skill fresh"; resume also says to load `safe-factory` |

Proof is the host's: gate or review line counts only when the named id's subagent file holds that handback on that commit.
