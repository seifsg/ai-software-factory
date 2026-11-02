# Performance

One question: will real usage cause jank, dropped frames, stalls, slow queries, memory growth, or wasted CPU, GPU, network, storage or battery?

Only performance. Ignore style, security and product fit unless they cause a performance problem. Read changed code and surroundings: callers, loops, rendering, queries, effects, resource lifetimes. Trace `trigger -> work -> result -> release`: size, frequency, concurrency, runtime, resource owner. Cover startup, active use, idle/background work.

## Rendering and updates (where present)

- Update storms: state changes redraw large trees/scenes or reschedule work. Unstable identities defeat reuse; broad subscriptions invalidate unrelated consumers.
- Expensive work repeated per render, frame, entity or row.
- Large lists/scenes without virtualization, culling or level of detail; unstable keys on reorderable data; poor size estimates; layout thrash.
- Games/graphics: CPU vs GPU frame time, pacing and spikes, draw calls, overdraw, shaders, streaming, physics, GPU memory. Averages hide stalls.

## Loops, threads and concurrency

- Heavy synchronous parsing, crypto, media, simulation or I/O blocking a critical loop or interaction thread. Check chunking, offloading, thread affinity, worker/bridge overhead.
- Input, gesture, animation and frame handlers over budget; work on wrong thread.
- Algorithms and data layout: repeated scans or setup, allocations and copies in hot loops.
- Serial independent work = waterfalls. Unbounded parallelism = contention, overload or memory spikes. Respect ordering, cancellation, limits.
- Busy polling, timers, duplicate tasks, unbounded queues, missing backpressure, locks, starvation. Prefer events; pause hidden work when valid.

## Data, network, database and storage

- Query/cache keys missing inputs or identity; refetch storms or stale results; pages, entries and retries growing without bounds.
- Duplicate fetches, N+1 queries, sequential independent requests; payloads beyond consumer need.
- Upload/download concurrency, chunking, timeouts, retries, backoff fit bandwidth, memory and provider limits. Preserve ordering, idempotency, authorization.
- Repeated storage reads on hot paths; full scans, missing indexes, unbounded fetches, excess round trips, transaction/lock contention, pool exhaustion. Read actual query plans on representative data. No destructive production probes.
- Disk I/O, write amplification, file handles, retained temporary data, storage growth.

## Memory, assets and startup

- Leaks, retained listeners/resources, allocation churn, GC pauses, oversized buffers. Release on cancel, replace and exit.
- Oversized images/textures/media; repeated decoding or conversion; thumbnails on a critical path.
- Eager heavy dependencies/assets that could load on demand; cold start, package size, warm-path latency.

## Caches and reused results

Remove work before caching. Cache only when savings justify validity, memory and complexity costs. Each cache needs:

- Identity: every result-changing input, setting, version and user/access scope. TTL alone proves neither freshness nor authorization.
- Bounds: entries, retained bytes, in-flight work; eviction, disposal, lifetime.
- Ownership: private data stays in memory by default; no credentials or cross-user reuse; no raw keys or private payloads in logs.
- Concurrency: coalesce valid duplicate work. One cancelled waiter cannot cancel others. Old work cannot refill an invalidated generation.
- Failure: no partial, failed or cancelled result stored as success. Negative entries expire. Miss, eviction or outage falls back to a bounded correct path. No retry storms or blocked exit.

Duplicate computation is not a duplicate user effect: never replay side effects or suppress intentional repeated commands.

## Calibrate

- Use realistic volume, concurrency, devices and latency/frame budgets. Workload-specific complexity, not universal O(1) claims.
- Label measured vs estimated, with workload, environment, cold/warm conditions and method. Source proves repetition; speed and memory claims need runtime evidence. Fake dependencies prove mechanics, not production speed. Percentages need a comparable baseline.
- A loop over 3 items is not an emergency. Demand no caching/memoization where cost is trivial.
- Required queries, synchronization and platform work may be load-bearing. Mark **KEEP** with a reason. Necessary cost is not waste. Faster stale or wrong results fail.

## Output

Findings use SKILL.md format, most severe first. Severity: CRITICAL freeze, OOM or unusable latency at real use. HIGH clear regression at scale. MEDIUM wasteful, fix soon. LOW minor. Impact: what degrades, at what scale, load and target environment.

End with: `PERFORMANCE VERDICT: <clean | minor | regression-risk | blocker> - <one sentence>`. Found nothing real: say so plainly.
