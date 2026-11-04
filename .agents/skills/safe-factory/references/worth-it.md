# Worth-it repair rounds

Use `deep-review`'s assessment for every finding.

1. Keep complete JSON `findings`: `location`, plain `description`, `severity`, `disposition`, `exception`, `worth`; clean reports use an empty list.
2. `worth` holds `notice` (0..2), `harm` (0..3), `minutes` (whole nonnegative estimate or null), `required` (boolean), `reason` (one line). Cost points are 2 under 15 minutes, 1 under 60, else 0; score is notice + harm + cost. Null cost stays unknown.
3. Required work, harm 3, HIGH/CRITICAL, blocking findings and missing/challenged proof are mandatory. Optional score >=5, or 3..4 under an hour: do now. Other optional work waits for Finishing touches. Estimate unknown optional cost before a fix round.
4. Park only with owner authority, reason, scope, revisit and `destination` in `exception`, in the epic's one existing follow-ups ticket. Low scores grant no consent; missing requirements stay open.
5. Batch known required/worthwhile findings of one report before final QA/media; fix as one round; low-value optional not selected. New failures: diagnose, select.
6. Owner-requested finishing batch: record instruction and source. Select whole agreed scope once; finish, use it, one final test pass on that candidate. Failure or changed input: repair, fresh affected proof. Only owner cancels.
7. Verify block: `Findings: none` only for clean checks with no repair rounds; otherwise name the final scored JSON. Reconcile every prior finding once: `retained` names the unchanged current finding; `resolved` adds actual `evidence`; `cancelled` adds `owner`, `authority` (instruction/source), `reason`. Selected findings need resolution or owner cancellation; Safe FAIL may retain them. Duties and remaining criteria survive retention/cancellation. Never invent proof. Show parked facts plainly, links separate.

Required criteria/checks pass: hand off. No speculative lenses, media variants or negative-control quotas. More work needs changed inputs, observed failure or owner request.
