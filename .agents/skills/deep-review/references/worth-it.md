# Worth-it assessment

Attach `worth` to every finding, including check failures. Keep location/source, plain description, severity, disposition and exception authority.

| Field | Value |
|---|---|
| notice | 0 unseen in a normal demo, 1 maybe, 2 visible |
| harm | 0 none, 1 blemish, 2 confusion, 3 broken behavior, wrong data, unsafe or illegal |
| minutes | Estimated nonnegative whole minutes, or null when unknown |
| required | true for unmet criteria, mandatory rules or accessibility, broken journeys, missing required proof or UI below the journey look bar |
| reason | One plain line explaining the inputs |

Cost points: under 15 minutes = 2; 15 to under 60 = 1; 60 or more = 0. Score = notice + harm + cost, out of 7. Unknown minutes means unknown score, never zero.

1. Required, harm 3, HIGH/CRITICAL, blocking or missing/challenged proof: do now. Never park by score.
2. Optional score 5 or more: do now. Score 3 or 4: do now under an hour, otherwise Finishing touches. Score 2 or less: Finishing touches.
3. Unknown optional cost: estimate before selecting a repair. Do not invent a number.
4. Deferral still needs actual owner authority, scope, reason, revisit condition and the epic's existing follow-ups destination. Preserve before-exposure duties. Never auto-drop a finding.
5. Before fixing, select each finding in the gate's fix round. A mixed round does not smuggle in low-value polish. An explicit owner-authorized finishing batch may select it.

Report parked work by description, score or unknown, and reason. Put source and destination links separately. A score is a priority judgment, not observed time, proof or permission.
