# Software efficiency from the first plan

Plan resource costs early. Use this for delivery across games, clients, services and tools. Analysis-only stays analysis-only.

New products cover significant workloads. Existing changes cover affected costs/consumers and supported in-scope fixes; record wider gaps. Small copy/input fixes do not require profiling or cache retrofits.

## Analyze cost and choose the smallest sound design

Trace `trigger → work → result → release`. Record input size, frequency, concurrency, hardware/runtime and resource ownership. Include startup, active use and idle/background work. Code inspection can prove repeated work; measured speed/memory needs runtime evidence.

In the original/revised plan, use:

`workload → target → cost → decision/reason → bound/lifetime → evidence or unknown`

Mark targets measured or provisional. Select provisional targets within delegated authority; verify before claiming success. Use workload-specific complexity and latency targets, not universal O(1) or benchmarks for every function. Research current domain/stack guidance through [Research Market](../../research-market/SKILL.md) when a material choice lacks evidence.

| Area | Inspect when applicable |
|---|---|
| CPU / concurrency | Algorithms, data layout/locality, repeated scans/setup, allocations/copies, hot loops, worker scheduling, batching and synchronization. Keep heavy work off interaction threads; bound queues and parallelism. |
| GPU / games / graphics | CPU/GPU frame time separately; frame pacing/spikes, draw calls, overdraw, shaders, asset streaming, simulation/physics and GPU memory. Choose representative hardware and scenes. A good average can hide stalls. |
| Memory / lifetime | Peak/retained memory, buffers, caches, leaks, GC pressure, worker/connection pools, subscriptions and ownership. Weigh warm reuse against residency; lazy-init/dispose where useful. Release on cancellation, replacement and exit. |
| Database / queries | Actual plans and representative data; N+1 calls, scans, indexes, selectivity, pagination, transactions, locks and connection bounds. Indexes cost writes/storage. Inspect plans safely: execution-based analysis may run writes or costly work. No destructive production probes. |
| Network | Round trips, waterfalls, payload size, compression tradeoffs, request deduplication, streaming, timeouts/backoff and offline/reconnect behavior. Preserve ordering, idempotency and authorization. |
| Storage | Read/write volume and amplification, serialization, file/asset size, buffering, atomicity, migrations, free-space failure, retention and recovery. Persistence must preserve correctness. |
| Interaction / background | Input-to-result latency, rendering, startup/loading, battery/thermal limits, timers/polling and idle work. Prefer events; pause hidden work when product behavior permits. CLI/API consumers need responsive output, backpressure and usable failures too. |

Record supported N/A where a resource does not exist. Do not introduce infrastructure to fill the table. Remove unnecessary work before adding caches. Prefer adequate existing facilities; batching, indexes, pools and coalescing solve different problems. A semaphore serializes work; it does not reuse results.

Inspect useful caching. Implement when savings justify validity, memory and complexity costs. Explain rejected opportunities or necessary uncached work. Do not precompute every combination, add distributed services, change deployment or spend without authority.

Important: duplicate computation and duplicate user effects differ. Reuse must not replay side effects, suppress intentional repeated commands or treat cached tool/model output as authority. Trace operation identity and user intent. Cheap one-off work may remain uncached.

## Contract for each cache or reused expensive result

Keep decisions beside plan/code; use an adequate library.

| Concern | Require |
|---|---|
| Identity / validity | Every result-changing input, setting/version and user/access scope. Invalidate on source/model/config changes. TTL cannot establish freshness or authorization alone. Keep integrity checks at the trust boundary; file metadata may be insufficient. |
| Capacity / lifetime | Bound entries, inputs, outputs, retained bytes, keys/copies and in-flight work. Define eviction/disposal and process/session/disk lifetime. TTL or a dictionary alone is no memory bound. |
| Ownership / privacy | Private content stays in memory by default. Persistence needs a product reason and protected retention/deletion. No credentials or cross-user reuse. Define immutable/copy/lease ownership; one consumer cannot corrupt another's buffers. Never log raw keys, prompts, audio or private payloads. |
| Concurrency / cancellation | Bound work; coalesce where valid. One cancelled waiter must not cancel other valid consumers. Release abandoned work where supported. Old work cannot refill an invalidated generation. |
| Failure / cold path | Never cache partial/failed/cancelled work as success. Negative caching needs expiry/recovery. Miss, eviction, corruption or unavailability must reach a bounded correct primary path or actionable error. No retry storm or blocked exit. |

For generated media, separate generation reuse from playback/delivery; key every content-changing input and verify consumer disposal. Caching media does not justify caching context-dependent model replies or skipping integrity checks.

## Focused evidence and handoff

Follow [tests-last order](../../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests): finish implementation, manually exercise it, then author/run final automated checks and benchmarks. Reuse valid unchanged evidence. For changed reuse/cache behavior, cover cold/warm inputs, changed inputs/versions, bounds, disposal, failures, concurrent callers/cancellation, disabled cache and enough distinct inputs to exercise eviction. Record what manual use proves and what final automation adds. Check correctness and user effects alongside avoided calls. A faster stale/wrong result fails.

Use counters for avoided work; measure representative timing, CPU/GPU, allocation/retention or query/network/storage costs supporting the claim. Include idle/release evidence for resident work, workload/environment and cold/warm conditions. Fake dependencies prove mechanics, not production speed/memory. Percentage claims need comparable baselines. Report limits and unmet targets.

Use [mandatory logging](app-diagnostics.md) for safe counts/timings and cache events. No unbounded/default per-frame log flood; targeted verbose diagnostics follow the logging contract's bounds, breadcrumbs and explicit loss markers. Review actual call sites, not just the cache class. Carry decisions, measured evidence, provisional targets and unresolved limits into review/handoff. No whole-product optimization claim from one path.
