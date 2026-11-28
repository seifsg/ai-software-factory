# Time blocks

Every factory run shows where its wall time went, in one block. Hooks and the commands a run already calls stamp the time; no model call writes it.

```text
total                        2h13m20s
plan                         █ 0m59s
build                        █ 6m18s
tests + CI                   ███ 21m10s  (1 full-suite run)
review + gates               █ 6m49s
idle                         ████████████ 1h38m04s  (1h38m04s lost: jobs: detached mia:ci (receipt start), nothing woke the session)
```

## Where it shows

| Place | How |
|---|---|
| Any time | `factory time [<run folder>]` prints the block; `--json` the same numbers in seconds |
| PR body | `factory guard step 6` ends its reply with the block: the PR body ends with it |
| Done handback | `factory guard step 8` ends its reply with the block: the handback ends with it |
| Across runs | every `factory time`, step 6 and 8 reply and closing Stop upserts the run's row in the project's `.factory/bench.md` |

## The block

- A `text` fence. `total` first: from the run's first step start to its end (closed) or now (open).
- One row per phase that took time, in this order: `waiting on you`, `plan`, `build`, `tests + CI`, `review + gates`, `publish`, `waiting on queue`, `idle`.
- Bars: 12 `█` for the longest phase, the others rounded to it, at least one. Labels pad to 29 characters.
- Times: `9m25s`, `0m41s`, from one hour `2h13m20s`.
- Notes in parentheses: the full-suite run count on `tests + CI`, then `<time> lost: <cause>`.

## Phases

Each second counts once, so the rows sum to the total. When two things overlap, the higher one wins:

| Rank | Phase | Comes from |
|---|---|---|
| 1 | waiting on you | a turn ended with `Waiting: owner:`, until the owner's reply |
| 2 | waiting on queue | `factory queue run` waited for its slot |
| 3 | tests + CI | a suite run with a receipt (`factory receipt run`, `start`, `write --secs`) |
| 4 | idle | a turn ended with no owner question and no running subagent, until the session came back |
| 5 | the step's phase | step starts: 0 to 4 plan, 5 build, 6 and 8 review + gates, 7 publish |

- A wait ends at the session's next sign of life, whichever came first: the first transcript entry after it (the Stop hook reads the transcript from where it stood when the wait began), a `factory guard step` or `guard wait` call, or the next step start. Hosts without a transcript count the wait until the next of those.
- A closed run ends at its first Stop after closing, dated by the run file's last write; a blocked Stop never ends it.
- Idle and queue time is lost whole; the cause is the `Waiting:` text or the queue name, on one line of at most 120 characters with backticks made plain quotes. Causes land in PR bodies: keep secrets out of `Waiting:` lines.
- Lost time only the agent knows (a toolchain path that failed): `factory time lost <phase> <11m03s> <cause>` adds it to that phase's note.
- A turn that ends while a subagent runs is not a wait: the subagent's result wakes the session.

## Files

| File | Holds |
|---|---|
| `.factory/guard/steps.jsonl` | step starts (the guard's timeline) |
| `.factory/guard/time.jsonl` | waits, resumes, suite and queue spans, lost time, the run's end; appended, one JSON object per line |
| `<main checkout>/.factory/bench.md` | `## Factory runs`: one row per run, keyed by its start; every other line and the line endings stay as written; a linked worktree writes its main checkout's file |

A new Ticket (step 0) starts a new clock: both stamp files restart. A torn or edited stamp line is skipped, never guessed.

## Detached suites

A suite started with `factory receipt start` runs outside the host's process tracking, so its end wakes no session. While one is live (its reservation stands and its process runs, same pid and start time) and no subagent or owner reply will wake the session, Stop refuses to end the turn and names the in-call wait: `factory receipt check --suite <name> --wait 540` with a 600 s tool timeout. These refusals never spend the guard's idle budget: they last only while the suite runs. A dead supervisor's leftover reservation never blocks. Better still, run the suite as a host background job (`factory receipt run ...`), which notifies the session on exit.
