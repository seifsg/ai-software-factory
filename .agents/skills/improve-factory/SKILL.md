---
name: improve-factory
description: "Repair Safe Engine's skills, controller, or delivery workflow from feedback. Preserve any active app, verify the factory correction in isolation, and return a safe resume step. Ordinary app bugs stay in the app workflow."
---

# Improve Factory

Understand what happened and what Seif expected. Fix the actual factory cause. Preserve his methods and the app's progress.

For a requested bounded instruction/helper correction, use [small-change](../small-change/SKILL.md). Keep this skill's checkpoint, isolation, consumer updates, and adoption rules. Its light routines replace the full analysis, planning, and review below for that scope. An analysis-only or planning-only request stays in that phase.

Factory-wide routing, acceptance, or interacting procedure changes need the relevant maintenance analysis and an independent behavioral exercise. Select checks from affected consumers; do not run unrelated controller/app suites. Keep one maintenance record and one final independent assessment. Combine it with PR review when the selected scope permits. Do not recursively start maintenance.

For an active build, follow this order:

`Checkpoint → isolated repair → independent review → compatible resume`

Parallel app work can continue only when it is demonstrably independent of the fault and repair. This is a procedure operated by the agent, not a hook or automatic upgrade service.

## Understand the report

Accept the user's own explanation. Record the report, expected behavior, and example. Find the session artifacts, source, actual commands, and factory version yourself. Ask only for consequential missing facts or decisions. Seif owns intended behavior and may delegate design and working-name choices through the [session contract](../safe-engine/references/session-contract.md).

Resolve the factory root from this file and the app root separately. Read both projects' rules and [approved decisions](../../../docs/safe-engine-decisions.md). Inspect their status before edits.

What actually failed?

- An agent skipped an existing instruction: recover that step and inspect the invocation or handoff. A new rule may be unnecessary.
- A skill is unclear or incomplete: fix its canonical owner and affected callers.
- The controller or adapter is faulty: reproduce the observable failure and fix that layer.
- A tool, access, or decision is missing: record the blocker. Do not invent an implementation.
- The app has a bug: return it to app work unless there is separate evidence of a factory defect.

For an active app run, read and execute [live-session maintenance](references/live-session.md) before changing either workspace. Capture the checkpoint before delegates start. Without an active run, use an isolated factory branch/worktree and skip app-resume steps. Never silently stash, reset, switch, or upgrade the app checkout.

## Prepare the correction

1. Read and execute [analyze-start](../analyze-start/SKILL.md). Inspect real source and consumers, draw the flow, separate claims from evidence, and state unknowns. Reproduce the smallest relevant case where possible. An unobserved failure stays unverified. Do not implement during analysis.
2. State what should change and what must remain: app goal, selected product/design decisions, complete routines, fresh evidence, continuous progress, owner stops, and human release decisions. Changing these needs the user's actual decision. Editing a failed acceptance definition is not a repair.
3. For a new substantive choice, compare three credible options and recommend one. Reuse approved choices and explicit delegation without asking again. A delegated choice or local correction restoring agreed behavior can proceed. Owner-reserved choices stay pending. Keep unrelated improvements out.
4. Read [get-ready-to-code](../get-ready-to-code/SKILL.md). Prepare its files, critique, phases, todos, and complete plan. Honor the file-summary stop unless existing user delegation explicitly covers continuing the plan. Include reproduction, behavioral checks, consumers, before/after evidence, compatibility, and the app's next safe step.

## Repair and check

Give one writer ownership of the factory candidate in its isolated checkout. The app coordinator owns app changes and run state. Delegation does not isolate files automatically: assign explicit paths and tools. For active runs, follow the live-session delegation contract.

Use Get Ready to Code's complete 0–4 execution loop and pre/change/post inspection for every todo. Use Skill Creator for skill edits when available. Otherwise preserve its structural and behavioral checks and report the host limitation.

Fix the canonical cause. Do not append a universal rule for every complaint. Update actual consumers, skill index, provenance, and affected usage/preview statements. Avoid duplicate procedures and recursive calls.

If required procedure inputs change, update [the factory input contract](../../../safe_engine/bundle-inputs.json) and its consumer map. Required files guard against deletion; declared source trees discover added code and guidance. Read [pilot usage](../../../docs/pilot-usage.md) for the fingerprint boundary and external-input limits. A whole-candidate snapshot and that fingerprint protect different things.

Batch relevant checks after the correction. Use a behavioral regression for executable bugs or a realistic agent exercise for changed instructions. Word matching or syntax checks alone do not prove behavior. Preserve the initial failure and candidate evidence. Choose applicable [validation scenarios](references/validation-scenarios.md); they are not a mandatory full suite for every edit.

Run [deep-review](../deep-review/SKILL.md) and its [security](../deep-review/references/theme-security.md), [performance](../deep-review/references/theme-performance.md), and [user-journey](../deep-review/references/theme-user-journey.md) reviews, then [change-guard](../change-guard/SKILL.md) and [compliance-check](../compliance-check/SKILL.md). Check the correction and preserved behavior. Support quality and performance claims with evidence.

Obtain a fresh assessment of the exact candidate from a separate instance. Delegate when supported. Give it raw evidence and context; do not ask for a particular verdict. If it makes repairs, get another fresh assessment. Missing independent execution blocks acceptance. For a changed gate, retain the old rule/reproduction and have the reviewer assess that change independently; its new passing output alone is insufficient.

Follow the session contract across retries and delegates. Do not invent credits, allowances, deadlines, or retry ceilings. Keep diagnostic history, make meaningful corrections, and reconcile uncertain effects before retrying. Find alternatives when stuck. Do not start another run to bypass failure or cancellation. Missing access or authority blocks only dependent work.

## Deliver and resume

For authorized PR creation or updates, execute [how-to-make-a-pr](../how-to-make-a-pr/SKILL.md), its separate-instance [how-to-review-a-pr](../how-to-review-a-pr/SKILL.md), and [the project adapter](../../../docs/pr-workflow.md). Local validation or candidate review does not replace that pair. Discover actual task, owner, and notification bindings before asking. Missing bindings block PR completion; independent local repair and owner testing continue. Keep the PR draft and ready/merge/release decisions with the human.

Give a short before/after explanation. Save one maintenance record with:

- Original report, expected result, reproduced cause or unknown.
- Approved/pending decisions, preserved requirements, methods read, analysis, and plan.
- App checkpoint when present, exact old/new commits, dirty candidate manifest and diff where needed, evidence, and actual reviewer identity.
- Checks and limits, diagnostic progress, real constraints, blockers, and any PR links.
- Adoption decision, compatibility, rollback destination, next responsible agent, and exact resume step.

Keep private records in an excluded directory such as `.factory/maintenance/<unique-id>/`. Verify exclusion. Share only minimal sanitized evidence externally. Add records alongside saved controller artifacts; do not overwrite them. A written receipt does not enforce host behavior or act as a controller command.

For an active app, use [review, adoption, and resume](references/live-session.md#review-adoption-and-resume). Report repair, PR delivery, and app adoption separately. A verified local candidate can support an explicitly authorized trial while its PR remains draft; it is not released. If adoption is blocked, preserve the checkpoint and say whether the old bundle can safely continue. Resume the original app through its supported workflow. Do not initialize it again or silently change its requirements.

## Invoke

For installation across projects or hosts, use [the portable GitHub entry](../../../docs/install-improve-factory.md). Keep this procedure in the full factory bundle; this folder alone lacks dependencies.

```text
Use $improve-factory. During this build, the factory did [what happened].
It should do [expected behavior]. Preserve this app's progress, repair the
factory in isolation, and tell me what can safely resume.
```

If skill discovery fails, read this entire file by absolute path. File access and actual host tools are still required.
