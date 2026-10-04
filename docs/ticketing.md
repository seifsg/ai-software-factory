# Ticketed factory work

GitHub Issues is Seif's selected backlog. For another project, discover its preferred tracker and authorized MCP tools; without a preference, try GitHub Issues. Resolve actual repo/access/privacy. Failed or uncertain writes need reconciliation, never duplicate issues or silent local fallback. The [Ticketing skill](../.agents/skills/ticketing/SKILL.md) owns the method; its [contract](../.agents/skills/ticketing/references/ticket-contract.md) defines durable records.

Each implementation ticket gets a dedicated builder session and full factory cycle, even bugfixes. Keep scope surgical and checks relevant. Separate worktrees can run independent tickets; shared epic checkouts are serial. Isolate shared ports, databases, caches and services too. Parent/coordinator owns scheduling, dependencies and integration acceptance. A closed child list does not prove the combined epic journey.

No detailed-ticket intake requested? Derive context from request/code/prior work and continue under actual authority. Follow the [writing recipe](../.agents/skills/ticketing/references/ticket-contract.md#write-the-ticket): brief titles/body/activity, complete cold-agent context, useful visuals, progress/PR links. Separate purpose/goal, source context and behavior change using the optional structured fields below. Meaningful expectations stay in confirmed scope. Explicit checkpoints/reserved choices remain.

## Commands

Use a key starting with a lowercase letter, then lowercase letters/digits/hyphens, at most 64 characters. Windows device names are rejected. One key per native ticket, preserved across its history.

```text
python -m safe_engine --project <absolute-target-root> --ticket <key> ticket-render --source <contract.json>
python -m safe_engine --project <absolute-target-root> --ticket <key> ticket-capture --source <capture.json>
python -m safe_engine --project <absolute-target-root> --ticket <key> ticket-status
python -m safe_engine --project <absolute-target-root> --ticket <key> init --task <task.json> --profile <profile.json> --session <real-builder-session-id>
python -m safe_engine --project <absolute-target-root> --ticket <key> status
```

These are command templates, not execution evidence. Render returns body/digest, writes nothing remotely. Capture imports an actual full MCP read; it neither creates remote tickets nor authenticates owner identity or dispatches sessions. Status reports imported evidence and limits. Failed imports invalidate existing captures. After failed/uncertain remote access, use `ticket-refresh-failed --reason <reason>`; never keep old completion authority silently.

## Remote contract

Write with the [ticket recipe](../.agents/skills/ticketing/references/ticket-contract.md#write-the-ticket): short, specific, complete. Render, confirm from actual owner instructions/delegation, write through MCP, then read back. New structured tickets show purpose/goal, context, behavior-only Before/After, approach, journey, criteria, guardrails, progress and activity. The native issue title supplies the headline. Full data sits in a collapsed `details` block: one fenced JSON contract between `<!-- safe-engine-ticket:v1 -->` and `<!-- /safe-engine-ticket -->`.

Exact old folded/unfolded projections still import. Without `presentation: "visual"`, rendering/validation stays legacy, including pre-existing custom scope fields. Python `render_ticket(..., layout="legacy")` retains the old projection for compatible old consumers; no new CLI command. Keep rendered prose exact; independent edits still block import. Folding/layout alone changes no digest/authority. Adding meaningful scope fields requires a new confirmed revision for existing tickets. Keep active pinned consumers' recorded format until supported adoption; do not silently restyle them.

Contract fields:

- `revision`: positive integer. `lifecycle`: `ready`, `active`, `blocked`, `done` or `cancelled`.
- `scope`: nonempty `original_request`, `before`, `after`, `completion`; sourced `owner_input: [{text, source}]`; nonempty `journeys`; explicit `exclusions`, `constraints`, `dependencies` arrays; optional `epic`; unique `acceptance: [{id, text}]`. Preserve reasons, actors/dates, choices and examples in sourced input/constraints. Dependencies use stable local keys, with native links in the input/epic context.
- New visual layout: top-level `presentation: "visual"`, nonempty `scope.purpose`, `goal`, `context`, `approach` together, plus top-level nonempty `progress`. Optional scope `flow` is raw ASCII; `optional` is a text array of nice-to-haves. These scope fields bind to the semantic digest. Use brief text/inline code in before/after table cells; put full snippets in context or supporting evidence. Context/progress support Markdown; no fake source/results.
- Optional top-level `activity: [{at, actor, what, why, result}]` renders a dated change/reason/result table for structured tickets; every value is nonempty text. Progress/activity are operational metadata, not requirement changes. Preserve full history/source input in the contract; meaningful new expectations belong in versioned scope.
- `confirmation: {revision, digest, actor, source, statement, at}` for that exact scope. `at` has a timezone. A draft without confirmation cannot start implementation. Local metadata never establishes human authority.
- Completed dependencies need `delivery: {status: "integrated", scope_digest, commit, evidence}`. Commit is their accepted 40-character SHA, in this ticket's HEAD ancestry. Evidence references actual acceptance/cloud review. Closed status alone fails.

Other canonical decision/activity fields are allowed. Put meaningful requirements in scope so its digest changes. Ordinary activity/status/observation time stays outside acceptance fingerprints. Preserve original owner input; append corrections and superseded input. New scope needs a new revision, never rewritten history.

Capture fields: `version: 1`, `key`, exact `identity: {provider, workspace, id, url}`, remote `title`/`status`, timezone-qualified `observed_at`/`remote_updated_at`, rendered `body`, `complete: true`, `transport: {tool, source}` and `activity`. GitHub identity uses `provider: "github"`, `workspace: "owner/repo"`, positive issue-number text and its actual HTTPS issue URL.

Fetch every activity/comment page. Each entry needs unique `id`, `at`, `author`, `text`, `disposition: "non-scope" | "resolved" | "pending"`. Resolved/non-scope entries need a sourced `reason`. Unreviewed owner scope stays pending. Preserve deleted entries through explicit reconciled history; known activity cannot silently vanish. No future timestamps, replayed reads or identity aliases.

Refresh at intake/resume, before build (`record plan`), after finished implementation (`record implementation`), and after local review before `handoff`/PR. Controller boundaries need a new complete observation after the saved phase, including dependencies. Reuse unchanged captures within a batch. Pending changes, inactive tickets, failed reads or changed confirmation block progression. Status remains inspectable when scope drifts/cache is missing.

## Runs and changes

Version-2 task request/criterion IDs/text must match the confirmed ticket. Binding includes identity, revision, scope digest, confirmation and full scope in acceptance and manual fingerprints. State: `.factory/runs/<key>/state.json`. Outputs: `.factory/runs/<key>/outputs/`; `{run}` resolves to that namespace. Record the real dedicated builder session with `--session`.

Changed scope: refresh, preserve input/activity, then use `contract-proposal`, independent exact old/new review and `amend --task ... --profile ... --review ... --reason ...`. Rebinding needs explicit `acceptance_change_authority`. Keep the original request, old contracts and failures. Changed scope restarts affected analysis/planning and invalidates manual/tests/review. No state patch, acceptance shrink or cancelled-run revival. Legacy runs retain `.factory/state.json` and pins; start ticket runs in a fresh worktree, never mix both in one checkout.

Keep execution/evidence in ignored `.factory/`. Shared immutable captures, identity index and durable claims live in `<git-common-directory>/safe-engine/tickets/`, shared across repository worktrees and outside tracked source. Boundary observations are copied into the run. These are private caches, not a second tracker. Missing current cache or interrupted saves need diagnosed recovery from preserved history; never delete records or restart numbering. One active claim per physical checkout, no expiry/stealing. Handoff/cancellation releases its writer while preserving lineage. Worktree transfer needs recorded reconciliation; fresh `init` cannot bypass an existing run.

## Final proof

Finish implementation/improvements → final manual action QA → useful final test authoring/execution → fresh independent assessment. No early tests/walkthroughs. Baseline capture uses the existing narrow [before/after exception](pr-workflow.md#beforeafter-proof). No game/app pilot is implied by checking this factory.

After final checks, before local review, use `ticket-proof --file <proof.json>`. Match `revision`/`scope_digest`; map every latest criterion exactly once in `criteria` as `{id, status: "PASS", before, after, implementation, evidence: [{path, sha256}], deviations: []}`. Evidence paths name actual project/run files. Approved deviations need `{change, reason, authority}`. Missing/unknown results, changed candidate or altered evidence block review/handoff. The reviewer inspects mapping and raw evidence; a recorded PASS cannot prove an action occurred.

Refresh the real tracker before each PR/update and compare latest confirmed expectation with implementation, before/after proof, evidence and deviations in the existing Compliance/journey pass. Include ticket/epic links, exact revision/digest, decisions/activity, checks/limits and resume step. Applicable UI screenshot pairs are mandatory; equivalent output covers nonvisual work. Optional useful journey video stays final-stage.

Authorized PRs follow the [adapter](pr-workflow.md): draft creation, separate cloud review with fresh context and exact remote base/head, human handoff. Local review never substitutes. Update canonical tickets with actual outcomes, not promised work. Local ready, cloud reviewed, integrated, merged, released and adopted remain distinct.

The controller binds supplied records and recency; it cannot authenticate MCP execution/owner identity, intercept arbitrary host actions, provision sessions or enforce remote merges. Keep secrets/private transcripts outside reusable Git and unauthorized tracker audiences. No automatic install/active-bundle adoption.
