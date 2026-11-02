# Compliance

Did we build the right thing? Does it follow our rules? Prove it.

Prove the confirmed iteration. Keep full-product criteria delivered, incomplete or explicitly deferred. Iteration acceptance cannot redefine requirements or certify the product.

## Baseline

Gather before judging:

- **User request**: the original ask
- **Confirmed criteria**: refresh the project's tracker ticket first. Use latest owner-confirmed criteria, approved scope changes and their owner source. PR claims and old plans cannot override them. Proposed changes stay pending
- **Accepted plan**: agreed intended behavior
- **Specs / constraints**: issue text, documented requirements
- **Project rules**: discover and read every applicable instruction/rule file; follow host precedence
- **User rules**: active session rules
- **Assumptions**: anything unclear, missing or inferred

Rules:

- Invent no requirements. Use only what is requested, confirmed, planned, documented or rule-constrained.
- Ambiguous requirement or plan detail: `UNCLEAR`, lower confidence.
- Always-applied rules are mandatory. Conditional rules apply when the change touches their domain. Relevant user rules are mandatory.
- Unsure a rule applies: `UNKNOWN`, never `N/A`. `N/A` needs evidence.
- Implementation fundamentally misses requirements: say so first. No sugarcoating.

## Check Order

1. **Requirements**: map each requirement/criterion to the code and proof that satisfy it.
   - Inventory the user request first. A requested item absent from every ticket, or replaced by a substitute, without owner's recorded decision is core `MISSING`. One open in its own ticket outside the confirmed iteration is not an iteration requirement: list as open, and verdict states product incomplete
   - `MET`, `PARTIAL`, `MISSING`, `INCORRECT`, `CONTRADICTED`, `UNCLEAR`
   - Code exists but misses intended behavior: not `MET`
   - Behavior never requested or planned: `DRIFT`
   - Each ticket's checklist: missing checklist, unticked item or tick without its check = ticket unfinished
2. **Rules**: cross-reference each applicable rule against changed code.
   - Cite rule source, rule text, offending location
   - Intentional violation needs authorized exception: owner, scope, record. Explanation alone waives nothing
3. **Plan vs result**: `MATCHED`, `PARTIAL`, `MISSING`, `EXTRA`, `DEVIATION`. Say whether each deviation is justified, risky or accidental.

Proof must be bound to the reviewed candidate. Closed ticket, ready flag or green suite does not prove delivery. Pending scope changes, drift, missing proof or failed ticket refresh block dependent acceptance.

## Severity

- Missing or incorrect core requirement: CRITICAL or HIGH
- Partial requirement: HIGH
- Significant plan drift: HIGH or MEDIUM
- Unrequested behavior added: MEDIUM
- Always-applied rule violation: HIGH
- Relevant user rule violation: HIGH or MEDIUM
- Advisory or low-impact rule violation: LOW or MEDIUM

## Verdict Gates

- Any core requirement `MISSING` or `INCORRECT`: FAIL
- Any ticket in scope unfinished (unticked item or unproven criterion, except items this review, the PR or the merge completes): FAIL; a Blocked one names its blocker
- Any always-applied rule violated without authorized exception: FAIL
- Required `UNKNOWN` or `UNCLEAR` on a core criterion: FAIL until resolved

## Output Format

```markdown
## Compliance Report

### Baseline
- User request: ...
- Confirmed criteria: [ticket link, scope revision, refresh result or gap]
- Accepted plan: ...
- Rule files checked: ...
- User rules: ...
- Assumptions / unknowns: ...

### Requirements Traceability
| # | Requirement / criterion | Status | Actual change / journey | Proof (File:Line or observation) | Gap / deviation |
|---|-------------------------|--------|-------------------------|----------------------------------|-----------------|

### Rules Matrix
| # | Rule source | Rule | Status (PASS / FAIL / UNKNOWN / N/A) | Evidence (File:Line) | Notes |
|---|-------------|------|--------------------------------------|----------------------|-------|

### Plan vs Result
| # | Planned item | Status | Evidence (File:Line) | Notes |
|---|--------------|--------|----------------------|-------|

### Findings
[Finding rows from SKILL.md format; Category: Req / Rule / Delta]

### Stats
- Requirements: X met | X partial | X missing | X incorrect | X unclear | X drift
- Rules: X pass | X fail | X unknown | X n/a
- Delta: X matched | X partial | X missing | X extra | X deviation
- Confidence: HIGH / MEDIUM / LOW

### Verdict
PASS / FAIL - [Is the implementation correct and compliant?]
- Unmet requirements
- Mandatory rule violations
- Significant plan deviations
```
