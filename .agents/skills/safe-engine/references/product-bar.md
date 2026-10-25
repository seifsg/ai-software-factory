# Product bar

Contents: Stack, Visual system, States and forms, Public pages, Data, Logging, Speed, Security, Dev sign-in, Environment and sample labels, Games and browser lifecycle, External effects, Release.

Quality floor for every app, game, service, tool and library, in every mode; the [size](sizes.md) sets which parts apply. A POC or MVP is never thrown away: record its stack, design brief and budgets in the plan.

- Minimal code means no waste, never a weaker stack, missing states or a bare UI.
- New products meet all of it except what their size skips. Changes cover affected paths and their consumers; record wider gaps, no unrelated restructuring.
- Analysis and review requests stay read-only: record gaps against this bar.

## Stack

Defaults for new products; existing projects keep their stack.

- Best current stack for the job: modern, popular, well maintained, fast locally, good looking by default. At kickoff compare three (run `research-market`), recommend one; the owner picks.
- Strict TypeScript for all JavaScript-ecosystem code, no plain JavaScript source.
- React web UIs: shadcn/ui, Tailwind CSS, lucide icons. Other platforms: best-in-class equivalents named in the stack options. One consistent icon set.
- One command starts it locally with seeded data.
- No AGENTS.md in built products unless non-standard commands or tools would trip an agent: then 10 lines or fewer, hand-written, never generated from code.
- Clean structure from day one (typed models, shared logging, clear modules); every size grows the same code.
- Dependencies: check license, maintenance, current version, security and cost; versioned packages over copied code.

## Visual system

Fill the design brief before UI code; run `ux-quality` on every UI change. Defaults:

- Palette: brand primary, accent, neutrals, success/warning/danger as tokens; at least 4 hex values; WCAG AA contrast.
- Font: one modern readable sans (Geist or Inter class), 16px base, clear type scale.
- Logo: own small SVG mark and wordmark; favicon from the mark.
- Layout: header (logo, navigation, account), content, footer (product, links, ©); signed-in screens drop sign-in and marketing links; responsive phone to desktop.
- Theme: light; dark mode optional later, never the default. Motion: subtle, respects reduced motion.

## States and forms

- Every screen has loading, empty (with next action), error (with retry) and success states.
- Design every collection for one, few and many items; one item shows in place, never behind a list of one.
- Errors say what happened and the next useful action; no blame, no false success.
- Forms validate inline and keep input; the server validates again.
- Button and link labels match what they do. One source each: a glossary module holds every object, state and action name; a typed route map per audience feeds nav, breadcrumbs, titles and H1s; lifecycle screens take their primary action and panels from a state map.

## Public pages

- Web products ship a landing page at `/`: who it is for, the outcome, one primary call to action, real proof only, features, FAQ, footer. Private-only product (decided at kickoff): a branded noindex sign-in page at `/` instead.
- Run `ux-quality` with its web SEO reference (search metadata) and copy reference (conversion copy).
- Private screens, staging and previews stay unindexed.

## Data

- New or materially changed persistence: run `database-schema`; design from real access patterns, index actual queries.
- Seed realistic data (sample media where the product shows media) so every screen looks used on first run.
- Collect only needed data; protect sensitive storage and backups.
- Analytics collect events, not people: no personal data, raw IP or fingerprinting; consent before non-essential tracking where the law requires it.

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

## Speed

Budget in the first plan: fast first load, instant common actions, no N+1, paginated lists. Small copy or input fixes need no profiling.

- Trace `trigger → work → result → release`: size, frequency, concurrency, hardware, owner; startup, active use and idle work included.
- Record `workload → target → cost → decision → bound/lifetime → evidence`; mark targets measured or provisional.
- Workload-specific complexity and latency; no blanket O(1) claim. Remove work before caching. Batching, indexes, pools and coalescing solve different problems.
- No distributed services, deployment changes or spending without authority. Justify N/A; invent no infrastructure.
- CPU: algorithms, data layout, repeated scans, allocations, hot loops. Heavy work off interaction threads; bound queues and parallelism.
- Memory: peak and retained memory, leaks, pools, subscriptions. Release on cancel, replace and exit.
- Database: real plans on representative data, N+1, indexes, pagination, locks, connection bounds, index write cost. No destructive production probes.
- Network: round trips, payload size, dedupe, streaming, timeouts/backoff, offline. Keep ordering, idempotency and authorization.
- Storage: write amplification, asset size, atomic writes, migrations, full disk.
- Interaction: input latency, startup, battery, polling. Prefer events; pause hidden work. CLI/API: responsive output, backpressure, usable errors.

Adding, changing or reviewing a cache, what cached work depends on (inputs, access scope), duplicate-work coalescing or generated-media reuse: [caching](cases.md#caching).

Evidence: source proves repetition; speed and memory claims need runtime measurement stating workload, environment and cold/warm conditions. Faster wrong or stale results fail. Fakes prove mechanics, not speed. Percentages need a comparable baseline. Log safe counts and timings. Report unmet targets.

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
- Webhooks: verify the signature over the original bytes before any effect ([external effects](#external-effects)).
- Dependencies: lockfiles. Review actual advisories; update vulnerable versions compatibly. No blind major upgrades or invented CVEs.

Before exposure: HTTPS, valid certificates, production config, fitting security headers, least-privilege network and storage; no debug consoles, stack traces, default credentials or test bypasses. Exercise denial paths with harmless accounts (anonymous, other user or tenant, tampered or expired token, forged webhook), then run the `deep-review` security lens. Fix demonstrated compromise risks or disable the path.

MVP and production-slice done-runs record `**Secrets:**` (secret scan of the working tree and Git history), `**Dependencies:**` (package manager audit) and `**Static:**` (the stack's static analyzer), each naming the tool, the command and the result; tools per stack. Fix each high or critical finding before handoff (a confirmed secret is critical) or record the owner's decision in the handoff and the follow-ups ticket. A confirmed secret left unfixed, a key rotation awaiting the owner included, is a blocker: the outcome stays unfinished until the owner answers. A missing tool is installed or recorded as a blocker, never skipped.

## Dev sign-in

Apps with accounts seed one user per role. Development builds show one-click buttons beside the normal sign-in form ("Sign in as Admin", "Sign in as Client" and so on); only development servers accept them; production builds drop the route and buttons. The handoff names the URL and buttons; the owner never hunts for credentials.

## Environment and sample labels

- A small fixed environment badge (DEV, STAGING, PREVIEW; games: a corner tag) follows the runtime environment from config, not the build mode: staging and preview show it even on a production build. Only production hides it: render nothing, not CSS-hidden.
- Sample data and mocked or sandbox integrations carry a visible label wherever they appear outside production: "Sample data", "Test mode: no real charge". Production never seeds sample data.
- No screen (CLI, API, library, service): print the environment in the startup log and version or health output.
- Done-run screenshots show the badge; the handoff names the environment.

## Games and browser lifecycle

A game or GPU-heavy rendering, built, changed or reviewed: [games](cases.md#games).

Final manual QA of web apps and games: relevant cases, not every permutation.

- Navigation: reload, deep link, back/forward, tab close/reopen, hide/resume, stale tabs, cancellation. Keep promised state; clear stuck input on focus loss or pointer cancel; release owned work.
- Game timing: elapsed-time or fixed-step simulation, refresh-rate independent, bounded resume delta. No catch-up jump after a hidden tab or suspended device.
- Connectivity: offline/reconnect, slow or interrupted requests, duplicate submit, expired session, uncertain completion. Truthful progress and recovery.
- Capabilities: touch, keyboard, controller, focus/pointer/fullscreen locks, audio unlock and mute, denied permissions, storage quota, device or context loss.
- Compatibility: supported browsers and devices, viewport, orientation, reduced motion, low-end performance, stale cached assets and client/server versions.

Record unsupported cases. One desktop browser proves nothing about mobile, audio or assistive behavior.

## External effects

Payments, messages, webhooks, remote jobs and any other state-changing call to another system:

- Record `operation identity → durable state → effect → completion/reconciliation owner`.
- Cover pending, success, failure and unknown outcomes; commit/effect order; ambiguous timeouts; duplicate or out-of-order delivery; bounded retry with backoff; cancellation; safe replay.
- A database commit, sent request or signed webhook does not prove the business effect happened.
- Choose once the smallest adequate mechanism: provider idempotency and reconciliation, a durable pending record, a transactional outbox or a workflow engine. No universal queue.
- Webhooks: after the signature check ([security](#security)), freshness and replay checks; dedupe; idempotent retries. Never trust unsigned payloads or IP allowlists alone.
- Final manual QA uses safe disposable operations, including interruption and retry. Read correlated logs and preserve unresolved effects before retrying.

## Release

Proof before any ready claim:

- Before dependent work, record actual capabilities: build tools, browser or native control, audio inspection, devices, safe accounts and data, integration access. Verify each route exists; surface blockers early and keep independent work moving. No purchases, installs or new credentials implied.
- Map each criterion to manual, automated or mixed evidence: candidate, environment/device, action, result, limits. Feel, art and interaction need honest observation, not an unrelated passing script. Missing evidence stays UNKNOWN. Never fabricate a tester or infer completion from a screenshot.
- A demo names the exact build, environment, device, data or save identity, actions and result. Same URL is not same context. Passing checks alone prove no outcome.
- Local ready, PR approval, merge and live release are separate; never infer deployment authority.
- One release record: reviewed build artifact, target environment and config, required services and secrets, migration and app ordering, compatible clients and data, rollback or roll-forward, backups with a usable restore. Attach security, UX, SEO and integration evidence.
- Operations: log access, failure, stalled-job and capacity signals, an authorized destination and operator, retention and recovery. Reuse existing facilities; no automatic paid monitor, new notifications or perpetual polling.
- Deploying or operating a live release: [live release](cases.md#live-release).
