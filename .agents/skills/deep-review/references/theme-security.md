# Review lens — SECURITY

You are reviewing your own freshly-drafted pull request through a single lens: **security**. Read
the actual changed files on the checked-out branch. Assume inputs can be hostile: every request
body, query param, deep link, and server/client response is potentially attacker-controlled.

The one question you obsess over: **can this leak data, expose a secret, or be abused via an
untrusted input the code trusts?**

## Essential checks — repo-agnostic

Apply to the target project's actual stack and trust boundaries. Web and mobile mechanisms below are examples, not required technologies.

- **Secrets** — real server/service secrets (DB URLs, signing keys, third-party API secrets) stay
  server-side and out of the repo. Anything in a client bundle or config ships to the user and is
  public; only publishable/anon keys belong there. A real secret shipped client-side is CRITICAL.
- **Token / PII storage** — sensitive data goes in encrypted, appropriate storage (e.g. httpOnly
  cookies on web, the OS keychain via secure storage on mobile), never plaintext or in logs.
  Moving sensitive data into unencrypted storage is CRITICAL.
- **Injection** — parameterized queries (no string-built SQL); validate and sanitize all inputs,
  DTOs, and params before they drive queries, navigation, or auth.
- **Untrusted input trusted by the code** — missing/loosened auth guards, IDOR (object access
  without ownership check), missing role checks, mass-assignment; untrusted URLs/deep-links or
  embedded content (e.g. a WebView payload, server-rendered HTML) driving privileged actions.
- **Data exposure & logging** — over-broad responses returning more PII than needed; secrets/PII
  in logs, analytics, crash reports, or session replay; verbose error stacks to the client.
- **Transport & permissions** — no cleartext `http://` for real data, no disabled TLS/cert
  validation, no over-permissive CORS; new device permissions scoped and their denial handled.
- **Dependencies** — new dep with a bad reputation, large attack surface, or unpinned/typosquatted.

## Calibrate — don't cry wolf

- Client-side "auth" is UX, not a security boundary — the **real** check is server-side. Don't flag
  the *absence* of client enforcement, but DO flag code *trusting* client-side state for something
  the backend must verify.
- Publishable/anon keys (e.g. a Supabase anon key, a client analytics token) are meant to ship —
  distinguish them from real secrets.
- A guard/whitelist that looks redundant may be defense-in-depth — mark KEEP, don't delete it.
- **Never weaken security to make a build pass or to simplify.** This is a hard gate.

## Output — return exactly this

```
| # | Severity | File:Line | Finding | Impact | Recommendation | Confidence |
|---|----------|-----------|---------|--------|----------------|------------|
```

- **Severity**: CRITICAL (real secret shipped, sensitive data in unencrypted storage/logs, injection
  or auth-bypass leading to account/data compromise) · HIGH (exploitable with conditions) · MEDIUM
  (hardening) · LOW (hygiene).
- **Impact**: what leaks / who gets in / what they can do.
- **Confidence**: HIGH / MED / LOW.

End with: `SECURITY VERDICT: <clean | hardening-needed | vulnerable | blocker> — <one sentence>`
A clean pass is valid — say so plainly if the change is genuinely safe.
