# Run cases

Run rules that apply only in the case each section names.

## Lucky, verify, promote

Lucky runs the Fast steps 1, 4, a short 5 and 6, 9, 10 and 11. It asks and researches nothing and takes product bar defaults for design and schema without comparisons. UI work keeps its UX verdicts (`ux-quality` step 4).

- `verify`: manual QA of the main and failure journeys, then write and run relevant tests; no controller or independent review.
- `promote`: commit the current code as the baseline, then optionally Safe on the existing epic.

## Review loops

One round = review, fixes, fresh review.

- Apply [worth-it rounds](worth-it.md) before fixing. Mandatory findings keep the loop open; optional polish needs a worthwhile selection or an authorized finishing batch.
- After round 3, authorized optional deferrals stay in the follow-ups ticket.
- Hard cap: 6 failed rounds. Then stop and give the owner findings per round, the shared cause and options: extend, authorized deferral, amend scope, cancel.

## Factory fault

A skill, the gate or the controller misbehaves, or a factory improvement shows up:

1. Document it: observed, expected, example, factory revision.
2. Open an issue in the factory's own repository asking for help. Mark it unverified.
3. Do not run `improve-factory`. The owner verifies the issue first. A session offered for it follows the skill's Delegate rule for another session, launching `improve-factory` on that issue with a factory repository checkout (never the bundle cache) instead of the project path, plus this project's absolute path and whether its run is still active. Only the owner starts it. Product bugs stay in delivery.
