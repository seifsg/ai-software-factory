# Coded run

Where `factory guard step <n>` runs, it applies the Stop guard's rules inline, so steps chain in one turn. "Command not found": SKILL.md's live guard, unchanged.

## Each step

1. Load the step's skill once per run; a later step of the same skill rereads only its section. Reload a skill after compaction.
2. Do the step's work; read, search or run fresh.
3. Post its full block as its own message, opening with its heading; a todo posts its `T<n> pre:` line.
4. Run `factory guard step <n>` (a todo: `factory guard step T<n>`). It applies the Stop rules to that message, writes it under its heading in `.factory/run.md`, ticks the heading and sets `Next:`. Never edit block text in run.md by hand; a refused block is fixed and posted again.
5. Do what it prints, in the same turn: the next step and its skill, or the fix it names. It asks for `stop-check` only when no command Stop hook guards the run; then load `stop-check` before each later block.
6. End the turn only where it prints `may stop`: `Waiting: owner:` (Safe after Gate A, owner-reserved choices), `Waiting: jobs:` with no independent work left, or a closed run.

Step 5 runs one todo per guard call, every todo in the same turn.

## Full suite

Record each full-suite run with `factory receipt write` (command, exit, log path). `factory receipt check` says whether HEAD's tree has a passing one; the guard refuses Gate B and Gate C lines without it. A receipt for the final head's tree is the one full-suite run: never rerun that tree.
