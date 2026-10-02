# Session authority and continuous progress

Read at intake, resume and delegation. This is the canonical operating procedure for the [decision ownership policy](../../../../docs/safe-engine-decisions.md#decision-ownership). Record it once in an ignored `.factory/session-contract.md` (or the existing equivalent), link it from stage artifacts, and carry it into every handoff. Supplement saved controller records; never rewrite their fixed task/profile or accepted evidence.

## Establish the contract

First inspect the user's request, earlier answers, repository instructions and existing contract. Reuse decisions. If essential preferences remain open, ask a short grouped intake covering only what matters: completion boundary, delegated versus reserved choices, desired checkpoints/update cadence, and any time/cost constraints. Do not present a questionnaire when the user already supplied these. Continue independent discovery while awaiting a required answer.

Record:

- Original outcome and acceptance; approved choices and their source; rejected choices; unresolved owner-reserved choices.
- Autonomy: advise/options only, owner checkpoints, or delegated execution. Record the actual request, not an inferred grant of external permissions.
- Which choices the agent may make and their rationale/evidence; which require the owner. Explicit full autonomy permits in-scope product, technical and working-name choices unless reserved or already fixed. Compare three credible approaches and recommend one when the methods call for it; delegated choice may proceed after the comparison without another vote.
- Intended handoff (for example a locally running application after QA and fresh review for initial owner testing), notification cadence, and owner-requested stop points. Progress updates and showing a plan are not approval gates.
- Completion boundary, owner-requested checkpoints/stops, actual access/provider constraints, and diagnostic attempts/progress across maintenance, delegates and resumes. Preserve historical allowance/deadline records as history, with the latest user instruction that supersedes them.

Continue authorized work until the agreed outcome passes the required checks and independent review, or the owner requests a stop/checkpoint. Do not invent repair allowances, credits, overall session deadlines or exhaustion gates. Reuse decisions rather than ask for more corrections. An explicit owner stop condition stays effective until the owner changes it. Allow existing authorized tool use, but no new purchases or paid provider fallback without authority. If authority to proceed is genuinely unclear, resolve only that missing boundary.

The continuous 0.1.0 controller has no repair ceiling: new runs omit `--max-repairs`; the deprecated flag and saved integers are historical metadata, while `repairs_used` records diagnostic history. `status` reports `repair_policy: continuous`, `max_repairs: null`, and `historical_max_repairs`. Existing runs use normal `repair --reason ...` without editing state; it still clears acceptance and requires a new batch, checks, improvement, final checks and fresh independent review. Never initialize a new run to bypass a failed gate or revive cancellation. Individual command watchdog timeouts detect stuck operations; they fail that operation for diagnosis and are not a session deadline. No background scheduler, unlimited provider quota or host-level continuous execution guarantee is implemented.

## Discover, decide and continue

For a missing fact/tool/binding, inspect actual files/configuration, existing session records and available authorized integrations; consult current primary documentation or market sources where relevant. Search plausible locations or alternatives before escalating. Keep a short discovery record. Do not invent identities, statuses, commands, access or evidence. A failed lookup is not automatically an owner decision; use an evidence-based in-scope fallback when authorized.

Every further attempt needs a diagnosed cause, meaningful correction, recovered dependency or new discriminating evidence. When progress stalls, change the hypothesis, inspect raw failures and consumers, research alternatives, or seek independent diagnosis; do not reroll an unchanged rejected candidate or repeat a known impossible mutation. Reconcile uncertain pushes, comments and external effects before retrying, to prevent duplicates. Continue useful independent work while a dependent action awaits actual access or an owner-reserved decision. A genuine obstacle is explained with evidence and a concrete resume step; no fixed attempt count manufactures a blocker.

Continue through planning, substantial build batches, QA, justified repairs, independent review and the agreed handoff. Pause dependent work only for a real access/tool/provider obstacle after reasonable discovery, an owner-reserved decision or changed requirement, a required failed gate that cannot be repaired within authority, or an explicit owner stop/checkpoint. Report the exact condition and attempts; finish independent authorized work that is still useful and safe.

Missing PR repository/tracker/owner/notification bindings block the affected PR step and complete PR delivery, not independent local implementation, QA or owner testing. Run both mandatory PR procedures when delivery is possible; do not label them completed if blocked. Discover existing bindings before asking; autonomy does not invent a recipient or authorize messages beyond the invoked procedure and actual binding.

Preserve ready/merge/release and deployment for the human unless explicitly separately authorized. A local controller `ready` state means checked local handoff only. Full autonomy does not waive acceptance, independent review, security, permissions or the human's final product acceptance. If a necessary QA tool is unavailable, report unverified coverage honestly instead of declaring the app finished.
