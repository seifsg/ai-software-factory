# Delivery readiness

Load applicable rows once. Reuse the plan, evidence and reviewer; no new skill fleet. Local MVPs stay small. All manual/user testing, playtesting and automated checks wait until implementation/improvements finish. Source inspection, research and existing-log reading may happen earlier.

## Before dependent work

Record actual capabilities: runtime/build tools, browser/native controls, audio inspection, representative devices, safe data/accounts, dependencies and authorized integration access. Full delivery also needs local controller review; PR delivery separately needs a remote/cloud agent with a fresh context and checkout. Verify the actual route exists; a local subagent never counts as cloud review. Identify blockers early; continue independent work. Metadata/tool discovery is not a product test. No purchases, installs or new credentials implied.

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

For factory publication, approved source reaches `main` only after actual cloud PR review and authorized merge. Verify remote commit and distributed inputs; report published, locally adopted and active-run adopted separately. Preserve old pins. Pilots remain deferred until requested; a guidance update is no end-to-end product proof.
