# Run cases

Run rules that apply only in the case each section names.

## Review loops

One round = review, fixes, fresh review.

- Apply `deep-review`'s worth-it rounds before fixing. Mandatory findings keep loop open; optional polish needs a worthwhile selection or authorized finishing batch.
- Caps, for every loop (review, gate checker, fix): each non-ready verdict or FAIL handback is a failed round.
- 3 failed rounds, no open `CRITICAL: <finding>` in current step's block or last handback: loop passes as `Gate <X>: PASS (cap, 3 rounds, no CRITICAL) @<sha>` or `Review: ready (cap, 3 rounds, no CRITICAL) @<sha>`, never a stop; rest goes to ticket's follow-ups and the PR.
- Open CRITICAL: rounds 4 and 5 run ([run file](run-file.md)). Open after 5: stop, `Waiting: owner:`, packet under current step: findings per round, shared cause, options (extend, amend scope, cancel).
- Guard takes a cap line only after 3 failed handbacks in host's subagent files; halted run waits for owner's `clear`.

## Factory fault

A skill or hook misbehaves, or a factory improvement shows up:

1. Document it: observed, expected, example, factory version.
2. Open an issue in the factory's own repository asking for help. Mark it unverified.
3. Do not run `improve-factory`. Owner verifies the issue first. A session offered for it launches `improve-factory` on that issue with a factory repository checkout instead of the project path, plus this project's absolute path and whether its run is still open. Only the owner starts it. Product bugs stay in delivery.

## Resume

Read run file and ticket, load `Next:` skill fresh, continue there. Outside run's folder: first turn ends on a message opening with `Next:`'s heading and `**Workspace:**`. Run file and ticket disagree: test both against checkout, keep what holds; log correction in ticket's activity. `Next:` past a gate without its PASS: run that gate's checker first. Never restart a run.

## New project

Owner named a project folder: create if missing; run and code live there, even when session cannot move. None named: create one beside owner's other projects (parent of current project, else current folder), named for product in kebab-case, report its absolute path. No Git: `git init`, first commit on default branch, then feature branch. No remote: `ticketing` creates it, unless owner said none.

## Another session

Work for another session launches the factory, never a bare task: record in its ticket, then a prompt opening with your agent's invoke form of `safe-factory`, naming mode, kind, ticket, project's absolute path, a worktree the new session creates; authority limited to that ticket.

## Update notice

Update notice, new run: before the run file, tell owner, link what's new, ask update or continue (owner-reserved); end turn, no block. Update: notice's command, new session. Resume or night: one line in current block; never wait or update mid-run.

## Guard not live

Step 1 finds no `.factory/guard/state` on a host with hooks: `safe-factory Resume <run folder>` in a fresh session, then stop; still none: `Waiting: owner:` with the cause.

## Hooks

Both use `scripts/run-guard.sh` on this session's run: its binding, nearest in its checkout, then its step block's `Workspace`. Ignored: untouched 12 hours (Stop), `Status: stopped`, finished (step 8 ticked, gates A, B, C and review proven). State: `.factory/guard/`, never edit.

| Hook | When | Does |
|---|---|---|
| Stop guard | turn ends | unless `Waiting: owner:`, `Waiting: jobs:` or reported background tasks: blocks, sends a step not ticked, a line over 300 characters, first unproven gate, else `Next:`'s prompt. A wait gets one block for a step not ticked. Past round 5, 6 idle turns or spent night budget: packet prompt, then halted. |
| Compact | compaction or resume | prints `Next:`, "load that skill fresh"; resume: load `safe-factory` |

Prompt Stop hook: same through `check`; place comes at next block.

Command guard: gate or review line counts only when the named id's subagent file holds that handback on that commit.
