# Coded run

Where `factory guard step <n>` runs, it applies the Stop guard's rules inline, so steps chain in one turn. "Command not found", or it says the Stop hook still runs `run-guard.sh`: SKILL.md's live guard, unchanged.

## Each step

1. Load the step's skill once per run; a later step of the same skill works from it, no reread. Reload a skill after compaction.
2. Do the step's work; read, search or run fresh.
3. Post its full block as its own message, opening with its heading; a todo posts its `T<n> pre:` line.
4. Run `factory guard step <n>` (`<n>`: the step, `0` to `8` or `2b`; a todo: `T<n>`). It applies the Stop rules to that message, writes it under its heading in `.factory/run.md`, ticks the heading, sets `Next:` and records the step in the guard state, so the Stop hook's `factory guard stop` accepts several steps in one turn. Never edit block text in run.md by hand; a refused block is fixed and posted again.
5. Do what it prints, in the same turn: the next step and its skill, or the fix it names. It asks for `stop-check` only when no command Stop hook guards the run; then load `stop-check` before each later block.
6. End the turn only where it prints `may stop`: `Waiting: owner:` (Safe after Gate A, owner-reserved choices), `Waiting: jobs:` with no independent work left, or a closed run.

Step 5 runs one todo per guard call, every todo in the same turn.

## Full suite

Run a suite that writes its own full receipt directly. For other suites, run `factory receipt run --suite full -- <command>`, or if already run, record it with `factory receipt write` (command, exit, log path). `factory receipt check` says whether a tree has a passing one: the base commit's is the suite Before, the final head's is the one full-suite run (never rerun that tree). Gate B can finish while the suite runs. Gate C and the final review require a passing receipt for their commit's tree, with exactly one passing run for Gate C.

## Gate backing

`factory guard check` (read-only) prints one verdict line per gate and review line in run.md: backed by its delegate's handback on that commit, or not. The step-8 reviewer runs it itself.

## Review evidence

Give fresh reviewers one `factory review packet --base <sha> --head <sha>` with named `--context`/`--proof` files and separate briefs. Validate head-bound handbacks with `factory review check` before gate handoff. A form check never decides a gate.
