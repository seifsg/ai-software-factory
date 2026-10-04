# Mandatory application logging

Every app, game, service and tool must have a working shared logging module. New or existing; any language/platform; small fixes included. Reuse an adequate module or create the missing internal module. An installed SDK, scattered console messages or an unused wrapper is not enough. Standalone analysis stays read-only and records missing logging.

## Choose the destination

Inspect existing logging, project preferences and authorized integrations first. Reuse recorded answers. If preference is unknown, ask whether the owner uses a provider such as PostHog or Datadog. If yes, request missing project/region and access through the host's secure credential/integration flow; never ask for secrets in chat. Verify actual log ingestion and read/search access, not just analytics events or an installed SDK.

No provider, pending answer or unavailable access: build/use the internal module with a working local/platform destination now. Missing cloud access cannot leave the app without logs. Keep the selected provider pending; do not silently switch vendors, buy services or enable new remote collection. Use existing authorized access; record remaining access needs.

Prefer a thin application module over a maintained native logger; add provider/OTLP adapters when useful and supported. Research the actual language, engine, runtime and deployment before choosing. Check license, maintenance, supported versions, security and cost; prefer a versioned package over copying a random repository. A provider SDK can back the same module. Do not write a cross-language logging engine or force a collector into a small app. See [research basis](../../../../docs/skill-provenance.md#mandatory-logging-research--4-october-2026).

## Cover the application

New products: plan logging before feature work and wire it from startup. Existing products: inspect coverage, reuse adequate facilities, fill the missing module and wire relevant boundaries. Mandatory logging is part of delivery scope, including surgical fixes; use shared middleware/hooks to avoid unrelated restructuring. A tiny fix does not exempt the module. Record legacy coverage gaps and their impact; never claim complete coverage from the changed path alone.

Use one record:

`area/journey → start/success/failure events → source/sink → evidence → gap`

| Area | Record |
|---|---|
| Lifecycle/configuration | Build/runtime/platform, startup, initialization, configuration validation, dependency availability, shutdown and cleanup. |
| User/consumer journey | Intended action, entry point, prior steps/state, transitions, validation/rejection, successful outcome, cancellation and recovery. Infer intent only from observed actions; label inference. |
| Functions/background work | Component, source file/line/function, operation, named inputs, relevant branches, output, jobs/queues, permissions, resource acquisition/release and handled/unhandled exceptions. |
| Network/providers | Request operation/route, parameters, response/status, latency, timeout, attempt, retries/backoff, fallback and cancellation. Link caller and downstream work. |
| Files/documents/data | Logical file name/path, operation, detected/declared type, size, encoding/parser/version, validation, read/write/save/migration/conflict and recovery. |
| Database | Query/template, bound parameter names/types/values, transaction, duration, affected rows and result/outcome. Apply the detail rules below before emission. |
| Games/resources | Scene/entity or job identity, input/state transitions, asset loading, simulation failures, frame/resource anomalies and recovery; correlate with CPU/GPU/memory evidence. |

Log successes as well as failures. Use trace/debug/info/warn/error/fatal as supported; severity and outcome are separate. Treat unexpected warnings as evidence to investigate. Never swallow an error because it was logged.

## One readable event trail

The module owns structured events, context propagation, sanitization, levels, sinks and configuration. Keep a human-readable view plus machine-readable records.

- **Identity/order:** UTC timestamp, sequence/duration, severity, stable event name, outcome, app/build/environment, component and source file/line/function. Capture real locations; never invent them.
- **Journey:** opaque session/action/operation IDs, trace/span or parent IDs, previous steps, attempted action and before/after state. Propagate context across async work, threads/jobs and services; keep concurrent users isolated. Bounded breadcrumbs preserve the lead-up to an error.
- **Detail:** named parameters with values/types, validation decision, expected versus actual result, output, error type/code/message, sanitized stack/cause chain, retries and recovery. Record missing, redacted or truncated fields explicitly. One trail should explain what happened, where, with which inputs, and why it failed.
- **Exact reproduction:** preserve complete non-sensitive queries, separate bindings and safe inputs/outputs within explicit size limits. Do not interpolate secrets into SQL or dump whole objects. For a bad character, capture escaped value/code point, position, encoding and normalization; for a document mismatch, capture declared/detected MIME/extension, parser, size and rejection reason. Use minimal harmless reproductions when real content is private. Redaction must preserve diagnostic types/shapes/reasons.
- **Sensitive detail:** never log passwords, API keys, tokens, cookies, authorization headers, private keys or connection credentials. Redact before every destination, including local buffers and SDK auto-capture. Private documents/messages, personal data and full bodies need scoped diagnostic capture with explicit owner authority, minimum necessary content, restricted access and short retention; no automatic upload. Prefer synthetic inputs. Inspect URLs, paths, stacks and queries for embedded data. Mark omissions; do not promise exact payload recovery after redaction.

## Keep logs usable

Libraries emit through caller-configured hooks/sinks; no global setup or files on import. The consuming app must configure a working destination. Standalone library work delivers the integration contract and demonstrates real consumer use; it does not create a host app as unrelated scope.

Provide local files, platform storage or captured stdout with working discovery, filtering and retention. Browsers/mobile/sandboxed runtimes use supported storage/export; do not assume filesystem access. Owner and agent must be able to inspect logs by severity, time and operation/journey ID. Give exact access steps and a sanitized export path.

Bound event/body/stack size, queue/memory/disk, retention and retries. Escape untrusted text to prevent forged log lines. Use async/batched writes and lazy serialization; logging must not freeze input or a game frame. Support targeted verbose diagnostics for function-level/hot-loop detail. Keep operational successes, warnings/errors and failure breadcrumbs; aggregate/rate-limit repetitive frame/poll events with counts and explicit dropped/truncated markers. Report coverage lost to limits, never silently claim exhaustive capture.

Logger initialization, serialization, writes, rotation, exports or full disks must not crash, recurse, stall the app or block exit. Provide bounded fallback and logger-health visibility. A provider outage retains local diagnostics where supported. State lost/unsaved records honestly; preserve original failures and the owner's unsaved-work choice.

## Read logs while working

During development and actual app use: inspect info/warn/error and relevant debug trails → correlate the journey → diagnose → fix the cause surgically → repeat the action and read the new trail. Logging and manual debugging run throughout development; automated tests still wait until the end.

After implementation is finished, manually exercise success, failure, invalid input/type and applicable retry/cancel/recovery paths with harmless data. Read the resulting trail: can it explain the failure without guessing? Exercise missing/offline destinations and retention/redaction behavior where changed; disclose unavailable paths. Fix gaps, then repeat affected actions.

Only after finished implementation and passing manual QA, author/polish/run relevant final tests under [tests-last order](../../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests). Review real event sites and emitted records, not module presence alone. Handoff: module/backend, access status, log location/query, correlation example, observed coverage, redactions/bounds, unresolved gaps and actual evidence. Instructions do not install instrumentation or enforce host behavior.
