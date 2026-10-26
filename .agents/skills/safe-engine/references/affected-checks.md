# Affected checks

New suite-policy runs: after completed-item use, `feature-check --checks <ids> --file <json>` runs fewer than all configured checks. Use the manual observation shape in [the controller](controller.md#evidence) with `candidate: status.feature_candidate`, `version: 1`, `item`, `completed: true` and a changed-file `mapping`. Supply fresh item observations and evidence, never carried final QA. Failed feedback needs repair. It does not advance Build or replace final manual, contract or complete-suite gates. Older states retain their prior restriction.
