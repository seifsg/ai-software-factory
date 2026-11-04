# Security

One question: can this leak data, expose a secret, or turn untrusted input into unauthorized access or actions?

Read actual changed code and trust boundaries. Client artifacts can be extracted; clients may be compromised. Treat external input, links, files, messages and dependency responses as untrusted. Trace input -> authority -> data/effect. Inspect config, dependencies and evidence, not scanner scores alone.

## Size the risk

- Record environment, reachable surfaces, identities/roles, valuable data, trust boundaries.
- Local = loopback/private access and harmless data. Public tunnel, shared preview or real credentials changes exposure. Offline apps still have files, plugins, updates and untrusted input.
- New products: every surface. Small fixes: affected paths and consumers. Record unrelated risks separately.

## Secrets and credentials (highest priority)

- Hardcoded tokens, passwords, private endpoints or signing material in source, config, generated artifacts, logs or Git history. Build-time variables shipped in a client bundle are not secret. Only restricted publishable keys belong there.
- Secret-bearing env files stay untracked and ignored. Leaked secret needs revocation/rotation with authority; deleting it alone fails.
- Credentials and sensitive data use the platform's protected storage: encryption, key handling, backups, retention. No move into plaintext, shared files or logged memory.

## Authority

- Authenticate and authorize at the server or real trusted boundary on every protected action. Deny by default. Check role, object ownership, tenant, allowed fields. Hidden routes/buttons and client state prove nothing. No client-supplied role escalation. Least-privilege service and database accounts.
- Row access: roles govern actions, row policies govern records. Where clients reach data directly, verify read/write policies with real roles, including accounts that bypass them. A toggle alone proves nothing.
- Accounts: verified email when identity or recovery depends on it. Expiring single-use tokens, safe recovery, neutral responses against enumeration. Established auth, no homemade crypto. Owned passwords use salted adaptive hashing (Argon2id preferred); never plaintext, reversible encryption or fast hashes. Strong admin auth; MFA by exposure.
- Sessions: no auth tokens in browser localStorage/sessionStorage. Prefer server sessions or a backend-for-frontend with HttpOnly, Secure, scoped SameSite cookies and CSRF protection. Native clients use protected OS storage. Validate signature, issuer, audience, expiry; revoke on logout and recovery. No tokens in URLs or logs.
- Abuse: rate, size, concurrency and cost limits on exposed surfaces; login/reset, search, uploads and expensive work first. Trusted proxy handling. Replay controls at the authoritative boundary.

## Untrusted input

- Validate type, length, range, allowed fields, business rules at the trusted boundary: links, routes, commands, invitations, API calls, game/network messages, uploads. Client validation = UX.
- Parameterize queries; allowlist dynamic identifiers. No command/template injection or unsafe deserialization.
- Context-aware output encoding; sanitize permitted rich HTML with a maintained sanitizer; no raw untrusted HTML or script. CSP as defense in depth.
- CSRF protection on cookie-authenticated mutations; no state changes through GET. CORS limited to needed origins, methods, headers; no reflected origins or wildcard with credentials. CORS is not authorization.
- Redirects, URLs, paths, archives: unsafe schemes, open redirects, traversal, unsafe extraction, archive bombs. Server-side fetches must not reach internal networks or metadata services.
- Uploads: authorization, size/count, extension and detected content; distrust MIME and name. Generated storage names, non-executable isolated storage, authorized downloads. Never serve active uploads from the app's trusted origin.
- Webhooks: verify provider signature over original bytes before any effect. Freshness/replay window, deduplicated events, idempotent retries. Never trust unsigned payloads or IP allowlists alone.
- Embedded browser, plugin and script surfaces: origin rules, message validation, file access, least capability. Untrusted pages gain no app authority.

## Data exposure

- No passwords, tokens, credentials, contact details, full records or file contents in logs, replay, telemetry or crash reports. Redact before the sink; keep useful diagnostics.
- Sensitive files in shared storage, caches or clipboard beyond needed lifetime.
- Cross-user/tenant cache leakage; cached responses or background workers bypassing access checks.

## Transport, permissions, deployment, dependencies

- TLS for sensitive traffic; no disabled certificate validation or weakened transport.
- Permissions match need. Denial must not crash or prompt repeatedly.
- Before exposure: HTTPS, production config, no debug consoles, stack traces, default credentials or test bypasses; least-privilege network/storage; fitting security headers.
- Direct and transitive dependencies, lockfiles, actual advisories. Update vulnerable versions compatibly; no blind major upgrades. Verify consequential claims against current authoritative sources. Invent no vulnerabilities.

## Calibrate

- Client-side "auth" = UX, not a boundary. Flag trust in client state, not absence of a redundant client check. Identify the real authority for local/offline systems too.
- Redundant-looking guard may be defense in depth. Mark **KEEP**, not "delete", when justified.
- MEDIUM hardening alone does not reject a local POC. Before public exposure or production: fix demonstrated compromise risks or isolate/disable the path. Unresolved material checks block a ready claim.
- Review grants no fixes, deployment, credential rotation, destructive cleanup or intrusive scans. Never probe unrelated systems or load production without authority.

## Output

Per applicable surface: `surface -> control -> evidence -> PASS / FAIL / UNKNOWN / N/A (justified)`.

Findings use SKILL.md format. Severity: CRITICAL real secret exposed, sensitive data exposed through storage/logs, account/data compromise. HIGH exploitable with conditions. MEDIUM hardening. LOW hygiene. Impact: what leaks, who gains access, what they can do.

End with: `SECURITY VERDICT: <clean | hardening-needed | vulnerable | blocker> - <one sentence>`. Clean result is valid; say so plainly.
