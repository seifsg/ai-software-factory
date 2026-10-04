# Factory checkpoint — 4 October 2026

Scope: accumulated skill improvements plus a whole-repository cleanup and repair of the [3 October findings](factory-audit-2026-10-03.md). Starting revision: `ca42f7877799217ab415f282ee8f9f2fa6016bd9`. Preserve existing dirty work, original methods and active bundle pins.

## What changed

- Compressed AI-written guidance; preserved the four core original skill files unchanged. Generic product research, resource planning, mandatory safe logging and final-stage tests now agree across delivery, review and maintenance.
- Added Database Schema and connected its index, provenance, planning, review and required bundle inputs.
- Replaced stale status-page instructions with current rules and twelve phone-readable skill links. Dated audits remain historical evidence.
- Full PR review retains four isolated themes. Hosts with fewer slots run them in bounded waves before synthesis; Small Change still uses one scoped reviewer.
- Compliance's adapter keeps uncertain rules UNKNOWN and requires actual authority for mandatory exceptions. Setup paths are examples; the obsolete TDD roadmap label now reads test-quality review.

## Audit repairs

| Finding | Repair | Manual evidence |
|---|---|---|
| F1: Windows junction cleanup | Reject symlinks/reparse points before run traversal, selection receipt access and generated-output cleanup. | Disposable junctions at run/output paths rejected; synthetic source files survived; normal lock worked. Independent review also caught the launcher path; repaired launcher left the outside directory empty. |
| F2: blocked prompt input | File-backed stdin avoids a blocking pipe write before timeout handling. | Ignored 64 KiB prompt: previously 3.765 s/natural exit for a 1 s timeout; now 1.719 s/terminated, including process-tree cleanup. |
| F3: colliding IDs | Check IDs unique under case folding. | `unit`/`UNIT` rejected; distinct IDs accepted. |
| F4: unbounded capture | Drain process output while keeping a bounded 1 MB tail. | 16,777,224 emitted bytes produced a 1,000,000-byte log retaining the final marker; inherited stdout did not hang completion. |
| F5: incomplete review packet | Explicit diagnostics, efficiency, research, schema and tests-last inputs. | Review packet walkthrough checks applicable evidence and leaves missing evidence unverified. |
| F6: research-only scope | Standalone research returns findings without requiring implementation/controller setup. | Instruction walkthrough preserves research-only boundary; new-product delivery still revises its plan. |
| F7: real pilot resume | Narrow compatibility path validates the exact documented legacy revision's operational files. | Actual `eeb0da9…` checkout selected/resumed; app state hash unchanged; missing runtime, unsupported maintenance entry and attempted upgrade rejected. |

These are local Windows observations. Reparse checks do not establish protection against hostile concurrent filesystem swaps. POSIX runner behavior needs its own executed evidence. Legacy compatibility does not authorize migration or relax current bundle completeness.

## Final validation and review

Implementation and manual actions preceded automated test authoring/execution. On Windows with bundled Python 3.12:

- **79/79 Python tests passed**, full final run in 183.973 s. Eight new regressions cover actual process behavior, junctions, ID collisions and the real legacy pilot; reviewer-resource coverage also expanded.
- The first full run had one new fixture teardown error: its sleeping child held the temporary working directory open. Moving that child's working directory fixed cleanup without weakening the pipe-lifetime assertion. All eight focused regressions and then the full suite passed. No production expectation was relaxed.
- **14 skill entrypoints validated** using UTF-8; **333 local links/anchors passed** after the report updates. Generated resolvers match; JavaScript syntax and whitespace checks passed.
- Four distinct reviewers covered security, performance, user journey and change guard in **2 → 1 → 1 waves**. Independent synthesis found no remaining source blocker after the launcher guard and setup-path corrections. Final source/test delta was reread separately.
- Four core original skill files have no diff against the starting revision.

Across the same 32 skill/reference/index files: **26,592 → 21,925 whitespace words (17.6% less)**. Including the new Database Schema and conditional trial reference, all 34 current skill text files total 23,202 words. These are word counts, not token counts; deliberate original repetition remains.

Publication branch: `refine/generic-concise-skills`, targeting `main`. The current request authorizes push and the retained preference calls for a non-draft PR. A historical completed merge request is not standing permission for a new merge. Check the [live PR list](https://github.com/seifsg/ai-software-factory/pulls?q=is%3Apr+is%3Aopen) for publication/merge state.

## Remaining work

See [current limits](factory-status.md#repairs-and-limits). A current end-to-end real app demonstration, personal launcher adoption and remote enforcement are separate work. No external tracker update, owner self-review, notification, deployment or active-run migration is claimed.

Private maintenance evidence stays under ignored `.factory/maintenance/`. The repository report contains only sanitized results.
