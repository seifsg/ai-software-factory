# Mandatory application logging

Every app/game/service/tool needs a working shared logging module: any language/platform, new/existing, small fixes included. Reuse an adequate module or create it. An SDK, scattered console messages or unused wrapper is insufficient. Standalone analysis stays read-only; record missing logging.

## Choose the destination

Inspect existing logging, preferences and authorized integrations; reuse answers. Unknown preference? Ask about the owner's provider, e.g. PostHog/Datadog. Request missing project/region/access through secure host credential/integration tools, never secrets in chat. Verify log ingestion and read/search access; analytics events or installed SDKs prove neither.

No provider, pending answer or missing access: use an internal module with working local/platform output now. Keep the preferred provider pending. Reuse authorized access; record gaps. No silent vendor switch, purchase or new remote collection.

Prefer a thin app module over a maintained native logger; provider SDK/OTLP adapters when supported/useful. Research actual language/engine/runtime/deployment; check license, maintenance, versions, security and cost. Prefer versioned packages over copied repositories. No cross-language logging engine or forced collector. [Research basis](../../../../docs/skill-provenance.md#mandatory-logging-research--4-october-2026).

## Cover the application

Wire bounded diagnostics into the first useful journey. Optional providers/dashboards must not delay it. Required coverage stays; verify emitted trails at final manual QA.

New products: plan logging before features; wire from startup. Existing products: inspect coverage, reuse facilities, fill missing module/boundaries. Mandatory logging stays in surgical scope; use shared middleware/hooks, no unrelated restructuring. Record legacy gaps/impact; one changed path cannot prove complete coverage.

Keep one map: `area/journey → start/success/failure events → source/sink → evidence → gap`.

| Area | Record |
|---|---|
| Lifecycle/configuration | Build/runtime/platform, startup/init, config validation, dependency availability, shutdown/cleanup. |
| Journey | Intent, entry, prior steps/state, transitions, validation/rejection, success, cancellation/recovery. Infer intent from observed actions; label inference. |
| Functions/background | Component, file/line/function, operation, named inputs, branches, output, jobs/queues, permissions, resource acquisition/release, handled/unhandled exceptions. |
| Network/providers | Operation/route, parameters, response/status, latency, timeout, attempt, retry/backoff, fallback/cancellation. Correlate caller/downstream work. |
| Files/documents/data | Logical name/path, operation, declared/detected type, size, encoding/parser/version, validation, read/write/save/migration/conflict/recovery. |
| Database | Query/template, bound names/types/values, transaction, duration, affected rows, result/outcome. Apply safe-detail rules below before emission. |
| Games/resources | Scene/entity/job, input/state transitions, asset loading, simulation failures, frame/resource anomalies/recovery; correlate CPU/GPU/memory evidence. |

Log successes and failures. Use supported trace/debug/info/warn/error/fatal; severity differs from outcome. Investigate unexpected warnings. Logging never replaces error handling.

## One readable trail

The module owns structured events, context propagation, sanitization, levels, sinks/configuration. Provide human-readable and machine-readable views.

- **Identity/order:** UTC time, sequence/duration, severity, stable event name, outcome, app/build/environment, component, real file/line/function. Invent no locations.
- **Journey:** opaque session/action/operation IDs, trace/span/parent IDs, prior steps, attempted action, before/after state. Propagate across async work, threads/jobs/services; isolate concurrent users. Bounded breadcrumbs preserve error lead-up.
- **Detail:** named values/types, validation, expected/actual results, output, error type/code/message, sanitized stack/causes, retries/recovery. Mark missing/redacted/truncated fields. One trail should explain what, where, inputs and failure cause.
- **Reproduction:** complete safe queries, separate bindings and safe inputs/outputs within explicit size limits. No SQL-secret interpolation or object dumps. Bad character: escaped value/code point, position, encoding/normalization. Document mismatch: declared/detected MIME/extension, parser, size, rejection. Use harmless reproductions for private content; preserve diagnostic types/shapes/reasons through redaction.
- **Sensitive detail:** never passwords, keys/tokens, cookies, authorization headers or connection credentials. Redact before every sink, local buffer and SDK auto-capture. Private documents/messages, personal data/full bodies require explicit scoped diagnostic authority, minimum content, restricted access and short retention; no automatic upload. Prefer synthetic inputs. Check URLs/paths/stacks/queries for embedded data. Mark omissions; redaction cannot promise exact payload recovery.

## Keep logs usable

Replacing or restoring state? Reset affected counters, timers, caches and diagnostics. Check no stale state survives.

Libraries emit through caller-configured hooks/sinks; no global setup/files on import. The app configures the destination. Standalone library work supplies the contract and demonstrates real consumer use; create no unrelated host app.

Use local files, platform storage or captured stdout with discovery/filtering/retention. Browser/mobile/sandbox storage/export must fit actual capabilities. Owner and agent need severity/time/operation/journey search, exact access steps and sanitized export.

Bound event/body/stack size, queue/memory/disk, retention and retries. Escape untrusted text against forged lines. Async/batched writes and lazy serialization must keep input/frames responsive. Use targeted verbose diagnostics for function/hot-loop detail. Keep operational successes, warnings/errors and failure breadcrumbs; aggregate/rate-limit repeated frame/poll events with counts and dropped/truncated markers. Disclose lost coverage.

Logger init/serialization/writes/rotation/export/full disk must not crash, recurse, stall or block exit. Provide bounded fallback and logger-health visibility; retain local diagnostics during provider outages where supported. Report lost/unsaved records; preserve original failures and the owner's unsaved-work choice.

## Read logs while working

During development: inspect source and existing info/warn/error/debug trails; correlate and fix surgically. Once implementation/improvements finish, perform final manual actions and read their new trails; fix defects and recheck affected actions before final automation.

After implementation, manually exercise success/failure, invalid input/type and applicable retry/cancel/recovery with harmless data. Can the trail explain failure without guessing? Where changed, exercise missing/offline sinks and retention/redaction. Disclose unavailable paths; fix gaps and repeat affected actions.

Final tests follow [tests-last order](../../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests). Review real event sites/emitted records, not module presence. Handoff: module/backend, access status, location/query, correlation example, observed coverage, redactions/bounds, gaps/evidence. Instructions install no instrumentation or host enforcement.
