# App diagnostics by default

Build enough logs to explain what failed, where, why, and what recovery did. This is part of app delivery. Use the existing logger if it is adequate. Otherwise add the smallest shared module the app needs. Scattered console messages are not proof of coverage.

Safe Engine owns this requirement for new apps and app changes. An analysis-only request stays analysis-only; this reference does not authorize coding.

## Plan coverage and fill the current gap

For a new app, include diagnostics in the original plan, revised plan, code, checks and handoff. Map each applicable area below to real events. Explain any N/A. Build it with the app.

For an existing app:
- Inspect the logger, destinations and actual event sites first.
- Make a compact app-wide inventory: covered, missing, unknown. A logger's existence does not prove coverage.
- Add the minimum missing shared module and events for changed journeys and directly affected consumers. This is already part of the authorized app change, including small fixes.
- Keep small changes small. Do not rewrite the app, instrument unrelated areas or run broad regression automatically.
- Record wider gaps, their impact and next step. Report a real scope/authority boundary. Do not claim app-wide coverage without evidence.

Use the existing plan/change record:

`area/journey → source/event sites → safe useful context → check/evidence → gap or supported N/A`

One record is enough. No new controller schema or task tree is needed.

| Area | What the events must explain |
|---|---|
| Lifecycle and configuration | Startup/build identity, initialization/config validation, dependencies, shutdown and cleanup. Log safe state flags, not configuration values. |
| User actions and state | Significant commands/navigation, state changes, rejection, cancellation and the UI result. Locate a stuck journey without recording typing or content. |
| External operations | Start/outcome, provider/service, safe route identity, status/error category, duration, timeout, retries/backoff, fallback and cancellation. Link attempts to one operation. |
| Persistence and recovery | Load/save/migration, conflict/corruption, draft/recording recovery, retries and unsaved-state decisions. Do not record document or media contents. |
| Background work and resources | Task/queue/stream/device changes, permissions, concurrency conflicts, resource acquisition/release, failures and unexpected exceptions at real app boundaries. |

Log successful transitions when they establish the last known good state. Do not log every function, render or poll. Keep useful error handling and user feedback. A silent failure is still broken even if a log explains it.

## Shared module contract

- Use structured events: UTC time, severity, app/build, component, stable event name, outcome and opaque session/operation ID. Add duration, attempt, safe error code/category/status and sanitized technical detail where useful. Carry correlation across UI, background and service boundaries. Distinguish a retry from a new operation. Include handled failures and safe unexpected-exception details.
- Allowlist fields. Sanitize and bound untrusted values before writing. Do not log credentials, authorization headers, secret/config values, raw requests/responses, private conversations/prompts, documents, audio/recordings or personal data by default. Errors/stacks, URLs/queries and paths can leak these too. Select safe detail; do not dump exception objects. Use harmless fixtures, never real API keys. Keep diagnostics out of Git.
- Use a discoverable local destination. State size/age/count retention; bound events and queues. Stdout is enough only if capture, retention and discovery actually work. Protect access, rotate/expire safely, limit repeated noise and avoid blocking hot paths. Reuse existing facilities. New telemetry, uploads, analytics or paid dependencies need applicable authority.
- A logger initialization/write/rotation/export failure must not crash the app, recurse, stall an action or block Quit. Use a bounded safe fallback or visible diagnostic-health signal where feasible. Preserve the underlying error; never claim an unsaved log was saved. Failed flush/cleanup must still allow exit with explicit unsaved-data consequences.
- Let the owner find/view or export safe logs. Give the location, retention and relevant correlation ID. Sanitize before every destination or export. Sharing requires separate authority.

## Focused evidence and handoff

After the coherent batch, use isolated safe fixtures to exercise a representative success and the changed journey's failure/recovery/cancel path. Read the emitted logs. Do they explain the sequence? Does correlation stay consistent?

When adding or changing the module, check secret/content canaries, bounded retention/event size and an unavailable or failing destination. Reuse valid checks for an unchanged logger. Test the actual patch, not every possible fault or an unrelated suite. Mark unavailable interaction/failure coverage honestly.

Use the existing review to check actual coverage/event sites, privacy, retention/resources, failure tolerance and owner discovery. Include log access, demonstrated coverage, gaps/unknowns and check limits in the normal handoff. A module or syntax check does not prove coverage. These instructions install no host hook or telemetry enforcement.

This implements Seif's 3 October 2026 request. [OWASP logging guidance](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) supports event selection, exclusions and failure checks. The [OpenTelemetry log data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/) informs structure/correlation. Neither requires OpenTelemetry or a remote collector.