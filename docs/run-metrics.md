# Factory run metrics

Local analytical records for Fast, Lucky and Safe runs. Distinct from
[owner reports](owner-reports.md) (per-ticket spend) and from the controlled
factory-versus-agent evaluation. Data stays under ignored `.factory/metrics/`.

## Event model (`metrics_schema` 1)

Each line in `.factory/metrics/<run-key>/events.jsonl` is one event. Correlate
run, task and operation ids with optional parent links. Duplicate `event_id`
values do not double-count.

| Field | Meaning |
|---|---|
| `metrics_schema` | Integer schema version |
| `event_id` | Stable id; duplicates do not double-count |
| `parent_id` | Optional parent event |
| `type` | `run.*`, `phase.*`, `operation.*`, `wait.*`, `reuse`, `invalidate`, `coverage_gap`, `cost` |
| `t` | UTC timestamp |
| `mono_ns` | Process monotonic stamp for in-process intervals |

Track phase start, finish, failure, cancellation and resume. Record command and
check durations, full-suite queue versus execution, helper/owner/approval waits,
fresh versus reused work, retry and proof invalidation reasons. Unobservable
agent activity stays unknown rather than inferred from silence.

Run meta (`.factory/metrics/<run-key>/meta.json`) stores factory revision, mode,
kind, platform and runtime. Structured operational metadata only: no prompts,
source trees, credentials or raw environment values. Event lines are size-capped;
runs retained are capped.

### Duration semantics

- **Elapsed** (`elapsed_seconds`): end-to-end wall from first to last event UTC time.
- **Summed operations** (`summed_operation_seconds`): sum of finished operation
  intervals (prefer `mono_ns` when both ends exist).
- **Overlap** (`overlap_seconds`): time covered by more than one finished
  operation. Do not add overlap into delivery time.
- Never label an elapsed field as CPU time without CPU measurement.
- Cross-process UTC alignment may skew; incomplete spans stay incomplete.

## API and CLI

Python (`safe_engine.run_metrics`): `emit`, `finalize`, `compare`, `export`,
`delete`, `measure_overhead`, plus `bound` / `emit_current` for nested helpers.
`finalize` writes `report.json` and `report.md` with `coverage_gaps`.

```text
python skills/safe-engine/scripts/fast_gate.py metrics report [--key <run>]
python skills/safe-engine/scripts/fast_gate.py metrics compare --keys <a> <b>
python skills/safe-engine/scripts/fast_gate.py metrics export --key <run> --dest <dir>
python skills/safe-engine/scripts/fast_gate.py metrics delete --key <run>
python skills/safe-engine/scripts/fast_gate.py metrics overhead [--key <run>] [--events N]
```

Reports: `report.json` and `report.md` in the run folder. Token/model/cost fields
appear only when a host adapter supplies attributable measurements with
provenance and units. Shared-session totals are never copied onto every ticket.

Analytics I/O faults become `coverage_gap` events (`analytics_unwritable` /
`analytics_corrupt`) and never turn a successful delivery operation into a
failure.

## Overhead budget

Agreed before implementation:

Agreed budget (plan + measured Windows NTFS revision recorded in the #175 plan):

- Event append pair p99 ≤ 10 ms
- Report generation ≤ 200 ms at ≤ 10_000 events
- Whole-run collection + reporting ≤ 1% of wall clock, or ≤ 2 s when wall < 200 s

`metrics overhead` is a single-shot measurement (with warm-up); `within_budget` checks all three rules. Approval waits are a reserved category and stay uncovered until an owner emits them. Container operations such as `full_suite` wrap per-command ops and are excluded from summed/overlap totals.
