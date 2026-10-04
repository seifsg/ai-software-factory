# Software efficiency from the first plan

Plan resource costs early across games, clients, services and tools. Analysis-only stays analysis-only.

New products: significant workloads. Existing changes: affected costs/consumers and supported fixes; record wider gaps. Small copy/input fixes need no profiling/cache retrofit.

## Analyze cost; choose the smallest sound design

Trace `trigger → work → result → release`: size, frequency, concurrency, hardware/runtime, resource owner. Include startup, active use and idle/background work. Source can prove repetition; speed/memory claims need runtime evidence.

In original/revised plans, record `workload → target → cost → decision/reason → bound/lifetime → evidence/unknown`.

Mark targets measured/provisional; choose within delegation and verify before claiming success. Use workload-specific complexity/latency, not universal O(1) or per-function benchmarks. Research material unknowns through [Research Market](../../research-market/SKILL.md).

| Area | Inspect when applicable |
|---|---|
| CPU/concurrency | Algorithms, data layout/locality, repeated scans/setup, allocations/copies, hot loops, scheduling, batching/synchronization. Keep heavy work off interaction threads; bound queues/parallelism. |
| GPU/games/graphics | Separate CPU/GPU frame time, pacing/spikes, draw calls, overdraw, shaders, streaming, simulation/physics, GPU memory. Representative hardware/scenes; averages hide stalls. |
| Memory/lifetime | Peak/retained memory, buffers/caches/leaks, GC, worker/connection pools, subscriptions/ownership. Weigh warm reuse against residency; lazy-init/dispose where useful. Release on cancellation/replacement/exit. |
| Database/queries | Actual plans, representative data, N+1, scans/indexes/selectivity/pagination, transactions/locks, connection bounds, index write/storage costs. Execution-based plans may run writes/costly work; no destructive production probes. |
| Network | Round trips/waterfalls, payloads, compression tradeoffs, deduplication, streaming, timeouts/backoff, offline/reconnect. Preserve ordering/idempotency/authorization. |
| Storage | Read/write volume/amplification, serialization, file/asset size, buffering/atomicity, migrations, full-disk failure, retention/recovery. Preserve correctness. |
| Interaction/background | Input latency, rendering/startup/loading, battery/thermal limits, timers/polling/idle work. Prefer events; pause hidden work when valid. CLI/API: responsive output, backpressure, usable errors. |

Justify N/A; invent no infrastructure. Remove work before caching. Reuse adequate facilities; batching/indexes/pools/coalescing solve different problems. Semaphores serialize; they do not reuse results.

Cache when savings justify validity/memory/complexity costs. Explain rejected opportunities/necessary uncached work. No exhaustive precomputation, distributed services, deployment changes or spending without authority.

Distinguish duplicate computation from duplicate user effects. Never replay side effects, suppress intentional repeated commands or treat cached tool/model output as authority. Trace operation identity/intent. Cheap one-off work may stay uncached.

## Contract for each cache or expensive reused result

Keep decisions beside plan/code; use an adequate library.

| Concern | Require |
|---|---|
| Identity/validity | All result-changing inputs, settings/versions and user/access scope. Invalidate source/model/config changes. TTL alone proves neither freshness nor authorization. Keep boundary integrity checks; file metadata may be insufficient. |
| Capacity/lifetime | Bound entries, inputs/outputs, retained bytes, keys/copies and in-flight work. Define eviction/disposal and process/session/disk lifetime. TTL/dictionaries alone cannot bound memory. |
| Ownership/privacy | Private content stays in memory by default. Persistence needs product purpose, protected retention/deletion. No credentials/cross-user reuse. Immutable/copy/lease ownership prevents consumer corruption. Never log raw keys/prompts/audio/private payloads. |
| Concurrency/cancellation | Bound/coalesce valid work. One cancelled waiter cannot cancel others. Release abandoned work where supported; old work cannot refill invalidated generations. |
| Failure/cold path | No partial/failed/cancelled result as success. Negative caching needs expiry/recovery. Miss/eviction/corruption/outage reaches a bounded correct primary path or actionable error. No retry storms/blocked exit. |

Generated media: separate generation reuse from playback/delivery; key all content-changing inputs and verify disposal. This grants no context-dependent model-reply caching or skipped integrity checks.

## Evidence and handoff

Follow [tests-last order](../../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests): finish implementation → manual use → final automated checks/benchmarks. Reuse valid unchanged evidence. Changed caching/reuse: cold/warm and changed inputs/versions, bounds/disposal, failures, concurrency/cancellation, disabled cache and enough distinct inputs for eviction. Separate manual/automated evidence. Check correctness/user effects alongside avoided calls; faster stale/wrong results fail.

Count avoided work. Measure representative timing, CPU/GPU, allocation/retention or query/network/storage costs supporting claims. Include resident-work idle/release, workload/environment and cold/warm conditions. Fake dependencies prove mechanics, not production speed/memory. Percentages need comparable baselines. Report limits/unmet targets.

Use [logging](app-diagnostics.md) for safe counts/timings/cache events; bounded targeted verbosity, breadcrumbs/loss markers, no default frame flood. Review real call sites. Handoff decisions, measurements, provisional targets and limits. One path proves no whole-product optimization.
