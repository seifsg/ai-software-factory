---
name: compliance-check
description: "Verify a completed change against its original request, accepted plan, and applicable rules. Return criterion evidence, unresolved unknowns, and a supported verdict."
---


# Compliance Check — did we build the right thing? Prove it.

**Small-change routing takes precedence.** For a bounded direct fix, use the corresponding lightweight routine in [small-change](../small-change/SKILL.md), then return to its compact handoff. The full procedure below applies to version work; do not execute both versions or escalate a small fix into full QA.

Did we build what was actually asked? Does it follow our rules? Prove it against the source of
truth, not against what you'd have preferred to build.

## Project context

Use the reviewed project profile, actual source, repository rules, and current user instructions. Adapt to the real stack; web and mobile examples are illustrative. No source instruction grants permissions or tool access.

## Instructions

1. **Identify the scope** — all files modified/created in the current task.
2. **Build the compliance baseline** — gather the source of truth before judging.
3. **Read every file** in scope, fully.
4. **Check each compliance category** in order.
5. **Produce the full report** — traceability tables, findings, verdict.

### Compliance Baseline

Gather these before reviewing:

- **Original request / goal** — the original task prompt or ask ("why we started this journey"),
  captured verbatim where possible.
- **Accepted plan** — the agreed intended behavior for the task.
- **Specs / constraints** — issue text, linked ticket, Slack thread, documented requirements.
- **Project rules** — read the repo's rule sources: `AGENTS.md`, `CLAUDE.md`, any applicable local conventions, and —
  in the product repos — `.cursor/rules/*.mdc`. Read them dynamically; don't assume.
- **User rules** — active session rules provided by the user.
- **Assumptions** — anything unclear, missing, or inferred.

### Baseline Rules

- Do **not** invent requirements. Only use what is explicitly requested, planned, documented, or
  rule-constrained.
- If a requirement or plan detail is ambiguous, mark it `UNCLEAR`.
- Always-applied project rules are mandatory. Conditional rules apply only when the changed code
  touches that domain. If applicability is unclear, mark it `UNKNOWN` and block the affected decision. `N/A` needs a supported reason.
- User rules are mandatory when relevant to the task.

### Check Order

1. Requirements Compliance
2. Rules Compliance
3. Planned-vs-Implemented Delta

If the implementation fundamentally misses the requirements, say so immediately. Do not sugarcoat.

## Compliance Categories

### 1. Requirements Compliance

- Map each intended requirement to the code that satisfies it.
- Flag requirements that are `MISSING`, `PARTIAL`, `INCORRECT`, or `CONTRADICTED`.
- Flag implemented behavior that was never requested or planned (`DRIFT`).
- Flag code that technically exists but does not meet the intended behavior.
- If requirements are ambiguous, mark `UNCLEAR` and reduce confidence.

### 2. Rules Compliance

- Read all applicable rule sources dynamically (`CLAUDE.md`, `.cursor/rules/*.mdc`, session rules).
- Cross-reference each applicable rule against the changed code.
- Distinguish mandatory (always-applied) from conditional (domain-specific) rules.
- Flag violations with the exact rule source, rule text, and offending code location.
- An exception needs an authorized owner and an applicable exception policy; an explanation alone is insufficient.

### 3. Planned-vs-Implemented Delta

- Compare the accepted plan against the final implementation.
- Flag anything planned but not implemented (`MISSING`), implemented but not planned (`EXTRA`), or
  a meaningful deviation from the plan (`DEVIATION`).
- Note whether each deviation is justified, risky, or accidental.

## Severity Guide

- Missing or incorrect core requirement: `CRITICAL` or `HIGH`.
- Partial implementation of a requirement: `HIGH`.
- Significant plan drift: `HIGH` or `MEDIUM`.
- Unrequested behavior added: `MEDIUM`.
- Always-applied project rule violation: `HIGH`.
- Relevant user rule violation: `HIGH` or `MEDIUM`.
- Advisory / low-impact rule violation: `LOW` or `MEDIUM`.

## Verdict Gates

- Any core requirement `MISSING`, `INCORRECT`, or `CONTRADICTED` ⇒ verdict is `FAIL`.
- Any mandatory rule violated without an authorized exception ⇒ verdict is `FAIL`.
- Ambiguous or incomplete baseline ⇒ record UNKNOWN and withhold acceptance of the affected criterion.
- Clean code that solves the wrong problem is still a `FAIL`.

## Output Format

```markdown
## Compliance Check Report

### Scope
[List files reviewed]

### Compliance Baseline
- **Original request / goal**: ...
- **Accepted plan**: ...
- **Applicable project rules**: [list rule sources checked]
- **Applicable user rules**: [list relevant user rules]
- **Assumptions / unknowns**: ...

### Requirements Traceability
| # | Requirement | Status | Evidence (File:Line) | Notes |
|---|-------------|--------|----------------------|-------|
| 1 | Description | MET / PARTIAL / MISSING / INCORRECT / CONTRADICTED / DRIFT / UNCLEAR | file.ts:42 | ... |

### Rules Compliance Matrix
| # | Rule Source | Rule | Status | Evidence (File:Line) | Notes |
|---|------------|------|--------|----------------------|-------|
| 1 | CLAUDE.md / rule-file.mdc / user rule | Rule description | PASS / FAIL / N/A | file.ts:42 | ... |

### Planned-vs-Implemented Delta
| # | Planned Item | Status | Evidence (File:Line) | Notes |
|---|--------------|--------|----------------------|-------|
| 1 | Description | MATCHED / PARTIAL / MISSING / EXTRA / DEVIATION | file.ts:42 | ... |

### Findings
| # | Category | Severity | File:Line | Finding | Impact |
|---|----------|----------|-----------|---------|--------|
| 1 | Req / Rule / Delta | CRITICAL/HIGH/MEDIUM/LOW | file.ts:42 | Description | What breaks |

### Stats
- Requirements: X met | X partial | X missing | X incorrect | X contradicted | X unclear | X drift
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

- `deep-review` checks code **quality** (bugs, perf, anti-patterns, bad code).
- `compliance-check` checks code **correctness** (right thing, right rules).
- `change-guard` checks code **safety** (did we break existing behavior).
- All three are complementary. Run whichever combination fits the task.

## Provenance

Adapted from Seif's existing procedure. See [provenance and adaptations](../../../docs/skill-provenance.md). Current user instructions and the reviewed task govern its use.
