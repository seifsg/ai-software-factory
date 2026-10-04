---
name: improve-factory
description: "Repair Safe Engine skills, controller, or workflow from feedback. Preserve active project work; repair in isolation and obtain independent review. Ordinary product bugs stay in delivery."
---

# Improve Factory

Fix the reported factory cause; preserve the user's methods and project progress.

For a bounded instruction/helper fix, read [Small Change](../small-change/SKILL.md). Its six routines replace the full methods below; checkpoint, isolation, consumer updates and adoption rules still apply. Analysis/planning requests stay in that phase.

Factory-wide routing, acceptance or interacting procedures need maintenance analysis and an independent behavioral exercise. Check affected consumers; skip unrelated suites. Keep one case and one final independent assessment; combine with PR review when scope permits. No recursive maintenance.

Active build: `checkpoint → isolated repair → independent review → compatible resume`.

Parallel project work must be independent of the fault and repair. No hook or upgrade service is installed.

## Understand the report

Record the report, expected behavior and example; find artifacts, source, commands and factory version. Read the [session contract](../safe-engine/references/session-contract.md); reuse authority and choices. Ask only for consequential missing facts/decisions.

Resolve factory and target roots separately; read both projects' rules, [approved decisions](../../../docs/current-decisions.md) and working status.

| Cause | Response |
|---|---|
| Existing instruction skipped | Recover that step; inspect invocation/handoff before adding rules. |
| Skill unclear/incomplete | Fix its canonical owner and callers. |
| Controller/adapter faulty | Reproduce and fix that layer. |
| Tool/access/decision missing | Record the blocker; invent nothing. |
| Product bug | Return to delivery unless evidence also shows a factory defect. |

For active runs, execute [live-session maintenance](references/live-session.md) before changing either workspace or starting delegates. Otherwise use an isolated factory branch/worktree without resume. Never silently stash, reset, switch or upgrade the target checkout.

## Prepare the correction

1. Execute [Analyze Start](../analyze-start/SKILL.md): read source/consumers, chart flow, distinguish evidence, claims and unknowns, and reproduce the smallest relevant case. Unobserved failure stays unverified. No coding during analysis.
2. Record changes and invariants: project goal, selected decisions, complete routines, fresh evidence, continuous progress, owner stops and human release. Changing these requires the user's decision. Weakening failed acceptance is not repair.
3. For new substantive choices, compare three credible options; recommend one. Preserve approved choices. Delegated choices and fixes restoring agreed behavior proceed; owner-reserved choices wait. Exclude unrelated improvements.
4. Execute [Get Ready to Code](../get-ready-to-code/SKILL.md): files, critique, phases, todos, complete plan. Honor its file-summary stop unless existing authority covers continuation. Include reproduction, behavioral checks, consumers, before/after evidence, compatibility and safe resume.

## Repair and check

One writer owns the isolated factory candidate; the project coordinator owns project changes/state. Assign paths/tools explicitly: delegation gives no isolation. Active runs use the live-session delegation contract.

Apply Get Ready to Code's full 0–4 loop and pre/change/post inspection to every todo. Use Skill Creator for skill edits; if unavailable, preserve structural/behavioral checks and report the limitation.

Fix the canonical cause. Update consumers, index, provenance and affected usage/preview statements. Avoid duplicate procedures and universal rules for isolated complaints.

For changed procedure inputs, update the [input contract](../../../safe_engine/bundle-inputs.json) and consumer map. Required files detect deletion; declared trees discover added code/guidance. Read [pilot usage](../../../docs/pilot-usage.md) for fingerprint/external-input limits. Also preserve the whole candidate; fingerprints cover a different boundary.

Follow [tests-last order](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests). Finish all repair/consumer edits, then manually use the changed behavior; instruction changes need realistic agent walkthroughs. Only after that passes, author/polish automated regressions and run relevant final checks. No test files or suites during repair. Syntax/word matching cannot replace manual use. Preserve failure/candidate evidence; select relevant [validation scenarios](references/validation-scenarios.md) without an automatic full suite.

Execute [Deep Review](../deep-review/SKILL.md), its [security](../deep-review/references/theme-security.md), [performance](../deep-review/references/theme-performance.md) and [user-journey](../deep-review/references/theme-user-journey.md) lenses, then [Change Guard](../change-guard/SKILL.md) and [Compliance Check](../compliance-check/SKILL.md). Verify correction and preserved behavior. Evidence must support quality/performance claims.

Get a separate instance's fresh assessment of the exact candidate, supplying raw evidence/context without prescribing a verdict. Reviewer repairs need fresh assessment; missing independent execution blocks acceptance. Changed gates also need the old rule/reproduction and independent assessment; their own passing output is insufficient.

Across retries/delegates, preserve meaningful corrections, diagnostic history, uncertain-effect reconciliation and permitted alternatives under the session contract. No invented credits/deadlines/retry ceilings or fresh-run bypass. Missing authority/access blocks dependent work only.

## Deliver and resume

For authorized PR work, execute [creation](../how-to-make-a-pr/SKILL.md), separate-instance [review](../how-to-review-a-pr/SKILL.md) and the [project adapter](../../../docs/pr-workflow.md); local validation cannot replace them. Discover actual task/owner/notification bindings before asking. Missing bindings block PR completion, not local repair/testing. Keep draft status and human ready/merge/release decisions.

Give a brief before/after. Save one maintenance record:
- Report, expected result, reproduced cause or unknown.
- Approved/pending choices, invariants, methods read, analysis and plan.
- App checkpoint if active; exact old/new commits; dirty manifest/diff; evidence and actual reviewer identity.
- Checks/limits, diagnostic progress, real constraints, blockers and PR links.
- Adoption, compatibility, rollback destination, responsible agent and exact resume step.

Verify the private record directory is excluded, e.g. `.factory/maintenance/<unique-id>/`; preserve controller artifacts alongside it. Share minimal sanitized evidence. Receipts neither enforce host behavior nor execute controller commands.

For active work, execute [review, adoption and resume](references/live-session.md#review-adoption-and-resume). Report repair, PR delivery and adoption separately. Authorized verified local trials may use unreleased draft candidates. If adoption is blocked, preserve the checkpoint and state whether the old bundle can continue. Resume the original supported workflow; never reinitialize or silently change requirements.

## Invoke

Other projects/hosts use the [portable entry](../../../docs/install-improve-factory.md) and complete factory bundle.

`$improve-factory The factory did [observed behavior]; expected [result]. Preserve project progress, repair in isolation, and report the safe resume step.`

If discovery fails, read this whole file by absolute path. File access and host tools remain required.
