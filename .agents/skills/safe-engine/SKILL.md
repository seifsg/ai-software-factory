---
name: safe-engine
description: "Build/resume games, apps, services and tools with Seif's methods, saved stages, final checks and independent review. Factory delivery; preserve phase-only requests."
---

# Safe Engine

Build the requested outcome. Read the complete methods. Keep decisions, work and evidence resumable.

For human-facing prose, apply [Clear Writing](references/clear-writing.md): preserve details/voice, ground claims, cut filler. One finishing pass within existing review.

Follow [tests-last order](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests): finish implementation/improvements → manual action QA → author/polish/run automated tests → final review/PR. No test writing, edits or execution during development. Carry this into delegates, repairs and resumed runs.

## Choose the scope

Analysis, planning and review requests stay in that phase. No implied coding.

For requested bounded fixes, read [Small Change](../small-change/SKILL.md) before loading the full workflow or starting a controller. Its six routines own checks, existing-run handling and scoped PR delivery. A focused handoff does not refresh full-version acceptance.

New software or substantial features use the flow below. Discover the actual domain, stack, platforms, interfaces, workload and constraints. Games, desktop/mobile/web apps, servers, libraries and tools share the method; their evidence differs.

Read [logging](references/app-diagnostics.md) and [efficiency](references/app-efficiency.md) during delivery analysis/planning. Every app/game needs working shared logging: adequate facilities/preferred provider or internal module/local sink. Discover preferences/access; log detailed successes/failures and read trails throughout development/manual debugging. Plan coverage, resource targets and evidence. Research material unknowns through [Research Market](../research-market/SKILL.md). Required logging stays surgical.

## Start or resume

Use [Application Security](references/app-security.md) from planning: cheap relevant protections now, exposure-based checks before production. Keep local MVPs simple; carry evidence into the existing security review.

Public landing/marketing/content pages meant for indexing use [Public Web SEO](../ux-quality/references/web-seo.md). Plan crawlability, metadata and production verification; preserve private/staging boundaries.

Every UI/interaction change uses [UX Quality](../ux-quality/SKILL.md) through planning, manual QA and independent review. Research uncertain patterns/assets; compare three options, justify/choose within delegation. Verify simplicity, accessibility, visuals/audio and interaction. No extra phase or automatic redesign.

New/material persistence design uses [Database Schema](../database-schema/SKILL.md) before dependent implementation: whole-product access map → three viable designs → reasoned choice → written schema → fresh audit. Preserve engine choices and routine-fix scope; pass query/migration evidence to review. No invented database or controller phase.

Resolve this bundle's root. Read [pilot usage](../../../docs/pilot-usage.md) for supported commands, profile, limits and recovery. Run from the bundle:

```text
python -m safe_engine --project <absolute-target-root> status
```

Read request, rules and [session contract](references/session-contract.md). Reuse answers/authority; discover tools before asking. No run? Preserve work in a suitable isolated checkout with clean Git baseline and ignored `.factory/`. Commit a minimal new-project baseline before initialization.

Inspect check definitions, protected acceptance files, runtime inputs and interaction tools; author/run no tests. Save original request/criteria in task JSON; map criteria to checks. Use actual browser/native/game/API/CLI interaction; screenshots cannot prove behavior. Missing setup tests: follow the [pilot limitation](../../../docs/pilot-usage.md#feature-feedback-and-version-checkpoints), never write them early. Missing tools/reserved choices block dependent work only.

Resolve acceptance-shaping unknowns before freezing task/profile where possible. Planning/research can precede initialization; record in stage order. Later plan revisions stay within accepted criteria. Changed criteria/check definitions/protected inputs require a newly reviewed task in a fresh worktree; preserve/link the old run, never patch its contract.

Initialize once. Resume the saved phase. Follow [control-route recovery](references/session-contract.md#recover-a-failed-control-route) when needed. No invented credits, retry ceilings, session deadlines or permissions. Honor real limits, checkpoints and stops.

## Follow the saved phase

Read each phase's full method/applicable references before using it. Reuse fully read, unchanged text while available; names/summaries never suffice. On resume/context loss/delegation, use [method handoff](references/method-handoff.md); receivers read methods themselves. Missing methods block their phase.

With no existing implementation, say so; analyze requirements, available platform facilities and intended consumers. Never invent code evidence. Preserve Get Ready's O(1) question as a prompt to examine workload-appropriate complexity, not a universal acceptance target; [I5](../../../docs/current-decisions.md#further-improvement-decisions) governs measured performance.

| Phase | Do |
|---|---|
| `analyze` | [Analyze Start](../analyze-start/SKILL.md): actual code, purpose, consumers, ASCII charts, verified claims and unknowns. Save analysis. No code. |
| `plan` | Compare three credible approaches for new substantive choices; recommend one under session authority. [Get Ready to Code](../get-ready-to-code/SKILL.md): five outputs, original file-summary stop unless continuation is authorized. For new software, preserve the first plan, run [research](../research-market/SKILL.md), revise all five outputs and link evidence/decisions. Research new material unknowns for existing features too. No code. |
| `build` | Get Ready's 0–4 loop for every todo: context → site analysis → apply → inspect → correct. Finish the whole requested task and worthwhile in-scope improvements. Manually exercise final behavior; fix and re-exercise defects. Only then author/polish useful tests at the final pre-PR stage and record the batch, including pre/change/post observations and manual evidence. No mid-build `feature-check`. |
| `verify` | After finished work and passing manual QA, run full configured version checks, including planned diagnostic/resource evidence. Read logs; investigate failures. Use `repair` before changing a recorded candidate. Production fixes require manual re-exercise before final tests resume. |
| `improve` | Record the improvement assessment completed before manual QA; leave sound work unchanged. Newly discovered necessary implementation work uses `repair`, then manual QA and final tests again. Do not plan development after tests. |
| `final-verify` | Full version QA on the final candidate. Reuse full evidence via `check` only with reviewed `reuse_unchanged_checks: true` and exact matching inputs, logs and outputs, including [required guidance](../../../safe_engine/bundle-inputs.json). Missing guidance blocks acceptance. Changed inputs require full checks; volatile/unresolved runtime concerns require `check --fresh`. Partial feedback never replaces full QA. |
| `review` | Fresh read-only Codex review: complete methods, diagnostics/efficiency, applicable research evidence, three themed passes plus Change Guard and Compliance. Never supply your own passing review. Repair supported findings, check corrections and obtain fresh assessment. |
| `ready` | Checked local handoff: results, diagnostic access/coverage, resource evidence, research decisions and remaining limits. Authorized PRs/updates require both [creation](../how-to-make-a-pr/SKILL.md) and separate-instance [review](../how-to-review-a-pr/SKILL.md) through the [project adapter](../../../docs/pr-workflow.md), including skill/docs PRs without controller runs. Preserve selected small/full scope and human ready/merge/release decisions. |
| `cancelled` | Stop. Preserve records and checkout. |

Keep evidence in excluded `.factory/` or equivalent. Report unverified coverage. Never edit protected acceptance files/task records to obtain a pass. Correcting an accepted task/profile requires a newly reviewed task in a fresh worktree; preserve the original run.

## Keep the work usable

Give brief batch updates. For watch/learn requests, show actual brief, criteria, chart, plan, running product and results; label historical walkthroughs. Updates grant no approval gate. Pause only for real authority/access/decision gaps, checkpoints/stops or unrecoverable required gates.

For factory faults, use [Improve Factory](../improve-factory/SKILL.md): checkpoint → isolated repair → independent review → compatible resume. No recursive delivery runs or silent upgrades. Reloaded text is not new QA.

For another host/session, read [setup](../../../docs/start-another-session.md). The current session builds; the controller records stages/checks and launches fresh read-only review. It does not provision tools, run a daemon, push, merge or deploy. Verify host capabilities and report limits. Missing PR bindings block that action, while independent local delivery continues. Bounded follow-ups use Small Change; full-version corrections retain their full acceptance requirements.
