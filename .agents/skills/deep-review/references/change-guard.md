# Change Guard

Post-implementation verification. Run this after every code change to catch damage before it ships.

One question: what elsewhere silently depends on this, and did the change pull the rug out?

Per edit: inspect source/diff. Actual actions/checks wait until the complete iteration is finished. Map change -> consumers -> required evidence. After a repair, rerun all configured checks. Reuse proof only when its inputs are exactly unchanged.

## Instructions

1. **Identify all files modified** in the current session or diff
2. **For each changed file**, read the full file and analyze it
3. **For each changed symbol, param, route, key or setting**, list everywhere it is used, including string and dynamic references, and check each still holds
4. **Read unchanged callers and dependents**. Prefer search/read over assumption

### Checklist

Copy and track:

```
Change Guard Report:
- [ ] No existing functionality broken
- [ ] No unintended logic changes
- [ ] No breaking changes introduced
- [ ] No data or runtime compatibility break
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
- Confirm loop boundaries, iteration order, early returns and termination conditions
- Verify type coercions, null checks, and guard clauses remain
- Check that side effects (DB writes, API calls, event emissions) are unchanged: none dropped or doubled, including navigation, notifications, analytics, cache invalidation, queued work, saves, uploads and purchases. Inspect subscriptions and lifecycle dependencies
- Check changed cache identities/invalidation do not leave consumers stale or mix user, session or version data

### Step 3: Breaking Changes

- Check public API signatures (controllers, services, DTOs) and every consumer of them
- Verify interface contracts and type definitions; types catch only some breaks
- Check renamed routes, commands and parameters: links, saved navigation, scripts and integrations
- Check changed shared state shape: every reader and writer
- Check removed/renamed exports, enums and storage/cache keys across the whole repository
- Check configuration changes that affect other modules, defaults, generated artifacts and deployment bindings
- Look for changed environment variable usage
- Verify database schema compatibility
- Check for changed event names, queue names, or message formats, including older/newer clients and services outside this repository. Label consumers you cannot verify

### Step 4: Data and Runtime Compatibility

- Old installations, databases or saved data lack new keys/columns/shapes: verify migrations, backfills and defaults; preserve supported upgrade and rollback paths
- Destructive clears, lost drafts/saves, unintended logout, duplicate effects or partial migrations
- Separately shipped parts (client/server, scripts/native binary, plugin/host, schema/save formats) update independently. A capability missing in a supported older runtime crashes it. Require compatible packaging or gating and a safe mixed-version rollout
- Dependency version bumps with breaking changes; removed dependencies or files still imported; generated artifacts or platform bindings out of sync

### Step 5: Hidden Bugs

- Look for off-by-one errors, race conditions, memory leaks
- Check for unhandled promise rejections or missing awaits
- Verify null/undefined safety on new code paths
- Check for circular dependencies introduced: run the project's checker or trace the changed import graph
- Look for hardcoded values that should be configurable
- Verify error messages are accurate and helpful

## Calibrate

- Additive, backward-compatible changes are low-risk. Say so; don't manufacture drama.
- Dynamically referenced code, string routes/keys and platform module names may look dead. Mark **KEEP** when used; do not recommend deletion.

## Output Format

Issues use the finding format from SKILL.md. Category: `broken-func`, `logic-change`, `breaking`, `compatibility`, `hidden-bug`.

Severity: CRITICAL definite existing-behavior break, incompatible-runtime crash or release hazard. HIGH likely break or unverified caller. MEDIUM risky, needs a guard or test. LOW minor. Impact: what used to work, what now fails, for whom.

```markdown
## Change Guard Report

### Files Analyzed
| File | Status |
|------|--------|
| path/to/file | PASS / ISSUE FOUND |

### Issues Found
[Finding rows]

### Verdict
PASS - Safe to proceed / FAIL - Issues must be addressed
```

If no issues found, output a clean PASS verdict with confidence level.
