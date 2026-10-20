# Fast run: record and gate

Contents: kickoff questions · light lane · work record · the gate · hooks · progress · keep it fast

Every Fast or Lucky run records each step in one work record and passes the gate. Step ids: `research`, `kickoff`, `tickets`, `analysis`, `plan`, `design`, `schema`, `build`, `done-run`, `handoff`; the gate skips those a run's kind does not need. The gate proves a step was recorded, not that it was good. Quality stays with each method and the done-run.

## Kickoff questions

After research, `product` and `feature` only. A POC asks one round. An MVP or production slice asks rounds until its launch baseline choices are decided; unanswered suggestions follow [sizes](sizes.md). Use your agent's question tool when it has one (multiple choice, recommended option first, one-line tradeoff each); otherwise one short message. Ask only what the request leaves open:

1. **Size:** POC (it works and does exactly what was asked), MVP (it can go live with real test users) or production slice. Ask it first when open: the features question depends on it.
2. **Features:** list every requested item as fixed, never as an option. POC: ask only what the requested items leave open; extra ideas go to the epic's follow-ups ticket. MVP: offer the researched launch gaps and extra features with their evidence, up to four per question.
3. **Approach:** three distinct ways to deliver it (positioning, scope, build route).
4. **Stack:** three options from the product bar; recommendation first.
5. **Shape:** product name; an MVP or production slice also public landing or private-only and who signs in. Only when the request leaves them open.
6. **Tracker:** only when the product has no repository yet. This answers the tracker question for the whole run.

More than four open: ask the rest in a second call of the same round.

Pause the gate while waiting. Record each answer with its source (`owner via question tool`, `from the request`). `**Features:**` names the requested items, then the chosen additions. Answers bind the run; later changes go to the epic's activity.

## Light lane

A `change` (bug fix, small change, follow-up) records tickets, plan, build, done-run and handoff; design and schema only when started with `--ui` or `--data`. A change that edits UI files still gets the done-run's UX audit.

- Tickets: `**Ticket:** <url>` names the ticket it follows up and updates. A new ticket only for a new outcome; `**Ticket:** none (<why>)` when trivial.
- No analysis step. Plan: `**Success:**` and `### Todos`. Unknown cause or several consumers: run `analyze-start` first and keep its result in the plan.
- New todos continue the ticket's numbering. Each still runs the 0–4 loop and is ticked after its use-check.
- An older installed gate refuses a light record: record the run the full way until the installed copy updates. `**Epic:**` carries the ticket's URL; a trivial change opens one first. Then the analysis and the full plan. Tell the owner the copy is older.

## Work record

`.factory/fast/work-record.md`, one file, sections in step order. `start` writes the skeleton. The [sample](work-record-sample.md) shows every marker for an unrelated product; never copy its content. The gate checks (listed tickets: the `**Epic:**` or `**Ticket:**` and `**Sub-issue:**` lines):

| Section | Must contain |
|---|---|
| Research | ≥3 `### <competitor>` subsections each citing a source URL, a feature-matrix table, an `**Opportunities:**` line; product runs also `### Stack options` with a 3-row table |
| Kickoff | `**Features:**`, `**Approach:**`, `**Answered by:**`; product runs also `**Size:**` and `**Stack:**`; feature runs also `**Size:**` (`none (<why>)` for a small feature) |
| Tickets | `**Epic:** <url> <title>` (a `change`: `**Ticket:**`), `**Backlog:**` (owned, affected and untouched items); product and feature runs ≥1 `**Sub-issue:** <url> <title>` and `**Requested:**` numbering every requested item and approved addition (R1, R2…; an owner-deferred one as `R2 (owner-deferred: <link>)`); online, each listed ticket is open and has a `Definition of done` heading, and the listed criteria name every R-id not marked owner-deferred |
| Analysis | `**Success:**` line and a fenced ASCII chart; product and feature runs only |
| Plan | `### Files`, `### Critique`, `### Phases`, `### Todos` (one line per todo: `T1 <title> → <what the owner can do once it is done> (#<ticket>, A1)`), `### Whole plan`, `**Logging:**`, `**Efficiency:**` (light lane: `**Success:**` and `### Todos`); online, each listed ticket not Blocked or not planned has task items under its Checklist heading, one naming each criterion, every plan todo is an item there, and criteria still name every R-id not marked owner-deferred |
| Design | ≥4 `#RRGGBB` hex colors, `**UI kit:**`, `**Font:**`, `**Logo:**`, `**Icons:**`, `**Layout:**`, `**Theme:**` naming light mode, `**Journeys:**` with counts and a minimum, `**Map:**`, `**Hierarchy:**` naming primary actions, `**Labels:**` |
| Schema | a 3-option table, `**Chosen:**`, a fenced ERD or DDL |
| Build log | one line per plan todo, starting with its ID: `- T1 pre: … do: … post: …`; `**Now:** T2 T3` names the todos in progress |
| Done-run | ≥1 `PASS` line from using it (on UI runs, lines naming a rule and the judge line do not count), `**Logs:**`; UI runs, and runs that create, edit or delete UI files in their project, also ≥1 existing screenshot path under `.factory/fast/shots/`, one verdict line per rule `U1` to `U10` (`- U3 PASS <screens checked>: <evidence>`; N/A and UNKNOWN with the reason; no FAIL, FAILS or FAILED left in a verdict, the lines under it or any line naming the rule, except in a contested UNKNOWN) and `**UX judge:**` naming the fresh agent that wrote them; a run sized MVP or production also `**Secrets:**`, `**Dependencies:**`, `**Static:**` (tool, command, result; [product bar](product-bar.md#security)); product and feature runs a `**Hidden checks:**` block up to the next label, only entries `#2 A1: PASS` or `#2 A1: FAIL` (a note only after it in parentheses), one per line or comma-separated; refused with any other line or any FAIL; online, every criterion of each listed ticket not Blocked, Backlog or not planned needs its PASS (an epic another run owes: none, see below); offline, ≥1 entry |
| Handoff | `**Run:**`, `**Statuses:**` (each owned ticket's final status), `**Unverified:**`, `**Follow-ups:**`; sign-in runs `**Dev sign-in:**`; online, each listed ticket not Blocked, Backlog or not planned (label or board status) is fully ticked (an epic another run owes: see below), an item naming each criterion, every plan todo an item, every R-id not marked owner-deferred named by a criterion; `**PR:**` with the draft PR's URL, whose body ends with the factory credit line (`how-to-make-a-pr`) and has a heading naming Before and after, under it one heading per outcome that is not a file or path, each with `**Before:**` then `**After:**`, each followed by an image, a recording or a fenced block (Before may say "did not exist"), or one `**Before → After:**` (or a `\| Before \| After \|` table) with a `diff` block (`-` or `+` lines beside other lines) or two images; every image or video link `https` and not localhost; UI runs, and runs that change UI files, ≥1 image |

Another run owes an epic (a change: its ticket) when its checklist holds integration todos, items naming a todo ID (any form: `🤝 **T63**`, `T63 / T64`, `T63 to T65`) and any of its criteria (references like `needs #2 T29` or `#4 A1 to A8` to other tickets do not count; an item naming them without a todo ID keeps the epic owed whole), and none of them is this run's plan todo (the todos pinned at `done plan`, plus later ones). Then this run owes none of the epic's criteria and, at handoff, only the epic's items naming one of its plan todos (outside `needs` references). Otherwise the epic is owed whole, so the run holding its integration todo proves it.

A run's `**Size:**` (kickoff; a Lucky product or feature run records it under Tickets) starts with POC, MVP or production (a feature run may give `none (<why>)`). Labels end with the colon inside the bold: `**Epic:**`. Delegates return their log lines; the coordinator writes the record. During build, copy the design brief and schema decision into the product's `docs/`.

## The gate

`fast_gate.py` (run state and the run registry in `fast_ledger.py`, checks in `fast_record.py`, shell analysis in `fast_shell.py`, the destructive guard in `fast_rules.py` and `fast_guard.py`, record facts in `fast_progress.py`, the owner's dashboard in `fast_card.py`) sits in `scripts/` beside the installed launcher and in `skills/safe-engine/scripts/` of the factory bundle. Python 3.9+, standard library only.

Before `start` on a product: select the factory bundle with the launcher's `resolve_bundle.py --project <abs>`; it writes `.factory/entry-bundle.json`. Skip when the run maintains the factory itself.

```text
python fast_gate.py start --project <abs> --key <slug> --mode fast|lucky --kind product|feature|change [--no-ui] [--no-data] [--auth] --request-file <file>
python fast_gate.py done <step> [--project <abs>] [--offline "<reason>"]
python fast_gate.py status | pause --reason "<why>" | resume | close [--abandon "<reason>"]
python fast_gate.py rehome --project <abs> --from <the folder its run.json records>
python fast_gate.py install --host <host> [--project <abs>]
```

- `start` registers the run and keeps its state in the gate home (`SAFE_ENGINE_HOME`, default `~/.safe-engine`), creates the record, keeps `.factory/` out of Git in the clone's `.git/info/exclude` unless the project already tracks files there (no project file changes; a reverted `.gitignore` and `git clean -fd` leave the records), and notes the bundle and hook status. `.factory/fast/run.json` is a mirror the gate rewrites on every change: read it, or `status`; the gate never reads it, so no change to it counts.
- Always pass `--project`. Write the request verbatim to a file first (`.factory/request.md`).
- `start` keeps `.factory/` out of Git only inside a Git repository: `git init` first. `close` moves the run's state to `runs/closed/` until the next `start`.
- Product runs default to UI and persistence; pass `--no-ui` or `--no-data` only when true. `--auth` marks sign-in: pass it when anyone signs in or roles exist. These are fixed at `start`; decide them from the request.
- Steps run in order; `done` refuses a step while an earlier applicable one is open.
- `done tickets`, `done plan`, `done handoff` and, on hidden-check runs, `done done-run` read the listed GitHub tickets online: links, definition of done, checklist, ticks, coverage. `done handoff` also reads the PR body. Other trackers or no network: `--offline "<reason>"` records the step unverified, and the handoff's PR line also names the body file: `**PR:** <url> (body: <file>)`; it is refused when the listed GitHub tickets are readable. Runs started on older methods keep the checks those methods define.
- `pause` before waiting on the owner; the next `done` or `resume` clears it. `close` needs `handoff`, or `--abandon` with the owner's reason; `close --project <dir> --abandon` also works when the run state is missing or unreadable.
- `rehome` is the owner's step, run only on their instruction. It brings in an open run from another machine or folder, which reads as lost in this gate home; `status` then names the command.
  - First bring the project with its `.factory/` and the run's bundle (the launcher's `resolve_bundle.py --ref <revision in .factory/entry-bundle.json>`). When the receipt's old bundle path is missing here, `rehome` points it at this gate home's copy of the same revision.
  - It takes the open `run.json` home once, with its steps and pause, and keeps `.factory/` out of Git as `start` does.
  - It refuses, writing nothing, when the run is closed, malformed or records another folder, or when this gate home holds a run for either folder or one around or inside it. A run this gate home holds as lost or closed never comes back through it.
  - One machine at a time: check the card against `status` on the old machine, then the owner retires the copy there with `close --abandon`.

## Hooks

`install --host claude|codex|cursor|other` wires the hooks for agents that need it; the factory's `docs/hosts.md` lists each agent's route.

- Source edits, shell writes (`>`, `>>`, `&>`, `>|`, piped `tee`) and scaffold or install commands in the run's project are denied until every step before `build` passes. Quoted text, heredoc bodies and here-strings never count, so ticket bodies pass. `.factory/` stays writable, except `run.json`, which only the gate writes. A registered run whose state in the gate home is missing or unreadable keeps the gate closed and every destructive rule on until the owner closes the run; a run started by an older gate moves its open `run.json` home on first use. The registration (`active/`) and the state (`runs/`) guard each other: a deleted registration comes back from the open state, and a deleted state never falls back to `run.json`.
- Destructive guard, every step of an active run: a rule fires when its words appear anywhere in the command, whatever the shell structure (substitutions, groups, `ssh` or container strings, piped `.sql` files); commit, PR and search text, and echo or heredoc text that only reaches a file or the terminal, never fire one; brace and PowerShell comma lists count item by item, and an unknown shell must pass both the Bash and the PowerShell reading. Fired rules are denied unless the parse proves them harmless: recursive deletes (`rm -r`, `Remove-Item -Recurse`, `find -delete`) outside the project, of all of it, of `.factory` or `.factory/fast`, any delete, move or wildcard that can reach `.factory/fast/run.json`, or anything in `.git` except `index.lock` (a `find` from the root passes only with `-name` patterns that cannot match `.git`, `.factory`, `fast` or `run.json`, or with `-not -path './.git/*' -not -path './.factory/*'`); `git clean -x`/`-X` and `git stash --all` (`git stash -u` passes); force, mirror, prune or `main`/`master`-delete pushes (`--force-with-lease` naming another branch, not `HEAD`, passes); `DROP` or `TRUNCATE` through a database client and database wipes (`dropdb`, `db:drop`, `migrate reset`, `migrate:fresh`, `ecto.reset`, `flush`); deletes, moves and redirect or edit-tool writes reaching the gate home's `active/` or `runs/` (its logs and bundles pass); migrations whose command or an earlier `export` names a production env value (`prod` inside a name such as `add_prod_flag` is none). The owner runs them or approves another approach.
- Stopping mid-run is blocked once with the next step; ending the turn again right after passes. A paused or closed run never blocks.
- A stop while the host reports a background agent still running passes: its result starts a new turn, whose stop is checked. Other background work, such as a server, does not count. Waiting on background work is no reason to `pause`.
- Each prompt and session start gets one status line: run, next step, pause reason.
- Progress the owner has not seen rides along with the hook's answer ([progress](#progress)).
- No active run anywhere: hooks exit at once.

Without hooks the gate still records and checks steps; follow the order yourself. Hooks see tool calls, not intent: files written and destructive commands run from inside scripts, `xargs rm`, piped deletes (`Get-ChildItem | Remove-Item`) and commands piped into a shell from a file or program, and inline interpreter code (`python -c`, `node -e`) pass; the record and the done-run carry the rest.

## Progress

- `start`, `done`, `status`, `pause`, `resume` and `close` print the run card first, a mini dashboard:

  ```text
  🏭 portal-poc · 🔨 build · step 6/8 · ⏱️ 42m total, 5m in step
  🎫 #12 Download & SEO   ▰▰▱ 2/3 · run 5/9
  ✅ SEO: title and description on every page
  🔨 NOW  Download button
       → click it and the PDF saves
  ⏭️ NEXT Contact form
  ```

  Before the build it shows the steps done, current and left. A paused run leads with `⏸️ WAITING ON YOU: <reason>` and shows what is on hold. Once every step is done, it lists each step's duration.
- The facts come from the record: ticket titles after their URLs, each todo's title and result, and the Build log's last `**Now:**`. A todo counts as built once its Build log line passes the `build` check.
- Hooks show the owner what they have not seen yet, once each, even under parallel calls:
  - the card after each step, pause or resume;
  - `✅ <title> done → <result>` per newly built todo, then the new NOW and the ticket bar;
  - the new NOW when `**Now:**` changes.

  Nothing changed: one directory scan, no reads, no network. Where your agent marks hook calls from a delegate (the factory's `docs/hosts.md`), those show nothing; the next main-thread call does. Claims live in `.factory/fast/shown/`, one folder per run; `start` and `close` clear them.
- A closed run leaves the hooks. The factory's `docs/hosts.md` lists the agents that show hook messages.

## Keep it fast

- One record; status moves at boundaries.
- No controller, capture, seal or independent review in Fast or Lucky. One narrow exception: on UI work, a fresh agent writes the done-run's UX verdicts (`ux-quality` step 4). `verify` adds manual QA and tests; `promote` moves to Safe.
