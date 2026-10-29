# Variant walkthrough

Paper fixtures only, within the existing maintenance run. No app, process, ticket, runtime, integration, test or benchmark was exercised. The only sources read were the two files below. Supplied fixture facts are assumptions for this walkthrough, not newly observed evidence.

## Sources

- `.agents/skills/safe-engine/SKILL.md`, SHA256 `118AB9D34C05012E4F11F77A6BBCC910615301DC3C7A318F577FB40F61E95F9E`.
- `.agents/skills/safe-engine/references/owner-reports.md`, SHA256 `F363C1DDA14467C0D5B1303971E02F8247D8DEC778E10506ECC6EE4EB19958E4`.

Both paths resolve under `<factory-checkout>`.

## Variant 1

Raw input: Ongoing authorized API implementation, preview running, user says 'This is BS. File a factory ticket for this.' They do not say stop and do not explicitly say resume. Pending API work remains unfinished.

First user-facing reply:

> I'll file the factory ticket and continue the unfinished API work.

Ordered next three actions/tool intents, after that reply:

1. Read the referenced Factory Fault route and discover the relevant fault and existing tracker context. Do not start `improve-factory` in this delivery session. This is a proposed next action, not a source read performed for this walkthrough. (`SKILL.md:121,143-145`.)
2. Record the requested factory fault in the appropriate ticket using the prescribed route, checking an uncertain external write before retrying. Do not claim it is filed until the actual tracker result supports that claim. (`SKILL.md:121,123,134,145`.)
3. Continue the first unfinished authorized API step, without waiting for a separate resume instruction. Verify any resulting work before claiming it is tested or ready. (`SKILL.md:92,105,119,141`.)

Original objective state: active and unfinished. A ticket-only request does not require a later resume command; frustration alone is not a stop. (`SKILL.md:105,119`; `owner-reports.md:6`.)

Preview impact: preserve the running preview. No shutdown, restart, worktree deletion or unrelated cleanup is warranted by this input. Preserve unrelated processes, worktrees, data and proof. Owned processes are the outer limit of stop authority, not a reason to stop them. (`owner-reports.md:6`; `SKILL.md:126`.)

Unverified claims: no ticket identifier, filing success, fault diagnosis, API completion, passing runtime behavior or readiness is established. The reply expresses the next action, not a completed filing. (`SKILL.md:92,121`.)

Ambiguity: these two sources point to `run-cases.md#factory-fault` and `ticketing` without supplying their procedure. The exact tracker, ticket contents, duplicate handling beyond uncertain writes, and fault-routing commands cannot be derived from this allowed packet. The noun 'this' does not identify a specific failure beyond the owner's dissatisfaction. Discovery must establish the reportable facts; no cause or reproduction should be invented.

## Variant 2

Raw input: Two implementation helpers pending and one completed unverified artifact, existing preview responds HTTP200 but key workflow never tested; user says 'What is going on? Run/test the app now.' At supported boundary no tool blocks delivery.

First user-facing reply:

> The preview responds HTTP200, but the key workflow is untested. Two helpers are pending and one artifact is unverified. I'm running the workflow now.

Ordered next three actions/tool intents, after that reply:

1. Immediately perform a bounded real-runtime smoke of the key workflow against the existing preview, through real controls. Inspect its concrete results and relevant logs. Do this before optional reporting tools, helper acceptance or further implementation dispatch. If browser control is unavailable, use the existing HTTP or CLI interface and disclose that limit. Do not invent a route, command or input. (`owner-reports.md:7`; `SKILL.md:69,71,105,121`.)
2. Report what the smoke actually demonstrated, concrete failures if any, and pending checks, including the unverified artifact and incomplete helper work. Do not upgrade HTTP200 or a single smoke to workflow, integration, full-test or release proof. (`owner-reports.md:7`; `SKILL.md:92,121,135`.)
3. Continue the unfinished authorized work from that evidence: repair an observed in-scope blocker if present, otherwise verify the relevant completed artifact and continue pending work. Keep required integrity, security and acceptance checks for completion. Do not wait for an additional resume instruction. (`SKILL.md:69,105,119,135`; `owner-reports.md:7`.)

Original objective state: active and unfinished. The immediate priority is real-runtime use and an evidence-bounded answer. The pending helpers and unverified artifact prevent an unsupported completion claim. (`SKILL.md:92,105,119,135`; `owner-reports.md:7`.)

Preview impact: reuse and preserve the existing preview. No supplied failure requires replacing it. Preserve unrelated resources, worktrees, data and proof. Defer optional dispatch that would delay the requested smoke; do not blanket-cancel the helpers merely because they are pending. If any dispatch is actually stale under the redirected priority, halt that stale dependent dispatch and limit cleanup to necessary owned in-flight work. (`owner-reports.md:6-7`; `SKILL.md:119,126`.)

Unverified claims: HTTP200 establishes only the fixture's response fact. It does not establish the key workflow, integration, recovery, artifact correctness, helper completion, full testing, security, acceptance or production readiness. No smoke outcome or failure is supplied, so no such outcome appears in the reply. (`SKILL.md:69,92,121,135`; `owner-reports.md:7`.)

Ambiguity: 'bounded' has no numerical duration, attempt count or prescribed command in these sources. The key workflow, inputs, runtime controls and helper dependencies are unspecified. Select the smallest meaningful real journey from existing project evidence; do not treat the missing details as permission for invented commands or a phase-long testing detour. The packet does not specify whether either helper is stale, so unconditional cancellation is unsupported.

## Gates

- G1: Each decision above traces to a cited line in the two allowed methods. The unavailable Factory Fault procedure remains explicit.
- G2: All tool entries are intentions. No runtime, integration, test, ticket or benchmark success is asserted.
- G3: Both variants preserve the preview and unrelated resources; pending helper work is not automatically destroyed or accepted.

## Variant2 supplied-result continuation

Explicitly synthetic supplied facts, not observed app behavior: the hypothetical smoke returns page loads HTTP200, main-form submission errors; the full suite and two helpers remain pending.

Next first user-facing report:

> The page loads HTTP200, but submitting the main form errors. The full suite and two helpers are still pending.

Next two action intents:

1. Inspect the form error and relevant runtime logs to diagnose the concrete blocker, then repair its in-scope cause. Do not invent the error text or a diagnosis. (`SKILL.md:69,121`; `owner-reports.md:7`.)
2. Retry the affected real form journey after the repair and verify its result; then continue the unfinished authorized work and required completion checks. Verify helper claims before accepting them. (`SKILL.md:69,105,119,135`; `owner-reports.md:7`.)

Preview impact: retain the existing preview for diagnosis and the affected journey. These supplied facts do not establish a need to stop or replace it. Preserve unrelated processes, worktrees, data and proof. (`owner-reports.md:6`; `SKILL.md:126`.)

Unverified claims: the form's cause, a successful repair, successful submission or recovery, integrations, helper results, the full suite, security, acceptance and readiness remain unverified. The supplied HTTP200 does not prove the failed form journey. No runtime action or result is newly observed here. (`SKILL.md:69,92,121,135`; `owner-reports.md:7`.)
