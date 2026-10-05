---
name: improve-factory
description: "Repair Safe Engine skills, controller or workflow. Preserve project progress; isolate repairs and obtain independent review. Product bugs stay in delivery."
---

# Improve Factory

Fix the factory cause. Preserve Seif's methods and project progress.

Use [Working iterations](../safe-engine/references/delivery-readiness.md#working-iterations). Complete useful correction first. Repeated failure: shared cause, prior-fix failure, prevention. Audit time from existing logs; no extra reporting gate.

New factory implementation uses [Ticketing](../ticketing/SKILL.md): canonical tracker, owner-confirmed before/after and a dedicated maintenance session. Every ticket follows the complete methods below. [Small Change](../small-change/SKILL.md) keeps bounded repairs surgical; its six shortcuts remain for legacy unticketed work. Analysis/planning stays in phase and creates no coding obligation.

Factory-wide routing, acceptance or interacting procedures need maintenance analysis and a final independent behavioral exercise. Choose prospective validation before initialization: instruction changes need actual instruction use and fitting structural checks; runtime/config/policy changes need affected behavioral proof. Mixed changes cover both. Check affected consumers, skip unrelated suites; retain required saved gates. One case, one local final assessment; authorized PR review remains separately remote/cloud. No recursive maintenance.

Active build: `checkpoint → isolated repair → independent review → compatible resume`. Parallel project work must be independent of the fault/repair. No hook or upgrade service is installed.

## Understand the report

Record report, expected behavior, example, artifacts, source, commands and factory version in the authorized ticket or phase artifact. Implementation uses the canonical ticket. Prefer the owner's chosen MCP; GitHub Issues is Seif's current choice/default. Reuse authority/choices under the [session contract](../safe-engine/references/session-contract.md); confirm missing outcome scope, ask only consequential gaps.

Resolve factory/target roots separately. Read both projects' rules, [approved decisions](../../../docs/current-decisions.md) and working status.

| Cause | Action |
|---|---|
| Instruction skipped | Recover step; inspect invocation/handoff before adding rules. |
| Skill unclear/incomplete | Fix canonical owner and callers. |
| Controller/adapter faulty | Diagnose from source/existing evidence; fix that layer. Reproduction tests wait until the final stage. |
| Missing tool/access/decision | Record blocker; invent nothing. |
| Product bug | Return to delivery unless evidence also shows a factory defect. |

Active run: execute [live-session maintenance](references/live-session.md) before workspace changes/delegation. Preserve the app ticket/run separately from the maintenance ticket; factory repair grants no product scope change. Otherwise use an isolated factory branch/worktree; no resume needed. Never silently stash, reset, switch or upgrade the target.

## Prepare the correction

1. Execute [Analyze Start](../analyze-start/SKILL.md): source/consumers, flow, evidence versus claims/unknowns, planned smallest final reproduction. Unobserved failure stays unverified. No coding or testing.
2. Record changes and invariants: project goal, selected decisions, complete routines, fresh evidence, continuous progress, owner stops, human release. Changing these invariants needs the user's decision. Never weaken failed acceptance.
3. New substantive choice: compare three credible options; recommend one. Preserve approved choices. Proceed with delegated choices/restoring agreed behavior; wait on owner-reserved choices. Exclude unrelated improvements.
4. Execute [Get Ready to Code](../get-ready-to-code/SKILL.md): files, critique, phases, todos, full plan. Honor file-summary stop unless existing authority covers continuation. Include reproduction, behavioral checks, consumers, before/after evidence, compatibility and safe resume.

## Repair and check

One writer owns the isolated candidate; project coordinator owns project changes/state. Independent tickets use separate worktrees; a shared maintenance epic checkout is serial with separate histories. Assign paths/tools: delegation gives no isolation. Active runs use the live-session delegation contract.

Apply Get Ready's full 0–4 loop and pre/change/post inspection per todo. Use Skill Creator for skill edits; if unavailable, retain structural/behavioral checks and disclose the limit.

Fix canonical cause and affected consumers, index, provenance, usage/preview. No duplicate procedures or universal rules for isolated complaints.

Changed procedure inputs: update [input contract](../../../safe_engine/bundle-inputs.json) and consumer map. Required files detect deletion; declared trees discover added code/guidance. Read [pilot usage](../../../docs/pilot-usage.md) for fingerprint/external-input limits. Preserve the whole candidate too; fingerprints cover a different boundary.

[Tests last](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests): finish repair/consumers → final manual use (realistic agent walkthrough for instructions) → only after manual QA passes, author/polish regressions and run relevant final checks. No manual reproduction, walkthroughs, test files or suites during implementation. Source inspection/existing-log reading remain allowed. Syntax/word matching cannot replace use. Preserve failure/candidate evidence; choose relevant [scenarios](references/validation-scenarios.md), no automatic full suite.

Execute [Deep Review](../deep-review/SKILL.md), [security](../deep-review/references/theme-security.md), [performance](../deep-review/references/theme-performance.md), [user-journey](../deep-review/references/theme-user-journey.md), then [Change Guard](../change-guard/SKILL.md) and [Compliance Check](../compliance-check/SKILL.md). Check correction and preserved behavior; evidence must support quality/performance claims.

Separate instance: freshly assess exact candidate from raw evidence/context, no prescribed verdict. Reviewer repairs need fresh assessment; missing independence blocks acceptance. Changed gates also need old rule/reproduction and independent assessment; their own pass proves too little.

Across retries/delegates, preserve meaningful corrections, diagnostic history, uncertain-effect reconciliation and permitted alternatives. No invented credits/deadlines/retry ceilings or fresh-run bypass. Missing authority/access blocks dependent work only.

## Deliver and resume

When ticketed, refresh the maintenance ticket before final acceptance/handoff and authorized PR work. Compare latest confirmed criteria with the correction, preserved behavior, final evidence and limits. Record decisions/scope changes in canonical activity; use reviewed amendments for legitimate rebinds. Pending changes, drift or failed refresh block dependent acceptance.

Authorized PR work: execute [creation](../how-to-make-a-pr/SKILL.md), remote/cloud [review](../how-to-review-a-pr/SKILL.md) and [project adapter](../../../docs/pr-workflow.md). Fresh context and remote execution required; local validation/subagents cannot replace PR review. Discover task/owner/notification bindings before asking; missing bindings block PR completion, not local repair/final testing. Keep draft status and human ready/merge/release decisions. Publish approved factory source to main only after actual cloud review and authorized merge; preserve active pins.

Give brief before/after. Maintain one ignored work record from analysis through handoff; all five plan outputs, 0–4 notes and proof links. Keep required immutable controller snapshots/raw evidence separately; no duplicate narrative. Carry:
- Report, expected result, reproduced cause/unknown.
- Canonical maintenance ticket, original/current confirmed scope and owner source, revision/digest, meaningful activity, latest refresh and criterion proof/deviations. Local record is cache/evidence, not a second tracker.
- Approved/pending choices, invariants, methods read, analysis, plan.
- Active app checkpoint; exact old/new commits; dirty manifest/diff; evidence; actual reviewer identity.
- Checks/limits, diagnostic progress, constraints, blockers, PR links.
- Adoption, compatibility, rollback destination, responsible agent, exact resume step.

Verify private records are excluded, e.g. `.factory/maintenance/<unique-id>/`; preserve controller artifacts alongside. Share minimal sanitized evidence. Receipts neither enforce host behavior nor execute controller commands.

Active work: execute [review, adoption and resume](references/live-session.md#review-adoption-and-resume). Report repair, PR delivery and adoption separately. Authorized verified local trials may use unreleased drafts. If adoption blocks, preserve checkpoint; state whether old bundle can continue. Resume original supported workflow; never reinitialize or silently change requirements.

## Invoke

Other projects/hosts need the [portable entry](../../../docs/install-improve-factory.md) and complete bundle.

`$improve-factory The factory did [observed behavior]; expected [result]. Preserve project progress, repair in isolation, and report the safe resume step.`

If discovery fails, read this whole file by absolute path. File access and host tools remain required.
