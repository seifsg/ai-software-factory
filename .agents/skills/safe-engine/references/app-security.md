# Application security

Handle cheap, relevant protections from the start. Reuse maintained framework/provider controls. Before public exposure or production, verify the actual deployment. Keep local MVPs simple; add no account system, service or ceremony without a need.

## Size the risk

Record environment, reachable surfaces, identities/roles, valuable data and trust boundaries. Local means loopback/private access and harmless data; a public tunnel, shared preview or real credentials changes exposure. Offline apps still have files, plugins, updates and untrusted input.

Apply the rows that fit. New products cover their surfaces; small fixes cover affected paths/consumers. Record unrelated risks separately. Research consequential unknowns in current platform guidance. Analysis/review-only stays read-only; no deployment, credential rotation, destructive cleanup or intrusive scanning authority implied.

## Build safely

| Surface | Check |
|---|---|
| Admin/permissions | Authenticate and authorize at the server or actual trusted boundary on every protected action. Deny by default; check role, object ownership, tenant and allowed fields. Hidden routes/buttons prove nothing. No client-supplied role escalation; least-privilege service/database accounts. |
| Row-level security | Roles govern actions; row policies govern accessible records. Enable database RLS where the architecture needs it, especially direct client data access. Verify read/write policies with real application roles, including owners/service accounts that bypass policies. Otherwise document/enforce equivalent isolation; a toggle alone proves nothing. |
| Accounts | Verify email ownership when identity/recovery depends on it, including changes. Expiring single-use tokens, safe recovery, neutral responses against enumeration. Use established auth; no homemade crypto. For owned passwords, salted adaptive hashing, preferably Argon2id with current supported settings. Never plaintext, reversible encryption or fast general hashes. Strong admin authentication; consider MFA by exposure. |
| Sessions | Keep auth tokens out of browser localStorage/sessionStorage. Prefer server sessions or a backend-for-frontend with HttpOnly, Secure, appropriately scoped SameSite cookies and CSRF protection. Respect provider/platform constraints; native clients use protected OS storage. Validate token signature, issuer, audience and expiry; rotate/revoke as supported, invalidate logout/recovery sessions. No tokens in URLs/logs. |
| Secrets/Git | API/service secrets stay server-side or in protected runtime configuration, never shipped bundles. Restricted publishable keys are distinct. Keep secret-bearing `.env` files untracked/ignored; preserve local copies and sanitized examples. Check tracked files, history and build artifacts. If leaked, revoke/rotate with authority first; deletion alone fails. Coordinate authorized history cleanup; no silent force-push. |
| Logs/data | Follow [safe logging](app-diagnostics.md): redact before sinks/replay/crash capture; no passwords, tokens, credentials or unnecessary private payloads. Keep useful events, bounded retention and restricted access. Protect sensitive storage/backups and cross-user caches; collect only needed data. |
| Inputs/queries | Validate types, lengths, ranges, allowed fields and business rules at the trusted boundary; client validation is UX. Parameterize SQL; allowlist dynamic identifiers. Reject unsafe command/template/deserialization paths. Validate URLs/redirects; server fetches must not expose internal networks or metadata services. |
| XSS/CSRF | Context-aware output encoding and safe framework sinks; sanitize permitted rich HTML with a maintained sanitizer. No raw untrusted HTML/script. Use fitting CSP as defense-in-depth. Protect cookie-authenticated mutations against CSRF; no state changes through GET. CORS is neither authorization nor CSRF protection. |
| Uploads | Check authorization, size/count, extension, detected type/content and parser limits; distrust MIME/name. Generated storage names, traversal/archive-bomb protection, non-executable isolated storage and authorized downloads. Scan/re-encode where risk warrants; don't serve active uploads on a trusted app origin. |
| Webhooks | Verify provider signatures over the required original bytes before effects, with the right endpoint secret. Enforce freshness/replay controls where supported; deduplicate events, make retries idempotent. Never trust unsigned payloads or IP allowlists alone. |
| Abuse/CORS | Cover exposed request surfaces with suitable rate, size, concurrency and cost limits; prioritize login/reset, search, uploads and expensive work. Use user/key/IP limits, trusted proxy handling and shared counters where needed. No identical limit for every route; preserve legitimate traffic/webhook retries. Restrict CORS to needed origins/methods/headers; no arbitrary origin reflection or wildcard credentials. Disable cross-origin access when unnecessary. |
| Deployment/dependencies | Before exposure: HTTPS, valid certificates, production config, no debug consoles/stack traces/default credentials/test bypasses, least-privilege network/storage access and fitting security headers. Review direct/transitive dependencies, lockfiles and actual advisories; update vulnerable supported versions compatibly. No blind major upgrades or invented CVEs. |

## Verify and review

Finish implementation, then manually exercise applicable success and denial paths using harmless authorized accounts/data: anonymous/user/admin, cross-user/tenant, tampered/expired tokens, invalid inputs/uploads, forged/replayed webhooks and safe log output. Never probe unrelated systems or load production without authority. Fix and recheck affected behavior.

Then author/run relevant final regressions and secret/dependency/static checks under [tests-last order](../../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests). No early scanner suites. Read source/advisories during development; validate dangerous behavior only in a controlled environment.

Use the existing independent [security code review](../../deep-review/references/theme-security.md). Trace input → authority → data/effect; inspect config, dependencies and evidence, not scanner scores alone. No extra review fleet.

Record `surface → control → evidence → PASS / FAIL / UNKNOWN / justified N/A`. Local development can continue with documented gaps. Before public exposure or production, fix demonstrated compromise risks or isolate/disable affected paths; unresolved material checks prevent a ready claim. Lower-risk deferrals need reason, owner and revisit trigger; mandatory exceptions retain existing authority rules. No blanket enterprise checklist or security guarantee.

[Sources and original adaptation](../../../../docs/skill-provenance.md#application-security-4-october-2026).
