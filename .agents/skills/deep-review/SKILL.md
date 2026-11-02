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

## Additions for every review

Read-only: no fixes unless told. Does the journey work? Keep overall requirements open. Size or code style prompts inspection; prove impact before blocking. UI below journey's look bar blocks.

- Scope adds callers and consumers. First gather baseline: request, confirmed criteria, plan, project rules, raw evidence (logs, manual QA notes, check results).
- Read code around each file too; diff alone is not enough. Then run lenses below.
- No test suites during review unless told.
- Label every claim verified (read or observed) or hypothesis. A raw count = hypothesis about impact until you read what it means.
- Any language: its debug output and loose types count in categories 5 and 8.
- Also hunt: non-critical integrations (analytics, history, messaging) breaking main logic when they fail; valid actions that leave unrecoverable state (creation, update, save and load limits must agree); bypassing project's wrapper for config or shared integrations; guards for states the design rules out (not defense in depth).
- Factory rules, for our own work (someone else's project: judge by its rules): extra code or over-engineering (least code that fully solves the problem; logic only, UI: best look); not O(1) or as close as the real workload allows, wasted CPU or memory; new code where an existing function fits; placeholders, stubs or TODOs; files at 1000 lines or more not split; functions without a short comment saying what they do and why; one more pass: less code? less complexity? faster?

### Lenses

| Lens | Load when |
|---|---|
| [change-guard](references/change-guard.md) | Existing code, contracts, config or data changed. |
| [compliance](references/compliance.md) | Always: a request, criteria, plan or project rules exist. |
| [security](references/security.md) | Input, auth, sessions, secrets, data, files, network, logs, dependencies or deployment touched. |
| [performance](references/performance.md) | Loops, rendering, queries, I/O, caching, concurrency, memory, assets or startup touched. |
| [journey](references/journey.md) | User- or consumer-visible behavior changed. |

Lenses may run as isolated parallel reviewers. Give each: scope, baseline, raw evidence, its lens, finding format below. Reviewers verify hypotheses and request missing evidence; an omission cannot hide a risk.

### Scale to the change

- Bounded fix: one independent reviewer covers changed lines, surrounding code, consumers and applicable lenses together. No whole-project audit, alternative designs or unrelated fixes.
- Update to reviewed change: review delta and its consumers; carry unresolved earlier findings. Do not re-audit accepted code.
- Repeat checks only for changed code or inputs, failures or unresolved concerns.
- State exact verdict scope. Narrow review never approves an unreviewed whole.

### Findings

Report = Output Format template; lens reports go inside it. Finding format, rows most severe first:

| # | Category | Severity | File:Line | Finding | Impact | Layer | Evidence | Fix | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Bug | HIGH | file.ts:42 | Description | What breaks, for whom | product | Raw proof: code, log, observation | Clear fix | HIGH |

Scope also names baseline, lenses run and verdict scope; `### Unknowns` (required evidence still missing) follows the Summary Table; verdict starts with PASS, FAIL or CONDITIONAL.

- Score every finding with [worth-it](references/worth-it.md).
- Layer: `product` (code or behavior), `evidence` (proof missing or wrong), `report` (claim does not match result). Fix the affected layer. Proof gap needs actual verification, not a label.
- Confidence: HIGH / MED / LOW.
- Load-bearing code is not over-engineering: mark **KEEP** with reason.
- Edge-case fix: at root cause, first rung that fits (impossible by design; normalized or rejected loudly at entry; specified, logged behavior); state beyond data, config and platform in use: one loud assertion. One cause, one finding.
- Out-of-scope opportunities: list as notes, not findings.
- Clean pass is valid. Invent no findings.

### Verdict

Disposition decides the gate: `blocking`, `before-exposure` or `accepted-deferral`.

- Blocking: any CRITICAL or HIGH, unmet core requirement, broken existing journey, required UNKNOWN, mandatory rule violated without authorized exception. Clean code that solves the wrong problem fails.
- UNKNOWN is never N/A; N/A needs evidence. Missing required evidence stays UNKNOWN and blocks dependent judgment.
- Deferral needs owner authority and a record: owner, reason, scope, its entry in follow-ups ticket, revisit trigger. A note alone grants nothing.
- Owner may delegate in advance deferral of LOW findings, and of MEDIUM while exposure stays local. MEDIUM and LOW left after round 3 go to the epic's one open follow-ups ticket in Backlog, never one ticket per finding. HIGH and CRITICAL never deferred.
- Before-exposure items resolve before public exposure or production. MEDIUM is not automatically a failure, and never silently waived.
- Verdict that depends on fixes not yet applied = **conditional**. Judge the actual candidate.

`PASS`: no blocking finding; every other finding listed with its disposition. `FAIL`: any blocking finding. PR verdicts: `how-to-review-a-pr`.

### Fixes and review rounds

- When told to fix: smallest change that removes the cause, affected layer only, intent unchanged. Then a fresh independent reviewer, not the fixer, assesses the result. Clean review needs no edits.
- One round = independent review, selected fixes, fresh review. Mandatory findings keep it open; optional fixes follow worth-it. Rounds 1-3 run; rounds 4 and 5 only while an open CRITICAL finding remains.
- After round 5, or round 3 with no open CRITICAL, stop that loop. Give owner one short packet: findings per round (new vs repeated), shared cause, options (extend, defer with owner record, amend scope, cancel).
- Keep independent work moving while you wait.

## Output contract

In a factory run this is step 6, Verify: builder runs this pass, independent review is step 8 (`how-to-review-a-pr`). The block `## 6 Verify` holds:

- [ ] Every requested journey used through real controls, with observed results
- [ ] compliance results, change-guard results when existing code, contracts or data changed, plus each other lens run, each with its findings table (possibly empty) and verdict, e.g. `**compliance:** <its table, or "no findings"> · PASS`
- [ ] An `after-<id>` file for every proof-list id, same ids as Before, captured in that same pass on the verified head, each naming that commit; a later edit recaptures the ids it touches; a full-suite id is that final run
- [ ] UI pass (new UI): analyst misses vs step 2 look + refs, primary platform; else `existing` or `no UI`
- [ ] The full suite: command and result, run once after manual use
- [ ] The verdict; blocking findings fixed through the build loop before the gate
