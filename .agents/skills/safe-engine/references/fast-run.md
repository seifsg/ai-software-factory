# Fast run: record and gate

Every Fast or Lucky run records each step in one work record and passes the gate. Step ids: `research`, `kickoff`, `tickets`, `analysis`, `plan`, `design`, `schema`, `build`, `done-run`, `handoff`; the gate skips those a run's kind does not need. The gate proves a step was recorded, not that it was good; quality stays with each method and the done-run.

## Kickoff questions

After research, `product` and `feature` only. A POC asks one round; an MVP or production slice asks rounds until its launch baseline choices are decided; unanswered suggestions follow [sizes](sizes.md). Use your agent's question tool when it has one (multiple choice, recommended option first, one-line tradeoff each), else one short message. Ask only what the request leaves open:

1. **Size:** POC (it works and does exactly what was asked), MVP (it can go live with real test users) or production slice. Ask it first; features depend on it.
2. **Features:** every requested item is fixed, never an option. POC: ask only what the requested items leave open; extra ideas go to the epic's follow-ups ticket. MVP: offer the researched launch gaps and extra features with their evidence, up to four per question.
3. **Approach:** three distinct ways to deliver it (positioning, scope, build route).
4. **Stack:** three options from the product bar, recommendation first.
5. **Shape:** product name; an MVP or production slice also public landing or private-only, and who signs in.
6. **Tracker:** only when the product has no repository yet; it answers the tracker question for the whole run.

More than four open: ask the rest in a second call of the same round. Pause the gate while waiting. Record each answer with its source (`owner via question tool`, `from the request`). `**Features:**` names the requested items, then the chosen additions. Answers bind the run; later changes go to the epic's activity.

## Light lane

A `change` (bug fix, small change, follow-up) records tickets, plan, build, done-run and handoff; design and schema only when started with `--ui` or `--data`.

- Tickets: `**Ticket:** <url>` names the ticket it follows up and updates. A new ticket only for a new outcome; `**Ticket:** none (<why>)` when trivial.
- No analysis step. Plan: `**Success:**` and `### Todos`. Unknown cause or several consumers: run `analyze-start` first and keep its result in the plan.
- New todos continue the ticket's numbering; each still runs the 0–4 loop and is ticked after its use-check.
- An older installed gate refuses a light record: [gate details](gate-details.md#older-gate).

## Work record

`.factory/fast/work-record.md`, sections in step order; `start` writes the skeleton. The rows below and the skeleton's hints name every marker; a `change` writes the markers its rows name, with the light-lane forms. A `done` refusal its message does not explain: the [sample](work-record-sample.md) shows each section complete for an unrelated product; never copy its content. Labels end with the colon inside the bold: `**Epic:**`. The gate checks (listed tickets: the `**Epic:**` or `**Ticket:**` and `**Sub-issue:**` lines):

| Section | Must contain |
|---|---|
| Research | ≥3 `### <competitor>` subsections each citing a source URL, a feature-matrix table, `**Opportunities:**`; product runs also `### Stack options` with a 3-row table |
| Kickoff | `**Features:**`, `**Approach:**`, `**Answered by:**`; product and feature runs `**Size:**` starting with POC, MVP or production (a small feature: `none (<why>)`; a Lucky run records it under Tickets); product runs `**Stack:**` |
| Tickets | `**Epic:** <url> <title>` (a `change`: `**Ticket:**`), `**Backlog:**` (owned, affected and untouched items); product and feature runs ≥1 `**Sub-issue:** <url> <title>` and `**Requested:**` numbering every requested item and approved addition (R1, R2…; an owner-deferred one as `R2 (owner-deferred: <link>)`); online, each listed ticket is open with a `Definition of done` heading, and the listed criteria name every R-id not marked owner-deferred |
| Analysis | `**Success:**` and a fenced ASCII chart; product and feature runs only |
| Plan | `### Files`, `### Critique`, `### Phases`, `### Todos` (one line per todo: `T1 <title> → <what the owner can do once it is done> (#<ticket>, A1)`), `### Whole plan`, `**Logging:**`, `**Efficiency:**` (light lane: `**Success:**` and `### Todos`); current methods also `**Ports:**` (no port another open run's plan holds), `### Interface` (not in the light lane) and, on UI runs, `**UX rules:**` naming U1 and U10 ([briefs](#briefs)); online, each listed ticket not Blocked or not planned has task items under its Checklist heading, one naming each criterion; every plan todo is an item there; criteria still name every R-id not marked owner-deferred |
| Design | ≥4 `#RRGGBB` hex colors, `**UI kit:**`, `**Font:**`, `**Logo:**`, `**Icons:**`, `**Layout:**`, `**Theme:**` naming light mode, `**Journeys:**` with counts and a minimum (`<journey>: 2 actions, 1 load, min 2`), `**Map:**`, `**Hierarchy:**` naming primary actions, `**Labels:**` |
| Schema | a 3-option table, `**Chosen:**`, a fenced ERD or DDL |
| Build log | one line per plan todo, starting with its ID: `- T1 pre: … do: … post: …`; `**Now:** T2 T3` names the todos in progress; `**Try:** T1 cmd\|url\|file <target>` lines come only from `try`, never by hand |
| Done-run | ≥1 `PASS` line from using it (on UI runs, lines naming a rule and the judge line do not count), `**Logs:**`; UI runs and runs that create, edit or delete UI files in their project also ≥1 existing screenshot path under `.factory/fast/shots/`, one verdict line per rule `U1` to `U10` (`- U3 PASS <screens checked>: <evidence>`; N/A and UNKNOWN with the reason; no FAIL, FAILS or FAILED left in a verdict, the lines under it or any line naming the rule, except in a contested UNKNOWN) and `**UX judge:**` naming the fresh agent that wrote them; a run sized MVP or production also `**Secrets:**`, `**Dependencies:**`, `**Static:**` (tool, command, result; [product bar](product-bar.md#security)); product and feature runs a `**Hidden checks:**` block up to the next label, only entries `#2 A1: PASS`, on current methods also `#2 A1: DEFERRED (owner: <why>)` or `(hardware: <why>)` (a note only after it in parentheses), one per line or comma-separated; any other line or a FAIL is refused; online, every criterion of each listed ticket not Blocked, Backlog or not planned needs its PASS or DEFERRED (an epic another run owes: none); offline, ≥1 entry |
| Handoff | `**Run:**`, `**Statuses:**` (each owned ticket's final status), `**Unverified:**`, `**Follow-ups:**`; current methods also `**Deferred:**` (`none`, or every deferred item, naming each DEFERRED hidden check), and an unticked checklist item ending `DEFERRED (owner|hardware: <why>)` is not open; sign-in runs `**Dev sign-in:**`; online, each listed ticket not Blocked, Backlog or not planned (label or board status) is fully ticked (an epic another run owes: only the items this run's todos lead), with an item naming each criterion, every plan todo an item and every R-id not marked owner-deferred named by a criterion; `**PR:**` with the draft PR's URL; its body (`how-to-make-a-pr`) ends with the factory credit line and has a heading naming Before and after, under it one heading per outcome that is not a file or path, each with `**Before:**` then `**After:**` (each followed by an image, a recording or a fenced block; Before may say "did not exist") or one `**Before → After:**` or `\| Before \| After \|` table with a `diff` block (`-` or `+` lines beside other lines) or two images; image and video links `https`, not localhost; on current methods each outcome declares Visual and Journey (yes, or no with a reason): a visual needs distinct before/after screenshots, a journey a Video link, unless an explicitly scoped owner media waiver covers it; UI runs need a visual outcome. The gate checks declarations and link structure, not full coverage, playable media or waiver authority |

An epic's checklist (a change: its ticket's) holds integration todos (`T<n>`-led items naming its criteria), each another run's: who owes it, [gate details](gate-details.md#owed-epic).

Delegates return their log lines; the coordinator writes the record. During build, copy the design brief and schema decision into the product's `docs/`.

## Briefs

Agents work from recorded facts, never guesses; the plan fixes them once:

- **Interface** (`### Interface`): the public names as written: exports, record shapes, UI labels and test ids, routes, commands and flags, and the committed files holding them. `none (<why>)` only when nothing is public. A light-lane plan writes it when it delegates.
- **Ports** (`**Ports:**`): this checkout's dev port per server the run starts (app, API, hub, a spare). The main checkout (lane 0) keeps the project's defaults; lane n, an extra worktree, takes its own fixed block for its whole life: the project's lane rule, else the defaults plus 100 × n. Add two spare ports for `shots`. Never start, reuse or stop another lane's stack. `done plan` refuses a port another open run's plan holds. `none (<why>)` when the run serves nothing.
- Own stacks with `fast_gate.py lane start` / `lane stop`; brief generation and resources. Verify cache writes; configure unsupported tools. Host limits: the factory's `docs/hosts.md`.
- **UX rules** (UI runs, `**UX rules:**`): U1 to U10 (`ux-quality` step 3) plus the project's own UX rule files by path.

Each brief (checker, builder, UX judge, reviewer) also carries the Interface and Ports verbatim and, for UI work, the UX rules line. A checker binds its checks to those names and reads the committed interface files they name, never the implementation. A name a brief lacks: read the named interface files; still missing, the agent returns `blocked: <name>` instead of inventing one, and the coordinator adds it to the Interface (committed code wins) and briefs again.

**Deferred (owner/hardware):** an item only the owner's hands or hardware this machine lacks can finish (another OS, a physical device, an owner sign-off or account) ends `DEFERRED (hardware: <what is needed>)` or `DEFERRED (owner: <what is needed>)` on its unticked checklist item and its hidden-check entry, and is listed once on the handoff's `**Deferred:**` line. Everything else gets done first. Never defer what the run can do, a FAIL, or access not yet sought. Its criterion still gets the checker's written manual check, for the owner to run. A run whose only open items are deferred closes as done; its tickets go to Ready for QA naming them.

## The gate

`fast_gate.py` (debugging the gate: [modules](gate-details.md#modules)) sits in `scripts/` beside the installed launcher and in `skills/safe-engine/scripts/` of the factory bundle. Python 3.9+, standard library only.

Before `start` on a product, select the factory bundle with the launcher's `resolve_bundle.py --project <abs>` (it writes `.factory/entry-bundle.json`); skip it when the run maintains the factory itself.
Git-backed starts fetch their upstream first, keeping dirty work; the start commit anchors UI proof.

```text
python fast_gate.py start --project <abs> --key <slug> --mode fast|lucky --kind product|feature|change [--[no-]ui] [--[no-]data] [--auth] --request-file <file>
python fast_gate.py done <step> [--project <abs>] [--offline "<reason>"]
python fast_gate.py status | scratch | pr-proof-method | pause --reason "<why>" | resume | close [--abandon "<reason>"]
python fast_gate.py try T3 --cmd "<command>" | --url <http(s) link> | --file <path in the project> [--project <abs>]
python fast_gate.py view --project <abs> [--port 8765] [--snapshot <file>]
python fast_gate.py view --all-projects [--port 8765] [--snapshot <file>]
python fast_gate.py shots --base <ref> --serve "<dev command, {port} for its port>" --path <view> [--path <view>] [--setup "<command>"] [--ports <before>,<after>] [--size 1280x800] [--browser <exe>] [--project <abs>]
```

- Always pass `--project`. Write the request verbatim to a file first (`.factory/request.md`).
- `start` keeps the run's state in the gate home (`SAFE_ENGINE_HOME`, default `~/.safe-engine`), creates the record and keeps `.factory/` out of Git unless the project already tracks files there: in a Git repository only, so `git init` first. Run state missing or unreadable here: [run state](gate-details.md#run-state); a run from another machine or folder: [rehome](gate-details.md#rehome).
- `.factory/fast/run.json` is a read-only mirror (or use `status`); the gate never reads it, so no change to it counts.
- Product runs default to UI and persistence; pass `--no-ui` or `--no-data` only when true, `--auth` when anyone signs in or roles exist. Fixed at `start`: decide them from the request.
- `start` creates scratch; `scratch` prints it. Put throwaway data there; set each tool's `TMPDIR`, `TEMP` and `TMP` to it. Profiles and caches use short lane resources. Stop owned processes before [cleanup](gate-details.md#scratch-deletes).
- Steps run in order; `done` refuses a step while an earlier applicable one is open.
- `done tickets`, `done plan`, `done handoff` and, on hidden-check runs, `done done-run` read the listed GitHub tickets online; `done handoff` also reads the PR body. Other trackers or no network: `--offline "<reason>"` records the step unverified, and the handoff's PR line names the body file, `**PR:** <url> (body: <file>)`; refused when the listed GitHub tickets are readable.
- Runs started on older methods keep their recorded checks unless the owner explicitly adopts the PR-proof policy.
- `pause` before waiting on the owner; the next `done` or `resume` clears it. `close` needs `handoff`, or `--abandon` with the owner's reason; `close --project <dir> --abandon` also works when the run state is missing or unreadable.
- [`shots`](gate-details.md#shots): the PR's Before and After screenshots of web views in one go.
- Only on the owner's explicit instruction: [`rehome`](gate-details.md#rehome) (move a run between machines or folders), [`adopt-pr-proof`](gate-details.md#adopt-pr-proof), [`cleanup-temp`](gate-details.md#cleanup-temp) (obsolete temp fixtures), [`recover-baseline`](gate-details.md#recover-baseline). Hook wiring: [`install`](gate-details.md#install).

## Hooks

- Until every step before `build` passes, source edits, shell writes (`>`, `>>`, `&>`, `>|`, piped `tee`) and scaffold or install commands in the run's project are denied. Quoted text, heredoc bodies and here-strings never count, so ticket bodies pass. `.factory/` stays writable, except `run.json`.
- Destructive commands are denied in every step of an active run; the owner runs them or approves another approach: recursive deletes (`rm -r`, `Remove-Item -Recurse`, `find -delete`) outside the project (the run's scratch folder excepted), of the whole project, of `.factory` or `.factory/fast`; any delete, move or wildcard that can reach `.factory/fast/run.json`, or anything in `.git` except `index.lock`; `git clean -x`/`-X`, `git stash --all`; force, mirror, prune or `main`/`master`-delete pushes; `DROP` or `TRUNCATE` through a database client, and database wipes; deletes, moves and writes reaching the gate home's `active/` or `runs/`; migrations naming a production env value. A command you need matches one, or a deny came: [what passes, what hooks miss](gate-details.md#destructive-guard).
- Stop reminds once for unfinished work; repeat, paused and closed stops pass. For finite helpers, `wait --add` records a supported completion wakeup: follow [quiet waits](waiting.md). Every owned run needs its own valid wait. Servers never qualify; do not `pause` for helpers.
- Each prompt and session start gets one status line: run, next step, pause reason.
- No active run anywhere: hooks exit at once. Without hooks the gate still records and checks steps; follow the order yourself.

## Progress

- `start`, `done`, `status`, `pause`, `resume` and `close` print the run card first, a mini dashboard. Hooks show the owner each unseen card, built todo and new NOW once (debugging it: [progress internals](gate-details.md#progress-internals)); a delegate's hook calls show nothing, the next main-thread call does.
- Never repeat a gate message your agent already showed. Where it shows no hook messages (the factory's `docs/hosts.md`), relay the card from the command output.

## Live view

- `view --project <abs>` serves that project's runs, open or closed today, at `http://127.0.0.1:8765/`; no `--project`: the current repository, never all. Start it in the background; give the owner the link once per run. Only the gate writes `view/state.json`. Debugging the view: [view internals](gate-details.md#live-view-internals).
- When a ticked todo leaves something the owner can use, record it with `try`; it refuses an unknown todo or any other target and names the form.
- The preview's goal, next test and child sessions: [preview reporting](preview-reporting.md), at dispatch, task change and finish.

## Keep it fast

- One record; status moves at boundaries.
- No controller capture/seal commands or routine independent code review in Fast or Lucky. PR screenshot and video capture still applies in full (`how-to-make-a-pr`). Exception: on UI work, a fresh agent writes the done-run's UX verdicts (`ux-quality` step 4). `verify` adds manual QA and tests; `promote` moves to Safe.
