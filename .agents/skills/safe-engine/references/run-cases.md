# Run cases

Run rules that apply only in the case each section names.

## Review loops

One round = review, fixes, fresh review.

- Apply [worth-it rounds](worth-it.md) before fixing. Mandatory findings keep loop open; optional polish needs a worthwhile selection or authorized finishing batch.
- Caps, for every loop (review, gate checker, fix): each non-ready verdict or FAIL handback is a failed round.
- 3 failed rounds, no open `CRITICAL: <finding>` in current step's block or last handback: loop passes as `Gate <X>: PASS (cap, 3 rounds, no CRITICAL) @<sha>` or `Review: ready (cap, 3 rounds, no CRITICAL) @<sha>`, never a stop; rest goes to ticket's follow-ups and the PR.
- Open CRITICAL: rounds 4 and 5 run; it turns `CRITICAL fixed: <finding>` once reviewer confirms. Open after 5: stop, `Waiting: owner:`, packet under current step: findings per round, shared cause, options (extend, amend scope, cancel).
- Guard takes a cap line only after 3 failed handbacks in host's subagent files; halted run waits for owner's `clear`.

## Factory fault

A skill or hook misbehaves, or a factory improvement shows up:

1. Document it: observed, expected, example, factory version.
2. Open an issue in the factory's own repository asking for help. Mark it unverified.
3. Do not run `improve-factory`. Owner verifies the issue first. A session offered for it launches `improve-factory` on that issue with a factory repository checkout instead of the project path, plus this project's absolute path and whether its run is still open. Only the owner starts it. Product bugs stay in delivery.
