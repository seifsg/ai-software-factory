# App diagnostics by default

Read for every new app and app change. Seif requires sufficient app-wide logs as a critical built-in component, without needing to request them separately. The goal is to reconstruct what failed, where, why, and what recovery did. Use the app's established logging facility when adequate; otherwise add the smallest shared diagnostics module appropriate to its stack. Scattered console messages alone do not establish coverage.

## Plan coverage and fill the current gap

For a **new app**, include diagnostics in the original and revised plan, implementation, checks and handoff. Map every applicable subsystem/journey below to actual event sites; record a supported reason for an inapplicable area. Implement this as part of the app, not a later optional feature.

For an **existing app**, inspect its current logger, sinks and real event sites before adding another mechanism. Make a compact app-wide inventory of covered, missing and unknown areas from the actual entrypoints/subsystems; do not infer coverage from a logger's existence. Automatically add an absent minimum shared module and missing events for the changed journeys and directly affected consumers. This is part of the authorized change, including a small feature or fix. Preserve the selected lightweight method: no full rewrite, unrelated instrumentation sweep or automatic broad regression. Record app-wide gaps outside the current patch with their impact and next step; never label the whole app sufficiently covered until evidence supports it. A real scope/authority boundary is reported rather than silently expanded.

Keep the coverage map in the existing plan/change record: area/journey → source/event sites → useful safe context → check/evidence → gap or supported N/A. One compact record suffices; no new controller schema, task tree or reporting ceremony.

| Applicable area | Events needed to explain failures and recovery |
|---|---|
| Lifecycle and configuration | Startup/build identity, initialization/configuration validation outcomes, dependency availability, shutdown and cleanup results; safe state flags rather than configuration values |
| User actions and state | Significant commands/navigation and state transitions, validation/rejection, cancellation and resulting UI outcome; enough to locate a stuck journey without recording typing or content |
| External operations | Start/outcome, provider/service and safe route identity, status/error category, duration, timeout, retries/backoff, fallback and cancellation; link attempts to one logical operation |
| Persistence and recovery | Load/save/migration outcomes, conflicts/corruption, draft/recording recovery, retry and unsaved-state decisions; no stored document or media contents |
| Background work and resources | Task/queue/stream/device transitions, permissions, concurrency conflicts, resource acquisition/release and failures, unexpected exceptions at real app boundaries |

Successful transitions matter where they establish the last known good state. Choose useful events rather than every function, render or repeated poll. Diagnostics supplement actionable user feedback and ordinary error handling; a silent failure with a log entry is still a broken journey.

## Shared module contract

- Use structured events with UTC time, severity, app/build identity, component, stable event name, outcome and an opaque session/operation correlation ID. Include duration, attempt number, safe error category/code/status and sanitized technical detail where useful. Propagate correlation across UI/background/service boundaries; distinguish a new attempt from a new operation. Capture handled failures and safe unexpected-exception details, not only crashes.
- Allowlist fields and sanitize/bound untrusted values before writing. Never log credentials, authorization headers, secret/configuration values, raw request/response bodies, private conversations/prompts, documents, audio/recordings or personal data by default. Error messages/stacks, URLs/query strings and paths can contain these too; select safe detail rather than dumping an exception object. Use harmless fixtures, never a real API key. Keep diagnostics out of source control.
- Use a discoverable local destination appropriate to the app/runtime, with stated size/age/count retention and bounded event/queue size. A runtime-managed stdout sink is adequate only when its actual capture, retention and discovery are established. Protect access, rotate/expire safely, limit noisy repetition and avoid hot-path blocking. Reuse existing facilities; do not add a telemetry service, upload, analytics or paid dependency without applicable authority.
- Logger initialization/write/rotation/export failure must not crash the app, recurse into logging, stall a user operation or block Quit. Provide a bounded safe fallback or observable diagnostic-health indication where feasible. Do not swallow the underlying app error or claim its log was saved. Cleanup/flush must have a usable exit even when the sink fails; preserve explicit unsaved-data consequences.
- Give the owner a usable way to find/view or export the safe logs, their location and retention, and the relevant correlation ID for support. Sharing remains a separate authorized action; sanitization applies before any sink or export.

## Focused evidence and handoff

After the coherent batch, exercise a representative success plus the changed journey's failure/recovery/cancel path using isolated safe fixtures. Inspect emitted records: they must explain the sequence and carry consistent correlation. Check secret/content canaries, bounded retention/event size and a failed/unavailable sink when creating or changing the module; reuse valid evidence for an unchanged logger. Select checks for the actual patch, not every possible fault or an unrelated full suite. Record unavailable interaction or failure coverage honestly.

Review the coverage map and actual event sites, privacy, retention/resource behavior, failure tolerance and owner discovery through the existing review method. Carry log access instructions, demonstrated coverage, remaining gaps/unknowns and exact check limits into the normal handoff. A logging module or passing word/syntax check alone cannot prove coverage. Instructions do not install a host hook or certify telemetry enforcement.

This standard is Seif's 3 October 2026 request, structured within his delegated factory repair. [OWASP logging guidance](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) supports risk-based events, exclusions and failure verification; the [OpenTelemetry log data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/) informs structured context/correlation. These references do not require OpenTelemetry or a remote collector.
