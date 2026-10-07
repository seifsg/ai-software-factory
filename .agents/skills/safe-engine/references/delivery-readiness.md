# Delivery readiness

## Working iterations

Tiny bug, tool or full product: build the next complete useful result and show it early. Keep the whole requested outcome visible; optional enhancement follows.

1. Name the promise and next result: real entry -> action -> result. Include required failure/recovery and usable presentation. Headless: real consumer/output. No canned proof.
2. Order by user value. Dependencies: required now, useful later, unrelated. Explain what fails without each blocker. Challenge supporting work that delays the promise.
3. Before dependent work: state owner/source of truth, interfaces, limits/budgets, compatibility, failure/recovery. Brief shared rules; current journey and safe evolution.
4. Complete outcome ticket -> finish implementation/improvements -> manual use/demo -> relevant final tests -> independent assessment. Keep original 0-4/checkpoints. One bounded fix may be one iteration.
5. Feedback and remaining requirements choose the next result. Deferrals need owner, destination ticket and acceptance/revisit condition. No vague later.
6. At integration/whole-product acceptance, one owner verifies the combined journey at the exact candidate. Accepted children alone cannot certify the product.

Required integrity, safety, compatibility, accessibility, logging and agreed quality stay. Reduce iteration size, keep quality. Production protections precede exposure.

A controller run accepts its whole confirmed ticket; intermediate pieces cannot pass separately. Split complete outcomes before initialization or use reviewed scope changes. No microticket quota, extra phase or silent criteria reduction.

Preserve existing behavior. Full-product criteria and exposure/release obligations stay open until delivered or explicitly changed under owner authority.

Repair: classify product, evidence or report defect. Second related failure? Trace the shared cause/consumers and prior-fix failure. Revise plan/contract where needed; explain recurrence prevention. Keep failure/diagnostic history, no retry cap.

Validation: change -> affected behavior/consumers -> required evidence.

Scope the reviewed profile before coding by changed behavior, consumers and risk. File extension proves no impact boundary.

| Change | Plan final proof |
|---|---|
| Guidance only; runtime/config unchanged | Real instruction use, affected callers and relevant structure/reference/package checks. No unrelated runtime suite. |
| Runtime, configuration, policy or shared assumptions | Actual affected success/failure/recovery plus relevant regressions. Broaden for changed shared behavior, trust boundaries or unresolved risk. |
| Mixed | Both affected surfaces; shared evidence may support several criteria. |

Keep required gates and quality. Separate a complete guidance outcome from optional runtime enhancement; coupled changes stay together. Every configured check runs. Never shrink saved/failed acceptance. Reuse raw proof only with valid inputs/context/scope/hashes; changed environment, dependencies or scope needs affected revalidation.

Ordinary controller repair reruns all configured checks. Reviewed v2 [records-only correction](../../../../docs/pilot-usage.md#records-only-corrections) keeps exact unchanged evidence; replace the cleared criterion mapping or append a correction note, never hashed originals. Any tracked documentation/source/test change invalidates reuse; no changed-code selective reuse. Missing/challenged proof needs fresh actions. Never relabel an old pass as fresh, reclassify a defect to bypass checks or weaken required gates/evidence.

Progress: working now -> missing now -> next observable result. Then blockers and proof.

Passing checks alone cannot prove the outcome.

Demo: exact source/build, environment/device/profile, data/save identity, scenario/actions/result. Same URL proves no same context. State unavailable parts; measurements prove only measured conditions.

Factory audit: reuse timestamps/logs for first useful demonstration, build/check/repair time and repair rounds. Separate active time from wall time/waits; label estimates/missing data. Compare similar scope; remove ceremony that adds no confidence. No reporting chore or invented timings.

Load applicable rows once. Reuse the plan, evidence and reviewer; no new skill fleet. Local MVPs stay small in process, never in quality ([product bar](product-bar.md)). Testing follows [tests-last order](../../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests).

## Before dependent work

Record actual capabilities: runtime/build tools, browser/native controls, audio inspection, representative devices, safe data/accounts, dependencies and authorized integration access. Full delivery also needs local controller review; PR delivery separately needs [cloud PR review](../../../../docs/pr-workflow.md#cloud-pr-review). Verify the actual route exists. Identify blockers early; continue independent work. Metadata/tool discovery is not a product test. No purchases, installs or new credentials implied.

Map acceptance to `manual`, `automated` or `mixed` evidence. Artistic quality, gameplay feel and actual interaction need honest observations; don't attach an irrelevant passing script. Name the criterion, candidate, environment/device, action, result, evidence and limits. Missing required evidence stays UNKNOWN. One receipt may support several explicitly mapped criteria; never fabricate a tester or infer completion from a screenshot.

State replacement/restore: check the [reset rule](app-diagnostics.md#keep-logs-usable) during final manual QA.

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

Factory publication follows the PR adapter's [enforcement](../../../../docs/pr-workflow.md#enforcement-and-evidence). Verify remote commit and distributed inputs; report published, locally adopted and active-run adopted separately. Preserve old pins. Pilots remain deferred until requested; a guidance update is no end-to-end product proof.
