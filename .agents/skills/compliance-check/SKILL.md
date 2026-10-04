---
name: compliance-check
description: Verify implementation against intended requirements, accepted plan, project/workspace rules, and active user rules. Use after completing a feature, task, or before merging to confirm the code solves the right problem the right way.
---

# Compliance Check

**Project adapter:** Discover the target project's actual rule sources and follow the host's instruction precedence. Preserve the complete checks and reminders below.

**Current decisions override:** Uncertain applicability stays UNKNOWN pending evidence. Mandatory exceptions require an authorized owner, scope and record; explanation alone cannot waive a rule. Apply [I1–I2](../../../docs/current-decisions.md#further-improvement-decisions) to the original checks below.

Did we build the right thing? Does it follow our rules? Prove it.

## Instructions

1. **Identify the scope** - all files modified/created in the current task
2. **Build the compliance baseline** - gather source of truth before judging
3. **Read every file** in scope, fully
4. **Check each compliance category** in order
5. **Produce the full report** - traceability tables, findings, verdict

### Compliance Baseline

Gather these before reviewing:

- **User request** - the original task prompt or ask
- **Accepted plan** - agreed-upon intended behavior for the task
- **Specs / constraints** - issue text, documented requirements, explicit specs
- **Workspace rules** - read all applicable project instruction/rule files
- **User rules** - active session rules provided by the user
- **Assumptions** - anything unclear, missing, or inferred

### Baseline Rules

- Do **not** invent requirements. Only use what is explicitly requested, planned, documented, or rule-constrained
- If a requirement or plan detail is ambiguous, mark it `UNCLEAR`
- Always-applied workspace rules are mandatory
- Conditional workspace rules apply only when the changed code touches that domain
- User rules are mandatory when relevant to the task
- If unclear whether a rule applies, mark it `N/A` with a note

### Check Order

1. Requirements Compliance
2. Rules Compliance
3. Planned-vs-Implemented Delta

If the implementation fundamentally misses the requirements, say so immediately. Do not sugarcoat it.

## Compliance Categories

### 1. Requirements Compliance

- Map each intended requirement to the code that satisfies it
- Flag requirements that are `MISSING`, `PARTIAL`, `INCORRECT`, or `CONTRADICTED`
- Flag implemented behavior that was never requested or planned (`DRIFT`)
- Flag code that technically exists but does not meet the intended behavior
- If requirements are ambiguous, mark `UNCLEAR` and reduce confidence

### 2. Rules Compliance

- Discover and read all applicable project instruction/rule files dynamically
- Read active user rules from the session context
- Cross-reference each applicable rule against the changed code
- Distinguish mandatory (always-applied) from conditional (domain-specific) rules
- Flag violations with the exact rule source, rule text, and offending code location
- If a rule is intentionally violated, verify the justification is explicit

### 3. Planned-vs-Implemented Delta

- Compare the accepted plan against the final implementation
- Flag anything planned but not implemented (`MISSING`)
- Flag anything implemented but not planned (`EXTRA`)
- Flag meaningful deviations from the plan (`DEVIATION`)
- Note whether each deviation is justified, risky, or accidental

## Severity Guide

- Missing or incorrect core requirement: `CRITICAL` or `HIGH`
- Partial implementation of a requirement: `HIGH`
- Significant plan drift: `HIGH` or `MEDIUM`
- Unrequested behavior added: `MEDIUM`
- Always-applied workspace rule violation: `HIGH`
- Relevant user rule violation: `HIGH` or `MEDIUM`
- Advisory or low-impact rule violation: `LOW` or `MEDIUM`

## Verdict Gates

- Any core requirement `MISSING` or `INCORRECT` => verdict is `FAIL`
- Any always-applied workspace rule violated without justification => verdict is `FAIL`
- Ambiguous or incomplete baseline => lower confidence explicitly
- Clean code that solves the wrong problem is still a `FAIL`

## Output Format

```markdown
## Compliance Check Report

### Scope
[List files reviewed]

### Compliance Baseline
- **User request**: ...
- **Accepted plan**: ...
- **Applicable workspace rules**: [list rule files checked]
- **Applicable user rules**: [list relevant user rules]
- **Assumptions / unknowns**: ...

### Requirements Traceability
| # | Requirement | Status | Evidence (File:Line) | Notes |
|---|-------------|--------|----------------------|-------|
| 1 | Description | MET / PARTIAL / MISSING / INCORRECT / DRIFT / UNCLEAR | file.ts:42 | ... |

### Rules Compliance Matrix
| # | Rule Source | Rule | Status | Evidence (File:Line) | Notes |
|---|------------|------|--------|----------------------|-------|
| 1 | rule-file.mdc / user rule | Rule description | PASS / FAIL / N/A | file.ts:42 | ... |

### Planned-vs-Implemented Delta
| # | Planned Item | Status | Evidence (File:Line) | Notes |
|---|--------------|--------|----------------------|-------|
| 1 | Description | MATCHED / PARTIAL / MISSING / EXTRA / DEVIATION | file.ts:42 | ... |

### Findings
| # | Category | Severity | File:Line | Finding | Impact |
|---|----------|----------|-----------|---------|--------|
| 1 | Req / Rule / Delta | CRITICAL/HIGH/MEDIUM/LOW | file.ts:42 | Description | What breaks |

### Stats
- Requirements: X met | X partial | X missing | X incorrect | X unclear | X drift
- Rules: X pass | X fail | X n/a
- Delta: X matched | X partial | X missing | X extra | X deviation
- Confidence: HIGH / MEDIUM / LOW

### Verdict
[PASS / FAIL] - [Is the implementation correct and compliant?]

### Verdict Rationale
- Unmet requirements
- Mandatory rule violations
- Significant plan deviations
```

## Relationship to Other Skills

- `deep-review` checks code **quality** (bugs, perf, anti-patterns, bad code)
- `compliance-check` checks code **correctness** (right thing, right rules)
- `change-guard` checks code **safety** (did we break existing behavior)
- All three are complementary. Run whichever combination fits the task
