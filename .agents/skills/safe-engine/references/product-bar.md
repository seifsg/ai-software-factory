# Product bar

Contents: Stack, Visual system, States and forms, Public pages, Data, Logging, Speed, Security, Dev sign-in, POC deferrals, Games and browser lifecycle, External effects, Release.

The quality floor for every app, game, service, tool and library, in every mode. A POC or MVP is the first slice of the real product: built right, never thrown away. Record its stack, design brief and budgets in the plan.

- Minimal code means no waste. It never justifies a weaker stack, missing states or a bare UI.
- New products meet all of it. Changes cover the affected paths and their consumers; record wider gaps, no unrelated restructuring.
- Analysis and review requests stay read-only: record gaps against this bar.

## Stack

Defaults for new products. Existing projects keep their stack.

- Pick the best current stack for the job: modern, popular, well maintained, fast to run locally, good looking by default. Compare three at kickoff (run `research-market`), recommend one, the owner picks.
- Strict TypeScript for all JavaScript-ecosystem code. No plain JavaScript source.
- React web UIs: shadcn/ui with Tailwind CSS and lucide icons. Other platforms: their best-in-class equivalent, named in the stack options.
- One command starts it locally with seeded data.
- Production structure from day one: typed models, migrations, shared logging, clear modules. The MVP grows from this code.
- Dependencies: check license, maintenance, current version, security and cost. Versioned packages over copied code.

## Visual system

Fill the design brief before UI code. Run `ux-quality` on every UI change.

| Item | Default |
|---|---|
| UI kit | The stack's component kit (shadcn/ui for React). |
| Palette | Brand primary, accent, neutrals, success/warning/danger as tokens; at least 4 hex values; WCAG AA contrast. |
| Font | One modern readable sans (Geist or Inter class), 16px base, clear type scale. |
| Logo | Own small SVG mark and wordmark; favicon from the mark. |
| Icons | One consistent set. |
| Layout | Header (logo, navigation, account), content, footer (product, links, ©). Responsive from phone to desktop. |
| Theme | Light by default. Dark mode optional later, never the default. |
| Motion | Subtle; respects reduced motion. |

## States and forms

- Every screen has loading, empty (with the next action), error (with retry) and success states.
- Errors say what happened and the next useful action. No blame, no false success.
- Forms validate inline and keep input. Client validation is UX; the server validates again.
- Labels on buttons and links match what they actually do.

## Public pages

- Web products ship a landing page at `/` in the POC: who it is for, the outcome, one primary call to action, real proof only, features, FAQ, footer.
- Run `ux-quality` and its web SEO reference for search metadata, and its copy reference for conversion copy.
- Private-only product (decided at kickoff): a branded sign-in page at `/` instead, marked noindex.
- Private screens, staging and previews stay unindexed.

## Data

- New or materially changed persistence: run `database-schema`. Design from real access patterns; index actual queries.
- Seed realistic data, sample media included where the product shows media, so every screen looks used on first run.
- Collect only needed data. Protect sensitive storage and backups.

## Logging

Every app, game, service and tool has one working shared logging module, small fixes included. Reuse an adequate one or create it. An SDK alone, scattered console prints or an unused wrapper does not count.

- **Destination:** reuse existing logging and the owner's stated provider. Unknown? Ask the owner. Missing access goes through secure credential tools, never secrets in chat. Verify ingestion and search access; an installed SDK proves neither.
- **No provider yet:** ship an internal module with working local output now; the provider stays pending. No silent vendor switch, purchase or new remote collection.
- **Shape:** thin app module over a maintained native logger; provider or OTLP adapters where useful. No cross-language engine or forced collector. The module owns structured events, context propagation, sanitization, levels and sinks, with human- and machine-readable views.
- **Wiring:** new products plan logging before features and wire it from startup into the first journey. Existing products reuse facilities, fill missing boundaries through shared middleware or hooks and record legacy gaps. Optional dashboards never delay the journey.
- **Libraries:** emit through caller-configured hooks; no global setup or files on import. Show real consumer use; build no unrelated host app.

Keep one map: `area/journey → start/success/failure events → sink → evidence → gap`.

| Area | Log |
|---|---|
| Lifecycle | Build, runtime, platform, startup, config validation, dependency availability, shutdown. |
| Journey | Intent (label inferred intent), entry, transitions, validation/rejection, success, cancel, recovery. |
| Functions/jobs | Component, real file/line/function, operation, named inputs, branches, output, queues, permissions, resource acquire/release, exceptions. |
| Network | Route, parameters, status, latency, timeout, attempt, retry/backoff, fallback. Correlate caller and downstream. |
| Files | Logical name, operation, declared/detected type, size, encoding/parser, validation, save/migration/conflict/recovery. |
| Database | Query template, bound names/types/values (sanitized), transaction, duration, rows, outcome. |
| Games | Scene/entity, input and state transitions, asset loading, simulation failures, frame/resource anomalies. |

- Every event: UTC time, sequence/duration, severity, stable name, outcome, app/build/environment, component, real location (never invented).
- Opaque session/action/operation and trace IDs propagate across async work, threads, jobs and services. Isolate concurrent users. Bounded breadcrumbs keep the lead-up to errors.
- Failures add named values, expected/actual, error type/code/message, sanitized stack and causes, retries. Mark missing, redacted or truncated fields.
- Log successes and failures. Severity is not outcome. Investigate unexpected warnings. Logging never replaces error handling.
- Reproduction: safe query text with separate bindings; no secret interpolation or object dumps. Bad character: escaped code point, position, encoding. Document mismatch: declared/detected type, parser, size, rejection.
- Never log passwords, keys, tokens, cookies, auth headers or connection credentials. Redact before every sink, buffer and SDK auto-capture; check URLs, paths, stacks and queries. Private documents or personal data need explicit scoped authority, minimum content, restricted access, short retention and no automatic upload; prefer synthetic inputs.
- Bound event, body and stack size, queues, memory, disk, retention and retries. Escape untrusted text against forged lines. Write async or batched; keep input and frames responsive. Aggregate repeated frame or poll events with counts and dropped markers; verbose detail only when targeted.
- Logger failures (init, write, rotation, full disk, provider outage) never crash, recurse, stall or block exit: bounded local fallback, visible logger health, lost records reported.
- Restoring or replacing state resets counters, timers, caches and diagnostics.
- Storage fits the platform (file, platform store, stdout) with retention. Owner and agent can search by severity, time, operation and journey, and export sanitized logs.
- After implementation, exercise success, failure, invalid input and retry/cancel with harmless data, then read the new trail. Can it explain the failure without guessing? Fix and repeat before final automated tests. Judge emitted records, not module presence.
- Handoff: backend, access steps, query, a correlation example, observed coverage, redactions, bounds and gaps.

## Speed

Budget in the first plan: fast first load, instant common actions, no N+1, paginated lists. Small copy or input fixes need no profiling.

- Trace `trigger → work → result → release`: size, frequency, concurrency, hardware, owner. Include startup, active use and idle work.
- Record `workload → target → cost → decision → bound/lifetime → evidence`. Mark targets measured or provisional.
- Workload-specific complexity and latency; no blanket O(1) claim. Remove work before caching. Batching, indexes, pools and coalescing solve different problems.
- No distributed services, deployment changes or spending without authority. Justify N/A; invent no infrastructure.

| Area | Check |
|---|---|
| CPU | Algorithms, data layout, repeated scans, allocations, hot loops. Heavy work off interaction threads; bound queues and parallelism. |
| GPU/games | CPU vs GPU frame time, pacing, spikes, draw calls, overdraw, shaders, streaming, GPU memory on representative hardware. Averages hide stalls. |
| Memory | Peak and retained memory, leaks, pools, subscriptions. Release on cancel, replace and exit. |
| Database | Real plans on representative data, N+1, indexes, pagination, locks, connection bounds, index write cost. No destructive production probes. |
| Network | Round trips, payload size, dedupe, streaming, timeouts/backoff, offline. Keep ordering, idempotency and authorization. |
| Storage | Write amplification, asset size, atomic writes, migrations, full disk. |
| Interaction | Input latency, startup, battery, polling. Prefer events; pause hidden work. CLI/API: responsive output, backpressure, usable errors. |

Cache only when savings outweigh validity, memory and complexity cost. Never replay side effects, suppress intentional repeats or treat cached tool or model output as authority. Generated media: key all content inputs, separate generation reuse from playback, verify disposal.

| Cache | Require |
|---|---|
| Identity | Key every result-changing input, version and user/access scope. Invalidate on source, model or config change. TTL alone proves neither freshness nor authorization. |
| Capacity | Bound entries, bytes and in-flight work; define eviction, disposal and lifetime. |
| Privacy | Private content in memory by default; no credentials or cross-user reuse; immutable or copied results; never log raw keys or payloads. |
| Concurrency | Coalesce duplicate work. One cancelled waiter cancels no others. Stale work cannot refill an invalidated generation. |
| Failure | Never cache failed, partial or cancelled results as success. Negative entries expire. Miss, eviction or outage falls back to a correct path. No retry storms. |

Evidence: source proves repetition; speed and memory claims need runtime measurement with workload, environment and cold/warm conditions stated. Changed caching: test cold/warm, changed inputs, eviction, failures, cancellation and cache disabled. Faster wrong or stale results fail. Fakes prove mechanics, not speed. Percentages need a comparable baseline. Log safe counts and timings, no default per-frame flood. Report unmet targets.

## Security

Cheap relevant protections from the start; reuse framework and provider controls. Local MVPs stay simple: no account system, service or ceremony without need.

- Size the risk: environment, reachable surfaces, roles, valuable data, trust boundaries. Local means loopback and harmless data; a public tunnel, shared preview or real credentials means exposed. Offline apps still have files, plugins, updates and untrusted input. Research consequential unknowns in current platform guidance.
- Required protections and denial paths precede exposure. They are never polish.

| Surface | Rule |
|---|---|
| Authorization | Check at the server or trusted boundary on every protected action. Deny by default; check role, ownership, tenant and allowed fields. Hidden UI proves nothing. No client-set roles; least-privilege service and database accounts. |
| Row access | Roles govern actions, row policies govern records. Enable database row-level security where clients reach data directly; verify with real roles, including owners that bypass policies. Otherwise enforce equivalent isolation. |
| Accounts | Established auth, no homemade crypto. Verify email when identity or recovery depends on it. Expiring single-use tokens; neutral responses against enumeration. Owned passwords: salted adaptive hash, Argon2id preferred. Strong admin auth; MFA by exposure. |
| Sessions | No auth tokens in browser storage, URLs or logs. Server sessions or backend-for-frontend with HttpOnly, Secure, scoped SameSite cookies. Native: protected OS storage. Validate signature, issuer, audience, expiry; revoke on logout and recovery. |
| Secrets | Server-side or protected runtime config only; never in bundles, code or Git. Secret `.env` files ignored; sanitized example tracked. Leak: revoke and rotate first, with authority; deletion alone fails. No silent force-push. |
| Input | Validate type, length, range, allowed fields and business rules at the trusted boundary. Parameterized SQL; allowlisted identifiers. No unsafe command, template or deserialization paths. Validate URLs and redirects; server fetches never reach internal networks or metadata. |
| Output | Context-aware encoding, safe framework sinks, maintained sanitizer for rich HTML, fitting CSP. CSRF protection on cookie-authenticated mutations; no state change on GET. CORS is neither authorization nor CSRF protection. |
| Uploads | Authorize; limit size and count; check extension and detected content, distrust MIME and name. Generated names, traversal and archive-bomb protection, non-executable isolated storage, authorized downloads. Never serve active uploads from the app origin. |
| Webhooks | Verify signatures over the original bytes before any effect. Freshness and replay checks; dedupe; idempotent retries. Never trust unsigned payloads or IP allowlists alone. |
| Abuse/CORS | Rate, size, concurrency and cost limits per surface: login, reset, search, uploads and expensive work first. Trusted proxy handling; keep legitimate retries working. CORS only for needed origins; no reflected origin or wildcard with credentials. |
| Dependencies | Lockfiles. Review actual advisories; update vulnerable versions compatibly. No blind major upgrades or invented CVEs. |

Before exposure, exercise denial paths with harmless accounts (anonymous, other user or tenant, tampered or expired token, forged webhook), then run the `deep-review` security lens. Fix demonstrated compromise risks or disable the path.

## Dev sign-in

Apps with accounts seed one user per role. Development builds show one-click buttons beside the normal sign-in form: "Sign in as Admin", "Sign in as Client" and so on. The server accepts them only in development; production builds drop the route and buttons. The handoff names the URL and buttons, so the owner never hunts for credentials.

## POC deferrals

Unless the owner asks, a POC may defer Docker, Kubernetes, CI/CD, deployment, unit-test suites and security hardening (rate limits, CSRF, headers, audits).

- Each deferral becomes a follow-up ticket in the epic with an owner and an acceptance or revisit condition. No vague "later".
- Never deferred: role checks the journeys need, secrets out of code and Git, logging, screen states, the visual system.
- Security applies in full before any public exposure.

## Games and browser lifecycle

Games: keep the intended challenge, mastery, discovery, pacing and reward. Remove accidental friction; difficulty is not a defect; add no hints or automation that defeat the approved design. Set the intended experience and supported inputs and devices in the plan; playtest at the final stage.

Web apps and games: pick the relevant cases for final manual QA, not every permutation.

| Boundary | Check |
|---|---|
| Navigation | Reload, deep link, back/forward, tab close/reopen, hide/resume, stale tabs, cancellation. Keep promised state; clear stuck input on focus loss or pointer cancel; release owned work. |
| Game timing | Elapsed-time or fixed-step simulation, refresh-rate independent, bounded resume delta. No catch-up jump after a hidden tab or suspended device. |
| Connectivity | Offline/reconnect, slow or interrupted requests, duplicate submit, expired session, uncertain completion. Truthful progress and recovery. |
| Capabilities | Touch, keyboard, controller, focus/pointer/fullscreen locks, audio unlock and mute, denied permissions, storage quota, device or context loss. |
| Compatibility | Supported browsers and devices, viewport, orientation, reduced motion, low-end performance, stale cached assets and client/server versions. |

Record unsupported cases. One desktop browser proves nothing about mobile, audio or assistive behavior.

## External effects

Payments, messages, remote jobs and any other state-changing call:

- Record `operation identity → durable state → effect → completion/reconciliation owner`.
- Cover pending, success, failure and unknown outcomes; commit/effect order; ambiguous timeouts; duplicate or out-of-order delivery; bounded retry with backoff; cancellation; safe replay.
- A database commit, sent request or signed webhook does not prove the business effect happened.
- Choose once the smallest adequate mechanism: provider idempotency and reconciliation, a durable pending record, a transactional outbox or a workflow engine. No universal queue.
- Final manual QA uses safe disposable operations, including interruption and retry. Read correlated logs and preserve unresolved effects before retrying.

## Release

Proof before any ready claim:

- Before dependent work, record actual capabilities: build tools, browser or native control, audio inspection, devices, safe accounts and data, integration access. Verify each route exists; surface blockers early and keep independent work moving. No purchases, installs or new credentials implied.
- Map each criterion to manual, automated or mixed evidence: candidate, environment/device, action, result, limits. Feel, art and interaction need honest observation, not an unrelated passing script. Missing evidence stays UNKNOWN. Never fabricate a tester or infer completion from a screenshot.
- A demo names the exact build, environment, device, data or save identity, actions and result. Same URL is not same context. Passing checks alone do not prove the outcome.

Release and operation:

- Local ready, PR approval, merge and live release are separate. Never infer deployment authority.
- Before exposure: HTTPS, valid certificates, production config, fitting security headers, least-privilege network and storage. No debug consoles, stack traces, default credentials or test bypasses.
- One release record: reviewed build artifact, target environment and config, required services and secrets, migration and app ordering, compatible clients and data, rollback or roll-forward, backups with a usable restore.
- Attach security, UX, SEO and integration evidence. After deploy, check live health and the critical journey; record failure threshold, recovery action and responsible owner. Local evidence is not production proof.
- Operations: log access, failure, stalled-job and capacity signals, an authorized destination and operator, retention and recovery. Reuse existing facilities; no automatic paid monitor, new notifications or perpetual polling.
