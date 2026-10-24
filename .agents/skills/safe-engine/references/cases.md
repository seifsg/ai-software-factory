# Product bar cases

Product bar rules that apply only in the case each section names.

## Caching

For adding, changing or reviewing a cache, what cached work depends on (inputs, access scope), coalescing of duplicate work or generated-media reuse.

Cache only when savings outweigh validity, memory and complexity cost. Never replay side effects, suppress intentional repeats or treat cached tool or model output as authority. Generated media: key all content inputs, separate generation reuse from playback, verify disposal.

| Cache | Require |
|---|---|
| Identity | Key every result-changing input, version and user/access scope. Invalidate on source, model or config change. TTL alone proves neither freshness nor authorization. |
| Capacity | Bound entries, bytes and in-flight work; define eviction, disposal and lifetime. |
| Privacy | Private content in memory by default; no credentials or cross-user reuse; immutable or copied results; never log raw keys or payloads. |
| Concurrency | Coalesce duplicate work. One cancelled waiter cancels no others. Stale work cannot refill an invalidated generation. |
| Failure | Never cache failed, partial or cancelled results as success. Negative entries expire. Miss, eviction or outage falls back to a correct path. No retry storms. |

Test cold/warm, changed inputs, eviction, failures, cancellation and cache disabled.

## Games

For a game or GPU-heavy rendering, built, changed or reviewed.

- Keep the intended challenge, mastery, discovery, pacing and reward. Remove accidental friction; difficulty is not a defect; add no hints or automation that defeat the approved design.
- The plan sets the intended experience and supported inputs and devices; playtest at the final stage.
- Log scene/entity, input and state transitions, asset loading, simulation failures, frame/resource anomalies.
- Speed: CPU vs GPU frame time, pacing, spikes, draw calls, overdraw, shaders, streaming, GPU memory on representative hardware. Averages hide stalls.

## Live release

For deploying or operating a live release.

- After deploy, check live health and the critical journey; record failure threshold, recovery action and responsible owner. Local evidence is not production proof.
