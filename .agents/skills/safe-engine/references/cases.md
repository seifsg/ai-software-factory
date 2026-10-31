# Product bar cases

Product bar rules for the case each heading names; `product-bar.md` points to each.

## Caching

Cache only when savings outweigh validity, memory and complexity cost. Never replay side effects, suppress intentional repeats or treat cached tool or model output as authority. Generated media: key all content inputs, separate generation reuse from playback, verify disposal.

| Cache | Require |
|---|---|
| Identity | Key every result-changing input, version and user/access scope. Invalidate on source, model or config change. TTL alone proves neither freshness nor authorization. |
| Capacity | Bound entries, bytes and in-flight work; define eviction, disposal and lifetime. |
| Privacy | Private content in memory by default; no credentials or cross-user reuse; immutable or copied results; never log raw keys or payloads. |
| Concurrency | Coalesce duplicate work. One cancelled waiter cancels no others. Stale work cannot refill an invalidated generation. |
| Failure | Never cache failed, partial or cancelled results as success. Negative entries expire. Miss, eviction or outage falls back to a correct path. No retry storms. |

Test cold/warm, changed inputs, eviction, failures, cancellation and cache disabled.

## Speed checklist

- CPU: algorithms, data layout, repeated scans, allocations, hot loops. Heavy work off interaction threads; bound queues and parallelism.
- Memory: peak and retained memory, leaks, pools, subscriptions. Release on cancel, replace and exit.
- Database: real plans on representative data, N+1, indexes, pagination, locks, connection bounds, index write cost. No destructive production probes.
- Network: round trips, payload size, dedupe, streaming, timeouts/backoff, offline. Keep ordering, idempotency and authorization.
- Storage: write amplification, asset size, atomic writes, migrations, full disk.
- Interaction: input latency, startup, battery, polling. Prefer events; pause hidden work. CLI/API: responsive output, backpressure, usable errors.

## External effects

- Record `operation identity → durable state → effect → completion/reconciliation owner`.
- Cover pending, success, failure and unknown outcomes; commit/effect order; ambiguous timeouts; duplicate or out-of-order delivery; bounded retry with backoff; cancellation; safe replay.
- A database commit, sent request or signed webhook does not prove the business effect happened.
- Choose once the smallest adequate mechanism: provider idempotency and reconciliation, a durable pending record, a transactional outbox or a workflow engine. No universal queue.
- Webhooks: after the signature check ([security](product-bar.md#security)), freshness and replay checks; dedupe; idempotent retries. Never trust unsigned payloads or IP allowlists alone.
- Final manual QA uses safe disposable operations, including interruption and retry. Read correlated logs and preserve unresolved effects before retrying.

## Games

- Keep the intended challenge, mastery, discovery, pacing and reward. Remove accidental friction; difficulty is not a defect; add no hints or automation that defeat the approved design.
- The plan sets the intended experience and supported inputs and devices; playtest at the final stage.
- Log scene/entity, input and state transitions, asset loading, simulation failures, frame/resource anomalies.
- Speed: CPU vs GPU frame time, pacing, spikes, draw calls, overdraw, shaders, streaming, GPU memory on representative hardware. Averages hide stalls.

## Live release

- After deploy, check live health and the critical journey; record failure threshold, recovery action and responsible owner. Local evidence is not production proof.
- One release record: reviewed build artifact, target environment and config, required services and secrets, migration and app ordering, compatible clients and data, rollback or roll-forward, backups with a usable restore. Attach security, UX, SEO and integration evidence.
- Operations: log access, failure, stalled-job and capacity signals, an authorized destination and operator, retention and recovery. Reuse existing facilities; no automatic paid monitor, new notifications or perpetual polling.
