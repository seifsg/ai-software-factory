# Delivery readiness

## Working iterations

Applies to tiny bugs, small tools and full products. Keep the whole requested outcome visible. Build the next complete useful result. Show it as soon as it works; then enhance it.

1. Name the main promise and next useful result. Real entry -> action -> result. Required failure/recovery and usable presentation. Headless: real consumer/output. No canned proof.
2. Order by user value. Dependencies: required now, useful later, unrelated. Explain what fails without each blocker. Challenge supporting work that delays the promise.
3. Before dependent work: state owner/source of truth, interfaces, limits/budgets, compatibility, failure/recovery. Keep it brief. Current journey first; safe evolution for later work.
4. Complete outcome ticket -> finish implementation/improvements -> manual use/demo -> relevant final tests -> independent assessment. Keep original 0-4/checkpoints. One bounded fix may be one iteration.
5. Feedback and remaining requirements choose the next result. Optional polish/enhancement later. Deferrals: owner, destination ticket, acceptance/revisit condition. No vague later.
6. One integration owner verifies the combined journey at the exact candidate. Accepted children alone cannot certify the product.

Required integrity, safety, compatibility, accessibility, logging and agreed quality stay in scope. Reduce iteration size; keep the quality bar. Production protections belong before applicable exposure.

A controller run accepts its entire confirmed ticket. Intermediate pieces have no separate acceptance. Split complete outcomes before initialization or use reviewed scope changes. No microticket quota, extra phase or silent criteria reduction.

Keep existing behavior, full-product criteria and exposure/release obligations open. Accepted requirements stay until delivered or explicitly changed under owner authority.

Repair: classify product, evidence or report defect. Second related failure? Stop symptom patches; trace the shared cause/consumers. Explain why the previous fix failed, change the plan/contract where needed and state what prevents recurrence. Keep diagnostic/failure history; no retry cap.

Validation: map change -> affected behavior/consumers -> required evidence.

Scope the reviewed profile to the complete ticket from the start; retain actual protected gates. Reuse raw evidence only while its inputs, context, scope and hashes remain valid. Changed shared behavior, config, environment, dependencies, scope or unresolved risk needs affected revalidation.

The controller reruns all configured checks after ordinary repair. Its optional records-only route repairs private records/mappings with exact unchanged evidence only; any tracked documentation/source/test change invalidates reuse; no changed-code selective reuse is implemented. Missing or challenged behavioral proof needs fresh actions, not a new classification. Never copy an old pass as a new action, weaken a gate or skip required evidence.

Progress: working now -> missing now -> next observable result. Then blockers and proof.

Checks support the outcome; passing checks alone is insufficient.

Demo names exact source/build, environment/device/profile, data/save identity and scenario/actions/result. Same URL proves no same context. State unavailable parts; measurements prove only the measured conditions.

Factory audit: reuse timestamps/logs to record time to first useful demonstration, building/checking/repairing time and repair rounds. Separate active work from wall time/waits; label estimates and missing data. Compare similar scope, find the bottleneck, remove ceremony that adds no confidence. No new reporting chore or invented timings.

Load applicable rows once. Reuse the plan, evidence and reviewer; no new skill fleet. Local MVPs stay small. All manual/user testing, playtesting and automated checks wait until the complete iteration's implementation/improvements finish. Source inspection, research and existing-log reading may happen earlier.

## Before dependent work

Record actual capabilities: runtime/build tools, browser/native controls, audio inspection, representative devices, safe data/accounts, dependencies and authorized integration access. Full delivery also needs local controller review; PR delivery separately needs a remote/cloud agent with a fresh context and checkout. Verify the actual route exists; a local subagent never counts as cloud review. Identify blockers early; continue independent work. Metadata/tool discovery is not a product test. No purchases, installs or new credentials implied.

Map acceptance to `manual`, `automated` or `mixed` evidence. Artistic quality, gameplay feel and actual interaction need honest observations; don't attach an irrelevant passing script. Name the criterion, candidate, environment/device, action, result, evidence and limits. Missing required evidence stays UNKNOWN. One receipt may support several explicitly mapped criteria; never fabricate a tester or infer completion from a screenshot.

## Games and browser lifecycles

Games: preserve intended challenge, mastery, discovery, pacing and reward. Remove accidental friction; don't turn difficulty into a defect or add hints/automation that defeat the approved game. Define intended experience and supported input/device targets in planning; playtest only at the final stage.

Web apps/games: select relevant cases, not every permutation:

| Boundary | Final manual evidence |
|---|---|
| Navigation/lifetime | Reload/deep link, back/forward, tab close/reopen, visibility loss/resume, stale tabs and cancellation; preserve promised state, clear stuck input on focus loss/pointer cancellation and release owned work. |
| Game timing | Elapsed-time/fixed-step simulation, refresh-rate independence and bounded resume delta; no giant catch-up jump after a hidden tab or suspended device. |
| Connectivity | Offline/reconnect, slow/interrupted requests, duplicate submission, expired session and uncertain completion; truthful progress/recovery. |
| Browser capabilities | Supported touch/keyboard/controller, focus/pointer/fullscreen locks, audio activation/mute, denied permissions, storage quota/eviction, device/context loss where relevant. |
| Compatibility | Supported browser/device classes, viewport/orientation, reduced motion, low-end performance and stale cached assets/client-server versions. |

Record unsupported/unavailable cases. No claim that one desktop browser proves mobile, audio or assistive behavior.

## State-changing external work

For remote effects/jobs, record `operation identity → durable state → effect → observed completion/reconciliation owner`. Cover pending/success/failure/unknown outcomes, commit/effect ordering, ambiguous timeouts, duplicate/out-of-order delivery, bounded retry/backoff, cancellation and safe replay. A DB commit, sent request or signed webhook alone proves no completed business effect.

Choose the smallest adequate mechanism: provider idempotency/reconciliation, durable pending record, transactional outbox or workflow engine according to actual need. No universal queue. Compare new substantive alternatives once. Final manual QA uses safe disposable operations and interruption/retry cases; final automated regressions follow. Read correlated logs and preserve unresolved effects before retrying.

## Authorized release and operation

Local `ready`, cloud PR approval, merge and live release are distinct. Reuse explicit authority; never infer deployment permission. Before release, keep one record:

- Exact reviewed source/build artifact, target environment/config, required services/secrets and migration/app ordering. Preserve compatible clients, data and rollback/roll-forward options; backups need usable restore.
- Relevant security, UX, SEO and integration evidence; actual live health and critical journey checks after deployment. Record failure threshold, recovery action and responsible owner. No local-only evidence called production proof.
- Log access, essential failure/stalled-job/capacity signals, authorized destination/operator and data retention/recovery. Reuse existing facilities; no automatic paid monitor, new notifications or perpetual polling.

For factory publication, approved source reaches `main` only after actual cloud PR review and authorized merge. Verify remote commit and distributed inputs; report published, locally adopted and active-run adopted separately. Preserve old pins. Pilots remain deferred until requested; a guidance update is no end-to-end product proof.
