# Run cases

Run rules that apply only in the case each section names.

## Review loops

One round = review, fixes, fresh review.

- Apply [worth-it rounds](worth-it.md) before fixing. Mandatory findings keep the loop open; optional polish needs a worthwhile selection or an authorized finishing batch.
- After round 3, authorized optional deferrals stay in the follow-ups ticket.
- Caps, for every loop (review, gate checker, fix): each non-ready verdict or FAIL handback is a failed round. Rounds 1 to 3 run; rounds 4 and 5 only while the current step's block holds an open `CRITICAL: <finding>` line, which turns into `CRITICAL fixed: <finding>` once the reviewer confirms the fix. After that, stop with `Waiting: owner:` and the packet under the current step: findings per round (new vs repeated), the shared cause, options (extend, authorized deferral of MEDIUM and LOW, amend scope, cancel).
- The guard counts failed rounds from the host's subagent files and halts the run at the cap, or after 6 turns without a new tick or proven gate. A halted run waits for the owner's `clear`.

## Factory fault

A skill or hook misbehaves, or a factory improvement shows up:

1. Document it: observed, expected, example, factory version.
2. Open an issue in the factory's own repository asking for help. Mark it unverified.
3. Do not run `improve-factory`. The owner verifies the issue first. A session offered for it launches `improve-factory` on that issue with a factory repository checkout instead of the project path, plus this project's absolute path and whether its run is still open. Only the owner starts it. Product bugs stay in delivery.
