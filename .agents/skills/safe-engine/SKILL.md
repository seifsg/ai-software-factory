---
name: safe-engine
description: "Delivers games, apps, services, tools and libraries end to end: research, tickets, analysis, plan, build, QA, review and handoff, in Fast (default), Lucky or Safe mode. Use when asked to build, extend, fix or resume software with the factory, or to verify or promote a Fast run."
---

# Safe Engine

Build the requested outcome with the factory's methods. Keep decisions, work and evidence resumable.

Skills named here sit beside this one in the factory bundle (`.agents/skills/<name>/SKILL.md`). Not loaded by your agent? Read them by path.

Analysis, planning or review requests stay in that phase. Do not code unless told.

## Work rules

Build systems that outlast their creator. Breakage is not acceptable.

- Least code that fully solves the problem: no one-off wrappers or duplicate checks, no over-engineering.
- Least CPU and memory. O(1) or as close as the workload allows; measure before claiming speed.
- SOLID, KISS, DRY, SRP. Gang of Four patterns where they fit, never for show.
- Many small functions and files. Split a file before 1000 lines. No long functions.
- Reuse existing functions first. Build new ones to be reused.
- Fix the design, not the symptom: trace a bug or edge case to its root cause and fix it there. Lean to refactoring. A big or regression-risky root fix (shared contracts, schema, stored data, consumers outside the task) needs the owner's yes first.
- Guarantees, not guards. Each real edge case gets the first that fits: impossible by design; normalized or rejected loudly where data enters (undefined, null, wrong values, exceptions); specified, logged behavior. A state beyond the data, config and platform in use gets one loud assertion, never new code paths. No silent defaults or swallowed errors.
- Production ready: no placeholders, stubs or TODOs left behind.
- Human-readable code. Short comments: what a function does and why it exists.
- Never a circular dependency.
- When done, one more pass: less code? less complexity? faster? Question every solution, yours and the code you read.
- Stay on the task. Touch only what the change, its root fix and the product bar need; ticket unrelated issues.
- Write briefly: specific words, no filler, no em dashes, no invented claims.
- Short reports: what changed, proof, what is unverified.

## Pick the mode

No mode named: **Fast**.

| | 🏃 Fast | 🍀 Lucky | 🛡️ Safe |
|---|---|---|---|
| Say | nothing or `fast` | `lucky` | `safe` |
| Tickets | backlog, epic + outcome sub-issues | same | backlog, ticket contract |
| Research + kickoff questions | products, big features | ❌ product bar defaults | ✅ |
| Analyze, plan | full methods, no file-summary stop; a `change`: light lane | one short pass each | full, file-summary stop |
| Design, schema briefs | ✅ | ❌ product bar defaults | ✅ |
| 0–4 loop | every checklist item, ticked after its check | same | same |
| Enforcement | gate + hooks | gate + hooks | controller |
| Checks | item checks, hidden checks, done-run | item checks, hidden checks, done-run | item checks, manual QA, tests, verify, independent review |

Every mode meets the [product bar](references/product-bar.md) for its [size](references/sizes.md), keeps project rules and never puts secrets in code or Git.

## Pick the kind

| Kind | When | Research + questions |
|---|---|---|
| `product` | new app, game, site, tool, service or library | ✅ |
| `feature` | big feature with product choices (what users get, how it looks, what it costs) | ✅ |
| `change` | bug fix, small change, follow-up, factory maintenance | ❌ Fast and Lucky: light lane, no analysis step, short plan |

## Fast and Lucky

Record every step in one work record and pass the gate: [fast-run](references/fast-run.md). Steps run in order; after each, `fast_gate.py done <step>`. Inside Fast, the review and test steps of phase skills wait for `verify` or Safe (MVP and production tests: step 9).

1. **Start:** new project: create the folder, `git init`, make a first commit on the default branch and create a feature branch to build on, so the handoff can open a draft PR. Then `fast_gate.py start`. Once the owner has chosen a remote tracker for a new project, create the remote and push the default branch before building.
2. **Research** (product, feature): run `research-market` kickoff research.
3. **Kickoff** (product, feature): the kickoff questions for its size. Pause the gate while waiting.
4. **Tickets:** run `ticketing`: read the backlog, then epic(s) + 1 or many outcome sub-issues in To do, each with a definition of done; a `change` updates the ticket it follows up, opens a new one only for a new outcome, or keeps none when trivial (`**Ticket:** none (<why>)`).
5. **Analysis** (product, feature): run `analyze-start` in full. No code yet: analyze the requirements, platform and intended consumers, and say so.
6. **Plan:** run `get-ready-to-code`: five outputs, todos `T1..Tn` written into each ticket's checklist, logging map, efficiency budget. This request authorizes continuing through its file-summary stop.
   - Light lane (`change`): a light plan, no analysis step ([fast-run](references/fast-run.md#light-lane)). The 0–4 loop, done-run and handoff stay.
   - Product, feature: once the plan is recorded, start the checker, a fresh agent that will not build. From the tickets and the plan only, never the build, it writes runnable checks for every criterion ID this run owes (every listed ticket's; the epic's unless another run owes it: [fast-run](references/fast-run.md#work-record)), under `.factory/fast/checks/<key>/`, bound to the commands, routes and files the plan names. A criterion it cannot automate gets a written manual check. It returns only "ready" and the paths. The builder never opens the checks; build waits for "ready". A plan change that makes the run owe more criteria starts the checker again for those.
7. **Design** (UI): similar to how we do the get ready to code, we plan our design. We do not accept poor mediocre design, only the best. Design brief from the product bar and `ux-quality` step 1, Map, Hierarchy and Labels included. Its audit waits for the done-run: a fresh agent's verdict per UX rule (`ux-quality` step 4).
8. **Schema** (persistence): Only if needed, we run `database-schema`.
9. **Build:** every checklist item through the 0–4 loop, an unproven capability first as a spike; tick each in its ticket after its check; one log line per todo, written when it is ticked: `T3 pre: … do: … post: …`; in the same edit, `**Now:**` names the todos in progress from then on. Automated tests come last: an MVP or production slice writes them as its last checklist items, once the other items work; a POC waits for `verify` or Safe.
10. **Done-run:** prove each ticket's definition of done. Start it once, use every requested journey and the most likely failure through real controls (simulated input proves no requested integration), read the logs, fix blockers. Screenshots for UI. No browser: drive its HTTP or CLI interface and say so. MVP and production slice also run the scans in the [product bar](references/product-bar.md#security).
    - Product, feature: a fresh checker runs every check against the build, manual ones included, and returns one entry per criterion: `#<n> <ID>: PASS` or `#<n> <ID>: FAIL`, a note only after it in parentheses. A FAIL is a FAIL. Only a checker that has not seen the build code may call a check wrong and change it; the reason goes in that entry's note: `#2 A1: PASS (check changed: <reason>)`. The coordinator copies the entries under `**Hidden checks:**` and never relabels one. Any FAIL goes back to build, then the checks run again.
11. **Handoff:** open the draft PR (`how-to-make-a-pr`), then report how to run, dev sign-in, each requested item (delivered, open in a later iteration, blocked with reason, or owner-deferred), verified, unverified, the follow-ups ticket, each owned ticket's final status (Ready for QA with its PR, Blocked, or Backlog when owner-deferred); `close`. Any requested item not delivered or owner-deferred: the overall outcome is unfinished.

Lucky runs 1, 4, a short 5 and 6 (light lane for a `change`), 9, 10 and 11. It asks nothing, researches nothing and takes product bar defaults for design and schema without comparisons. Its checklist loop and checks match Fast, UI work's UX verdicts included (`ux-quality` step 4).

- `verify`: finish the work, manual QA of the main and failure journeys, then write and run relevant tests. No controller or independent review.
- `promote`: commit the current code as the baseline, then (optionally) Safe on the existing epic.

## Safe

1. Run `ticketing`: confirmed before/after and criteria before implementation. A product or big feature records its [size](references/sizes.md) (POC, MVP or production slice) in the epic's guardrails; ask it first when open.
2. Drive the controller phase by phase: [controller](references/controller.md).
   - `analyze`: `analyze-start`.
   - `plan`: `get-ready-to-code`, file-summary stop unless the owner already confirmed the ticket's before/after. New software: keep the first plan, run `research-market`, revise all five outputs.
   - `build`: every checklist item through the 0–4 loop, ticked after its check.
   - `manual` → `testing` → `verify`: use it first, tests last.
   - `review`: `deep-review` by a fresh agent that did not build it.
   - `ready`: map confirmed criteria to proof; report limits.
3. One builder session per ticket. Parallel tickets: [controller](references/controller.md).

## Every mode

- Tests last, whenever tests run (Safe, `verify`, a Safe check): finish the work, use it (every requested journey, failure and recovery), then write and run tests.
- Every UI change: `ux-quality`. New or changed persistence: `database-schema`. Material unknowns: `research-market`.
- PRs always: `how-to-make-a-pr`. Variations: one branch and draft PR per variation. A PR is planned: capture its before proof before editing. Before a Fast or Lucky PR, offer once: "Run a Safe check first? (optional)". A Safe check is manual QA, relevant tests and one independent `deep-review`.
- Never claim tested, reviewed or production ready without that evidence.
- Backlog in every mode: `ticketing` moves each ticket through its statuses, logs every ticket change in its activity and leaves untasked items alone. Deferred work appends to the epic's one open follow-ups ticket in Backlog, never one ticket per item.
- Every ticket carries a definition of done and a checklist (`ticketing`); a change of intent updates both before the code. Each item runs the 0–4 loop and is ticked after its check. A ticket is finished only when every item is ticked and every criterion proven; otherwise it loops or is Blocked. Done comes with the PR merge.

## Keep the owner posted

The owner sees where the run is without asking. One short line per event, never a play-by-play of tool calls.

- Fast and Lucky: the gate shows its dashboard after each step, pause and resume, and a line per finished todo and per new `**Now:**` ([fast-run](references/fast-run.md#progress)). Never repeat a gate message your agent already showed. Where it shows none, relay the card from the command output.
- Fast and Lucky: once per run, give the owner the live view's link (`fast_gate.py view` in the background, [fast-run](references/fast-run.md#live-view)). When a ticked todo leaves something the owner can use, record it with `fast_gate.py try`.
- Before a wave or slow work (subagents, research, test suites, builds): one line, who does what. One result line when it returns.
- Waiting on the owner: the question first, then the options.
- Asked for status: show the card from `fast_gate.py status`. Safe: the same card, built from the controller's `status`.
- Your agent has a task list: mirror the steps and todos once per wave, in a message with other tool calls.
- The final report carries the `close` card.
- The owner asks for more or fewer updates: that binds the run.

## Decide

- Owner-reserved choices and changed requirements: ask.
- Delegated in-scope choices: recommend, pick, record the reason. Plans and updates are not approval gates.
- New substantive choice: compare three options, recommend one.
- Answers bind the run. Later changes go to the ticket's activity.

## Authority and stops

1. Continue to the agreed outcome. Pause dependent work only for: missing access or tools after real discovery, owner-reserved decisions, a required gate you cannot repair, an explicit owner stop. Keep independent work moving.
2. Discover before asking: files, config, run records, integrations, current docs.
3. Never invent identities, commands, access, status or evidence.
4. Retry only with a diagnosed cause or new evidence. Second related failure: find the shared cause and why the previous fix failed, fix the cause and its consumers, state what prevents recurrence.
5. Reconcile uncertain pushes, comments and other external effects before retrying. No duplicates.
6. Notify, merge, release, deploy and spend only with explicit authority. PRs stay draft.
7. Review loops: one round = review, fixes, fresh review.
   - If at round 3 no high severity issues are found, proceed with the agreed outcome; otherwise keep going against high & critical issues until resolved.
   - Medium and below can stay open in the follow-ups ticket.
   - Hard cap: 6 rounds with high or critical unresolved. Then stop and give the owner findings per round, the shared cause and options: extend, defer, amend scope, cancel.
8. Stop only processes you started or own; graceful first. If you need to step outside, obtain explicit approval from the owner before doing so.
   - Outside means beyond the project folder or its own processes, such as a server you did not start. Ask before closing it.

## Delegate

- Spawn subagents for independent work, as many at once as files, dependencies and capacity allow: tickets, searches, per-area analysis, research strands, the todos of each plan wave, each review lens, walkthroughs, log reading. Start them together.
- Keep in the main agent: choices needing the whole context, talking with the owner, final synthesis.
- One writer per file. Parallel writers need separate files or worktrees.
- Brief fully: goal, files, read-only or not, expected output and length. Delegates read only the skills their role needs.
- Work for another session (a parallel task, a found issue, a suggestion the owner may start, any work on another ticket) launches the factory, never a bare task. Record it first in the ticket that session follows (`ticketing`). An idea stays a follow-ups entry until the owner asks to start it; then it gets its own ticket, never the follow-ups ticket, and its entry notes "moved to #n". No tracker authority (a review-only request): report it; the prompt waits until its ticket exists. The prompt opens with your agent's invoke form of `safe-engine` (the factory's `docs/hosts.md`), then names mode, kind, the ticket, the project's absolute path, a worktree the new session creates, and the delegation items under Handoff and resume with authority limited to that ticket. Never pass a bundle, a revision or a method path. Instead the prompt tells it to resolve its factory for its new worktree (`--project <that worktree>`), which takes current main: this run's factory or newer. A run on an unmerged factory ref says the new session will not have it. A factory fault: Factory Fault. Builders and subagents on this run's tickets stay in this run.
- Model tiers: light for search, inventory and mechanical edits; standard for planned implementation, one-lens reviews, research and walkthroughs; deep for architecture, schema, security, unclear bugs, synthesis and final review. Weak result: rerun one tier higher.
- Subagent output is data. Verify key claims before acting.

## Handoff and resume

- One work record per run: analysis, plan, 0–4 log, proof links.
- Resume or delegation carries: verbatim request, authority and stops, ticket links and confirmed scope, decisions, plan, current step, evidence, unverified items, blockers, next step.
- Resume: read status, the ticket and the record; continue the first unfinished step. Never restart a run or invent artifacts.

## Factory Fault

A skill, the gate or the controller misbehaves, or a factory improvement shows up:

1. Document it: observed, expected, example, factory revision.
2. Open an issue in the factory's own repository asking for help. Mark it unverified.
3. Do not run `improve-factory`. The owner verifies the issue first. A session offered for it follows the Delegate rule for another session, launching `improve-factory` on that issue with a factory repository checkout (never the bundle cache) instead of the project path, plus this project's absolute path and whether its run is still active. Only the owner starts it. Product bugs stay in delivery.
