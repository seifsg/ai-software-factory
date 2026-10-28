# Factory run metrics

Local analytical records for Fast, Lucky and Safe runs. Distinct from
[owner reports](owner-reports.md) (per-ticket spend) and from the controlled
factory-versus-agent evaluation. Data stays under ignored `.factory/metrics/`.

## Event model (`metrics_schema` 1)

Each line in `.factory/metrics/<run-key>/events.jsonl` is one event. Correlate
run, task and operation ids with optional parent links. Duplicate `event_id`
values do not double-count.
Writers hold a per-run file lock and refresh an in-memory count/ID index from
only newly appended bytes. A process restart or detected rewrite rebuilds the
index once from `events.jsonl`; the JSONL remains the source of truth. The
50,000-line cap counts corrupt lines too. A corrupt line produces a coverage
gap, and a later valid append remains readable. Concurrent writers using this
API serialize through the lock; external writes that ignore it are unsupported.

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
python skills/safe-engine/scripts/fast_gate.py metrics usage --key <run> --file <record> [--rates <card.json>]
```

Reports: `report.json` and `report.md` in the run folder. Token and dollar lines
appear only after `metrics usage --key <run> --file <host record>`. The command
refreshes the report, calls no model and scans no other sessions. It accepts
Claude Code `cost-state` records and Codex JSONL with `session_meta`,
`turn_context` and cumulative `event_msg.token_count` rows. Codex cached input
is a subset of input; reasoning output is a subset of output. Those categories
are counted once. A session with multiple models is labeled `mixed/unknown`
because its cumulative total cannot be split by model. Importing the same
snapshot twice is idempotent; a newer cumulative snapshot supersedes the older
one for that session. Separate sessions using the same model remain separate.

The host session ID is stored as a hash. When the host record lacks one, the
usage command hashes the explicitly supplied file path as a stable fallback;
moving or copying that file changes this fallback identity. Direct Python
summaries without an identity are labeled `unattributed` and are not added as
separate sessions. All imported usage is labeled `shared_session` or
`unattributed`, never assigned to individual tickets. Host `costUSD` is shown
as host-reported. A `--rates` card prices tokens only when every model and every
counted field has a rate; that figure is labeled estimated, not a bill.
Anything else stays `unavailable`.

Analytics I/O faults become `coverage_gap` events (`analytics_unwritable` /
`analytics_corrupt`) and never turn a successful delivery operation into a
failure.

## Overhead budget

Agreed budget (plan + measured Windows NTFS revision recorded in the #175 plan):

- Event append pair p99 ≤ 10 ms
- Report generation ≤ 200 ms at ≤ 10_000 events
- Whole-run collection + reporting ≤ 1% of wall clock, or ≤ 2 s when wall < 200 s

`metrics overhead` is a single-shot measurement (with warm-up); `within_budget` checks all three rules. Approval waits are a reserved category and stay uncovered until an owner emits them. Container operations such as `full_suite` wrap per-command ops and are excluded from summed/overlap totals.

On Windows 11 NTFS, a single 100-pair CLI sample with 20 warm-up pairs measured
2.001 ms append-pair p99, 23.721 ms report generation for 242 events, and
0.167 s combined collection/report time. A separate 10,000-event local sample
measured 69.453 ms report generation. These are workload measurements, not
whole-delivery savings or CPU measurements; rerun on the target machine before
comparing performance.
