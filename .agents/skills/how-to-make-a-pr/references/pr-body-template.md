# PR body template

For selected small-change mode, use a concise request/result, affected scope, actual focused checks, review limits, adjustment history and human handoff. The full version template below is optional in that mode; do not fill empty sections merely to reproduce it. Keep required project fields and truthful bindings.

Use within the target repository's template. Fill every applicable section with actual evidence. Explain unsupported applicability; never leave placeholder claims. Keep attribution first and Why immediately after it. Use the project's plain professional heading style; decorative emojis are not required.

````markdown
_Requested by **<human>**_
<Truthful credit for the supplied work or method.>

## Why
<Original problem and the decision that led to this change.>

## Before / after
```text
BEFORE                           AFTER
<observable previous behavior>    <observable resulting behavior>
```

## Flow
```text
<actual trigger> -> <actual stages> -> <outcome>
                        | failure -> <diagnosed in-scope recovery>
```

## Decisions
| Decision | Choice | Reason / authority |
|---|---|---|
| <decision> | <chosen direction> | <actual rationale> |

## Files
| Change | Paths | Purpose |
|---|---|---|
| <NEW/M/D> | <actual paths or coherent groups> | <result> |

## Verification
| Command / inspection | Result | Candidate / coverage limit |
|---|---|---|
| <actual command> | <actual outcome> | <evidence and limits> |

## Guards / review
| Severity | Finding | Resolution / current status |
|---|---|---|
| <actual severity> | <actual finding> | <fix or explicit blocker> |

## Not covered / follow-ups
<Remaining scope, unrun checks, workflow blockers and next owner/action.>

## Adjustment History
| Date | Requested by | What / why | Action |
|---|---|---|---|
| <date or unknown> | <human> | <request and reason> | <actual result> |

## Context and handoff
| Item | Evidence / state |
|---|---|
| Original request | <enough verbatim context to recover the goal> |
| Base | <remote topology evidence and any no-dev fallback> |
| Task | <clickable link, dedup evidence, reverse link and exact status> |
| Discussion | <actual visible link, or source context with no invented link> |
| Observability | <relevant session link, or no relevant session informed this work> |
| Owner / notification | <verified delivery, or blocker> |
| Independent PR review | <current-head report link, or pending/blocker> |
| State | Draft; human owns ready/merge/release |
````
