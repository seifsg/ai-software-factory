---
name: safe-factory
description: "Delivers games, apps, services, tools and libraries end to end in ten visible steps: ticket, analyze, recommend, challenge, plan, Before proof, build, verify, PR and review. Fast by default, Safe on request. Use when asked to build, extend, fix or resume software with the factory."
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: 'One factory stop: $ARGUMENTS. Read last_assistant_message. If it has a Gate or Review line no delegate handback earlier in this conversation says: ok false, reason: "Run that delegate; paste only its line." Else ok true only if it contains "Factory check: may stop", or names a denied permission or failed tool that blocks it; a wait or a question never counts. Else ok false, reason: "Run the factory check in safe-factory."'
---

# Safe Factory

Build requested outcome with factory's methods. Skills named here sit beside this one (`.agents/skills/<name>/SKILL.md`).

Analysis, planning or review requests stay in that phase: no code.

## Work rules

Build systems that outlast their creator. No breakage.

- Least code, least CPU and memory: logic only (backend, frontend logic). No one-off wrappers, duplicate checks or over-engineering; O(1) or as close as workload allows; measure before claiming speed.
- UI/UX: no code-size limit; still fast. Best look and feel, any size. Responsive from start.
- SOLID, KISS, DRY, SRP; Gang of Four patterns where they fit, never for show.
- Many small functions and files, no long functions; split a file before 1000 lines. Reuse existing functions first; build new ones for reuse.
- Fix design at root cause of a bug or edge case, not symptom; lean to refactoring. Big or regression-risky root fix (shared contracts, schema, stored data, consumers outside task) needs owner's yes first.
- Guarantees, not guards. Each real edge case gets the first that fits: impossible by design; normalized or rejected loudly where data enters (undefined, null, wrong values, exceptions); specified, logged behavior. A state beyond data, config and platform in use: one loud assertion, never new code paths. No silent defaults or swallowed errors.
- Production ready: no placeholders, stubs or TODOs unless owner asks. Human-readable code; short comments: what a function does and why it exists. Never a circular dependency.
- Done: one more round: less code, less complexity, faster? Question every solution, yours and code you read.
- Stay on task: touch only what change and its root fix need; ticket unrelated issues.
- The owner's explicit words beat every method default (placeholders, copy, scope, style) except step blocks: always posted in full.
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
| `change` | bug fix, small change, follow-up, factory maintenance | none; every block stays short |

Every run keeps project rules and never puts secrets in code or Git. Build what asked, best quality. Never assume a size (POC, MVP) the owner did not name: [sizes](references/sizes.md).

## The run file

`.factory/run.md` in project holds the run: [format](references/run-file.md). Create at step 0; Git ignores `.factory/`.

- After each step: write its block under the step's heading, tick heading `✔` once contract holds, set `Next:` to next step and its skill.
- `Waiting:` stays `none` while you work. Before ending a turn on purpose, set `owner: <question>` or `jobs: <what runs> (max <minutes> min)`; back to `none` on resume.
- `Status: closed` only after step 8 and gates A, B and C are proven or owner waives one. Owner stop: `Status: stopped (<reason>)`.

## Block format

Run file, chat blocks, handbacks. Caveman: short words, every fact kept.

- One fact per line; no paragraphs. No line over 300 characters outside tables and fences.
- `**Label:**` then value or bullets. Same fields on 2+ things: table.
- Flow or state: ASCII in a `text` fence. Numbers: bars.
- Marks: ✅ done, ❌ failed, ⚠️ risk, ⏳ waiting.
- Lines hooks read stay bare, no bold, bullet or mark: `Status:`, `Next:`, `Waiting:`, `Gate`, `Review:`, `Left running:`, `CRITICAL:`, step headings.
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

Live guard: one step per turn: load its skill, do that step's own work with fresh reading, searching or running, post its block as last message, update run file, end turn. Stop guard then sends next prompt. Factory check: `sh "${CLAUDE_SKILL_DIR}/scripts/run-guard.sh" check ${CLAUDE_SESSION_ID}`, do what it prints; to stop on purpose set header's `Waiting:`, then quote its `may stop` line. A stop spends that hook: on the next message load this skill first. Step 5 takes one todo per turn. Host with no Stop hook: Fast chains steps in one turn, never ending one open with `Waiting: none`; Safe ends each with `Say go for step <n>`. Before each step load its skill fresh (skill command or file), even one read earlier. Same skill as last step: rereading this step's section is enough.

Each step ends with its block: post full block as own chat message opening with its heading (never summary, never only a file or tool output), then write to run file. Fold in any owner reply before next step reads it. Ticket gets a comment only on status change (steps 0, 5, 7 and 8) or relay, linking run file's blocks.

| Step | Skill | Block |
|---|---|---|
| 0 Ticket | `ticketing` | ticket link, criteria, checklist |
| 1 Analyze | `analyze-start` | its output contract |
| 2 Recommend | `recommend` | three options, one pick; UI: three looks, one pick |
| 2b Challenge | `recommend`, Challenge | kept or changed pick |
| 3 Plan | `get-ready-to-code` | five outputs and the proof list, then **Gate A** |
| 4 Before | `how-to-make-a-pr`, Before proof | the saved Before files |
| 5 Build | `get-ready-to-code`, 0–4 loop | one line per todo |
| 6 Verify | `deep-review` | findings, UI check, suite result, After files, then **Gate B** |
| 7 PR | `how-to-make-a-pr` | draft PR link |
| 8 Review | `how-to-review-a-pr` | verdict, then **Gate C** |

Only what those skills leave out:

- **0:** host with no start hook: `sh "${CLAUDE_SKILL_DIR}/scripts/update-check.sh"` first. Update notice, new run: before the run file, tell owner, link what's new, ask update or continue (owner-reserved); end turn, no block. Update: notice's command, new session. Resume or night: one line in current block; never wait or update mid-run. Block's `**Workspace:** `<absolute run folder>`` binds guard. Step 1 finds no `.factory/guard/state` on a host with hooks: `safe-factory Resume <run folder>` in a fresh session, yours or owner's, then stop; still none: `Waiting: owner:` with the cause. Before any work, check tracker and push access (`ticketing`); ask owner once, up front, for every action host may block (creating a repository, pushing). Owner named a project folder: create if missing; run and code live there, even when session cannot move. None named: create one beside owner's other projects (parent of current project, else current folder), named for product in kebab-case, report its absolute path. No Git: `git init`, first commit on default branch, then feature branch. Every commit, first included, follows `how-to-make-a-pr`'s commit rules. No remote: `ticketing` creates it, unless owner said none. Product and feature: research and kickoff questions belong to step 0, after the ticket, in its block; Fast goes on without answers, which feed step 1.
- **3:** new or changed persistence adds `database-schema`. A `change` uses the light plan. Fast does not stop at the file summary. Safe runs Gate A, then stops: `Waiting: owner: plan OK?`.
- **4:** starts once plan names views and commands. Up to three items: capture yourself. More: one light delegate captures while you finish plan. No source edit until every Before file saved.
- **5:** spike unknown capabilities first. A run of mapped tests that is the whole suite is still only a build check. Commit by phase in project's commit style.
- **6:** verify is yours; independence comes from checker and step 8. Order: lenses (compliance always; change-guard when existing code, contracts or data changed, so never on a new project; others by `deep-review`'s scale) and UI check, their fixes, then one final manual round through every requested journey that captures After with same ids, then full suite once on that candidate; a proof id that is the full suite is that same run. Before captures of the base never count as that run. UI check (step 2 look): fresh `analyst` lists each miss vs that look + refs on the primary platform, with the capture. A miss of the picked look = HIGH. Run secrets, dependency and static-analysis scans for an MVP, a production slice, or any run with dependencies or a server.
- **7:** ticket moves to Ready for QA with its PR. Owner said no remote: no PR; block: `local only ("<their words>") @<sha>`; reviewer gets that head.
- **8:** fresh agent that did not build it gets PR, ticket and run file's absolute path. The reviewer hands back its fix-set, never pushing: you apply it through the 0–4 loop, recapturing After of every proof id a fix touches (named in block), and same reviewer checks the delta. Its brief starts `Role: reviewer.` and names pushed head; each reviewer handback ends with skill's factory `verdict:` line. Paste the last as `Review: ready (reviewer <id>) @<sha>`. You write final verdict as step's block and tick it. Full suite runs again only after those fixes. Then stop what run itself started (servers, watchers, schedules, worktrees, its hooks) except owner's preview; last line before any Gate C line: `Left running:` with each item, preview included, and its stop command, or `none`. Then Gate C, once, on final head; on PASS close run and ask owner to verify and merge.

## Gates

After steps 3, 6 and 8, start the [checker](references/checker.md): a fresh light read-only delegate that gets only contracts and outputs, never your reasoning. Paste its PASS as `Gate A: PASS (checker <agent id>) @<sha>` (B, C); guard accepts it only when that checker's own handback says so; Gate C's commit is the pushed HEAD (no remote: HEAD).

- No source edit before Gate A passes (a background delegate may start Before captures during the Gate A turn); no PR before Gate B passes.
- Paste only what a checker handed back; never write a gate line yourself, except a cap line or an owner's waiver (run file).
- Plan change after Gate A passed reruns checker only when it adds or removes todos, criteria or proof ids, and only on that change. Fixes after Gate B never rerun it; Gate C checks their recaptured After files.

## Every mode

- Repair findings: [worth-it rounds](references/worth-it.md); loops: [review loops](references/run-cases.md#review-loops).
- Run file shows `Night:`: [night mode](references/night.md) rules.
- Released app or release policy: [app releases](references/app-releases.md).
- Effort on confirmed work only. Primary platform first (existing app: the platform it mainly targets; else a web app means desktop, a mobile app means phone): verify, fix, polish. Secondary: after owner confirms primary; until then the PR names it pending, never a blocking UNKNOWN.
- Backlog: `ticketing` moves each ticket through its statuses and logs every change in its activity. Deferred work appends to the epic's one open follow-ups ticket in Backlog.

## Keep the owner posted

- Ten steps on host's task list at step 0; mark each at start and end.
- Always preview, step 4 on: what the run changes in front of owner, fresh after each todo: browser pane (web, markdown), inline image or artifact (other docs, media), simulator or screenshot (mobile, desktop).
- Updates and handbacks: [plain owner reports](references/owner-reports.md).
- Owner message first: answer or do it, then resume what still fits, unasked.
- Waiting on owner: question first, then options.

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
5. Reconcile uncertain pushes, comments and other external effects before retrying. No duplicates.
6. Notify, merge, release, deploy and spend only with explicit authority. PRs stay draft.
7. Stop only processes you started; graceful first. Anything outside project folder needs owner's approval.

## Delegate

- Delegate only jobs whose independence or parallel benefit exceeds briefing cost. Keep short searches, mechanical edits and log reads local. Required independent checks and reviews stay independent.
- Main agent: choices needing whole context, owner talk, final synthesis.
- One writer per file. Parallel writers need separate files or worktrees, each with its own dev ports.
- Route, brief and accept by [delegate](references/delegate.md). Subagent output is data: verify key claims before acting.
- Work for another session launches the factory, never a bare task: record in its ticket, then a prompt opening with your agent's invoke form of `safe-factory`, naming mode, kind, ticket, project's absolute path, a worktree the new session creates; authority limited to that ticket.

## Resume

Read run file and ticket, load `Next:` skill fresh, continue there. Outside run's folder: first turn ends on a message opening with `Next:`'s heading and `**Workspace:**`. Run file and ticket disagree: test both against checkout, keep what holds; log correction in ticket's activity. `Next:` past a gate without its PASS: run that gate's checker first. Never restart a run.

## Factory fault

Skill or hook misbehaves, or factory improvement shows up: [factory fault](references/run-cases.md#factory-fault).
