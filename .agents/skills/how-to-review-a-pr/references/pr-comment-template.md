# Detailed PR review handoff

Fill with observed results; delete unused illustrative rows, never leave empty placeholders. No model/tool signatures, dev-time estimates, invented fixes or formal self-approval. Keep all five pass outcomes even when clean. This template complements the target project's required review fields.

````markdown
## PR review and fixes

**Verdict:** <APPROVE / APPROVE-WITH-FIXES / REQUEST-CHANGES / BLOCK> — <reason>
**Candidate:** <repo/PR; exact base and head SHAs; candidate after any repairs>
**Review:** <separate from builder; fresh assessment after repairs, or blocker>
**Gate / pushed:** <actual results / commit SHAs or no changes>
**State:** draft; human owns ready/merge/release.

### Original goal
> <verbatim original request>

**Delivered:** <YES / PARTIAL / NO; evidence and limits>

### Analysis — analyze-start
```text
<actual flow, changed area and consumers>
```
| Claim | Actual code / document evidence | Supported? |
|---|---|---|
| <claim> | <path:line or exact result> | <yes/no/unknown> |

### Solutions considered
| Option | Approach | Recommendation | Reason / decision authority |
|---|---|---|---|
| A | <credible option> | <one recommendation only> | <comparison> |
| B | <credible option> | <status> | <comparison> |
| C | <credible option> | <status> | <comparison> |

### Plan and execution — get-ready-to-code
| Step | Evidence |
|---|---|
| File set and critique | <actual correction scope or empty set> |
| Phases, todos, full plan | <actual plan/artifact> |
| 0–4 execution | <pre/change/post per correction; or no edits needed> |
| Before → after | <observable difference for each substantive correction> |

### Full review battery
| Pass | Verdict | Evidence / findings / applicability |
|---|---|---|
| Security | <outcome> | <actual evidence> |
| Performance | <outcome> | <actual evidence> |
| User journey vs original goal | <outcome> | <actual evidence and feedback trace> |
| Change guard | <outcome> | <actual consumer/regression evidence> |
| Compliance | <outcome> | <requirement coverage> |

| # | Severity | Lenses | Location | Finding / impact | Fixed or flagged; reason |
|---|---|---|---|---|---|
| <id> | <severity> | <passes> | <path:line> | <supported finding> | <status> |

### Build gate
| Command / inspection | Result | Coverage / limits |
|---|---|---|
| <actual command> | <exit/count> | <candidate and relevant limitation> |

### Blockers and handoff
| Item | Status / next owner and action |
|---|---|
| Original requirements | <complete or remaining evidence> |
| Creation workflow | <task, owner, notification and body evidence/blockers> |
| Retry record | <failed step, correction, retry outcome; or none> |
| Shared limits | <used/remaining when part of a factory run> |
| Fresh assessment | <exact reviewed candidate after repairs, or blocker> |
| Resume | <branch, commands, artifacts, unresolved decisions> |
````

Post using the available GitHub tooling and verify read-back. Preserve any earlier review as history. If a post's outcome is uncertain, find it before retrying. An unpushed correction is a proposal/patch, never a completed remote fix.
