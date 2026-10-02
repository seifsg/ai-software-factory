---
name: improve-factory
description: "Repair or improve Safe Engine's skills, controller, or delivery workflow from user feedback, including during an app-building session. Preserve the active app, diagnose the factory failure, verify an isolated correction, and hand back a resumable checkpoint. Ordinary app defects stay in the app workflow."
---

# Improve Factory

Turn Seif's explanation of what happened and what should happen into an evidenced factory correction. He owns the intended behavior and may delegate in-scope design and working-name choices through the [session contract](../safe-engine/references/session-contract.md). Reuse his existing methods in full; this skill coordinates them and does not replace them.

The selected mid-build policy is **checkpoint → isolated repair → independent review → compatible resume**. Parallel app work is allowed only when demonstrably independent of the fault and the factory repair. This is an agent-operated procedure, not an installed hook, automatic upgrade service, or guarantee of uninterrupted execution.

## Intake and scope

Accept a natural-language complaint; do not require the user to fill a technical form. Capture the original report, expected behavior, and any example. Find the relevant session artifacts, source, actual commands, and factory version yourself where accessible. Ask only for material missing facts or decisions.

Resolve the factory root from this file and the app root separately. Read factory/project rules and [approved decisions](../../../docs/safe-engine-decisions.md). Inspect status before editing. Distinguish:

- An agent skipped an existing instruction: recover the missed step and investigate the invocation/handoff; a new rule may be unnecessary.
- A skill is ambiguous or incomplete: correct its canonical owner and affected callers.
- A controller or adapter is faulty: reproduce its observable failure and repair that layer.
- A tool/access limitation or unresolved decision: preserve it as a blocker, not an invented implementation.
- An application defect: return it to the app workflow unless there is separate evidence of a factory defect.

If an app run is active, **read and execute [live-session maintenance](references/live-session.md) before changing either workspace**. Capture its checkpoint before delegates start. If no run is active, use an isolated factory branch/worktree and skip the app-resume steps. Never silently stash, reset, switch, or upgrade the app's checkout.

## Understand and prepare

1. Read and execute [analyze-start](../analyze-start/SKILL.md), including real source, every consumer, an ASCII flow, claims versus evidence, and unknowns. Reproduce the reported behavior with the smallest relevant case where possible. Label an unobserved failure as unverified. No implementation during analysis.
2. State the expected correction and preserved invariants: the original app goal, selected product/design decisions, Seif's complete routines, evidence freshness, continuous progress, owner stop decisions, and human release boundary. Changes to these invariants need the user's actual decision; editing a failing acceptance definition is not a repair.
3. For a new substantive choice, compare three credible alternatives, recommend exactly one and explain why. Reuse approved choices and explicit delegation without asking again. An in-scope delegated selection or localized correction restoring agreed behavior may proceed under existing authority; owner-reserved choices remain pending. Keep unrelated opportunities out of the repair.
4. Execute [get-ready-to-code](../get-ready-to-code/SKILL.md) Part A: file set, critique, phases, all todos, complete plan. Include reproduction/behavioral verification, affected consumers, before/after evidence, compatibility, and the app's next safe step.

## Repair and verify

- Give one writer ownership of the factory candidate in its isolated checkout. The app coordinator owns app changes and run state. A sub-agent has no automatic filesystem isolation: explicitly scope paths and tools. Follow the delegation contract in the live-session reference when applicable.
- Execute the existing method's Part B, including the full 0–4 loop and pre/change/post inspection for every todo. Use Skill Creator for skill changes when available; otherwise preserve its required structural and behavioral checks and report the host limitation.
- Fix the canonical cause rather than append a universal instruction for every complaint. Update actual consumers, skill index, provenance, and relevant usage/preview statements together. Avoid duplicated procedures and recursive skill invocation.
- Batch relevant checks after the substantive correction. Use a behavioral regression for an executable bug or a realistic agent exercise for changed instructions; syntax/word matching alone does not demonstrate behavior. Preserve the initial failure and candidate evidence. See [validation scenarios](references/validation-scenarios.md) for applicable exercises, not a mandatory full suite on every edit.
- Run [deep-review](../deep-review/SKILL.md) with its security, performance, and user-journey references, then [change-guard](../change-guard/SKILL.md) and [compliance-check](../compliance-check/SKILL.md). Check both the reported outcome and preserved behavior. No unsupported performance/quality claims.
- Obtain a fresh **separate-instance** assessment of the exact candidate. Delegate that assessment when the host permits; supply raw evidence and required context, not a requested verdict. If the reviewer makes repairs, obtain another fresh assessment. Missing independent execution leaves acceptance blocked. Do not certify a changed gate using only that gate's new passing output: retain the old rule/repro and have the reviewer assess the gate change independently.
- Follow the canonical session contract across delegates, retries and follow-ups: no invented credits, allowances, session deadlines or fixed retry ceiling. Preserve diagnostic history, require meaningful corrections and reconcile uncertain effects before another attempt. Discover alternatives when progress stalls. Never start another run to bypass failed acceptance or cancellation; actual missing access/authority blocks only dependent work.

## Deliver and return to the app

For every PR or PR update, read and execute [how-to-make-a-pr](../how-to-make-a-pr/SKILL.md) and its complete separate-instance [how-to-review-a-pr](../how-to-review-a-pr/SKILL.md). Local skill validation or a local candidate assessment does not replace this pair. Use actual [project bindings](../../../docs/pr-workflow.md); discover actual task/owner/notification settings before asking. Unresolved settings remain PR blockers; independent local repair and owner-test delivery continue. Preserve draft status and the human's ready/merge/release decision.

Return a concise before/after explanation plus a durable maintenance record containing:

- Original report and intended behavior; reproduced cause or explicit unknown.
- Approved/pending decisions and invariants; canonical files/routines read and analysis/plan artifacts.
- App checkpoint reference when present; exact old/new bundle commits plus any dirty candidate manifest, diff, evidence and reviewer identity as actually known.
- Verification results and their limits; diagnostic attempts/progress and actual constraints, blockers, and PR links when present.
- Adoption decision, compatibility, rollback destination, next responsible agent and exact resume step.

Keep private runtime records in an excluded local directory (for example `.factory/maintenance/<unique-id>/`), verify exclusion, and share only minimal sanitized evidence outside it. Preserve saved controller artifacts; add supplementary records rather than overwrite them. A user-visible receipt is not a controller command or a proof of host enforcement.

For an active app, return to [the live-session adoption procedure](references/live-session.md#review-adoption-and-resume). Report factory repair, PR delivery, and app adoption separately. A verified local candidate can be offered for an explicitly authorized local trial while its PR remains draft; do not describe it as released. If adoption is blocked, preserve the checkpoint and state whether the old bundle can safely continue. Resume the original app task only through its supported workflow, without initializing it again or silently changing its requirements.

## Invocation

```text
Use $improve-factory. During this build, the factory did [what happened].
It should do [expected behavior]. Preserve this app's progress, repair the
factory in isolation, and tell me what can safely resume.
```

If the skill is not discovered in the current project, ask the agent to read this full file by its absolute path. File access and actual host capabilities are prerequisites; a name alone does not install a command.
