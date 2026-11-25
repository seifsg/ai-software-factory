# Parallel runs on one machine

One session can launch several factory sessions that build in parallel on the same computer. Four things cost time and tokens there: turn ends that wake the launcher, full suites run again on every new head, heavy jobs that fight over the machine, and ids two sessions both take. The factory handles each one.

## Turn ends

Each turn end of a launched session wakes the session that launched it, and that session re-reads its whole context to answer. So a launched session ends a turn only when it is done, blocked, or has proof the owner should see (`run-cases`, Another session). Everything else waits inside a call:

- `factory guard step` never asks for a turn end at an open gate, review or missing receipt: run the checker or reviewer and wait for it in the call, then go on. The Stop hook's own replies are unchanged.
- A background suite: `factory receipt check --wait <secs>` (1 to 3600) checks every second inside the binary and returns on the PASS, on a FAIL receipt for that tree, or at the deadline. Give the call a tool timeout above the wait (`--wait 540` with 600 s on Claude Code, whose default is 120 s) and repeat it while the suite runs.

## Suite receipts across inert changes

`factory receipt run|start|write --inert <glob>` (repeatable) records paths the suite never reads, such as `docs/**`. A later head whose change from that receipt's tree touches only such paths keeps the PASS: `receipt check` and the guard read it as carried, and `receipt check` names it with its globs (`carried from tree <id>: <n> inert paths changed (inert: docs/**)`). The change is read from Git (`git diff --name-only` of the two trees), never from an agent. A carry never stands when that exact tree has its own receipt (a FAIL wins) or a suite still running on it. A glob that matches ordinary source paths (`*`, `**`, `?**`, `**.*`) is refused. Format: [receipts](receipts.md).

The base is merged into a PR once, at the final run, and that merge is reviewed as a delta.

## Heavy-job queue

```text
factory queue run [--name <queue>] [--slots <n>] -- <command>...
factory queue list [--name <queue>]
```

Jobs of one queue (default `heavy`, one slot) run first in, first out across every session on the machine. Queue the full suite as `factory queue run -- factory receipt run --suite full -- <command>` in the background: `receipt start` returns at once, so it would not hold the slot. The waiting happens inside the binary: no polling turns, no tokens. A ticket whose process died (its pid gone or its start time changed) is dropped at the next scan. The command's output and exit code pass through. Tickets hold the working folder and command line, which `queue list` and waiting jobs print: keep secrets out of queued arguments. Queue files live in `FACTORY_QUEUE_DIR`, else the user cache folder (`%LOCALAPPDATA%` on Windows, `$XDG_CACHE_HOME` or `~/.cache` elsewhere) under `ai-software-factory/`.

## Id reservation

```text
factory reserve <key> [--floor <n>] [--count <k>]
```

Prints the next free numbers for `<key>` (for example `myrepo-decision`), one per line, under a machine-wide lock: two sessions never get the same number. `--floor` is the highest number already used on the base branch; the first number handed out is above both it and every earlier reservation. A damaged state file stops the command with an error and is never reset silently.
