# Coded run

Use native `factory` from PATH or its package. Use the live guard only when both fail or Stop runs `run-guard.sh`.

After creating a new run header, run `factory guard begin` before Ticket work.

## Each step

1. Load the step's skill once per run; a later step of the same skill works from it, no reread. Reload a skill after compaction.
2. Do the step's work; read, search or run fresh.
3. Pipe its full block (a todo: its `T<n> pre:` line) on stdin to step 4's command: its one copy. The owner reads blocks on the live run page.
4. Run `factory guard step <n>` (`<n>`: the step, `0` to `8` or `2b`; a todo: `T<n>`) <<'EOF'. It applies the Stop rules, writes the block under its heading in run.md, ticks it, sets `Next:` and records the step, so several steps run in one turn. Never edit block text in run.md by hand; fix a refused block and pipe it again. Then post one progress line in chat: `<heading> ✅ <key result>`.
5. Do what it prints, in the same turn: the next step and its skill, or the fix it names. It asks for `stop-check` only when no command Stop hook guards the run; then load `stop-check` before each later block.
6. `Waiting:` only by `factory guard wait <value>`; no `sed`, no block read-back.
7. End the turn only where it prints `may stop`.

Step 5 runs one todo per guard call, every todo in the same turn.

## Full suite

A suite that writes no full receipt itself runs as `factory receipt start --suite full -- <command>` on the clean final head. Cite its launch receipt or reused PASS in Verify. If already run, record it with `factory receipt write` (command, exit, log path). `factory receipt check` finds the base or final PASS. Gate B can finish while the suite runs. Gate C and the final review require a passing receipt on their commit's tree, with exactly one passing run for Gate C.

## Gate backing

`factory guard check` (read-only) prints one verdict line per gate and review line in run.md: backed by its delegate's handback on that commit, or not; the step-8 reviewer runs it too.

## Review evidence

Give fresh reviewers one `factory review packet --base <sha> --head <sha>` with named `--context`/`--proof` files and separate briefs. Validate head-bound handbacks with `factory review check` before gate handoff. A form check never decides a gate.
