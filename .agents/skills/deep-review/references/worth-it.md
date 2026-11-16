# Worth-it assessment

Attach `worth` to every finding, including check failures. Keep complete JSON `findings`: `location`, plain `description`, `severity`, `disposition`, `exception` (authority), `worth`; a clean report uses an empty list.

| Field | Value |
|---|---|
| notice | 0 unseen in a normal demo, 1 maybe, 2 visible |
| harm | 0 none, 1 blemish, 2 confusion, 3 broken behavior, wrong data, unsafe or illegal |
| minutes | Estimated nonnegative whole minutes, or null when unknown |
| required | true for unmet criteria, mandatory rules or accessibility, broken journeys, missing required proof or UI below the journey look bar |
| reason | One plain line explaining the inputs |

Cost points: under 15 minutes = 2; 15 to under 60 = 1; 60 or more = 0. Score = notice + harm + cost, out of 7. Unknown minutes = unknown score, never zero.

1. Required, harm 3, HIGH/CRITICAL, blocking or missing/challenged proof: do now. Never park by score.
2. Optional score 5 or more: do now. Score 3 or 4: do now under an hour, otherwise Finishing touches. Score 2 or less: Finishing touches.
3. Unknown optional cost: estimate before selecting a repair. Invent no number.
4. Deferral still needs actual owner authority, scope, reason, revisit condition and the epic's existing follow-ups destination, in `exception`. Preserve before-exposure duties. Missing requirements stay open. Never auto-drop a finding.
5. Before fixing, select each finding in the gate's fix round. Batch one report's known required and worthwhile findings before final QA and media; fix them as one round. A mixed round does not smuggle in low-value polish. New failures: diagnose, select.
6. Owner-requested finishing batch: record instruction and source. Select whole agreed scope once; finish, use it, one final test run on that candidate. Failure or changed input: repair, fresh affected proof. Only owner cancels.
7. Verify block: `Findings: none` only for clean checks with no repair rounds; otherwise name the final scored JSON. Reconcile every prior finding once: `retained` names the unchanged current finding; `resolved` adds actual `evidence`; `cancelled` adds `owner`, `authority` (instruction/source), `reason`. Selected findings need resolution or owner cancellation; Safe FAIL may retain them. Duties and remaining criteria survive retention/cancellation. Never invent proof.

Required criteria and checks met: hand off. No speculative lenses, media variants or negative-control quotas. More work needs changed inputs, observed failure or owner request.

Report parked work by description, score or unknown, and reason, plainly. Put source and destination links separately. Score = priority judgment, not observed time, proof or permission.
