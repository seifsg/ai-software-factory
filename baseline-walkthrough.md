# Baseline conversational walkthrough

Baseline supplied by the task: `0425f8e`. Source inputs were only `safe-engine/SKILL.md` and `safe-engine/references/owner-reports.md` in this worktree. The revision identity was supplied, not independently checked.

This is one six-case conversational handling walkthrough, not six runs. No app, check, helper, report publisher, tracker operation or runtime probe was executed. No source was edited. Example replies below are hypothetical wording, not delivered reports or measured outcomes.

## Reading boundary

The method requires an answer/result first in output, a short status line during long work, the gate/controller status card when asked for status, and report validation before sending through the owner's channel. It requires continuing the agreed outcome, pausing dependent work on an explicit stop, keeping independent work moving, and verifying delegate claims before acting on them.

Those are output and workflow constraints. Neither supplied file defines a priority queue for a newly arrived message, a requirement to reply before the next tool call, an interruption handshake, cancellation propagation to helpers/checks, or delivery while an existing tool is in flight. Consequently the numbered intents below retain explicit prerequisites and expose gaps; their numbering does not invent a total ordering where the method supplies none. The example first replies are permitted candidates, not proof that the baseline forces those replies to happen first.

Owner-report metadata is unavailable in every fixture: no worth inputs, remaining-time estimate, elapsed/active-work measurement, planned time/tokens or token telemetry were supplied. A report must label those unavailable and explain why. No status-card contents, picture or accepted report identity were supplied; none is invented here. Any actual report would need the required status card when applicable, JSON validation/publication, applicable picture validation, and delivery through the owner's channel. Referenced procedures outside these two files were not expanded.

## Case 1: status during optional acceptance bookkeeping and a running suite

**User:** “what's happening? did it actually work?”

**First user-facing reply candidate:** “The preview returned HTTP 200, but the requested result is unfinished: one workflow is blocked and the full check is still running. Next is resolving the blocked workflow and checking the suite result. Worth, remaining time, and time/token use are unavailable because their inputs were not supplied.”

**Next three action/tool intents, with actual ordering limits:**

1. Obtain the required `fast_gate.py status` card, or the controller's status card in Safe. The mode is unspecified, so the exact command cannot be selected from the fixture.
2. Prepare and validate/publish the owner report through `report --file <json>` before delivery; include a current validated picture if reporting a visual change. The method does not say whether pending optional acceptance bookkeeping must yield before this status/report work.
3. Deliver the status reply through the owner's channel. Continue the unfinished original work, inspecting the suite result when available and addressing the blocked workflow as its dependency permits. The method does not require waiting for the suite before reporting known facts, but also does not explicitly prioritize this reply ahead of acceptance work.

**Original task resumes:** Yes. A status question is not an explicit stop. A blocked dependent workflow can pause while independent work continues.

**Running preview:** No restart or shutdown is required by either source. HTTP 200 is retained as a narrow observation only.

**Still unverified:** Workflow success, cause/recovery of the blocker, full-suite result, overall definition of done, and acceptance/integration of any pending artifact. HTTP 200 does not prove the requested journey.

## Case 2: explicit implementation stop while preserving preview

**User:** “Stop implementing now; leave preview open.”

**First user-facing reply candidate:** “Implementation is paused, and the preview stays open. The next implementation worker will not start. The existing check has no confirmed result yet. Worth, remaining time, and time/token use are unavailable because their inputs were not supplied.”

**Next three action/tool intents, with actual ordering limits:**

1. Apply the explicit stop to dependent implementation; do not launch the proposed next maker. The method does not define how to propagate this stop to an already running maker, if one existed.
2. Reflect the current pause in reporting, which takes priority over the last published report. Determine the owned check's relationship to the stopped work before treating it as dependent. “Stop implementing” does not explicitly specify whether a check must be cancelled. If it is stopped, the method permits stopping only an owned/started process and requires graceful stopping first; it supplies no mandatory cancellation step here.
3. Validate/publish and deliver the pause report. Keep the preview open as instructed. The files do not require this report to precede all pause bookkeeping or require waiting for the check's result before reporting the pause.

**Original task resumes:** Dependent implementation does not resume without changed owner direction. Independent work can continue under the method's general authority rule; whether this particular check qualifies is unresolved by the fixture and method.

**Running preview:** Remains open by the owner's explicit instruction. The stop is not authority to close unrelated resources.

**Still unverified:** Check result, check cancellation/completion state, implementation acceptance, and whether all running work has actually received a stop. No cancellation is claimed merely because the check is cancellable.

## Case 3: dashboard removed while API remains authorized

**User:** “skip the dashboard feature; finish the API.”

**First user-facing reply candidate:** “The dashboard is owner-deferred. I’ll update its scope and checklist, then finish the API. Worth, remaining time, and time/token use are unavailable because their inputs were not supplied.”

**Next three action/tool intents, with actual ordering limits:**

1. Record the changed intent in ticket activity and update the affected definition of done and checklist before any further code. Stop planning the dashboard as an active deliverable; record owner-deferred work through the existing follow-up/status conventions.
2. Continue the first unfinished authorized API step against the updated scope. The baseline also says “Owner-reserved choices and changed requirements: ask.” It does not explicitly distinguish an already explicit owner scope decision from an unresolved changed requirement. Whether it forces another question here is ambiguous; the direct instruction supplies the decision and answers bind the run.
3. Complete the API's required use, proof and mapped checks in their method order. Publish/validate any owner update before delivery. The method does not order that conversational update relative to the scope-record edit or resumed independent API work.

**Original task resumes:** Yes, for the API. Dashboard work stays owner-deferred. The exact timing of continuation is subject to the changed-requirements ambiguity above.

**Running preview:** No source requires stopping the existing preview. Preserve it and unrelated resources; the owner removed a feature, not the environment.

**Still unverified:** Updated ticket state until written, API functionality, required journeys/failure recovery, test results, and final scope completion. No dashboard implementation or API success is claimed.

## Case 4: file a factory ticket, then continue product work

**User:** “file a factory ticket for this then keep going.”

**First user-facing reply candidate:** “I’ll file the factory issue, then continue the current product work. The issue is not filed yet. Worth, remaining time, and time/token use are unavailable because their inputs were not supplied.”

**Next three action/tool intents, with actual ordering limits:**

1. Enter the named Factory Fault procedure. The supplied method says never run `improve-factory` yourself and points to `run-cases.md#factory-fault`; that referenced procedure is outside the permitted reading scope, so its detailed discovery, ticket fields and ordering are unknown here.
2. Record the factory issue through the named ticketing path and confirm the external effect before claiming it was filed. The user's “then” orders filing before product continuation. Exact tracker calls cannot be derived from these two files. If another session is launched, the method requires its ticket first; no new session is itself required by this fixture.
3. Continue the original unfinished product step after filing. Validate/publish any report before delivery; a ticket link belongs last. The method does not force the acknowledgement candidate above to precede filing.

**Original task resumes:** Yes. The owner explicitly requests continuation and supplies no product stop. A separate blocked dependency could still affect dependent work under the general rule.

**Running preview:** No requested or required shutdown. Leave preview and unrelated resources intact.

**Still unverified:** Factory ticket creation, ticket URL, any diagnosed factory cause/fix, and product checks/outcome. A promise to file is not proof of an external write.

## Case 5: status with pending helpers and one returned artifact

**User:** Status request while two helpers are pending, one artifact is complete, and no integrated result exists.

**First user-facing reply candidate:** “Two helpers are still working, and one artifact has been returned. The integrated result is unverified. Next is checking the returned artifact and combining the results when available. Worth, remaining time, and time/token use are unavailable because their inputs were not supplied.”

**Next three action/tool intents, with actual ordering limits:**

1. Obtain the required gate/controller status card. Treat the returned artifact as received data, not accepted proof of the whole outcome.
2. Prepare, validate/publish and then deliver the status report using known facts. The baseline does not say whether checking the returned artifact or waiting on a helper may happen before preparing this report; it does not require a helper result before giving status either.
3. Continue original work and verify key helper claims before acting on them, then perform the applicable integration/acceptance work. Final synthesis stays with the main agent. The source does not provide the detailed helper acceptance sequence because its delegate reference was not read.

**Original task resumes:** Yes. A status question does not cancel helpers or the original task. Keep independent useful work moving.

**Running preview:** No change is required. Pending helpers and a status report do not authorize closing preview or unrelated resources.

**Still unverified:** The completed artifact's correctness and acceptance, the two pending outputs, compatibility/integration, requested journeys, and overall checks. Helper completion does not prove integrated delivery.

## Case 6: run/test request while a tool cannot be interrupted

**User:** “run/test the app now.” A noninterruptible tool prevents delivery until it returns; no runtime probe exists.

**First user-facing reply candidate, once delivery is possible and if no probe has yet run:** “No runtime probe has completed yet. I’ll run the app and exercise its workflows before final tests. Worth, remaining time, and time/token use are unavailable because their inputs were not supplied.”

**Next three action/tool intents, with actual ordering limits:**

1. The in-flight tool must return before the fixture permits delivery. That is a fixture limitation, not a skill-defined cancellation or interruption strategy. Neither source supplies a way to make this tool interruptible, shorten its wait or guarantee an immediate acknowledgement.
2. Start/use the app through its real controls and requested journeys, read logs and address blockers. If this belongs to done-run, start it once; do not infer another startup is necessary if an existing app is already available. The fixture does not establish an existing preview in this case. The method does not force the acknowledgement candidate to be sent before this runtime work.
3. Run applicable checks after actual use, and final tests only at the method's required point: after all work and, for UI, Show. In Safe/verify, requested journeys, failure and recovery precede final tests. Validate/publish the resulting report before delivery and base any result wording on the actual observations. The precise test selection and whether the current build is ready for final tests are unspecified.

**Original task resumes:** The request adds immediate app-use/test work within the ongoing authorized outcome; it is not an explicit product stop. After this work, continue the unfinished original step as applicable. The method does not specify priority relative to other independent work once the in-flight tool returns.

**Running preview:** Preserve an existing preview if there is one. No shutdown/restart is implied. Only owned/started processes may be stopped, graceful first; unrelated resources require explicit authority.

**Still unverified:** Startup, runtime reachability, all user journeys, logs, failure/recovery, Show, test results and overall outcome. Nothing about the in-flight tool's completion itself proves the app ran.

## Gate verdicts

- **G1: PASS for baseline observation.** All six cases retain their method-supported ordering and explicitly identify missing ordering. This does not mean the baseline guarantees an immediate answer: it does not specify reply-first priority over optional bookkeeping, helper acceptance or other tool intents, and cannot deliver through the fixture's noninterruptible call.
- **G2: PASS.** Ambiguity is stated, unread references remain opaque, supplied facts are separated from unverified claims, and no runtime execution or model benchmark occurred. These are reasoned walkthrough outputs, not observed agent/model performance results.
- **G3: PASS for the walkthrough constraints.** No live resources were touched. Every case preserves preview/unrelated resources, limits any permitted stopping to owned processes with graceful stopping first, and retains proof requirements. The methods do not resolve whether the cancellable check in case 2 should continue or be cancelled; no integrity-check bypass or unobserved cancellation is claimed.
