# Speed modes

Seif's 6 October choice. Pick the mode from the request. No mode named means **Fast**, for every factory activity: delivery, tickets, PRs and factory maintenance. In Fast and Lucky this file overrides any conflicting factory rule; everything it keeps still applies.

Seif's 7 October correction: fast never means thin. Fast and Lucky keep tickets, the recorded methods and the [product bar](product-bar.md); a [gate and hooks](fast-run.md#the-gate) hold them to it. [Fast run](fast-run.md) owns the steps.

| | 🏃 Fast (default) | 🍀 Lucky | 🛡️ Safe |
|---|---|---|---|
| Say | nothing, or `fast` | `lucky` | `safe` |
| Spec, project rules, Clear Writing | ✅ | ✅ | ✅ |
| [Product bar](product-bar.md) | ✅ | ✅ as its defaults | ✅ |
| Cheap security, no secrets in code/Git | ✅ POC hardening → follow-up ticket | ✅ same | ✅ |
| Shared logger | ✅ working module, local sink | ✅ minimal module, local sink | ✅ full [logging](app-diagnostics.md) |
| Ticket | ✅ epic + outcome sub-issues ([Fast/Lucky tickets](../../ticketing/SKILL.md#fast-and-lucky-tickets)) | ✅ same | ✅ [Ticketing](../../ticketing/SKILL.md) |
| Quick research: 3 competitors, feature matrix, 3 stacks | ✅ products and big features | ❌ product bar defaults | ✅ |
| [Kickoff questions](fast-run.md#kickoff-questions) | ✅ products and big features | ❌ | ✅ with ticket confirmation |
| Analyze | [Analyze Start](../../analyze-start/SKILL.md) | one short pass | ✅ |
| Plan | [Get Ready](../../get-ready-to-code/SKILL.md) five outputs, no file-summary stop | one short plan, no stop | ✅ stop, skipped if before/after owner-confirmed |
| Design and schema briefs; three-option choices where the methods call for them | ✅ | ❌ product bar defaults | ✅ |
| 0–4 loop | ✅ every todo, logged | one pass: apply, inspect once, logged | ✅ |
| [Gate and hooks](fast-run.md#the-gate) | ✅ | ✅ | ❌ controller instead |
| Build, run, manual QA, tests, review | done-run only; the rest ❌ until `verify` | ❌ until `verify` | ✅ full cycle |
| Controller run (`python -m safe_engine`) | ❌ | ❌ | ✅ |
| Bundle resolver and its receipt | ✅ | ✅ | ✅ |

## Fast

Follow [Fast run](fast-run.md) step by step. Build the whole requested outcome without testing it along the way. When the implementation is done, before handing it over: build and start it once, use the main journey and its most likely failure, fix blockers. Report what was not checked.

## Lucky

One shot. Create the epic and sub-issues, read the request and the code, write the complete outcome to the product bar, record the run, stop. No builds, runs, tests, research, questions or comparisons. Report it as unverified.

## Safe

Keep Get Ready's file-summary stop unless existing user instructions explicitly authorize continuing through it, or the ticket's before/after was already owner-confirmed. Phase-only requests still stop.

## Both

- `verify` (this command, not Safe's `verify` phase) replaces Fast's done-run: finish the work, final manual QA of the main and failure journeys, then write and run relevant automated tests ([tests-last order](../../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests)). No controller or Codex review.
- `promote`: commit the current code as the Git baseline; it is the ticket's actual before. Then [Ticketing](../../ticketing/SKILL.md) on the existing epic, a builder session and the full Safe cycle from analyze, including the file-summary stop unless the owner has confirmed the ticket's before/after.
- PRs only when asked: a draft via [creation](../../how-to-make-a-pr/SKILL.md), linked to the run's epic. List missing tests, review and baseline as unverified in the PR; attach the finished screenshot. Cloud PR review only when asked. Safe keeps both PR procedures for authorized PRs.
- Before creating or updating a Fast/Lucky PR, offer once: **"Run a Safe check first? (optional)"**. A Safe check is final manual QA, relevant tests and one independent review of the finished work. Yes: run it, fix, then open the PR. No: open the draft as is. Never repeat the offer for the same PR.
- Factory maintenance runs Fast too, as a `change` run: tickets and the gate apply; keep [Improve Factory](../../improve-factory/SKILL.md)'s isolation (own branch/worktree, preserve active app work); its review cycle is Safe only.
- Seif's explicit stops, reserved decisions and external-action limits stay. Keep work surgical.
- Never claim tested, reviewed or production ready without that evidence.
