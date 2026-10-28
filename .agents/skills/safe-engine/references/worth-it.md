# Worth-it repair rounds

Use `deep-review`'s assessment for every finding. Keep required quality and owner authority; optional polish may wait in the epic's existing follow-ups ticket.

1. Keep complete JSON `findings`: `location`, plain `description`, `severity`, `disposition`, `exception`, `worth`; clean reports use an empty list.
2. `worth` holds `notice` (0..2), `harm` (0..3), `minutes` (whole nonnegative estimate or null), `required` (boolean), `reason` (one line). Cost points are 2 under 15 minutes, 1 under 60, else 0; score is notice + harm + cost. Null cost stays unknown.
3. Required work, harm 3, HIGH/CRITICAL, blocking findings and missing/challenged proof are mandatory. Optional score >=5, or 3..4 under an hour: do now. Other optional work waits for Finishing touches. Estimate unknown optional cost before a fix round.
4. Park only with owner authority, reason, scope, revisit and `destination` in `exception`, in the epic's one existing follow-ups ticket. Low scores grant no consent; missing requirements stay open.
5. Batch known required/worthwhile findings from one report before final QA/media. Run `fast_gate.py fix-round --project <abs> --file <report.json> --finding F1 [--finding F2]`; IDs follow report order. Preserve its receipt. The gate rejects low-value optional selections and reopens build. New failures need diagnosis and selection.
6. For an explicitly requested finishing batch add `--finishing-authority "<owner instruction and source>"`. Select its whole agreed scope once; finish the batch, use it, then run one final test pass for that candidate. A failure or changed input needs repair and fresh affected proof. Only the owner cancels it.
7. Done-run: `**Findings:** none` only for clean checks with no repair rounds; otherwise name the final scored JSON. Reconcile every prior finding once by `report_sha256`/`finding`: `retained` names an unchanged `current_finding`; `resolved` adds actual `evidence`; `cancelled` adds `owner`, `authority` (instruction/source), `reason`. Selected findings need resolution or owner cancellation; Safe FAIL may retain them. Duties and remaining criteria survive retention/cancellation. Never invent proof. Show parked facts plainly, links separate.

After required criteria/checks pass, hand off. No speculative lenses, media variants or negative-control quotas. More work needs changed inputs, observed failure or owner request. Required/severe findings stay mandatory; parking still needs step 4 authority.

Safe: `repair --finding F1` selects from the recorded review; before review or after a clean review add `--findings <report.json>`. `--finishing-authority` is unchanged. Old runs keep validation; new complete-cycle runs need scores. Authority declarations are not authentication.
