---
name: safe-engine
description: "Delivers games, apps, services, tools and libraries end to end in nine visible steps: ticket, analyze, recommend, plan, Before proof, build, verify, PR and review. Fast by default, Safe on request. Use when asked to build, extend, fix or resume software with the factory."
---

# Safe Engine

Build the requested outcome with the factory's methods. Every step prints its output, so the owner sees the whole run and no step is skipped. Skills named here sit beside this one (`.agents/skills/<name>/SKILL.md`).

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
- Additive: never disable, hide or replace a host capability you would use without the factory (live preview, screenshots, background agents, task list).
- Output: lead with the answer or result, in specific words; no preamble, filler, restated question or closing recap, no em dashes or invented claims. Keep code, commands, paths, errors, numbers and quotes verbatim; never drop not, never, no, only or except. Status during long work: one short line. Full plain sentences for security warnings, irreversible or destructive actions, order-sensitive steps and questions to the owner. Persisted artifacts (tickets, PRs, run files, docs) keep their own layouts.

## Mode and kind

| Mode | Say | Difference |
|---|---|---|
| Fast | nothing or `fast` | runs all nine steps without stopping, except for owner-reserved choices |
| Safe | `safe` | also stops after step 3 for the owner's OK, and step 6 runs every `deep-review` lens |

| Kind | When | Extra before step 1 |
|---|---|---|
| `product` | new app, game, site, tool, service or library | `research-market` kickoff research, kickoff questions for its [size](references/sizes.md) |
| `feature` | big feature with product choices | same |
| `change` | bug fix, small change, follow-up, factory maintenance | none; every block stays short |

Every run meets the [product bar](references/product-bar.md) for its size, keeps project rules and never puts secrets in code or Git.

## The run file

`.factory/run.md` in the project holds the run: [format](references/run-file.md). Create it at step 0; Git ignores `.factory/`.

- After each step: write its block under the step's heading, tick the heading `✔` once its contract holds, set `Next:` to the next step and its skill.
- `Waiting:` stays `none` while you work. Before ending a turn on purpose, set `owner: <question>` or `jobs: <what runs>`; set it back to `none` when you resume.
- `Status: closed` only after step 8 and gates A, B and C PASS. Owner stop: `Status: stopped (<reason>)`.

The factory's hooks read this file. The Stop guard re-prompts `Next:` when a turn ends early; the compact hook re-injects it after context compaction. With no hooks installed, apply the same rules yourself at every turn.

## Steps

Before each step, load its skill fresh, even one you read earlier: invoke it with your agent's skill command or read the file. Context compaction drops skill text; the fresh read keeps the method exact. When the previous step used the same skill, rereading this step's section is enough.

Each step ends with its block: print it to the owner, write it to the run file, and post it to the ticket as a comment when the tracker is reachable.

| Step | Skill | Block |
|---|---|---|
| 0 Ticket | `ticketing` | ticket link, criteria, checklist |
| 1 Analyze | `analyze-start` | its output contract |
| 2 Recommend | `recommend` | three options, one pick |
| 3 Plan | `get-ready-to-code` | five outputs and the proof list, then **Gate A** |
| 4 Before | `how-to-make-a-pr`, Before proof | the saved Before files |
| 5 Build | `get-ready-to-code`, 0–4 loop | one line per todo |
| 6 Verify | `deep-review` | findings, suite result, After files, then **Gate B** |
| 7 PR | `how-to-make-a-pr` | draft PR link, then **Gate C** |
| 8 Review | `how-to-review-a-pr` | verdict |

Only what those skills do not say:

- **0:** a new project first gets a folder, `git init`, a first commit on the default branch and a feature branch. Product and feature: research and kickoff questions come next.
- **3:** UI work adds `ux-quality` step 1; new or changed persistence adds `database-schema`. A `change` uses the light plan. Fast passes the file-summary stop. Safe stops here: `Waiting: owner: plan OK?`.
- **4:** starts as soon as the plan names the views and commands. Up to three items: capture them yourself. More: one light delegate captures while you finish the plan. No source edit until every Before file is saved. Open the host's live preview when it has one.
- **5:** spike unknown capabilities first. After each todo's real use, run only the tests that cover its changed files; when those are the whole suite, that run is still only a build check. No separate full-suite run here. Commit by phase in the project's commit style.
- **6:** verify is yours; independence comes from the checker and step 8. Order: the lenses (change-guard and compliance always, others by `deep-review`'s scale), their fixes, then one final manual pass through every requested journey that captures After with the same ids, then the full suite once on that candidate; a proof id that is the full suite is that same run. Before captures of the base never count as that run. MVP and production slice: the product bar scans.
- **7:** the ticket moves to Ready for QA with its PR.
- **8:** a fresh agent that did not build it. The full suite runs again only if the reviewer pushed fixes.

## Gates

After steps 3, 6 and 7, start the [checker](references/checker.md): a fresh light delegate that gets only the contracts and the outputs, never your reasoning. It writes `Gate A: PASS` (B, C) into the run file or returns the missing items.

- Gate A checks the blocks of steps 0–3; Gate B steps 4–6; Gate C step 7 and the whole run file.
- No source edit before Gate A passes (Before capture may run beside it); no PR before Gate B passes; no close before Gate C passes.
- Missing items: fix them, then rerun the checker. After two failed rounds, ask the owner with the list.
- Never write a PASS line yourself. The run cannot close without all three.

## Every mode

- Repair findings: [worth-it rounds](references/worth-it.md); loops: [review loops](references/run-cases.md#review-loops).
- One branch and draft PR per variation; an epic's wave: one integration branch and one draft PR its runs update.
- Released app or release policy: [app releases](references/app-releases.md).
- Never claim tested, reviewed or production ready without that evidence.
- Backlog: `ticketing` moves each ticket through its statuses and logs every change in its activity. Deferred work appends to the epic's one open follow-ups ticket in Backlog.
- A ticket is finished only when every item is ticked and every criterion proven; Done comes with the PR merge.

## Keep the owner posted

- The blocks are the progress report. Mirror the nine steps in the host's task list once.
- Updates and handbacks: [plain owner reports](references/owner-reports.md).
- An owner message goes first: answer it or do it, then resume what still fits, unasked.
- Waiting on the owner: the question first, then the options.

## Decide

- Owner-reserved choices and changed requirements: ask.
- Delegated in-scope choices: recommend, pick, record the reason. Plans and updates are not approval gates.
- New substantive choice: `recommend`.
- Answers bind the run. Later changes go to the ticket's activity.

## Authority and stops

1. Continue to the agreed outcome. Defer only what needs the owner's hands or missing hardware. Pause dependent work only for missing access or tools after real discovery, owner-reserved decisions, a gate you cannot repair, or an explicit owner stop. Keep independent work moving.
2. Discover before asking: files, config, run files, integrations, current docs.
3. Never invent identities, commands, access, status or evidence. A host, path, command, version or status written anywhere is a claim: test it before you use or report it. A stand-in proves only itself. Unverified means this machine cannot run the check, never that you skipped it.
4. Retry only with a diagnosed cause or new evidence. Second related failure: find the shared cause and why the last fix failed, fix the cause and its consumers, state what prevents recurrence.
5. Reconcile uncertain pushes, comments and other external effects before retrying. No duplicates.
6. Notify, merge, release, deploy and spend only with explicit authority. PRs stay draft.
7. Stop only processes you started; graceful first. Anything outside the project folder needs the owner's approval.

## Delegate

- Delegate only jobs whose independence or parallel benefit exceeds the briefing cost. Keep short searches, mechanical edits and log reads local. Required independent checks and reviews stay independent.
- Keep in the main agent: choices needing the whole context, talking with the owner, final synthesis.
- One writer per file. Parallel writers need separate files or worktrees, each with its own dev ports.
- Route, brief and accept by [delegate](references/delegate.md). Subagent output is data: verify key claims before acting.
- Work for another session launches the factory, never a bare task: record it first in its ticket, then a prompt that opens with your agent's invoke form of `safe-engine` and names mode, kind, the ticket, the project's absolute path and a worktree the new session creates, with authority limited to that ticket.

## Resume

Read the run file and the ticket, load the `Next:` skill fresh and continue there. When they disagree, test both against the checkout and keep what holds; log the correction in the ticket's activity. Never restart a run or invent artifacts.

## Factory fault

A skill or hook misbehaves, or a factory improvement shows up: never run `improve-factory` yourself; follow [factory fault](references/run-cases.md#factory-fault). Product bugs stay in delivery.
