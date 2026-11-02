# Change Guard

Post-implementation verification. Run after every code change to catch damage before it ships.

One question: what elsewhere silently depends on this, and did the change pull the rug out?

Per edit: inspect source/diff. Actual actions/checks wait until whole iteration is finished. Map change -> consumers -> required evidence. After a repair, rerun all configured checks. Reuse proof only when its inputs are exactly unchanged.

## Instructions

1. **Identify all files modified** in current session or diff
2. **For each changed file**, read the full file and analyze it
3. **For each changed symbol, param, route, key or setting**, list every use, including string and dynamic references, and check each still holds
4. **Read unchanged callers and dependents**. Search/read, do not assume

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

- Compare before/after behavior of every modified function
- Check callers of modified functions still work
- Verify imports, exports, module boundaries intact
- Confirm error handling paths still function
- Check removed or renamed symbols for remaining references

### Step 2: Unintended Logic Changes

- Verify conditional branches not accidentally altered
- Check default values, fallbacks, edge cases preserved
- Confirm loop boundaries, iteration order, early returns, termination conditions
- Verify type coercions, null checks and guard clauses remain, unless a stronger guarantee replaces them in the same change (defense in depth stays)
- Check side effects (DB writes, API calls, event emissions) unchanged: none dropped or doubled, including navigation, notifications, analytics, cache invalidation, queued work, saves, uploads and purchases. Inspect subscriptions and lifecycle dependencies
- Check changed cache identities/invalidation leave no stale consumers and mix no user, session or version data

### Step 3: Breaking Changes

- Check public API signatures (controllers, services, DTOs) and every consumer
- Verify interface contracts and type definitions; types catch only some breaks
- Check renamed routes, commands and parameters: links, saved navigation, scripts, integrations
- Check changed shared state shape: every reader and writer
- Check removed/renamed exports, enums and storage/cache keys across whole repository
- Check configuration changes that affect other modules, defaults, generated artifacts, deployment bindings
- Look for changed environment variable usage
- Verify database schema compatibility
- Check changed event names, queue names, message formats, including older/newer clients and services outside this repository. Label consumers you cannot verify

### Step 4: Data and Runtime Compatibility

- Old installations, databases or saved data lack new keys/columns/shapes: verify migrations, backfills, defaults; keep supported upgrade and rollback paths
- Destructive clears, lost drafts/saves, unintended logout, duplicate effects, partial migrations
- Separately shipped parts (client/server, scripts/native binary, plugin/host, schema/save formats) update independently. Capability missing in a supported older runtime crashes it. Require compatible packaging or gating and a safe mixed-version rollout
- Dependency version bumps with breaking changes; removed dependencies or files still imported; generated artifacts or platform bindings out of sync

### Step 5: Hidden Bugs

- Look for off-by-one errors, race conditions, memory leaks
- Check unhandled promise rejections, missing awaits
- Verify null/undefined safety on new code paths
- Check for new circular dependencies: run the project's checker or trace the changed import graph
- Look for hardcoded values that should be configurable
- Verify error messages are accurate and helpful

## Calibrate

- Additive, backward-compatible changes = low risk. Say so; no manufactured drama.
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

No issues: clean PASS verdict with confidence level.
