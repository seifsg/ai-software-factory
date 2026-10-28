# Quality cases

Contents: Logging, Security. Read only the section matching the condition in `product-bar.md`.

## Logging

Every app, game, service and tool has one working shared logging module, small fixes included: reuse an adequate one or create it. An SDK alone, scattered console prints or an unused wrapper does not count.

- Destination: reuse existing logging and the owner's stated provider; unknown, ask the owner. Missing access goes through secure credential tools, never secrets in chat. Verify ingestion and search access; an installed SDK proves neither.
- No provider yet: ship an internal module with working local output now; the provider stays pending. No silent vendor switch, purchase or new remote collection.
- Shape: thin app module over a maintained native logger, provider or OTLP adapters where useful; no cross-language engine or forced collector. It owns structured events, context propagation, sanitization, levels and sinks, with human- and machine-readable views.
- Wiring: new products plan logging before features and wire it from startup into the first journey. Existing products reuse facilities, fill missing boundaries through shared middleware or hooks, record legacy gaps. Optional dashboards never delay the journey.
- Libraries: emit through caller-configured hooks; no global setup or files on import. Show real consumer use; build no unrelated host app.

Keep one map: `area/journey → start/success/failure events → sink → evidence → gap`. Log per area:

- Lifecycle: build, runtime, platform, startup, config validation, dependency availability, shutdown.
- Journey: intent (label inferred intent), entry, transitions, validation/rejection, success, cancel, recovery.
- Functions/jobs: component, real file/line/function, operation, named inputs, branches, output, queues, permissions, resource acquire/release, exceptions.
- Network: route, parameters, status, latency, timeout, attempt, retry/backoff, fallback; correlate caller and downstream.
- Files: logical name, operation, declared/detected type, size, encoding/parser, validation, save/migration/conflict/recovery.
- Database: query template, bound names/types/values (sanitized), transaction, duration, rows, outcome.

Every event: UTC time, sequence/duration, severity, stable name, outcome, app/build/environment, component, real location (never invented).

- Opaque session/action/operation and trace IDs cross async work, threads, jobs and services; isolate concurrent users; bounded breadcrumbs keep the lead-up to errors.
- Failures add named values, expected/actual, error type/code/message, sanitized stack and causes, retries; mark missing, redacted or truncated fields.
- Log successes and failures; severity is not outcome. Investigate unexpected warnings. Logging never replaces error handling.
- Reproduction: safe query text with separate bindings, no secret interpolation or object dumps. Bad character: escaped code point, position, encoding. Document mismatch: declared/detected type, parser, size, rejection.
- Never log passwords, keys, tokens, cookies, auth headers or connection credentials. Redact before every sink, buffer and SDK auto-capture; check URLs, paths, stacks and queries. Private documents or personal data need explicit scoped authority, minimum content, restricted access, short retention and no automatic upload; prefer synthetic inputs.
- Bound event, body and stack size, queues, memory, disk, retention and retries. Escape untrusted text against forged lines. Write async or batched; keep input and frames responsive. Aggregate repeated frame or poll events with counts and dropped markers; verbose detail only when targeted.
- Logger failures (init, write, rotation, full disk, provider outage) never crash, recurse, stall or block exit: bounded local fallback, visible logger health, lost records reported.
- Restoring or replacing state resets counters, timers, caches and diagnostics.
- Storage fits the platform (file, platform store, stdout) with retention; owner and agent can search by severity, time, operation and journey and export sanitized logs.
- After implementation, exercise success, failure, invalid input and retry/cancel with harmless data, then read the new trail. If it cannot explain the failure without guessing, fix and repeat before final automated tests. Judge emitted records, not module presence.
- Handoff: backend, access steps, query, correlation example, observed coverage, redactions, bounds and gaps.

## Security

Cheap relevant protections from the start; required ones and denial paths in full before any exposure, never as polish. Reuse framework and provider controls.

Size the risk: environment, reachable surfaces, roles, valuable data, trust boundaries. Local means loopback and harmless data; a public tunnel, shared preview or real credentials means exposed. Offline apps still have files, plugins, updates and untrusted input. Research consequential unknowns in current platform guidance.

- Authorization: server or trusted-boundary check on every protected action. Deny by default; check role, ownership, tenant and allowed fields. Hidden UI proves nothing. No client-set roles; least-privilege service and database accounts.
- Row access: roles govern actions, row policies govern records. Enable database row-level security where clients reach data directly; verify with real roles, including owners that bypass policies. Otherwise enforce equivalent isolation.
- Accounts: established auth, no homemade crypto. Verify email when identity or recovery depends on it. Expiring single-use tokens; neutral responses against enumeration. Owned passwords: salted adaptive hash, Argon2id preferred. Strong admin auth; MFA by exposure.
- Sessions: no auth tokens in browser storage, URLs or logs. Server sessions or backend-for-frontend with HttpOnly, Secure, scoped SameSite cookies. Native: protected OS storage. Validate signature, issuer, audience, expiry; revoke on logout and recovery.
- Secrets: server-side or protected runtime config only, never in bundles, code or Git. Secret `.env` files ignored; sanitized example tracked. Leak: revoke and rotate first, with authority; deletion alone fails. No silent force-push.
- Input: validate type, length, range, allowed fields and business rules at the trusted boundary. Parameterized SQL; allowlisted identifiers. No unsafe command, template or deserialization paths. Validate URLs and redirects; server fetches never reach internal networks or metadata.
- Output: context-aware encoding, safe framework sinks, maintained sanitizer for rich HTML, fitting CSP. CSRF protection on cookie-authenticated mutations; no state change on GET. CORS is neither authorization nor CSRF protection.
- Uploads: authorize; limit size and count; check extension and detected content, distrust MIME and name. Generated names, traversal and archive-bomb protection, non-executable isolated storage, authorized downloads. Never serve active uploads from the app origin.
- Abuse/CORS: rate, size, concurrency and cost limits per surface, login, reset, search, uploads and expensive work first. Trusted proxy handling; keep legitimate retries working. CORS only for needed origins; no reflected origin or wildcard with credentials.
- Webhooks: verify the signature over the original bytes before any effect ([external effects](product-bar.md#external-effects)).
- Dependencies: lockfiles. Review actual advisories; update vulnerable versions compatibly. No blind major upgrades or invented CVEs.

Before exposure: HTTPS, valid certificates, production config, fitting security headers, least-privilege network and storage; no debug consoles, stack traces, default credentials or test bypasses. Exercise denial paths with harmless accounts (anonymous, other user or tenant, tampered or expired token, forged webhook), then run the `deep-review` security lens. Fix demonstrated compromise risks or disable the path.

MVP and production-slice done-runs record `**Secrets:**` (secret scan of the working tree and Git history), `**Dependencies:**` (package manager audit) and `**Static:**` (the stack's static analyzer), each naming the tool, the command and the result; tools per stack. Fix each high or critical finding before handoff (a confirmed secret is critical) or record the owner's decision in the handoff and the follow-ups ticket. A confirmed secret left unfixed, a key rotation awaiting the owner included, is a blocker: the outcome stays unfinished until the owner answers. A missing tool is installed or recorded as a blocker, never skipped.

