---
name: deep-review
description: Deep code analysis and review that hunts for bugs, oversights, anti-patterns, performance issues, stupid mistakes, potential blockers, wrong implementations, and bad code. Use when wanting a thorough code review, quality audit, or pre-merge verification of implementation quality.
---

# Deep Review

Ruthless code review. No mercy, no shortcuts. Find every damn problem.

## Instructions

1. **Identify the scope** - all files modified/created in the current task
2. **Read every file** in scope, fully
3. **Analyze against each category below**
4. **Produce the summary table** - no fluff, just findings

### Analysis Categories

#### 1. Bugs
- Logic errors, wrong conditions, incorrect comparisons
- Missing null/undefined checks
- Unhandled exceptions or promise rejections
- Missing await on async calls
- Wrong variable used (copy-paste errors)
- Array/object mutation when immutability expected
- Off-by-one errors

#### 2. Oversights
- Missing edge cases (empty arrays, null inputs, concurrent access)
- Forgotten cleanup (subscriptions, listeners, timers, streams)
- Missing validation on inputs (DTOs, params, query strings)
- Incomplete error handling (catch blocks that swallow errors)
- Missing logging for debugging critical paths
- Forgotten TODO/FIXME items that should be addressed now

#### 3. Anti-Patterns
- God classes or functions doing too much
- Tight coupling between modules
- Magic numbers/strings without constants
- Callback hell or deeply nested conditionals
- Premature abstraction or over-engineering
- Violating SOLID, DRY, SRP, KISS principles
- Circular dependencies

#### 4. Performance Issues
- N+1 queries or unnecessary DB calls
- Missing indexes on queried fields
- Unbounded data fetching (no pagination/limits)
- Synchronous operations that should be async
- Memory leaks (unclosed streams, growing arrays, retained references)
- Unnecessary re-computation (missing caching/memoization)
- Heavy operations in hot paths

#### 5. Stupid Mistakes
- Console.log left in production code
- Commented-out code that should be removed
- Dead code or unreachable branches
- Wrong file/module imported
- Copy-pasted code with unchanged variable names
- Typos in string literals, enum values, or identifiers

#### 6. Potential Blockers
- Missing environment variables or config
- Undeclared dependencies
- Breaking changes to shared interfaces
- Missing database migrations
- Incompatible version requirements
- Missing permissions or auth checks

#### 7. Wrong Implementation
- Doesn't match requirements or intended behavior
- Solves the wrong problem
- Incorrect algorithm or data structure choice
- Wrong HTTP method, status code, or response format
- Misuse of framework/library APIs

#### 8. Bad Code
- Poor naming (single letters, misleading names, abbreviations)
- Functions over 50 lines
- Files over 500 lines
- No error messages or unhelpful ones
- Inconsistent patterns within the same module
- Missing TypeScript types (any, unknown abuse)

## Output Format

**Do NOT factor development time. Focus purely on impact to the application.**

```markdown
## Deep Review Report

### Scope
[List files reviewed]

### Summary Table
| # | Category | Severity | File:Line | Finding | Impact |
|---|----------|----------|-----------|---------|--------|
| 1 | Bug | CRITICAL/HIGH/MEDIUM/LOW | file.ts:42 | Description | What breaks |

### Severity Guide
- CRITICAL: Will cause failures in production
- HIGH: Likely to cause issues, must fix
- MEDIUM: Should fix, could cause problems
- LOW: Code quality, nice to fix

### Stats
- Total findings: X
- Critical: X | High: X | Medium: X | Low: X

### Top 3 Priority Fixes
1. [Most impactful finding]
2. [Second most impactful]
3. [Third most impactful]

### Verdict
[Overall assessment - is this code ready to ship?]
```
