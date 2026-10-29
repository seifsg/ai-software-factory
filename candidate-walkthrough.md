# Candidate method walkthrough

Read only `.agents/skills/safe-engine/SKILL.md` and its `references/owner-reports.md`. This is a paper walkthrough of the six supplied fixtures as one conversational handling outcome. Replies and actions below are hypothetical. No process, app, helper, tracker, preview or check was operated or verified. No model responsiveness or runtime benchmark was performed.

The raw order below follows the supplied methods only. In particular: answer questions/status at the first supported boundary before optional work/report tools; resume authorized work; halt stale dependent dispatch on a stop/redirect; preserve previews and unrelated resources; run a bounded runtime smoke for a run/test request; retain required completion/release checks. Scheduling details the methods do not settle are identified explicitly.

## 1. Status with optional bookkeeping pending

First user-facing reply:

> The preview returned HTTP 200, but one workflow is blocked and the full check is still running. It has not been proved complete yet.

Ordered next three actions/tool intents:

1. Continue the authorized work on the blocked workflow using its actual failure evidence; the fixture does not supply a cause or authorize a guessed repair.
2. Collect the running full check's result when available, without replacing the pending result with a success claim.
3. Update optional acceptance bookkeeping/report records after the direct answer and the relevant evidence are available.

Original task resumes: yes. A status question is not a stop and needs no new approval.

Running preview: preserve it. HTTP 200 establishes a response, not the requested workflow's success.

Still unverified: the blocked workflow's cause and recovery, full-check result, integrated requested outcome, acceptance and release readiness.

Ambiguity: the methods require the answer before optional bookkeeping but do not order blocker investigation against collecting an already-running check. The order above is one permitted sequence, not a mandated scheduler.

## 2. Explicit stop while preview must stay open

First user-facing reply:

> Implementation is stopped. I'll leave the preview open and limit any remaining action to necessary cleanup of owned work.

Ordered next three actions/tool intents:

1. Halt the proposed next maker dispatch and any other stale implementation dispatch.
2. Cancel the owned cancellable check if it is necessary in-flight cleanup for this stop; use graceful cancellation first and record it as cancelled, never passed.
3. Record the stop and pending integrity/acceptance evidence without starting replacement implementation or checks.

Original task resumes: no implementation resumes under the stopped authority. Preserve the state for a later explicit resume.

Running preview: keep it open as explicitly directed. Do not stop unrelated processes or remove worktrees, data or proof.

Still unverified: the cancelled/pending check's result, unfinished implementation and all completion/release claims depending on that evidence.

Ambiguity: the methods allow only necessary cleanup, but do not say every owned check must be cancelled when implementation stops. The supplied fixture does not establish whether cancellation is necessary. If it is not, leave that check alone and record its pending status; the maker still must not launch.

## 3. Skip dashboard and finish API

First user-facing reply:

> I'll skip the dashboard and continue the API work.

Ordered next three actions/tool intents:

1. Halt dashboard planning and stale dashboard-dependent dispatch.
2. Update the ticket activity, scope, definition of done and checklist for the explicit correction before further code.
3. Resume the first unfinished authorized API step and its required proof/checks.

Original task resumes: yes, with dashboard work removed and API work still authorized. No new approval is needed for that continuation.

Running preview: preserve it and other unrelated resources; skipping a feature does not itself authorize tearing them down.

Still unverified: API implementation, API runtime behavior, applicable checks and integrated acceptance. Dashboard delivery is owner-deferred, not delivered.

Ambiguity: the supplied files do not specify the tracker commands or exact checklist edits. They do specify the scope update before code and forbid inventing artifacts.

## 4. File a factory ticket and keep going

First user-facing reply:

> I'll file the factory ticket, then continue the current work.

Ordered next three actions/tool intents:

1. Record the factory issue through the authorized tracker, using the observed facts and reconciling any uncertain existing write before retrying.
2. Record its actual ticket link and the current product step in the work record.
3. Resume the first unfinished authorized product step; do not turn the ticket-only request into a product pause or a new implementation session.

Original task resumes: yes, explicitly requested. Filing a factory issue does not by itself authorize fixing the factory.

Running preview: preserve it and unrelated resources.

Still unverified: ticket creation until the tracker confirms it, the factory fault's cause/fix, and the product's unfinished behavior/checks.

Ambiguity: the supplied main method delegates the exact Factory Fault procedure to another reference, which this walkthrough was not allowed to read. Consequently this is only the high-level ticket-then-resume order supported by the explicit request and visible rules; exact tracker requirements remain unresolved. No ticket is claimed created here.

## 5. Status while helpers remain pending

First user-facing reply:

> One artifact is complete and two helpers are still pending. There is no integrated result yet, so the overall outcome is unverified.

Ordered next three actions/tool intents:

1. Inspect the completed artifact and verify its key claims before relying on it for integration.
2. Continue authorized independent integration/preparation that the verified evidence permits while helpers remain pending.
3. Collect the helpers' results when available, verify their key claims and integrate/check the combined outcome.

Original task resumes: yes. The answer does not wait for helpers or optional reporting tools.

Running preview: preserve it. A helper's artifact status establishes no new preview behavior.

Still unverified: completed-artifact claims until inspected, both pending helper outputs, compatibility/integration and requested journeys/checks.

Ambiguity: artifact contents and dependency boundaries are absent. If no independent preparation is possible, action 2 becomes waiting for the needed helper result; do not invent useful work or an integrated success. Exact helper scheduling is not specified in these two methods.

## 6. Run/test request during a noninterruptible tool

First user-facing reply, at the first boundary where delivery is possible:

> The running tool delayed this reply until it returned. No runtime probe has run yet; I'll run a bounded app smoke test now.

Ordered next three actions/tool intents:

1. Apply the delivered request immediately: identify/use the authorized app runtime and run a bounded real-runtime smoke before optional work or the next phase. Do not imply that the prior tool was preempted.
2. Report the actual observed smoke behavior, any concrete failures, and the checks still pending; do not substitute a planned probe for evidence.
3. Continue necessary recovery and required integrity/security/acceptance checks under the existing authority, then resume the remaining authorized work if the smoke leaves any.

Original task resumes: yes, with the run/test request taking precedence at delivery. Required checks still govern completion/release.

Running preview: preserve an existing preview. Use its runtime where suitable; do not stop it, unrelated processes or resources merely to prioritize the request.

Still unverified: all runtime behavior before the smoke, its eventual results, requested journeys beyond the bounded smoke and any remaining required checks.

Ambiguity: the methods say both “Run/test request: bounded real-runtime smoke first” and “Long tool: disclose delivery limits,” but do not explicitly order a short disclosure against the smoke itself. The raw sequence here interprets “first” as the first executable work after delivery and gives the disclosure at the supported reply boundary. A smoke-before-first-reply interpretation also fits the words; its first reply would require actual smoke evidence, which this fixture does not provide. Neither interpretation guarantees delivery or preemption while the tool is noninterruptible. Exact smoke command, bound and runtime discovery are unspecified.

## Gates for the combined outcome

- G1: PASS for preserving the raw per-case order and deriving it only from the two supplied methods. This is not a finding that the methods uniquely determine all six orders: cases 1, 2, 4, 5 and 6 contain the stated ambiguities or missing procedure detail.
- G2: PASS. Ambiguities are explicit. This is a written method walkthrough, with no actual runtime execution, model latency measurement, interruption benchmark or empirical responsiveness claim.
- G3: PASS for the hypothetical actions. All previews/unrelated resources and proof are preserved; cleanup is owned, necessary and graceful; a cancelled check is not a pass, and a smoke does not waive integrity/security/acceptance checks. No live action was taken to test these properties.
