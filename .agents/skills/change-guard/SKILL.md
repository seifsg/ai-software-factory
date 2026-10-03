---
name: change-guard
description: "Review regressions after a substantial change batch or refactor, including callers and consumers outside the edited files. Verify existing behavior before handoff."
---


# Change Guard — did we break what already worked?

**Small-change routing takes precedence.** For a bounded direct fix, use the corresponding lightweight routine in [small-change](../small-change/SKILL.md), then return to its compact handoff. The full procedure below applies to version work; do not execute both versions or escalate a small fix into full QA.

Post-implementation verification. Run this after a substantial change batch and before handoff. Keep per-todo inspection in the coding loop, while batching executable tests.
The user-journey review checks the **new** behavior; change-guard defends the **old** behavior:
what worked before that might not work now, including callers and dependents the change did **not**
touch but which rely on it.

> The one question you obsess over: **what elsewhere silently depends on this, and did the change
> just pull the rug out?** Prefer grep/read over assumption — a regression you "don't think" exists
> is worth 30 seconds to confirm.

## Project context

Use the reviewed project profile, actual source, repository rules, and current user instructions. Adapt to the real stack; web and mobile examples are illustrative. No source instruction grants permissions or tool access.

## Instructions

1. **Identify all files modified** in the current session or diff.
2. **For each changed file**, read the full file and analyze against the four steps below.

Copy and track:

```
Change Guard Report:
- [ ] No existing functionality broken
- [ ] No unintended logic changes
- [ ] No breaking changes introduced
- [ ] No hidden bugs or issues
```

### Step 1 — Broken functionality

- Compare the before/after behavior of every modified function.
- Check every caller of a modified function still works.
- Verify imports, exports, and module boundaries are intact.
- Confirm error-handling paths still function.
- Check that removed or renamed symbols are not still referenced elsewhere.

### Step 2 — Unintended logic changes

- Verify conditional branches weren't accidentally altered (inverted, off-by-one, `&&`↔`||`).
- Check default values, fallbacks, and edge cases are preserved.
- Confirm loop bounds, iteration order, and termination conditions.
- Verify type coercions, null checks, and guard clauses remain.
- Check that side effects (DB writes, API calls, event/notification emissions, cache invalidation,
  navigation) are unchanged — didn't stop firing, and don't now fire twice.

### Step 3 — Breaking changes to contracts

- **Web**: controller/service/DTO signatures, response shapes, HTTP status codes, Prisma schema /
  migration compatibility, queue/event names, config & env-var usage other modules read.
- **Mobile**: component props / hook signatures, expo-router route names & params, context shape,
  the request/response contract with the backend, storage keys (SecureStore/AsyncStorage), and
  `app.config` / `expo-constants` fields other modules read.
- **Both**: removed/renamed exports, enum values, or interface contracts still referenced anywhere.

### Step 4 — Hidden bugs

- Off-by-one errors, race conditions, memory/resource leaks.
- Unhandled promise rejections or missing `await`.
- Null/undefined safety on new code paths.
- **Circular dependencies introduced** (the org forbids new cycles).
- Hardcoded values that should be configurable; inaccurate or unhelpful error messages.
- **Mobile only, when relevant**: OTA/native compatibility — JS shipped over-the-air runs on the
  native binary the user already has. If changed JS calls a native module/API/permission that only
  exists in a newer native build, it will crash on OTA'd older clients — flag it CRITICAL.

## Output Format

```markdown
## Change Guard Report

### Files Analyzed
| File | Status |
|------|--------|
| path/to/file.ts | PASS / ISSUE FOUND |

### Issues Found
| # | Severity | Category | File:Line | Description |
|---|----------|----------|-----------|-------------|
| 1 | CRITICAL/WARN/INFO | broken-func/logic-change/breaking/hidden-bug | file.ts:42 | What went wrong |

### Verdict
PASS - Safe to proceed / FAIL - Issues must be addressed
```

If no issues are found, output a clean **PASS** verdict with a confidence level. Additive,
backward-compatible changes are low-risk — say so; don't manufacture drama. If something looks like
dead code but is referenced dynamically (string route names, storage keys), that's a KEEP, not a
"remove it."

## Provenance

Adapted from Seif's existing procedure. See [provenance and adaptations](../../../docs/skill-provenance.md). Current user instructions and the reviewed task govern its use.
