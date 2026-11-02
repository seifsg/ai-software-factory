# Worth-it repair rounds

Use `deep-review`'s assessment for every finding.

1. Keep complete JSON `findings`: `location`, plain `description`, `severity`, `disposition`, `exception`, `worth`; clean reports use an empty list.
2. `worth` holds `notice` (0..2), `harm` (0..3), `minutes` (whole nonnegative estimate or null), `required` (boolean), `reason` (one line). Cost points are 2 under 15 minutes, 1 under 60, else 0; score is notice + harm + cost. Null cost stays unknown.
3. Required work, harm 3, HIGH/CRITICAL, blocking findings and missing/challenged proof are mandatory. Optional score >=5, or 3..4 under an hour: do now. Other optional work waits for Finishing touches. Estimate unknown optional cost before a fix round.
4. Park only with owner authority, reason, scope, revisit and `destination` in `exception`, in the epic's one existing follow-ups ticket. Low scores grant no consent; missing requirements stay open.
5. Batch known required/worthwhile findings from one report before final QA/media. Fix them as one round; low-value optional findings are not selected. New failures need diagnosis and selection.
6. For an explicitly requested finishing batch, record the owner's instruction and source. Select its whole agreed scope once; finish the batch, use it, then run one final test pass for that candidate. A failure or changed input needs repair and fresh affected proof. Only the owner cancels it.
7. Verify block: `Findings: none` only for clean checks with no repair rounds; otherwise name the final scored JSON. Reconcile every prior finding once: `retained` names the unchanged current finding; `resolved` adds actual `evidence`; `cancelled` adds `owner`, `authority` (instruction/source), `reason`. Selected findings need resolution or owner cancellation; Safe FAIL may retain them. Duties and remaining criteria survive retention/cancellation. Never invent proof. Show parked facts plainly, links separate.

After required criteria/checks pass, hand off. No speculative lenses, media variants or negative-control quotas. More work needs changed inputs, observed failure or owner request.
