# Coded run

Use native `factory` from PATH or its package. Use the live guard only when both fail or Stop runs `run-guard.sh`.

After creating a new run header, run `factory guard begin` before Ticket work.

## Each step

1. Load each step's skill once per run (again after compaction); a later step of the same skill needs no reread.
2. Do the step's work; read, search or run fresh.
3. Pipe its full block (a todo: its `T<n> pre:` line) on stdin to step 4's command: its one copy. The owner reads blocks on the run report, else `.factory/run.md` opened in the host preview at step 0; no preview: post each block in chat too.
4. Run `factory guard step <n>` (`0`-`8`, `2b`, `T<n>`) <<'EOF'. It applies the Stop rules, writes and ticks the block, sets `Next:`: steps chain in one turn. Never hand-edit block text in run.md; fix a refused block and pipe it again. Then post one progress line in chat: `<heading> ✅ <key result>`.
5. Do what it prints, in the same turn: the next step and its skill, or the fix it names. Load `stop-check` only when it asks.
6. `Waiting:` only by `factory guard wait <value>`; no `sed`, no block read-back.
7. End the turn only where it prints `may stop`.

Step 5 runs one todo per guard call, every todo in the same turn. Step 6 launches each delegate once; while they run, draft step 7's PR text and the report.

## Full suite

A suite that writes no full receipt itself runs on the clean final head as `factory receipt start --suite full [--inert <glob>] -- <command>`; shared machine: `factory queue run -- factory receipt run ...` in the background. A head changing only `--inert` paths keeps the PASS. Other heavy jobs: `factory queue run -- <cmd>`; shared ids: `factory reserve <key> --floor <n>`. Cite its receipt in Verify; a suite already run: `factory receipt write` (command, exit, log). `factory receipt check` finds the base or final PASS. Gate B can finish while the suite runs. Gate C and the final review need a PASS receipt for their commit's tree; Gate C exactly one run.

## Gate backing

`factory guard check` (read-only) prints one verdict line per gate and review line in run.md: backed by its delegate's handback on that commit, or not; the step-8 reviewer runs it too.

## Review evidence

Give fresh reviewers one `factory review packet --base <sha> --head <sha>` with named `--context`/`--proof` files and separate briefs. Validate head-bound handbacks with `factory review check` before gate handoff. A form check never decides a gate.
