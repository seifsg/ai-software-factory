# Synthesis, verdict and fix selection

Pool analysis plus the three deep-review passes, change-guard and compliance-check. Merge duplicate root causes at the higher severity, retain the contributing lenses, and rank impact rather than development time.

| # | Severity | Lenses | File:line / evidence | Finding | Impact | Fix now? | Confidence |
|---|---|---|---|---|---|---|---|

Use CRITICAL > HIGH > MEDIUM > LOW. Normalize change-guard CRITICAL → CRITICAL, WARN → HIGH, INFO → LOW. Duplicate/stacked, wrong/confusing, or silent user feedback floors at MEDIUM; never call it cosmetic to waive it.

Make cross-cutting judgments explicit: worthwhile in-scope opportunities, necessary complexity to KEEP, and compliance with the original goal. New substantive design decisions belong to Seif. Unrequested opportunities are notes unless clearly minor, authorized and in scope.

**Fix now** only when the defect is supported, the correction is localized and within authority, confidence is high (or medium with an obvious safe correction), and verification is possible. **Flag only** for scope/design decisions, large refactors, low confidence, uncertain necessary complexity, or environment-specific changes that cannot be validated. A flag is not permission to accept a material defect.

| Verdict | Meaning after corrections |
|---|---|
| APPROVE | Goal delivered; all required checks and workflow steps evidenced; no unresolved material findings |
| APPROVE-WITH-FIXES | Bounded corrections verified by a fresh independent assessment; same acceptance conditions as APPROVE |
| REQUEST-CHANGES | Supported material findings or decisions remain; cannot safely correct within authority |
| BLOCK | Critical issue, failed/missing required gate, inaccessible essential evidence, missing independent execution, or unresolved required task/handoff binding |

The source's severity ladder and four verdicts are preserved. Seif's selected exact-evidence and acceptance rules tighten approval: unresolved CRITICAL/HIGH/MEDIUM findings cannot silently pass. An exception needs the actual authorized policy/decision; do not invent waivers. State code findings and workflow blockers separately while keeping one honest overall verdict.

Keep open questions, retries used, remaining shared budget and the next responsible action. No verdict grants ready/merge/release authority.
