# Session authority and continuous progress

Read at intake, resume and delegation. Follow the [decision ownership policy](../../../../docs/safe-engine-decisions.md#decision-ownership). Save one ignored `.factory/session-contract.md` or use its existing equivalent. Link it from stage artifacts and carry it into handoffs. Keep the controller's fixed task/profile and accepted evidence intact.

For a bounded direct fix, use [small-change](../../small-change/SKILL.md). Do not run broad regression or full-version validation automatically for each fix. Reuse session answers, preserve scoped evidence and let the owner choose a later broader checkpoint. An analysis-only request does not become a fix.

## Establish the contract

Read the request, earlier answers, repo instructions and existing contract first. Ask only about essential missing preferences: completion boundary, delegated/reserved choices, checkpoints/update cadence and actual time/cost constraints. Group the questions. Do not ask again for answers already given. Continue independent discovery while waiting for a required answer.

Record:
- The original outcome and acceptance. Approved choices and their sources. Rejected and unresolved owner-reserved choices.
- The actual autonomy granted: advice/options, owner checkpoints or delegated execution. Do not infer external permissions.
- Decisions the agent may make, their reasons/evidence, and decisions reserved for the owner. Full autonomy covers in-scope product, technical and working-name choices unless reserved or already fixed.
- The intended handoff, updates and owner stop points. Showing a plan or giving an update is not an approval gate.
- Actual access/provider constraints, diagnostic attempts and progress. Carry these across maintenance, delegation and resume. Keep old allowance/deadline records as history and record the user instruction that superseded them.

Where the method calls for alternatives, compare three credible approaches and recommend one. An explicitly delegated choice can then proceed without another vote.

Continue until the agreed outcome passes its required checks and independent review, or the owner requests a stop/checkpoint. Do not invent repair allowances, credits, session deadlines or exhaustion gates. An owner stop stays in force until changed. Reuse existing authorized tools; new purchases or paid fallbacks need authority. Resolve only the missing boundary when authority is actually unclear.

For the continuous 0.1.0 controller:
- New runs omit `--max-repairs`. The deprecated flag and saved integers are history; `repairs_used` records diagnostic corrections.
- `status` reports `repair_policy: continuous`, `max_repairs: null` and `historical_max_repairs`.
- Existing runs use `repair --reason ...`. Do not edit state. Repair clears acceptance and requires a new version batch, full checks, improvement, full final-QA validation and fresh independent review.
- Partial feature checks remain in build. They cannot satisfy version acceptance.
- Reusing unchanged full evidence requires explicit reviewed-profile eligibility and integrity validation. Read the [usage guide](../../../../docs/pilot-usage.md#feature-feedback-and-version-checkpoints).
- Never start a new run to bypass a failed gate or revive cancellation.

A command watchdog detects a stuck operation. Diagnose that operation; do not treat the timeout as a session deadline. These instructions provide no scheduler, unlimited quota or host-level execution guarantee.

## Discover, decide and continue

Missing a fact, tool or binding? Inspect files/config, session records and authorized integrations. Consult current primary docs or market sources where relevant. Search plausible locations and alternatives. Keep a short discovery record. Do not invent identities, status, commands, access or evidence. Use a supported in-scope fallback when authorized; a failed lookup alone does not require an owner decision.

Every next attempt needs a diagnosed cause, meaningful correction, recovered dependency or new evidence that distinguishes the possibilities. When stuck, change the hypothesis, inspect raw failures and consumers, research alternatives or seek independent diagnosis. Do not reroll an unchanged rejected candidate or repeat a known impossible mutation.

Reconcile uncertain pushes, comments and external effects before retrying. Do not duplicate actions. Continue useful independent work while another step needs access or an owner decision. Explain real obstacles with evidence and a concrete resume step. Do not manufacture a blocker from an attempt count.

### Recover a failed control route

A missing window or failed tool action only proves that route failed. Before returning a runtime problem to the owner, inspect permitted alternatives: the app's command/API, a supported CLI or OS process management. Read tool instructions and current primary docs when behavior/permissions are uncertain.

Keep restrictions in force. Do not invent UI handles, bypass a denied action through another interface, change host security or treat a search result as new authority.

To stop a local app:
1. Establish the exact process, executable path and ownership from evidence. Record active work. Preserve accessible saved state without exposing secrets.
2. Recheck identity before acting; a PID can be reused.
3. Prefer graceful stop so the app can save and clean up.
4. If it fails or the app is unresponsive, force-stop only within authority for that exact app and the risk to unsaved work. Reuse explicit authorization. A general project request does not authorize killing unrelated apps or discarding private work.
5. Verify the process exited and relevant resources were released before dependent QA or restart.
6. Record what was preserved, what was unrecoverable, the route and observed result. A saved-file backup does not capture an in-memory draft.

If permitted alternatives still fail or essential access/authority is missing, explain the obstacle and smallest owner action needed. Continue useful independent work. Keep recovery within the original task and normal evidence/review cycle. Research supports meaningful attempts, not an endless unchanged loop or guaranteed recovery.

Continue through planning, substantial build batches, QA, repairs, independent review and the agreed handoff. Pause dependent work only for:
- A real access/tool/provider obstacle after reasonable discovery.
- An owner-reserved decision or changed requirement.
- A required failed gate that cannot be repaired within authority.
- An explicit owner stop/checkpoint.

Report the condition and attempts. Finish independent work that remains useful and safe.

Missing PR repository/tracker/owner/notification bindings block the affected PR step and complete PR delivery. They do not block independent local implementation, QA or owner testing. Discover bindings before asking. Run both PR procedures when delivery is possible; do not call blocked procedures complete. Do not invent recipients or messaging authority beyond the invoked procedure and real binding.

Ready/merge/release and deployment stay with the human unless separately authorized. Controller `ready` means checked local handoff. Autonomy does not waive acceptance, independent review, security, permissions or final human product acceptance. If QA tools are unavailable, report the unverified coverage; do not declare the app finished.