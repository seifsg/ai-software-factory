# Run cases

Run rules that apply only in the case each section names.

## Review loops

One round = review, fixes, fresh review.

- If at round 3 no high severity issues are found, proceed with the agreed outcome; otherwise keep going against high and critical issues until resolved.
- Medium and below can stay open in the follow-ups ticket.
- Hard cap: 6 rounds with high or critical unresolved. Then stop and give the owner findings per round, the shared cause and options: extend, defer, amend scope, cancel.

## Factory fault

A skill, the gate or the controller misbehaves, or a factory improvement shows up:

1. Document it: observed, expected, example, factory revision.
2. Open an issue in the factory's own repository asking for help. Mark it unverified.
3. Do not run `improve-factory`. The owner verifies the issue first. A session offered for it follows the skill's Delegate rule for another session, launching `improve-factory` on that issue with a factory repository checkout (never the bundle cache) instead of the project path, plus this project's absolute path and whether its run is still active. Only the owner starts it. Product bugs stay in delivery.
