# Compliance

Did we build the right thing? Does it follow our rules? Prove it.

Prove the confirmed iteration. Keep every original product requirement delivered, incomplete or explicitly owner-deferred with its decision source. Reconcile the original input with the coverage map before trusting the ticket. POC/MVP labels and iteration acceptance cannot redefine requirements or certify the whole product.

## Baseline

Gather before judging:

- **User request**: the original ask
- **Confirmed criteria**: refresh the project's tracker ticket first. Use the latest owner-confirmed criteria, approved scope changes and their owner source. PR claims and old plans cannot override them. Proposed changes stay pending
- **Accepted plan**: agreed intended behavior
- **Specs / constraints**: issue text, documented requirements
- **Project rules**: discover and read every applicable instruction/rule file; follow the host's precedence
- **User rules**: active session rules
- **Assumptions**: anything unclear, missing or inferred

Rules:

- Do not invent requirements. Use only what is requested, confirmed, planned, documented or rule-constrained.
- Ambiguous requirement or plan detail: `UNCLEAR`, lower confidence.
- Always-applied rules are mandatory. Conditional rules apply when the change touches their domain. Relevant user rules are mandatory.
- Unsure whether a rule applies: `UNKNOWN`, never `N/A`. `N/A` needs evidence.
- If the implementation fundamentally misses the requirements, say so first. Do not sugarcoat it.

## Check Order

1. **Requirements**: map each requirement/criterion to the code and the proof that satisfy it.
   - `MET`, `PARTIAL`, `MISSING`, `INCORRECT`, `CONTRADICTED`, `UNCLEAR`
   - Code that exists but misses the intended behavior is not `MET`
   - Behavior never requested or planned: `DRIFT`
   - Missing requested capabilities or integrations remain `MISSING` even when a reduced ticket or optional follow-up omits them. A blocked requirement is incomplete, never a whole-product pass
   - Research-backed MVP additions need recorded adoption authority, compatible constraints and evidence; distinguish those from unauthorized scope expansion
2. **Rules**: cross-reference each applicable rule against the changed code.
   - Cite the rule source, rule text and offending location
   - An intentional violation needs an authorized exception: owner, scope, record. Explanation alone waives nothing
3. **Plan vs result**: `MATCHED`, `PARTIAL`, `MISSING`, `EXTRA`, `DEVIATION`. Say whether each deviation is justified, risky or accidental.

Proof must be bound to the reviewed candidate. A closed ticket, a ready flag or a green suite does not prove delivery. Pending scope changes, drift, missing proof or a failed ticket refresh block dependent acceptance.

## Severity

- Missing or incorrect core requirement: CRITICAL or HIGH
- Partial requirement: HIGH
- Significant plan drift: HIGH or MEDIUM
- Unauthorized or unjustified behavior added: MEDIUM
- Always-applied rule violation: HIGH
- Relevant user rule violation: HIGH or MEDIUM
- Advisory or low-impact rule violation: LOW or MEDIUM

## Verdict Gates

- Any core requirement `MISSING` or `INCORRECT`: FAIL
- Any always-applied rule violated without an authorized exception: FAIL
- A required `UNKNOWN` or `UNCLEAR` on a core criterion: FAIL until resolved
- Ambiguous or incomplete baseline: lower confidence explicitly
- Clean code that solves the wrong problem is still FAIL

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
