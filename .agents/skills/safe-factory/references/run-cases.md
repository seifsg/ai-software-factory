# Run cases

Run rules that apply only in the case each section names.

## Review loops

One round = review, fixes, fresh review.

- Apply `deep-review`'s worth-it rounds before fixing. Mandatory findings keep loop open; optional polish needs a worthwhile selection or authorized finishing batch.
- Caps, for every loop (review, gate checker, fix): each non-ready verdict or FAIL handback is a failed round.
- 3 failed rounds, no open `CRITICAL: <finding>` in current step's block or last handback: loop passes as `Gate <X>: PASS (cap, 3 rounds, no CRITICAL) @<sha>` or `Review: ready (cap, 3 rounds, no CRITICAL) @<sha>`, never a stop; rest goes to ticket's follow-ups and the PR.
- Open CRITICAL: rounds 4 and 5 run ([run file](run-file.md)). Open after 5: stop, `Waiting: owner:`, packet under current step: findings per round, shared cause, options (extend, amend scope, cancel).
- Guard takes a cap line only after 3 failed handbacks in subagent files; a halted run waits for owner's `clear`.

## Factory fault

A skill or hook misbehaves, or a factory improvement shows up:

1. Document it: observed, expected, example, factory version.
2. Open an issue in the factory's own repository asking for help. Mark it unverified.
3. Do not run `improve-factory`: the owner verifies the issue, then may start a session running it on that issue in a factory checkout, given this project's absolute path and whether its run is open. Product bugs stay in delivery.

## Resume

Read run file and ticket, load `Next:` skill fresh, continue there. Outside run's folder: first turn ends on a message opening with `Next:`'s heading and `**Workspace:**`. Run file and ticket disagree: test both against checkout, keep what holds; log correction in ticket's activity. `Next:` past a gate without its PASS: run that gate's checker first. Never restart a run.

## New project

Owner named a project folder: create if missing; run and code live there, even when session cannot move. None named: create one beside owner's other projects (parent of current project, else current folder), named for product in kebab-case, report its absolute path. No Git: `git init`, first commit on default branch, then feature branch. No remote: `ticketing` creates it, unless owner said none.

## Another session

Work for another session launches the factory, never a bare task: record in its ticket, then a prompt opening with your agent's invoke form of `safe-factory`, naming mode, kind, ticket, project's absolute path, a worktree the new session creates; authority limited to that ticket. That session ends a turn (waking you) only when done, blocked or with proof to show.

## Update notice

Update notice, new run: before the run file, tell owner, link what's new, ask update or continue (owner-reserved); end turn, no block. Update: notice's command, new session. Resume or night: one line in current block; never wait or update mid-run.

## Guard not live

Step 1 finds no `.factory/guard/state` on a host with hooks: `safe-factory Resume <run folder>` in a fresh session, then stop; still none: `Waiting: owner:` with the cause.

## Hooks

Both use `scripts/run-guard.sh` on this session's run: its binding, nearest in its checkout, then its step block's `Workspace`. Ignored: untouched 12 hours (Stop), `Status: stopped`, finished (step 8, gates A-C and review proven). State: `.factory/guard/`, never edit.

| Hook | When | Does |
|---|---|---|
| Stop guard | turn ends | unless `Waiting: owner:`, `Waiting: jobs:` or reported background tasks: blocks with a step not ticked, a line over 300 characters, the first unproven gate, else `Next:`'s prompt; a wait, once for a step not ticked. Past round 5, 6 idle turns or spent night budget: packet prompt, then halted. |
| Compact | compaction or resume | prints `Next:`, "load that skill fresh"; resume: load `safe-factory` |

Prompt Stop hook: same through `check`; place comes at next block.

Command guard: a gate or review line needs the named id's own handback, in its subagent file, on that commit.

## Escalation

Escalate, don't coach: two failed gate rounds send job and handbacks to a fresh delegate one tier up, same edit access (runner to analyst, analyst to reviewer, maker to builder). A deep job that fails twice comes back to you (Authority and stops, rule 4).

## UI check

UI check (step 2 look): step 6's UI-check delegate (no subagents: you) also lists each miss vs that look + refs on the primary platform, with the capture. A miss of the picked look = HIGH.
