---
name: deep-review
description: Ruthless review of a code change, a finished feature or a pull request. Hunts bugs, oversights, anti-patterns, regressions, requirement and rule gaps, security holes, performance problems and broken user journeys, then gives one evidence-backed verdict. Use when reviewing a diff or change, verifying work before merge, auditing implementation quality, re-reviewing fixes from an earlier review, or reviewing an incoming pull request.
---

# Deep Review

Read-only. Do not fix unless told to.
Judge severity by impact; effort only prioritizes optional polish.

Review the complete iteration and affected consumers. Does the journey work? Separate blockers from polish; keep the overall requirements open. Size/style prompts inspection; prove impact before blocking.

## Instructions

1. **Identify the scope**: all files modified/created in the task, plus their callers and consumers.
2. **Gather the baseline**: request, confirmed criteria, plan, project rules, raw evidence (logs, manual QA observations, check results).
3. **Read every file** in scope, fully, and the code around it. The diff alone is insufficient.
4. **Deep bug hunt**: every category below.
5. **Lenses**: load each reference only when its line applies.
6. **Produce the report**: no fluff, just findings, then one verdict.

Inspect source, diffs, logs and supplied evidence. Run no test suites during review unless told.
Label every claim verified (read or observed) or hypothesis. A raw count is a hypothesis about impact until you read what it means.

## Lenses

| Lens | Load when |
|---|---|
| [change-guard](references/change-guard.md) | Existing code, contracts, config or data changed. |
| [compliance](references/compliance.md) | Always: a request, criteria, plan or project rules exist. |
| [security](references/security.md) | Input, auth, sessions, secrets, data, files, network, logs, dependencies or deployment touched. |
| [performance](references/performance.md) | Loops, rendering, queries, I/O, caching, concurrency, memory, assets or startup touched. |
| [journey](references/journey.md) | User- or consumer-visible behavior changed. |

Lenses may run as isolated parallel reviewers. Give each the scope, baseline, raw evidence, its lens and the finding format below. Reviewers verify hypotheses and request missing evidence; an omission cannot hide a risk.

## Scale to the change

- Bounded fix: one independent reviewer covers changed lines, surrounding code, consumers and the applicable lenses together. No whole-project audit, alternative designs or unrelated fixes.
- Update to a reviewed change: review the delta and its consumers; carry unresolved earlier findings. Do not re-audit accepted code.
- Repeat checks only for changed code or inputs, failures or unresolved concerns.
- State the exact verdict scope. A narrow review never approves an unreviewed whole.

## Analysis Categories

### 1. Bugs
- Logic errors, wrong conditions, incorrect comparisons
- Missing null/undefined checks
- Unhandled exceptions or promise rejections
- Missing await on async calls
- Wrong variable used (copy-paste errors)
- Array/object mutation when immutability expected
- Off-by-one errors

### 2. Oversights
- Missing edge cases (empty arrays, null inputs, concurrent access)
- Forgotten cleanup (subscriptions, listeners, timers, streams)
- Missing validation on inputs (DTOs, params, query strings)
- Incomplete error handling (catch blocks that swallow errors)
- Non-critical integrations (analytics, history, messaging) breaking the main logic when they fail
- Missing logging for debugging critical paths
- Forgotten TODO/FIXME items that should be addressed now
- Valid actions must leave recoverable state. Check creation, update, save and load limits agree.

### 3. Anti-Patterns
- God classes or functions doing too much
- Tight coupling between modules
- Magic numbers/strings without constants
- Callback hell or deeply nested conditionals
- Premature abstraction or over-engineering
- Violating SOLID, DRY, SRP, KISS principles
- Bypassing the project's wrapper for config or shared integrations
- Circular dependencies

### 4. Performance Issues
- N+1 queries or unnecessary DB calls
- Missing indexes on queried fields
- Unbounded data fetching (no pagination/limits)
- Synchronous operations that should be async
- Memory leaks (unclosed streams, growing arrays, retained references)
- Unnecessary re-computation (missing caching/memoization)
- Heavy operations in hot paths

### 5. Stupid Mistakes
- Debug output (console.log, print) left in production code
- Commented-out code that should be removed
- Dead code, unreachable branches, guards for states the design rules out (not defense in depth)
- Wrong file/module imported
- Copy-pasted code with unchanged variable names
- Typos in string literals, enum values, or identifiers

### 6. Potential Blockers
- Missing environment variables or config
- Undeclared dependencies
- Breaking changes to shared interfaces
- Missing database migrations
- Incompatible version requirements
- Missing permissions or auth checks

### 7. Wrong Implementation
- Doesn't match requirements or intended behavior
- Solves the wrong problem
- Incorrect algorithm or data structure choice
- Wrong HTTP method, status code, or response format
- Misuse of framework/library APIs

### 8. Bad Code
- Poor naming (single letters, misleading names, abbreviations)
- Functions over 50 lines
- Files over 500 lines (inspect; 1000 or more must be split)
- No error messages or unhelpful ones
- Inconsistent patterns within the same module
- Loose or missing types (any, unknown abuse)

### 9. Factory Rules

Our own work. Someone else's project: judge by its rules instead.

- Extra code or over-engineering. Least code that fully solves the problem.
- Not O(1) or as close as the real workload allows; wasted CPU or memory
- New code where an existing function fits
- Placeholders, stubs or TODOs left behind: not production ready
- Files at 1000 lines or more: must be split
- Functions without a short comment saying what they do and why
- One more pass: less code? less complexity? faster?

## Findings

Score every review/check finding with [worth-it](references/worth-it.md). Keep severity, disposition and proof.

| # | Severity | Category / layer | File:Line | Finding / impact | Evidence | Fix | Confidence |
|---|----------|------------------|-----------|------------------|----------|-----|------------|
| 1 | HIGH | Bug / product | file.ts:42 | What breaks, for whom | Raw proof: code, log, observation | Clear fix | HIGH |

- Severity: CRITICAL will cause failures in production. HIGH likely to cause issues, must fix. MEDIUM should fix, could cause problems. LOW code quality, nice to fix.
- Layer: `product` (code or behavior), `evidence` (proof missing or wrong), `report` (claim does not match result). Fix the affected layer. A proof gap needs actual verification, not a label.
- Confidence: HIGH / MED / LOW. Label hunches.
- Load-bearing code is not over-engineering: mark it **KEEP** with the reason.
- Edge-case fix: at the root cause, first rung that fits (impossible by design; normalized or rejected loudly at entry; specified, logged behavior); a state beyond the data, config and platform in use: one loud assertion. One cause, one finding.
- Out-of-scope opportunities: list as notes, not findings.
- A clean pass is valid. Invent no findings.

## Verdict

Severity is impact. Disposition decides the gate: `blocking`, `before-exposure` or `accepted-deferral`.

- Blocking: any CRITICAL or HIGH, an unmet core requirement, a broken existing journey, a required UNKNOWN, a mandatory rule violated without an authorized exception. Clean code that solves the wrong problem fails.
- UNKNOWN is never N/A. Missing required evidence stays UNKNOWN and blocks dependent judgment. N/A needs evidence.
- Deferral needs owner authority and a record: owner, reason, scope, its entry in the follow-ups ticket, revisit trigger. A note alone grants nothing.
- The owner may delegate in advance the deferral of LOW findings, and of MEDIUM while exposure stays local. MEDIUM and LOW left after round 3 are appended to the epic's one open follow-ups ticket in Backlog, never one ticket per finding. HIGH and CRITICAL are never deferred.
- Before-exposure items resolve before public exposure or production. A MEDIUM is not automatically a failure, and never silently waived.
- Mandatory rule exceptions need an authorized owner, scope and record. Explanation alone waives nothing.
- A verdict that depends on fixes not yet applied is **conditional**. Judge the actual candidate.

`PASS`: no blocking finding; every other finding listed with its disposition. `FAIL`: any blocking finding. PR verdicts: `how-to-review-a-pr`.

## Fixes and review rounds

- When told to fix: smallest change that removes the cause, affected layer only, intent unchanged. Then a fresh independent reviewer, not the one who fixed, assesses the result. A clean review needs no edits.
- After any repair, rerun all configured checks. Reuse proof only when its inputs are exactly unchanged.
- One round = independent review, selected fixes, fresh review. Mandatory findings keep it open; optional fixes follow worth-it. At most 6 failed rounds per review loop.
- After the sixth failed round, stop that loop. Give the owner one short packet: findings per round (new vs repeated), the shared cause, options (extend 1-3 rounds, defer with an owner record, amend scope, cancel).
- Keep independent work moving while you wait.

## Output Format

`## Deep Review Report` with, in order:

1. **Scope**: files reviewed, baseline used, lenses run, verdict scope
2. **Summary Table**: finding rows, most severe first
3. **Unknowns**: required evidence still missing
4. **Stats**: total findings; Critical: X | High: X | Medium: X | Low: X
5. **Top 3 Priority Fixes**: the most impactful findings
6. **Verdict**: PASS / FAIL / CONDITIONAL - one line: is this code ready to ship?

## Output contract

In a factory run this is step 6, Verify: the builder runs this pass, and the independent review is step 8 (`how-to-review-a-pr`). The block `## 6 Verify` holds:

- [ ] Every requested journey used through real controls, with observed results
- [ ] change-guard and compliance results, plus each other lens run, each with its findings table (possibly empty) and verdict
- [ ] An `after-<id>` file for every proof-list id, same ids as Before, captured in that same pass
- [ ] The full suite: command and result, run once after manual use
- [ ] The verdict; blocking findings fixed through the build loop before the gate
