# Speed modes

Seif's 6 October choice. Pick the mode from the request; no mode named means **Fast**. In Fast and Lucky this file overrides any conflicting factory rule; everything it keeps still applies.

| | 🏃 Fast (default) | 🍀 Lucky | 🛡️ Safe |
|---|---|---|---|
| Say | nothing, or `fast` | `lucky` | `safe` |
| Spec, project rules, Clear Writing | ✅ | ✅ | ✅ |
| Cheap security, no secrets in code/Git | ✅ | ✅ | ✅ |
| Shared logger | ✅ working module, local sink | ✅ minimal module, local sink | ✅ full [logging](app-diagnostics.md) |
| Ticket | only when asked | ❌ | ✅ [Ticketing](../../ticketing/SKILL.md) |
| Analyze | [Analyze Start](../../analyze-start/SKILL.md) | one short pass | ✅ |
| Plan | [Get Ready](../../get-ready-to-code/SKILL.md) five outputs, no file-summary stop | one short plan, no stop | ✅ with stop |
| Research, three options, UX/schema choices | ✅ | ❌ take the obvious standard default | ✅ |
| 0–4 loop | ✅ every todo | one pass: apply, inspect once | ✅ |
| Build, run, manual QA, tests, review | ❌ until done or `verify` | ❌ until `verify` | ✅ full cycle |
| Controller run (`python -m safe_engine`) | ❌ | ❌ | ✅ |
| Bundle resolver and its receipt | ✅ | ✅ | ✅ |

## Fast

Build the whole requested outcome without building, running or testing it. When the implementation is done, before handing it over to run: build and start it once, use the main journey once, fix blockers. Report what was not checked.

## Lucky

One shot. Read the request and the code, write the complete outcome, stop. No builds, runs, tests, research or comparisons. Report it as unverified.

## Both

- `verify` (this command, not Safe's `verify` phase) replaces Fast's done-run: finish the work, final manual QA of the main and failure journeys, then write and run relevant automated tests ([tests-last order](../../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests)). No ticket, controller or Codex review.
- `promote`: commit the current code as the Git baseline; it is the ticket's actual before. Then [Ticketing](../../ticketing/SKILL.md), a builder session and the full Safe cycle from analyze, including the file-summary stop.
- PRs only when asked: a draft via [creation](../../how-to-make-a-pr/SKILL.md), no ticket needed. List missing tests, review and baseline as unverified in the PR; attach the finished screenshot. Cloud PR review only when asked. Safe keeps both PR procedures for authorized PRs.
- Factory maintenance keeps [Improve Factory](../../improve-factory/SKILL.md) unless Seif names a mode.
- Seif's explicit stops, reserved decisions and external-action limits stay. Keep work surgical.
- Never claim tested, reviewed or production ready without that evidence.
