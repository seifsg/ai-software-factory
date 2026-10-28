# Run metrics (reference)

Contents: store, events, reports, budget, privacy.

Local analytics for factory runs. Full detail: repository `docs/run-metrics.md`.
Distinct from owner-reports and evaluation harnesses.

## Store

`.factory/metrics/<run-key>/`: `events.jsonl`, `meta.json`, `report.json`, `report.md`.
Gitignored. Export and delete via `fast_gate.py metrics`.

## Emit rules

- Schema field `metrics_schema` (integer).
- IDs: `event_id`, optional `parent_id`; duplicates do not double-count.
- Types: run/phase/operation/wait lifecycle, `reuse`, `invalidate`, `coverage_gap`, `cost`.
- Instrument existing owners only; no model polling.
- Failure-open: analytics faults become coverage gaps, never fail delivery.

## Report fields

`elapsed_seconds`, `summed_operation_seconds`, `overlap_seconds`, wait totals,
reuse/invalidation, `coverage_gaps`, `incomplete_spans`, optional host `costs`
with provenance. `metrics usage --file` reads a host record already on disk
(Claude `cost-state`). Dollars are host-reported, or estimated only from a
complete `--rates` card. No record: unavailable. Never name a field CPU time
without CPU measurement.

## Budget

Append pair p99 ≤ 10 ms; report ≤ 200 ms at ≤ 10k events; whole-run ≤ 1% wall
or ≤ 2 s when wall < 200 s. See `OVERHEAD_BUDGET` in `safe_engine/run_metrics.py`.
