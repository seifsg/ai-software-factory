# Fast run: record and gate

Contents: kickoff questions · light lane · work record · the gate · hooks · keep it fast

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

A `change` (bug fix, small change, follow-up) records tickets, plan, build, done-run and handoff; design and schema only when started with `--ui` or `--data`.

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
| Tickets | `**Epic:** <url>` (a `change`: `**Ticket:**`), `**Backlog:**` (owned, affected and untouched items); product and feature runs ≥1 `**Sub-issue:** <url>` and `**Requested:**` numbering every requested item and approved addition (R1, R2…; an owner-deferred one as `R2 (owner-deferred: <link>)`); online, each listed ticket is open and has a `Definition of done` heading, and the listed criteria name every R-id not marked owner-deferred |
| Analysis | `**Success:**` line and a fenced ASCII chart; product and feature runs only |
| Plan | `### Files`, `### Critique`, `### Phases`, `### Todos` (with `T1`…), `### Whole plan`, `**Logging:**`, `**Efficiency:**` (light lane: `**Success:**` and `### Todos`); online, each listed ticket not Blocked or not planned has task items under its Checklist heading, one naming each criterion, every plan todo is an item there, and criteria still name every R-id not marked owner-deferred |
| Design | ≥4 `#RRGGBB` hex colors, `**UI kit:**`, `**Font:**`, `**Logo:**`, `**Icons:**`, `**Layout:**`, `**Theme:**` naming light mode, `**Journeys:**` with counts and a minimum |
| Schema | a 3-option table, `**Chosen:**`, a fenced ERD or DDL |
| Build log | one line per plan todo, starting with its ID: `- T1 pre: … do: … post: …` |
| Done-run | ≥1 `PASS` line, `**Logs:**`; UI runs ≥1 existing screenshot path under `.factory/fast/shots/` |
| Handoff | `**Run:**`, `**Statuses:**` (each owned ticket's final status), `**Unverified:**`, `**Follow-ups:**`; sign-in runs `**Dev sign-in:**`; online, each listed ticket not Blocked, Backlog or not planned (label or board status) is fully ticked, an item naming each criterion, every plan todo an item, every R-id not marked owner-deferred named by a criterion |

Labels end with the colon inside the bold: `**Epic:**`. Delegates return their log lines; the coordinator writes the record. During build, copy the design brief and schema decision into the product's `docs/`.

## The gate

`fast_gate.py` (checks in `fast_record.py`, shell analysis in `fast_shell.py`) sits in `scripts/` beside the installed launcher and in `skills/safe-engine/scripts/` of the factory bundle. Python 3.9+, standard library only.

Before `start` on a product: select the factory bundle with the launcher's `resolve_bundle.py --project <abs>`; it writes `.factory/entry-bundle.json`. Skip when the run maintains the factory itself.

```text
python fast_gate.py start --project <abs> --key <slug> --mode fast|lucky --kind product|feature|change [--no-ui] [--no-data] [--auth] --request-file <file>
python fast_gate.py done <step> [--project <abs>] [--offline "<reason>"]
python fast_gate.py status | pause --reason "<why>" | resume | close [--abandon "<reason>"]
python fast_gate.py install --host <host> [--project <abs>]
```

- `start` creates `.factory/fast/run.json` and the record, keeps `.factory/` out of Git, notes the bundle and hook status, and registers the run for hooks.
- Always pass `--project`. Write the request verbatim to a file first (`.factory/request.md`).
- `start` keeps `.factory/` out of Git only inside a Git repository: `git init` first.
- Product runs default to UI and persistence; pass `--no-ui` or `--no-data` only when true. `--auth` marks sign-in: pass it when anyone signs in or roles exist. These are fixed at `start`; decide them from the request.
- Steps run in order; `done` refuses a step while an earlier applicable one is open.
- `done tickets`, `done plan` and `done handoff` read the listed GitHub tickets online: links, definition of done, checklist, ticks, coverage. Other trackers or no network: `--offline "<reason>"` records the step unverified; it is refused when the listed GitHub tickets are readable. Runs started on older methods keep the checks those methods define.
- `pause` before waiting on the owner; the next `done` or `resume` clears it. `close` needs `handoff`, or `--abandon` with the owner's reason.

## Hooks

`install --host claude|codex|cursor|other` wires the hooks for agents that need it; the factory's `docs/hosts.md` lists each agent's route.

- Source edits, shell writes (`>`, `>>`, `&>`, `>|`, piped `tee`) and scaffold or install commands in the run's project are denied until every step before `build` passes. Quoted text, heredoc bodies and here-strings never count, so ticket bodies pass. `.factory/` stays writable, except `run.json`, which only the gate writes.
- Stopping mid-run is blocked once with the next step, unless the run is paused or closed.
- Each prompt and session start gets one status line: run, next step, pause reason.
- No active run anywhere: hooks exit at once.

Without hooks the gate still records and checks steps; follow the order yourself. Hooks see tool calls, not intent: files written from inside scripts pass; the record and the done-run carry the rest.

## Keep it fast

- One record; status moves at boundaries.
- No controller, capture, seal or independent review in Fast or Lucky. `verify` adds manual QA and tests; `promote` moves to Safe.
