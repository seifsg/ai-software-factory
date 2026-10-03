# App efficiency from the first plan

Plan CPU, memory and infrastructure costs early. Build useful safe reuse into the feature. Safe Engine owns this default for app delivery; no separate optimization request is needed. An analysis-only request still stops before coding.

For new apps, cover significant journeys. For existing changes, inspect affected costs and consumers, fix supported waste within scope and record wider gaps. A small input/copy fix does not require profiling or a cache retrofit. Use the selected method's plan, checks and handoff.

## Analyze cost and choose the smallest sound design

Trace `trigger → work → result → release`.

Identify repeated/expensive work, frequency, input sizes and concurrency. Who owns the memory, workers, connections, timers and subscriptions? When are they released? Include startup, active use and idle/background work where relevant. Code can prove repetition; it cannot prove measured latency, CPU or memory use. Record measurements or unknowns.

For each material operation, add one row to the original and revised plan:

`workload/target → main cost → decision/reason → resource bound/lifetime → focused evidence`

Mark targets measured or provisional. Choose reasonable provisional targets within delegated authority; verify them in the actual environment before claiming success. Do not impose one complexity target or benchmark every function.

First remove unnecessary calls, duplicate subscriptions, scans, allocations/copies and repeated setup. Then choose the useful approach: existing facilities, batching/indexing, caching, reusable workers/connections, or coalescing identical concurrent work. Serializing calls with a semaphore does not reuse results.

Weigh retained memory against startup cost. Consider lazy initialization and idle disposal. Bound queues/concurrency and response sizes. Keep expensive work off the UI thread. Stop/dispose owned resources on cancellation, replacement and Quit. Prefer events to unnecessary polling; pause invisible animation/idle work when the product allows it.

Inspect useful caching opportunities. Implement them when savings justify validity, memory and maintenance costs. Briefly explain necessary uncached work or rejected opportunities. Do not add distributed caches, precompute every combination, change deployment infrastructure or buy services just to meet this rule. Inspect actual dependency/asset size, data access, initialization and resource lifetimes.

Important: Duplicate work and duplicate user effects are different problems. Reusing audio can avoid synthesis but still play twice if two handlers fire. Trace request/event identity and user intent. Preserve intentional repeated commands. Do not repeat side effects from cached results or treat cached chat/tool output as authority. Changing, personalized or time-sensitive data needs valid freshness/access scope. Cheap one-off work can stay uncached.

## Contract for each cache or reused expensive result

Keep these decisions beside the plan/code. Reuse an adequate library.

| Concern | Decide and check |
|---|---|
| Identity and validity | Include every result-changing input, setting and version, plus user/access scope. Invalidate on source/model/config changes. TTL alone cannot detect these or authorize stale/security-sensitive results. Keep integrity checks at the real trust boundary; file metadata may not prove trusted identity. |
| Capacity and lifetime | Bound entries, inputs, outputs and retained bytes. Define eviction/disposal and process/session/disk lifetime. Count keys, buffers/copies and in-flight work. A dictionary or TTL is not a memory bound. Do not populate unbounded arbitrary-input caches. |
| Ownership and privacy | Keep private content in memory by default. Persistence needs a product reason and protected retention/deletion. No credentials or cross-user reuse. Define immutable/copy/lease ownership so one consumer cannot mutate or clear another's buffer. Do not log raw keys, prompts, audio or private payloads. |
| Concurrency and cancellation | Define coalescing, bounded independent work and cleanup. One cancelled waiter must not corrupt shared results or cancel other valid consumers. Release work when no consumers remain where supported. Prevent late old work from repopulating an invalidated generation. |
| Failure and cold path | Never retain partial/cancelled/failed work as success. Justify negative caching separately with expiry/recovery. On miss, eviction, corruption or unavailability, take a bounded correct primary path or return an actionable error. No retry storm or blocked Quit. |

For repeated speech, inspect synthesis and playback separately. Identity may need exact text, voice, model/engine revision, synthesis options and format. Check playback, consumer buffer disposal and generator call counts. A speech cache does not justify caching context-dependent LLM replies or skipping model integrity checks. This is an example, not a feature to add elsewhere.

## Focused evidence and handoff

Run relevant checks after the meaningful batch. Reuse unchanged relevant evidence. For a new/changed cache, check:
- Cold input, then identical warm input.
- A result-changing input/version.
- Applicable capacity, lifecycle and failure behavior.
- Concurrent callers and cancellation when concurrency exists.
- Semantic output and user effects, as well as avoided calls.
- Disabled/empty-cache behavior and enough distinct inputs to verify bounds.

A faster wrong/stale result fails. These checks do not require a full load suite.

Use counters to prove avoided work. Measure representative elapsed/CPU/allocation or retained-memory costs that support the claim. Include idle/release evidence for resident/background work. Record workload, environment and cold/warm conditions. A fake costly dependency can prove coalescing/invalidation, not real-model speed or production memory. Report measurements, provisional targets and limits. Percentage claims need comparable evidence.

Use [app diagnostics](app-diagnostics.md) for useful safe counts/timings and hit/miss/eviction/coalescing events. Bound sampling/aggregation; do not log every frame or hot-loop iteration. Review call sites, keys/validity, memory/ownership, failures and cancellation. A cache class alone proves nothing.

Carry decisions, demonstrated reuse/resource evidence and unresolved limits into the normal scoped handoff. Missing material evidence stays unverified. Do not add unrelated regression or claim whole-app optimization from one path.

This implements Seif's 3 October 2026 requirement. Primary guidance checked that day: [Microsoft memory caching](https://learn.microsoft.com/en-us/aspnet/core/performance/caching/memory?view=aspnetcore-10.0) covers capacity and uncached fallback; [AWS caching strategies](https://aws.amazon.com/builders-library/caching-challenges-and-strategies/) covers coalescing, cold behavior and measured sizing. Neither requires a particular runtime or hosted cache. These instructions are not an automatic optimizer or proof of app speedup.