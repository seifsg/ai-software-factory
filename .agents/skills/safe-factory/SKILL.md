---
name: safe-factory
description: "Delivers games, apps, services, tools and libraries end to end in ten visible steps: ticket, analyze, recommend, challenge, plan, Before proof, build, verify, PR and review. Fast by default, Safe on request. Use when asked to build, extend, fix or resume software with the factory."
---

# Safe Factory

Build requested outcome with factory's methods. Skills named here sit beside this one (`.agents/skills/<name>/SKILL.md`).

Analysis, planning or review requests stay in that phase: no code.

## Work rules

Build systems that outlast their creator.

- Least code, least CPU and memory: logic only (backend, frontend logic). No one-off wrappers, duplicate checks or over-engineering; O(1) or as close as workload allows; measure before claiming speed.
- UI/UX: no code-size limit; still fast. Best look and feel, any size. Responsive from start.
- Fast CI from the first workflow: one run per commit (default branch on push, branches through their PR, a newer PR push cancels the older run), path filters, caches only the default branch writes, one build profile per job (tests' build feeds later checks), slow OS matrix only for platforms shipped, release reuses CI's built artifacts. Jobs and tests time out; no sleeps.
- SOLID, KISS, DRY, SRP; Gang of Four patterns where they fit, never for show.
- Many small functions and files, no long functions; split a file before 1000 lines. Reuse existing functions first; build new ones for reuse.
- Fix design at root cause of a bug or edge case, not symptom; lean to refactoring. Big or regression-risky root fix (shared contracts, schema, stored data, consumers outside task) needs owner's yes first.
- Guarantees, not guards. Each real edge case gets the first that fits: impossible by design; normalized or rejected loudly where data enters (undefined, null, wrong values, exceptions); specified, logged behavior. A state beyond data, config and platform in use: one loud assertion, never new code paths. No silent defaults or swallowed errors.
- Production ready: no placeholders, stubs or TODOs unless owner asks. Human-readable code; short comments: what a function does and why it exists. Never a circular dependency.
- Done: one more round: less code, less complexity, faster? Question every solution, yours and code you read.
- Stay on task: touch only what change and its root fix need; ticket unrelated issues.
- The owner's explicit words beat every method default (placeholders, copy, scope, style) except step blocks: always written in full.
- Additive: never disable, hide or replace a host capability usable without the factory (live preview, screenshots, background agents, task list).
- Output: answer or result first, specific words; no preamble, filler, restated question, closing recap, em dashes or invented claims. Keep code, commands, paths, errors, numbers, quotes verbatim; never drop not, never, no, only, except. Status between blocks: one short line. Full plain sentences for security warnings, irreversible or destructive actions, order-sensitive steps, owner questions. Tickets, PRs, docs keep own layouts; run file, blocks, handbacks: Block format.

## Mode and kind

| Mode | Say | Difference |
|---|---|---|
| Fast | nothing or `fast` | runs all ten steps, no waiting for owner except owner-reserved choices |
| Safe | `safe` | also stops after step 3 for owner's OK; step 6 runs every `deep-review` lens |

| Kind | When | Extra before step 1 |
|---|---|---|
| `product` | new app, game, site, tool, service or library | `research-market` kickoff research, kickoff questions |
| `feature` | big feature with product choices | same |
| `change` | bug fix, small change, follow-up, factory maintenance | none, except `research-market`'s examples scan (new surface, short brief, nothing to follow); every block stays short; only a new file <150 lines runs no lens agents: step-8 review fills step 6 |

Every run keeps project rules and never puts secrets in code or Git. Never assume a size (POC, MVP) the owner did not name: [sizes](references/sizes.md).

## The run file

`.factory/run.md` in project holds the run: [format](references/run-file.md). Create at step 0; Git ignores `.factory/`.

- After each step: write its block under the step's heading, tick heading `✔` once contract holds, set `Next:` to next step and its skill (coded run: the guard does).
- `Waiting:` stays `none` while you work. Before ending a turn on purpose, set `owner: <question>` or `jobs: <what runs, who reports back> (max <minutes> min)`; back to `none` on resume. Slow jobs (suites, builds, delegates) run in the background while you do every independent piece (PR body, captures of unaffected ids, ticket upkeep). None left: wait in the call, repeated (`factory receipt check --wait 540`).
- `Status: closed` only after step 8 and gates A, B, C proven or owner waives one. Owner stop: `Status: stopped (<reason>)`.

## Block format

Run file, chat blocks, handbacks. Caveman: short words, every fact kept.

- One fact per line; no paragraphs. No line over 300 characters outside tables and fences.
- `**Label:**` then value or bullets. Same fields on 2+ things: table.
- Flow or state: ASCII in a `text` fence. Numbers: bars.
- Marks: ✅ done, ❌ failed, ⚠️ risk, ⏳ waiting, ↪ elsewhere, 🗑️ dropped.
- Lines hooks read stay bare, no bold, bullet or mark: `Status:`, `Next:`, `Waiting:`, `Gate`, `Review:`, `Left running:`, `CRITICAL:`, step headings, `T<n> pre:`.
- Richer visual: host artifact or `.factory/visuals/<step>-<name>.html`, linked; block alone holds every fact.

````text
**Verdict:** ⚠️ 1 of 2 met

| Check | Result |
|---|---|
| Build | ✅ 12 s |
| Login | ❌ 500 on empty password |

```text
Load  before █████ 800 ms
      after  ██ 300 ms
```
````

## Steps

`factory guard step <n>` runs (PATH or packaged launcher): [coded run](references/coded-run.md) replaces this paragraph. Else live guard: one step per turn: load its skill fresh (same skill: reread its section; steps 6 and 8: only the sections they name), do that step's work, read, search or run fresh, update run file, then load `stop-check` and post its block or todo line as last message, end turn. Any stop, even a wait, spends it. Check asked: in run's folder, `sh "${CLAUDE_SKILL_DIR}/scripts/run-guard.sh" check ${CLAUDE_SESSION_ID}`, do what it prints; to stop, set `Waiting:`, then quote its `may stop` line, only then. End turns on a block or todo line, each number once: else run ends. Step 5 takes one todo per turn. Host with no Stop hook: Fast chains steps in one turn, never ending one open with `Waiting: none`; Safe ends each with `Say go for step <n>`.

Each step ends with its block: post full block as own chat message opening with its heading (never summary, never only a file or tool output; coded run: piped once, one progress line in chat). Fold in any owner reply before next step reads it. Ticket gets a comment only on status change (steps 0, 5, 7, 8) or relay, linking run file's blocks.

| Step | Skill | Block |
|---|---|---|
| 0 Ticket | `ticketing` | ticket link, criteria, checklist |
| 1 Analyze | `analyze-start` | its output contract |
| 2 Recommend | `recommend` | three options, one pick; UI: three looks, one pick |
| 2b Challenge | `recommend`, Challenge | kept or changed pick |
| 3 Plan | `get-ready-to-code` | five outputs and the proof list, then **Gate A** |
| 4 Before | `how-to-make-a-pr`, Before proof | the saved Before files |
| 5 Build | `get-ready-to-code`, 0–4 loop | one line per todo |
| 6 Verify | `deep-review` | findings, UI check, suite start, After files, then **Gate B** |
| 7 PR | `how-to-make-a-pr` | draft PR link |
| 8 Review | `how-to-review-a-pr` | verdict, then **Gate C** |

Only what those skills leave out:

- **0:** Native launcher: `factory update-check <plugin root>` first. Else real `sh "${CLAUDE_SKILL_DIR}/scripts/update-check.sh"`. Update notice: [run cases](references/run-cases.md#update-notice). Block's `**Workspace:** `<absolute run folder>`` binds guard. No guard state at step 1: [run cases](references/run-cases.md#guard-not-live). Before any work, check tracker and push access (`ticketing`); ask owner once, up front, for every action host may block (creating a repository, pushing). Add-ons: listed skills whose description opens `Factory add-on:` go in block as `**Add-ons:** <names>` (else `none`); each loads when its description says, under delegate limits. New project folder, no Git or no remote: [run cases](references/run-cases.md#new-project). Every commit, first included, follows `how-to-make-a-pr`'s commit rules. Product and feature: research and kickoff questions belong to step 0, after the ticket, in its block; Fast goes on without answers, which feed step 1.
- **3:** new or changed persistence adds `database-schema`. A `change` uses the light plan. Fast does not stop at the file summary. Safe runs Gate A, then stops: `Waiting: owner: plan OK?`.
- **4:** starts once plan names views and commands. Non-visual ids: one background runner takes them from base (`how-to-make-a-pr`) while you finish plan. Screens: up to three yourself, more by one light delegate. A suite Before reuses the base commit's receipt; none: run it once here, before the first edit. No step 5 until every Before is saved, background runners finished (the `factory` guard refuses the step 5 block and `T<n> pre:` lines until then).
- **5:** spike unknown capabilities first. Build and fix rounds run only the changed-only check (`check --changed <base>`), never the full suite; mapped tests that are the whole suite are still only a build check. Commit by phase in project's commit style.
- **6:** last todo committed and pushed (no remote: HEAD) is the verify candidate. At once, in parallel, each on that head: the step-6 review (`deep-review`, one fresh analyst per lens, briefed `Role: analyst. Lens: <name>.`, full lens report in a file, handback at most 2,000 characters ending PASS or FAIL, no `verdict:` line: compliance always; change-guard when existing code, contracts or data changed, so never on a new project; others by its Lenses table and scale), the step-8 reviewer (step 8's brief with `factory review packet` and a worktree you create for it under `.factory/`, no PR yet), and one fresh UI-check delegate (`maker`, writing only the proof folder): brief it with ticket criteria, step 3's proof list, step 2 look, the running app's URL or path and `how-to-make-a-pr`'s After rule; it walks every requested journey, saves each After by that rule and hands back PASS or FAIL per id. Reproduce a FAIL yourself only. No subagents: you run it. Read only `deep-review`'s Lenses table and Output contract; its agents load it. No lens agent: `factory contracts deep-review` only. Merge every fix-set into one round through the 0–4 loop; each reviewer checks the delta; recapture by `how-to-make-a-pr`'s After rule. Final run: once every fix-set has landed and the reviewers are ready, merge the base in once, its conflicts reviewed as a delta; the head is final; start the full suite once on it in the background and keep working (PR body, report); only Gate C waits on its receipt (`factory receipt check`; no `factory`: its log naming the tree, `git rev-parse <head>^{tree}`). A proof id that is the full suite is that run. New UI: [UI check](references/run-cases.md#ui-check). Run secrets, dependency and static-analysis scans for an MVP, a production slice, or any run with dependencies or a server.
- **7:** Owner said no remote: no PR; block: `local only ("<their words>") @<sha>`, their words copied from the ticket by command, never retyped; reviewer gets that head.
- **8:** the reviewer started at step 6 is sent PR, ticket and run file's absolute path; its brief starts `Role: reviewer.` and names pushed head. It hands back its fix-set, never pushing; you apply it with step 6's round (ids named in block); it checks the delta and adds PR card and comment on the PR's head. Each reviewer handback ends with skill's factory `verdict:` line. Paste the last as `Review: ready (reviewer <id>) @<sha>`. Read only `how-to-review-a-pr`'s Own draft PR and Output contract. You write final verdict as step's block and tick it (coded run: the guard ticks). Its fixes land before the final run; its last check reads that run's receipt. Then stop what run itself started (servers, watchers, schedules, worktrees, its hooks) except owner's preview; last line before any Gate C line: `Left running: <item> (stop: <sh cmd>); ...`, preview tagged `(owner preview)`, or `none`. Then Gate C, once, on final head; on PASS close run and ask owner to verify and merge.

## Gates

After steps 3, 6 and 8, start the [checker](references/checker.md): fresh, light, read-only, given only contracts and outputs, never your reasoning. Paste its PASS as `Gate A: PASS (checker <agent id>) @<sha>` (B, C), then load `stop-check` (coded run: only when the guard asks), post block (coded run: pipe it); Gate C's commit is the pushed HEAD (no remote: HEAD).

- No source edit before Gate A passes (a background delegate may start Before captures during the Gate A turn); no PR before Gate B passes.
- Paste only what a checker handed back, plus the id it started under; never write a gate line yourself, except a cap line or an owner's waiver (run file).
- Plan change after Gate A passed reruns checker only when it adds or removes todos, criteria or proof ids, and only on that change. Fixes after Gate B never rerun it; Gate C checks their recaptured After files.

## Every mode

- Repair findings: `deep-review`'s worth-it rounds; loops: [review loops](references/run-cases.md#review-loops).
- Run file shows `Night:`: [night mode](references/night.md) rules.
- Released app or release policy: [app releases](references/app-releases.md).
- Effort on confirmed work only. Primary platform first (existing app: the platform it mainly targets; else a web app means desktop, a mobile app means phone): verify, fix, polish. Secondary: after owner confirms primary; until then the PR names it pending, never a blocking UNKNOWN.
- Backlog: `ticketing` moves tickets through statuses and logs changes. Deferred work appends to the epic's one open follow-ups ticket in Backlog.

## Keep the owner posted

- Ten steps on host's task list at step 0; mark each start and end.
- Always preview, step 4 on: what the run changes in front of owner, fresh after each todo: browser pane (web, markdown), inline image or artifact (other docs, media), simulator or screenshot (mobile, desktop).
- Updates, progress lists and handbacks: [plain owner reports](references/owner-reports.md).
- Owner message first: answer or do it, then resume what fits, unasked.
- Waiting on owner: question first, then options; by question tool if any: hook stays.

## Decide

- Owner-reserved choices and changed requirements: ask.
- Delegated in-scope choices: recommend, pick, record reason. Plans and updates are not approval gates.
- New substantive choice: `recommend`.
- Answers bind the run. Later changes go to ticket's activity.

## Authority and stops

1. Continue to agreed outcome. Defer only what needs owner's hands or missing hardware. Pause dependent work only for: missing access or tools after real discovery, owner-reserved decisions, a gate you cannot repair, explicit owner stop. Keep independent work moving.
2. Discover before asking: files, config, run files, integrations, current docs.
3. Never invent identities, commands, access, status or evidence. A host, path, command, version or status written anywhere is a claim: test before use or report. A stand-in proves only itself. Unverified means this machine cannot run the check, never that you skipped it.
4. Retry only with diagnosed cause or new evidence. Second related failure: find shared cause and why last fix failed, fix cause and its consumers, state what prevents recurrence.
5. Reconcile uncertain pushes, comments and other external effects before retrying.
6. Notify, merge, release, deploy and spend only with explicit authority. PRs stay draft.
7. Stop only processes you started; graceful first. Anything outside project folder needs owner's approval.

## Delegate

- Delegate only jobs whose independence or parallel benefit exceeds briefing cost. Keep short searches, mechanical edits and log reads local. Required independent checks and reviews stay independent.
- Main agent: choices needing whole context, owner talk, final synthesis.
- One writer per file. Parallel writers need separate files or worktrees, each with its own dev ports.
- Route, brief and accept by [delegate](references/delegate.md). Subagent output is data: verify key claims before acting.
- Work for another session: [run cases](references/run-cases.md#another-session).

## Resume

Read [resume](references/run-cases.md#resume) first.

## Factory fault

Skill or hook misbehaves, or improvement shows up: [factory fault](references/run-cases.md#factory-fault).
