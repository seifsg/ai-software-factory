---
name: change-guard
description: Post-change verification guard that checks if recent code changes broke existing functionality, altered logic unintentionally, introduced breaking changes, or hid bugs. Use after completing any code modification, refactor, or feature implementation to verify nothing was damaged.
---

# Change Guard

Post-implementation verification. Run this after every code change to catch damage before it ships.

Per edit: inspect source/diff. Actual actions and automated checks wait until the complete iteration is finished. Map change -> affected consumers -> checks -> valid prior evidence. Broaden for shared behavior, changed inputs or unresolved risk. Keep required gates. Ordinary controller repair runs all configured checks; records-only reuse needs exact unchanged inputs/provenance. [Working iterations](../safe-engine/references/delivery-readiness.md#working-iterations).

## Instructions

1. **Identify all files modified** in the current session or diff
2. **For each changed file**, read the full file and analyze:

### Checklist

Copy and track:

```
Change Guard Report:
- [ ] No existing functionality broken
- [ ] No unintended logic changes
- [ ] No breaking changes introduced
- [ ] No hidden bugs or issues
```

### Step 1: Broken Functionality

- Compare the before/after behavior of every modified function
- Check if any callers of modified functions still work correctly
- Verify imports, exports, and module boundaries are intact
- Confirm error handling paths still function
- Check if removed or renamed symbols are still referenced elsewhere

### Step 2: Unintended Logic Changes

- Verify conditional branches haven't been accidentally altered
- Check that default values, fallbacks, and edge cases are preserved
- Confirm loop boundaries, iteration order, and termination conditions
- Verify type coercions, null checks, and guard clauses remain
- Check that side effects (DB writes, API calls, event emissions) are unchanged

### Step 3: Breaking Changes

- Check public API signatures (controllers, services, DTOs)
- Verify interface contracts and type definitions
- Check configuration changes that affect other modules
- Look for changed environment variable usage
- Verify database schema compatibility
- Check for changed event names, queue names, or message formats

### Step 4: Hidden Bugs

- Look for off-by-one errors, race conditions, memory leaks
- Check for unhandled promise rejections or missing awaits
- Verify null/undefined safety on new code paths
- Check for circular dependencies introduced
- Look for hardcoded values that should be configurable
- Verify error messages are accurate and helpful

## Output Format

In each issue row, Description names layer (`product`, `evidence`, `report`), impact, raw proof and clear action. Link details if needed. Keep missing/challenged proof explicit.

```markdown
## Change Guard Report

### Files Analyzed
| File | Status |
|------|--------|
| path/to/file.ts | PASS / ISSUE FOUND |

### Issues Found
| # | Severity | Category | File | Description |
|---|----------|----------|------|-------------|
| 1 | CRITICAL/WARN/INFO | broken-func/logic-change/breaking/hidden-bug | file.ts | What went wrong |

### Verdict
PASS - Safe to proceed / FAIL - Issues must be addressed
```

If no issues found, output a clean PASS verdict with confidence level.
