# Fast and Lucky runs

Seif, 7 October 2026: Fast must be fast, never thin. Tickets, quick research, owner questions, the full analyze/plan/0–4 method and a production-grade result stay. Speed comes from parallel agents and no controller ceremony, not from skipped steps. [Speed modes](speed-modes.md) owns what each mode keeps; this file owns how a Fast or Lucky run executes.

Every run records its steps in one work record and passes [the gate](#the-gate). Hooks hold the run to it.

Read at start: [speed modes](speed-modes.md), this file and the [product bar](product-bar.md). Read each step's linked method fully when that step starts, not before.

## Pick the kind

| Kind | When | Asks Seif |
|---|---|---|
| `product` | New app, game, site, tool, service or library | ✅ after quick research |
| `feature` | Big feature with product choices in an existing product | ✅ after quick research |
| `change` | Bug fix, small change, factory maintenance | ❌ goes straight through |

Unsure between `feature` and `change`? Product choices (what users get, how it looks, what it costs) make it a `feature`.

## Steps

Fast runs every applicable step. Lucky runs `tickets`, a short `analysis` and `plan`, `build` and `handoff`; it asks nothing, researches nothing and takes the [product bar](product-bar.md) defaults.

| # | Step | Kinds | Do | Record section |
|---|---|---|---|---|
| 0 | bundle | all | Select the factory bundle with the Safe Engine entry's resolver (`resolve_bundle.py --project`); it writes `.factory/entry-bundle.json`. Skip only when the run maintains the factory itself. | none |
| 1 | start | all | `fast_gate.py start` creates `.factory/fast/run.json` and the work record skeleton, keeps `.factory/` out of Git, notes the bundle receipt and hook status, and registers the run for hooks. | none |
| 2 | research | product, feature | Quick [research](../../research-market/SKILL.md#fast-kickoff-research) as parallel agents, one per competitor plus one for stacks: 3 top competitors, feature matrix, opportunities, 3 stack options (product runs). Show Seif a short summary. | `## Research` |
| 3 | kickoff | product, feature | One question round (below). `fast_gate.py pause` while waiting in chat. Record answers verbatim. | `## Kickoff` |
| 4 | tickets | all | [Fast/Lucky tickets](../../ticketing/SKILL.md#fast-and-lucky-tickets): epic + 3–6 outcome sub-issues (`change`: one ticket) in the product's repository tracker. | `## Tickets` |
| 5 | analysis | all | [Analyze Start](../../analyze-start/SKILL.md) in full: purpose, consumers, ASCII charts, success, unknowns. | `## Analysis` |
| 6 | plan | all | [Get Ready](../../get-ready-to-code/SKILL.md) five outputs, todos `T1..Tn`, logging map and efficiency budget. No file-summary stop. | `## Plan` |
| 7 | design | Fast, UI | Design brief per the [product bar](product-bar.md#visual-system) and [UX Quality](../../ux-quality/SKILL.md). | `## Design` |
| 8 | schema | Fast, persistence | Short [Database Schema](../../database-schema/SKILL.md): access map, 3 designs, choice, ERD/DDL, indexes. | `## Schema` |
| 9 | build | all | Every todo through the 0–4 loop; one log line per todo: `T3 pre: … do: … post: …`. Delegates return their lines; the coordinator writes the record. Copy the design brief and schema decision into the product's `docs/`. Gate opens source edits here. | `## Build log` |
| 10 | done-run | Fast | Start the app once; use the main journey and its most likely failure through real controls; copy UI screenshots (the browser tool's saved image, or a fresh capture) into `.factory/fast/shots/` and cite those relative paths; read the logs; fix blockers. | `## Done-run` |
| 11 | handoff | all | How to run, dev sign-in, what is verified and unverified, follow-up tickets, ticket updates. Then `close`. | `## Handoff` |

Steps run in order; the gate refuses a step while an earlier applicable one is open. Design and schema follow the plan but precede source edits.

## Kickoff questions

One round, after research, for `product` and `feature`. Use the host's question tool (Claude Code: AskUserQuestion, at most 4 questions with 4 options each; otherwise one short chat message). Recommended option first, each with a one-line tradeoff. Ask only what the request and earlier answers leave open:

1. **Features:** multi-select of up to four feature groups from the matrix; must-haves stated in the question, not asked.
2. **Size:** POC (one core journey, seeded data), MVP (first sellable slice) or production slice.
3. **Approach:** three distinct ways to deliver it, from the research (positioning, scope, build route).
4. **Stack:** three options from the product bar's [stack rules](product-bar.md#stack); recommendation first.
5. **Tracker:** only when the product has no repository yet: where its tickets live (recommend a new private GitHub repository).

More than four open: ask the rest in a second call of the same round. Record each answer with source (`Seif via AskUserQuestion, <date>`; `from the request` for answers the request already gave). Answers bind the run; later changes go to the epic's activity table. Owner-reserved choices outside these still follow [decision ownership](../../../../docs/current-decisions.md#decision-ownership).

## Work record

`.factory/fast/work-record.md`, one file, sections in step order. `start` writes the skeleton; the [filled sample](../../../../examples/fast-run/work-record.sample.md) shows every marker for a different product. Never copy its content; research and decide fresh. The gate checks these markers:

| Section | Must contain |
|---|---|
| Research | ≥3 `### <competitor>` subsections each citing a source URL, a feature-matrix table, an `**Opportunities:**` line; product runs also `### Stack options` with a 3-row table |
| Kickoff | `**Features:**`, `**Approach:**`, `**Answered by:**`; product runs also `**Size:**` and `**Stack:**` |
| Tickets | `**Epic:** <url>`; product and feature runs ≥1 `**Sub-issue:** <url>` |
| Analysis | `**Success:**` line and a fenced ASCII chart |
| Plan | `### Files`, `### Critique`, `### Phases`, `### Todos` (with `T1`…), `### Whole plan`, `**Logging:**`, `**Efficiency:**` |
| Design | ≥4 hex colors, `**UI kit:**`, `**Font:**`, `**Logo:**`, `**Icons:**`, `**Layout:**`, `**Theme:**` naming light mode |
| Schema | a 3-option table, `**Chosen:**`, a fenced ERD or DDL |
| Build log | every plan todo ID with `pre:`, `do:` and `post:` |
| Done-run | ≥1 `PASS` line, `**Logs:**`; UI runs ≥1 existing screenshot path |
| Handoff | `**Run:**`, `**Unverified:**`, `**Follow-ups:**`; sign-in runs `**Dev sign-in:**` |

Markers prove the step was recorded, not that it was good. Method quality stays with each method and the done-run.

## The gate

`fast_gate.py` (step checks in `fast_record.py`, shell command analysis in `fast_shell.py`) lives in `skills/safe-engine/scripts/` of the bundle and beside the installed Safe Engine entry. Python 3.9+, stdlib only.

```text
python fast_gate.py start --project <abs> --key <slug> --mode fast|lucky --kind product|feature|change [--no-ui] [--no-data] [--auth] --request-file <file>
python fast_gate.py done <step> [--project <abs>] [--offline "<reason>"]
python fast_gate.py status | pause --reason "<why>" | resume | close [--abandon "<reason>"]
```

- `--project` defaults to the nearest folder holding `.factory/fast/run.json`.
- Product runs default to UI and persistence; pass `--no-ui`/`--no-data` only when true. `--auth` marks sign-in.
- `done tickets` checks GitHub URLs and sub-issue links with `gh`; `--offline` records an unverified reason.
- `pause` before waiting on Seif; the next `done` or `resume` clears it. `close` needs `handoff`, or `--abandon` with Seif's reason.

## Hooks

The Claude Code plugin ([install](../../../../docs/install-safe-engine.md#claude-code)) and optional Codex hooks call the gate:

- Source edits (Write/Edit/apply_patch), shell writes (`>`, `>>`, `&>`, `>|`, piped `tee`) and scaffold or install commands in the run's project are denied until every step before `build` passes. Quoted text, heredoc bodies and here-strings never count, so ticket bodies pass. `.factory/` stays writable, except `run.json`, which only the gate writes.
- Stopping mid-run is blocked once with the next step, unless the run is paused or closed.
- Each prompt and session start gets one line: run, next step, pause reason.
- No active run anywhere: the hook exits before Python starts.

`start` reports whether hooks are installed. Without them the gate still records and checks steps; nothing blocks, so follow the order yourself. Hooks see tool calls, not intent: files written from inside scripts (Python, Node) and other projects pass; the record and the done-run carry the rest.

## Keep it fast

- Parallel agents per [agent routing](agent-routing.md): research strands together, independent todos in separate files together, one writer per file.
- No controller, capture, seal or Codex review. `verify` adds manual QA of failure journeys and tests; `promote` moves to Safe.
- One question round, one record, ticket updates only at boundaries.
