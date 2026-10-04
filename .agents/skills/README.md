# Skill index

Keep Seif's originals and deliberate reminders. Adapt project assumptions to the actual target; compress AI-written explanations. The [source map](../../docs/skill-provenance.md) records originals and generic adaptations.

| Skill | Job | Source / dependencies |
|---|---|---|
| [analyze-start](analyze-start/SKILL.md) | Understand the feature and every use. Explain with ASCII charts. No coding. | Mobile original + three approved lines; actual source and read/search tools |
| [get-ready-to-code](get-ready-to-code/SKILL.md) | Prepare files, critique, phases, todos and plan. Define the 0–4 execution loop. | Mobile original; honor its file-summary stop and no-code planning boundary |
| [deep-review](deep-review/SKILL.md) | Find bugs, oversights, bad implementation and unnecessary complexity. | Mobile original; candidate files and surrounding code |
| [change-guard](change-guard/SKILL.md) | Check the change against existing behavior and consumers. | Mobile original; base/diff, consumers and relevant evidence |
| [compliance-check](compliance-check/SKILL.md) | Check the original request, plan and project rules against the actual result. | Original method; generic rule discovery |
| [how-to-make-a-pr](how-to-make-a-pr/SKILL.md) | Prepare a feature draft and its task/reviewer handoff. | Routines-derived generic method; [PR adapter](../../docs/pr-workflow.md) |
| [how-to-review-a-pr](how-to-review-a-pr/SKILL.md) | Capture claims, analyze, run four themes, synthesize and hand off permitted fixes. | Mobile-derived method and reminders; generic stack/bindings, original checkpoints |
| [safe-engine](safe-engine/SKILL.md) | Coordinate app delivery or resume from its saved phase. | Factory-specific; controller, complete methods, real project checks |
| [improve-factory](improve-factory/SKILL.md) | Repair the factory while preserving active app work. | Factory-specific; isolation, affected checks and independent review |
| [research-market](research-market/SKILL.md) | Research product/UX, stack, architecture and patterns; resolve material unknowns. | Factory-specific; original/revised plans for delivery, findings only for standalone research |
| [database-schema](database-schema/SKILL.md) | Map the whole product, compare three schema designs, choose, write and audit. | Factory-specific; original analysis/planning methods, real access patterns, engine constraints and scoped review |
| [ux-quality](ux-quality/SKILL.md) | Audit every UI change for simple, familiar, accessible interaction and high-quality visuals/audio. | Factory-specific; current research, three-option uncertain choices, real inspection and scoped independent review |
| [small-change](small-change/SKILL.md) | Deliver a requested bounded fix with six light routines. | Factory-specific; affected code, focused checks and narrow independent review |

Thirteen canonical skills: seven with originals, six factory-specific. Two portable entries, [Safe Engine](../../skills/safe-engine/SKILL.md) and [Improve Factory](../../skills/improve-factory/SKILL.md), load the same complete bundle. Install using their [delivery](../../docs/install-safe-engine.md) or [maintenance](../../docs/install-improve-factory.md) guide.

A direct analysis/planning/review request keeps its phase. Small Change is for requested implementation. [Mandatory logging](safe-engine/references/app-diagnostics.md) and [efficiency](safe-engine/references/app-efficiency.md) belong to the delivery coordinator; restored originals do not import them automatically. Every app/game, including small fixes, needs a working shared logger and detailed safe journey evidence; inspect logs throughout development/manual debugging.

All delivery and maintenance follows [tests-last order](../../docs/current-decisions.md#finish-work-use-it-then-automate-tests): finish work → manual action QA → write/polish/run final automated tests → review/PR. Keep bounded fixes surgical. This coordination rule preserves the original methods' wording.

The controller keeps five acceptance passes. PR review uses four themes and synthesis/compliance. These are separate workflows. Product scope includes games, apps, services and tools; discover applicable interfaces, resources and evidence.

The 38-skill source catalog is background, not 38 installed skills. [Pilot evidence](../../docs/pilot-verification.md) is dated; packaging a rewritten skill does not demonstrate a new app run.

[Clear Writing](safe-engine/references/clear-writing.md) applies to authored output: brief, natural, specific, evidenced. One shared rule; no extra skill or review stage.

[Public Web SEO](ux-quality/references/web-seo.md) covers public pages intended for search. Shared checklist from planning through verification; private/staging routes retain exclusions.

[Application Security](safe-engine/references/app-security.md) covers proportional early protections and production checks through the existing security code review.
