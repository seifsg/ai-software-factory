# Controller

Contents: setup, task and profile, phases, ticket commands, repair, review, evidence, status and resume.

Records stages, checks and reviews; never builds, pushes, merges, deploys, provisions sessions/worktrees or runs as a daemon.

## Setup

Run from the factory bundle root. Every command takes:

```text
python -m safe_engine --project <absolute-project-root> --ticket <key> <command>
```

`discover` and `preflight` need no `--ticket`. Needs Python 3.9+, Git, the project's check tools, one installed agent CLI for review (or the review packet).

1. `discover`: proposes a profile from Git and package scripts. Executes nothing.
2. Ignore `.factory/` in the project's Git rules; run state lives in `.factory/runs/<key>/`. Start from a clean committed baseline in an isolated checkout.
3. `preflight --profile <profile.json>`: lists tools and installed reviewer agents. Runs no tests, launches no app. Record missing capabilities before dependent work.

## Task and profile

Task file:

```json
{"request": "<original request, verbatim>",
 "acceptance": [{"id": "A1", "text": "<observable outcome>", "mode": "manual", "checks": []}]}
```

- `mode`: `manual`, `automated` or `mixed`. Manual takes `checks: []`. The others start empty and need real check ids before `seal`.
- Ticketed: `request` and every criterion id and text equal the confirmed ticket.

Draft profile (checks and protected paths stay empty until `seal`):

```json
{"version": 2, "interface": "web", "exposure": "local", "checks": [], "protected_paths": [],
 "test_paths": ["tests"], "environment_inputs": [], "input_files": [], "review_scopes": []}
```

- `interface`: `web`, `cli`, `library`, `desktop`, `mobile`, `game`, `service`, by what ships. `exposure`: `local`, `public` or `production`, the real one.
- `review_scopes`: `ui`, `assets`, `persistence`, `research`, `seo`, `security`, `integrations`, `release`. Core methods always apply; explain exclusions.
- `test_paths`: test-only files and folders. Never hide production or config files there.
- `environment_inputs`, `input_files`: variables and ignored or external inputs that change results (manifests, runtime config, test data). Hashed, not copied.
- Check: `{"id", "kind", "argv", "timeout_seconds", "artifacts"}`. `kind`: `unit`, `integration`, `browser`, `interaction`, `api`, `build`, `security`, `performance`. `argv` is an array, not a shell string; `{python}`, `{project}`, `{run}` expand. `artifacts` are generated evidence files under `.factory/runs/<key>/outputs/`, removed before each run and required fresh after.
- `parallel_checks: true` only when checks share no ports, databases, files or caches. Choose checks before coding from changed effects and consumers. Every configured check runs; never narrow a saved profile.

## Phases

Each `record` needs its matching phase. Artifacts are substantive Markdown; the controller checks presence and hash, the reviewer judges substance.

| Phase | Do | Command |
|---|---|---|
| `analyze` | Run `analyze-start`. No code. | `record analysis --file <analysis.md>` |
| `plan` | Run `get-ready-to-code`: five outputs; file-summary stop unless the owner already confirmed the ticket's before/after. New software: first plan, `research-market`, revised plan; save all three. Write the todos into the ticket's checklist. No code. | `record plan --file <plan.md>` |
| `build` | Run the 0-4 loop per item; tick it after actual use. New runs permit selected feedback below. Finish implementation and worthwhile improvements; final walkthrough comes next. | `record implementation --file <summary.md>` |
| `manual` | Final actual-use QA with failure and recovery paths. | `record manual --file <receipt.json>` |
| `testing` | Write tests in `test_paths`. Seal reviewed acceptance, then record the batch (tests written, commands run, results). | `contract-proposal`, `seal`, `record batch --file <tests.md>` |
| `verify` | One complete final gate. Read the logs. | `check` |
| `review` | Map criteria to proof, then run the independent review. | `ticket-proof`, `review` |
| `ready` | Every checklist item ticked. Write the handoff. | `handoff` |
| `cancelled` | Stop. Records and checkout stay. | `cancel --reason "<why>"` |

- `record analysis` and `record plan` are refused if source or declared inputs changed since `init`. Restore the starting candidate.
- `record implementation` freezes the production candidate (`manual_candidate`). A production change after it invalidates manual evidence: `repair`. Test-only changes do not.

For item feedback, follow [affected checks](affected-checks.md).

## Ticket commands

Key: lowercase letter first, then lowercase letters, digits, hyphens; at most 64. One key per ticket for its life. Your agent reads and writes the tracker; the controller only imports what you supply. An import proves no tracker call and no human identity. Write order: render, owner confirms, write, read back, capture.

| Command | Use |
|---|---|
| `ticket-render --source <contract.json>` | Returns the body to write and its `scope_digest`. Writes nothing remote. |
| `ticket-capture --source <capture.json>` | Imports a complete tracker read. |
| `ticket-capture --unchanged --source <observation.json>` | Cheap refresh. |
| `ticket-refresh-failed --reason "<why>"` | After a failed or uncertain read. Invalidates the capture. |
| `ticket-status` | Imported scope, freshness, pending activity. |

Capture file: `version: 1`, `key`, `identity {provider, workspace, id, url}`, `title`, `status`, `observed_at`, `remote_updated_at` (timezone, not future, update not after observation), `body` (exactly as rendered), `complete: true`, `transport {tool, source}`, `activity`. GitHub identity: provider `github`, workspace `owner/repo`, id the issue number, url its HTTPS issue URL.
- Activity: every comment page. Entry: `id`, `at`, `author`, `text`, `disposition` (`non-scope`, `resolved`, `pending`). The run's own status moves are `non-scope`. Non-pending needs `reason`. Pending blocks progress. Deleted entries need reconciliation, never silent loss.
- The body carries the contract as fenced JSON between `<!-- safe-engine-ticket:v1 -->` and `<!-- /safe-engine-ticket -->`. Prose must match the render; independent edits block import.
- Contract: `revision`, `lifecycle` (`ready` for To do, `active` for In progress through Ready for QA, `blocked` also for a ticket sent back to Backlog, `done`, `cancelled`), `scope {original_request, before, after, completion, owner_input [{text, source}], journeys, exclusions, constraints, dependencies, acceptance [{id, text}]}`, `confirmation {revision, digest, actor, source, statement, at}`, optional `checklist [{id, text, done, proof}]`. The digest equals `scope_digest`. `presentation: "visual"` renders the ticket layout (Definition of done, Checklist); without it, the older Before, After, Acceptance layout. The checklist sits outside scope: ticking re-renders, writes and captures the body without a new confirmation; a tick needs its proof, and `handoff` refuses unticked items and a missing checklist. Never tick by editing the body or clicking its box: import refuses prose that differs from the render. No matching confirmation, no `init`. Scope changes need a new revision; append owner input, never rewrite.
- A dependency needs `delivery {status: "integrated", scope_digest, commit, evidence}`; the 40-character commit is in this ticket's HEAD history. Record it when the dependency hands off with its review, and branch the dependent worktree from that commit; the owner's merge is not needed. Closed status alone fails. Re-delivered after a fix: record the new commit, merge it into the dependent, then `repair` after build or a reviewed `amend` before it.

Cheap refresh file: `{version: 1, unchanged: true, key, observed_at, remote_updated_at, status, transport}`. Valid only when the tracker's `updated_at` and status equal the current capture's, and only where `updated_at` moves on body, comment and status edits. Any mismatch: full capture.

Refresh at intake and resume, before `record implementation`, before `repair --records-only`, and after local review before `handoff` and the PR. Not at `record plan`. Each needs a new observation, never a replay. Reuse one within a batch. Pending changes, inactive tickets or failed reads block progression; `status` still works.

Bind: `init --task <task.json> --profile <profile.json> --session <builder-session-id>`.

- Needs a confirmed current capture and a clean committed checkout. `--session` is the real dedicated builder session's id. Never invent one.
- One ticket, one builder session, one worktree; run tickets in parallel, each in its own worktree. Isolate ports, databases and caches too.
- The controller claims the checkout. `handoff` and `cancel` release it. A fresh `init` never replaces an existing run. Parallel worktrees share one coordination lock: retry a command refused because another operation is active; a refused ticket refresh then needs a full capture.

Amend (changed scope, criteria, checks or protected files):

1. Refresh. New owner scope becomes a new confirmed revision.
2. `contract-proposal --task <new-task.json> --profile <new-profile.json>` returns `old_digest`, `new_digest` and protected hashes. It approves nothing.
3. An independent reviewer inspects them and writes the review file: `verdict: "PASS"`, `independent: true`, `reviewer`, `reason`, `authority`, `old_digest`, `new_digest`. Changed criteria or a rebound ticket also need `acceptance_change_authority`.
4. `amend --task <new-task.json> --profile <new-profile.json> --review <review.json> --reason "<why>"`.

Amend returns to `build` (to `analyze` when the ticket scope changed) and clears checks, review, manual evidence and proof. The original request never changes. Never shrink criteria to turn a gate green, revive a cancelled run or patch state.

## Repair

Failed check, blocking finding or a defect found after `record implementation`:

1. Classify it: product, evidence or report defect. Second related failure: find the shared cause, why the last fix failed, and what prevents recurrence.
2. `repair --reason "<failure and cause>"`, with [scored selections](worth-it.md). Returns to `build`; clears checks/review/manual proof, archives receipts for carrying. Counts repairs without limit.
3. Fix surgically. Then `record implementation`, re-observe affected criteria, `record manual`, tests, `record batch`, `check`, review. The sealed contract stands; a protected-file or contract fix goes through `amend`.

Records-only correction: `repair --records-only --reason "<defective record, why raw proof stays valid>"`. Keeps original manual and check evidence. Needs all of: profile `reuse_record_evidence: true`, sealed contract, fresh unchanged ticket, phase `review` or `ready`, intact checks, manual receipt, outputs and review report, every criterion PASS, method followed, every finding on layer `evidence` or `report` with `evidence_status: valid`.

Product defects, missing or challenged proof, FAIL or UNKNOWN criteria, and any change to tracked source, docs, tests, profile, config, environment or dependencies need ordinary repair. After it: phase `review`. Replace the cleared criterion mapping or append an unhashed correction note under `.factory/`. Never touch hashed originals. Run `ticket-proof` again and get a fresh review.

## Review

1. Phase `review`, checks current and passed.
2. `ticket-proof-draft --out <proof.json>` pre-fills revision, digest, evidence hashes and changed files. Status is `PASS` only where receipt and checks support it, else `UNKNOWN`. Write the real `before` and `after` per criterion; refine `implementation`.
3. `ticket-proof --file <proof.json>`. Shape: `revision`, `scope_digest`, `criteria [{id, status: "PASS", before, after, implementation, evidence [{path, sha256}], deviations [{change, reason, authority}]}]`. Every latest criterion once. Missing or UNKNOWN blocks review.
4. Keep proof, packet and report files in the run directory (not its reserved names) or outside the project.

Review with an installed agent CLI: `review --timeout 600 --agent auto --builder <the agent that built>`.

- `--timeout` is 1-3600 seconds. The reviewer is fresh, headless and read-only. `auto` picks an installed agent other than the builder. Several installed and no known builder: pass `--builder`, or `--agent <name>` to force one.

No agent CLI, or by choice: the review packet.

1. `review-packet --out <packet.md>` writes the prompt, bound to current inputs and records.
2. Hand it to one fresh, read-only, separately spawned subagent. One packet per reviewer.
3. `review --report <report.json> --reviewer "<agent id and model>"`. The report matches the review schema and its summary starts with the packet's nonce.
4. Changed inputs, records or packet file: issue a new packet. Reissuing before submitting a report counts as a failed round. Status shows "external reviewer; independence not verified".

Never supply your own passing review, write the report yourself or reuse an old one.

Pass needs: verdict PASS, method followed, every criterion PASS, no blocking finding. Blocking: CRITICAL, HIGH, disposition `blocking`, and `before-exposure` at public or production exposure or `release` scope. `accepted-deferral` needs an exception (`owner`, `reason`, `scope`, `revisit`, `authority`, the epic's follow-ups ticket as `destination`) under the owner's real delegation: LOW, and MEDIUM at local exposure only. A failed review: `repair` the supported findings, then a fresh review.

Review rounds: a failed review, or a packet reissued before its report, is a failed round. After 3, `review` refuses. Stop that loop and ask the owner once with: findings per round (new or repeated), the shared cause, and options (extend 1-3 rounds, defer with an owner record, amend scope, cancel). Keep independent work moving. Only the owner's decision unlocks more: `extend-reviews --rounds <1-3> --reason "<owner decision>"`.

The cap applies to every review loop: controller review, seal and amend review, remote PR review. Build corrections stay uncapped.

## Evidence

- Final proof: finish implementation, `record manual`, then complete tests.
- Receipt file:

```json
{"candidate": "<status.manual_candidate>",
 "observations": [{"criterion": "A1", "device": "<environment>", "action": "<performed>",
                   "result": "<observed, with limits>", "status": "PASS", "evidence": [".factory/evidence/a1.md"]}]}
```

- Cover every `manual` and `mixed` criterion. Automated-only tasks still need a relevant actual-use observation. Evidence paths are existing project files, hashed. One receipt may cover several criteria.
- Never submit fictional PASS evidence or a dummy check for a manual criterion. Unobserved stays unverified.
- Carried criteria: after a repair, an unaffected criterion may be `{"criterion": "A2", "status": "PASS", "carried": {"receipt_sha256": "<hash from status.prior_manual_receipts>", "reason": "unaffected by <change>"}}`. Taken only from an archived receipt of this run where it passed. At least one criterion is freshly observed. The reviewer judges the carry; a doubtful carry is UNKNOWN. Amend clears the archive.
- `seal`: `contract-proposal`, independent review file, then `seal --task <final-task.json> --profile <final-profile.json> --review <review.json>`. Needs phase `testing` and a current manual receipt. It adds check bindings and `protected_paths` (the acceptance check files). Request, criterion ids and text, `interface`, `test_paths`, `environment_inputs`, `input_files`, `review_scopes` and `exposure` cannot change at seal.
- `check` runs every configured check once; exit 1 on failure. Read the logs under `.factory/runs/<key>/logs/`. Failure: `repair`.
- Never edit protected files, saved state, task, profile, recorded artifacts, captures or run history. Never weaken a check or relabel an old pass as fresh. Legitimate changes go through `amend`. Records are same-user integrity, not tamper-proof; report what is unverified.

## Status and resume

`status` is read-only: no lock, creates nothing. Other commands except `init` stop when no saved run exists. Read first:
`phase`, `ticket_current`, `checks_current`, `checks_passed`, `review_current`, `manual_candidate`, `prior_manual_receipts`, `pending_operation`, `review_packet`, `review_execution`, `repairs_used`, `failed_reviews`, `review_rounds`, `builder_session`.

Resume:
1. `status` with `--ticket`. Refresh the ticket. Select the recorded run and session.
2. A `pending_operation` or interrupted check or review is no acceptance. Rerun it on current inputs.
3. Changed candidate after its batch record: `repair`. Old passing evidence is never current.
4. Stop an active check or review by interrupting the foreground controller. `cancel` does not bypass its lock.

`handoff` needs phase `ready`, a refreshed ticket, `ticket-proof`, current passing checks and review. It writes `handoff.md` in the run directory: criterion, change, proof, gap table and deferred findings. Paste the table into the PR verification section. It releases the checkout claim. Local `ready` is not PR approval.
