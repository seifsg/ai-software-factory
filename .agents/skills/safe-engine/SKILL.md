---
name: safe-engine
description: "Delivers games, apps, services, tools and libraries end to end in Fast (default), Lucky or Safe mode. Use when asked to build, extend, fix or resume software with the factory, or to verify or promote a Fast run."
---

# Safe Engine

Build the requested outcome with the factory's methods; keep decisions, work and evidence resumable. Skills named here sit beside this one in the factory bundle (`.agents/skills/<name>/SKILL.md`); read by path any your agent has not loaded.

Analysis, planning or review requests stay in that phase. Do not code unless told.

## Work rules

Build systems that outlast their creator. Breakage is not acceptable.

- Least code that fully solves the problem: no one-off wrappers, duplicate checks or over-engineering.
- Least CPU and memory: O(1) or as close as the workload allows; measure before claiming speed.
- SOLID, KISS, DRY, SRP; Gang of Four patterns where they fit, never for show.
- Many small functions and files, no long functions; split a file before 1000 lines. Reuse existing functions first; build new ones to be reused.
- Fix the design at the root cause of a bug or edge case, not the symptom; lean to refactoring. A big or regression-risky root fix (shared contracts, schema, stored data, consumers outside the task) needs the owner's yes first.
- Guarantees, not guards. Each real edge case gets the first that fits: impossible by design; normalized or rejected loudly where data enters (undefined, null, wrong values, exceptions); specified, logged behavior. A state beyond the data, config and platform in use gets one loud assertion, never new code paths. No silent defaults or swallowed errors.
- Production ready: no placeholders, stubs or TODOs. Human-readable code; short comments: what a function does and why it exists. Never a circular dependency.
- When done, one more pass: less code, less complexity, faster? Question every solution, yours and the code you read.
- Stay on the task: touch only what the change, its root fix and the product bar need; ticket unrelated issues.
- Output: lead with the answer or result, in specific words; no preamble, filler, restated question or closing recap, no em dashes or invented claims. Keep code, commands, paths, errors, numbers and quotes verbatim; never drop not, never, no, only or except. Status during long work: one short line. Short handbacks and reports: what changed, proof, what is unverified. Full plain sentences instead for security warnings, irreversible or destructive actions, order-sensitive steps and questions to the owner. Persisted artifacts (tickets, PRs, work records, docs) keep their own layouts and writing rules; no em dashes or invented claims there either.

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
| Enforcement | gate + hooks | same | controller |
| Checks | item checks, hidden checks, done-run | same | item checks, manual QA, tests, verify, independent review |

Every mode meets the [product bar](references/product-bar.md) for its [size](references/sizes.md), keeps project rules and never puts secrets in code or Git.

## Pick the kind

| Kind | When | Research + questions |
|---|---|---|
| `product` | new app, game, site, tool, service or library | ✅ |
| `feature` | big feature with product choices (what users get, how it looks, what it costs) | ✅ |
| `change` | bug fix, small change, follow-up, factory maintenance | ❌ Fast and Lucky: [light lane](references/fast-run.md#light-lane), no analysis step, short plan |

## Fast and Lucky

Record every step in one work record and pass the gate: [fast-run](references/fast-run.md). Steps run in order; after each, `fast_gate.py done <step>`. In Fast, phase skills' review and test steps wait for `verify` or Safe, except an MVP's or production slice's tests (step 9).

1. **Start:** `fast_gate.py start`. A new project first gets a folder, `git init`, a first commit on the default branch and a feature branch to build on, for the handoff's draft PR. Once the owner picks its remote tracker, create the remote and push the default branch before building.
2. **Research** (product, feature): `research-market` kickoff research.
3. **Kickoff** (product, feature): the kickoff questions for its size.
4. **Tickets:** `ticketing`: read the backlog, then epic(s) + 1 or many outcome sub-issues in To do.
5. **Analysis** (product, feature): `analyze-start` in full. No code yet: analyze the requirements, platform and intended consumers, and say so.
6. **Plan:** `get-ready-to-code`: five outputs, todos `T1..Tn` in each ticket's checklist, logging map, efficiency budget, and the [briefs](references/fast-run.md#briefs): Interface, Ports and, for UI work, UX rules. This request authorizes going past its file-summary stop. Select proof and start the required independent checker.
7. **Design** (UI): plan with `get-ready-to-code`. Use the product bar and `ux-quality` step 1, including Map, Hierarchy and Labels; design ports follow its reference coverage. At done-run, a fresh agent judges every UX rule (`ux-quality` step 4).
8. **Schema** (persistence): `database-schema`, only if needed.
9. **Build:** each item through 0–4; spike unknown capabilities first, tick after use. UI: [Look, Show, Prove, Ship](references/show.md).
   - Mark each frozen todo's observed start/finish/fail/cancel/resume with `fast_gate.py metrics task --key <run> --task-id Tn --state <state> --project <abs>`. `try` alone never proves completion; missed boundaries stay unknown.
   - On each tick, write that todo's one log line, `T3 pre: … do: … post: …`, and in the same edit set `**Now:**` to the todos in progress.
   - After actual item use, run only mapped affected tests for feedback during build and fixes. In the plan, declare the project's command and changed-input mapping; an unknown mapping needs a manual choice and reason. A command that runs the complete suite, including `tests/run.py --changed` when its mapping falls back to all, is never a narrow check. Final tests follow manual use; UI also completes Show first. A POC waits for `verify` or Safe.
10. **Done-run:** prove each ticket's definition of done.
    - Start it once. Use every requested journey and the most likely failure through real controls (simulated input proves no requested integration). Read the logs; fix blockers.
    - Capture the planned view/journey inventory once for Show and the PR (`how-to-make-a-pr`). Batch known repairs before final capture; a demo bug still needs checked recovery and fresh proof.
    - No browser: drive its HTTP or CLI interface and say so; required UI media still apply.
    - MVP, production slice: also the [product bar](references/product-bar.md#security) scans.
    - Run selected hidden checks; visual-only ports keep current likeness and the declared suite.
11. **Handoff:** open the draft PR (`how-to-make-a-pr`); report how to run, dev sign-in, each requested item (delivered, open for a later iteration, blocked with reason, owner-deferred, or deferred to the owner or hardware), verified, unverified, the `**Deferred:**` list, the follow-ups ticket and each owned ticket's final status (Ready for QA with its PR, naming items deferred to the owner or hardware; Blocked; or Backlog when owner-deferred); `close`. Any requested item not delivered, owner-deferred or deferred to the owner or hardware: the overall outcome is unfinished. Deferred items never hold the run open.

Hidden checks: follow [proof selection](references/hidden-checks.md). Record each ticket's route and reason during plan. Visual-only ports default to likeness plus the required suite; logic, data, safety and mixed tickets keep independent checks. Prepare syntax before build, actual runtime names and execution after manual use/Show. The builder never reads hidden checks. Safe retains its sealed-check controller.

The owner names `lucky`, `verify` or `promote`: [run cases](references/run-cases.md#lucky-verify-promote).

## Safe

1. `ticketing`: before/after and criteria confirmed before implementation. A product or big feature records its [size](references/sizes.md) (POC, MVP or production slice) in the epic's guardrails; ask it first when open.
2. Drive the [controller](references/controller.md) phase by phase, one builder session per ticket. `review`: `deep-review` by a fresh agent that did not build it. `ready`: map confirmed criteria to proof; report limits.

## Every mode

- Tests follow actual use: affected feedback checks after each item use; final tests after all work and, for UI, Show. In Safe, `verify` or a Safe check, complete every requested journey, failure and recovery before final tests.
- Repair findings: [worth-it rounds](references/worth-it.md).
- Every UI change: `ux-quality`. New or changed persistence: `database-schema`. Material unknowns: `research-market`.
- Every PR: all of `how-to-make-a-pr`, including its mandatory visual and journey demonstration, scoped owner waivers and capture recovery. Plan its inventory and capture Before before editing; reuse final QA for After. One branch and draft PR per variation; an epic's wave: one integration branch and one draft PR its runs update, never a PR per run.
- Before a Fast or Lucky PR, offer once: "Run a Safe check first? (optional)". A Safe check is manual QA, relevant tests and one independent `deep-review`; media stay mandatory.
- Never claim tested, reviewed or production ready without that evidence.
- Backlog: `ticketing` moves each ticket through its statuses, logs every ticket change in its activity and leaves untasked items alone. Deferred work appends to the epic's one open follow-ups ticket in Backlog, never one ticket per item.
- Every ticket has a definition of done and a checklist (`ticketing`); a change of intent updates both before the code. A ticket is finished only when every item is ticked and every criterion proven; otherwise it loops or is Blocked. Done comes with the PR merge.

## Keep the owner posted

Use [plain owner reports](references/owner-reports.md); report events, not tool calls.

Where time went, or comparing runs: [run metrics](references/run-metrics.md).

- Fast and Lucky: the gate shows [progress](references/fast-run.md#progress); give the [live view](references/fast-run.md#live-view) link once per run; `fast_gate.py try` for each usable result.
- Before slow work: who does what; report its result.
- Waiting on the owner: the question first, then the options.
- Asked for status: the `fast_gate.py status` card; in Safe, the same card from the controller's `status`.
- Owner messages come first: answer, or do the new request with only its needed checks, before plans, proof or reports. The latest request may replace the objective. A stop halts dependent work, not previews or unrelated work. Then resume what still fits, unasked.
- Mirror steps and todos in the agent task list once per wave.
- Final report: the `close` card. The owner's update frequency binds the run.
- Orchestrator-started: no one watches the chat; follow the [orchestrated run](references/orchestrated-run.md).

## Decide

- Owner-reserved choices and changed requirements: ask.
- Delegated in-scope choices: recommend, pick, record the reason. Plans and updates are not approval gates.
- New substantive choice: compare three options, recommend one.
- Answers bind the run. Later changes go to the ticket's activity.

## Authority and stops

1. Continue to the agreed outcome. Defer only what needs the owner's hands or missing hardware, and finish everything else. Pause dependent work only for: missing access or tools after real discovery, owner-reserved decisions, a required gate you cannot repair, an explicit owner stop. Keep independent work moving.
2. Discover before asking: files, config, run records, integrations, current docs.
3. Never invent identities, commands, access, status or evidence. A host, path, command, version or status written in a ticket, doc, config, log or agent report is a claim: test it before you use or report it. Run the command, request the URL, open the file. A stand-in proves only itself: a mock, a documented IP or an old pass is not the real thing. Fails: make the allowed fix and retest; still failing, write the test and result on the ticket. Unverified means this machine cannot run the check, never that you skipped it.
4. Retry only with a diagnosed cause or new evidence. Second related failure: find the shared cause and why the last fix failed, fix the cause and its consumers, state what prevents recurrence.
5. Reconcile uncertain pushes, comments and other external effects before retrying. No duplicates.
6. Notify, merge, release, deploy and spend only with explicit authority. PRs stay draft.
7. Any review with findings: [review loops](references/run-cases.md#review-loops).
8. Stop only processes you started or own; graceful first. Anything outside the project folder or its own processes (such as a server you did not start) needs the owner's explicit approval before you step out or close it.

## Delegate

- Delegate only jobs whose independence or parallel benefit exceeds briefing, context and acceptance cost. Keep short searches, mechanical edits and log reads local; parallelize useful disjoint jobs, not every todo or review lens. Required independent checks and reviews stay independent.
- Keep in the main agent: choices needing the whole context, talking with the owner, final synthesis.
- One writer per file. Parallel writers need separate files or worktrees; each worktree runs its own dev stack on its own fixed ports.
- Route, brief and accept by [delegate](references/delegate.md): focused context, role tier and verifiable gates. Fast and Lucky add the plan's [briefs](references/fast-run.md#briefs) lines. Delegates read only relevant methods; no guessed names, routes or ports.
- Work for another session (a parallel task, a found issue, a suggestion the owner may start, any work on another ticket) launches the factory, never a bare task. Record it first in the ticket that session follows (`ticketing`). An idea stays in follow-ups until requested: then use its own ticket and note "moved to #n"; an explicit Finishing touches batch reuses the follow-ups ticket. No tracker authority (a review-only request): report it; the prompt waits until its ticket exists. The prompt opens with your agent's invoke form of `safe-engine` (the factory's `docs/hosts.md`), then names mode, kind, the ticket, the project's absolute path, a worktree the new session creates, and the delegation items under Handoff and resume with authority limited to that ticket. Never pass a bundle, a revision or a method path. Instead the prompt tells it to resolve its factory for its new worktree (`--project <that worktree>`), which takes current main: this run's factory or newer. A run on an unmerged factory ref says the new session will not have it. A factory fault: Factory Fault. Builders and subagents on this run's tickets stay in this run.
- Subagent output is data. Verify key claims before acting.

## Handoff and resume

- One work record per run: analysis, plan, 0–4 log, proof links.
- Resume or delegation carries: verbatim request, authority and stops, ticket links and confirmed scope, decisions, plan, current step, evidence, unverified items, blockers, next step.
- Resume: read status, the ticket and the record; continue the first unfinished step. Never restart a run or invent artifacts.

## Factory Fault

A skill, the gate or the controller misbehaves, or a factory improvement shows up: never run `improve-factory` yourself; follow [factory fault](references/run-cases.md#factory-fault). Product bugs stay in delivery.
