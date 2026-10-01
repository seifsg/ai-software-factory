# Safe Engine design decisions

Seif selected these directions on 1 October 2026. **Safe Engine** is the engine name. The repository remains AI Software Factory. These are approved design choices; the engine and connected skills are not implemented yet.

The decision IDs refer to the 25-option discussion: N1–N2 cover naming, G1–G13 cover confirmed gaps, and I1–I10 cover further improvements. They do not match the numbering in the earlier 24-gap research document.

## Decision ownership

Seif owns naming and design decisions. For each new improvement or unresolved design choice, present three credible alternatives in a comparison table, recommend exactly one, and explain why. A recommendation is a proposal until Seif selects it. Preserve approved choices across sessions and reopen them only when requested or when new evidence warrants a proposed revision.

Choosing an architectural direction does not silently settle remaining language, format, host, numerical limit, or permission choices. Already authorized work can continue within the selected scope; unresolved choices stay visible.

## Skill authorship

Seif is the primary skill author. He supplies the working method in his own words and owns the final procedures. The assistant helps him examine examples, structure his writing, expose gaps and contradictions, refine wording, and test the resulting skills. Existing Seif-authored skills are the starting material; external examples provide inspiration. The assistant may prepare a specific draft when asked, but should not independently write the majority of the skill library.

Plans for skill counts, individual skill boundaries, and new skill names require Seif's selection. No new skill files are created merely to reserve proposed roles.

## Expanded capability requirements

Seif explicitly requested worktree management, assisted skill writing, planning, execution, debugging, TDD and TDD review, architecture, UX, browser QA with quick diagnosis and repair, security, product design review, and idea assessment. The TDD applicability policy remains open; the requested capability and its review must be considered in the design.

The factory must be designed to open and navigate the actual application, identify broken UI and poor user experiences, make authorized in-scope repairs autonomously, and verify the result without Seif repeatedly identifying defects. High quality includes the rendered experience and complete user journeys. Preserve Seif's product decisions and the selected human handoff/release boundaries.

The [expanded capability plan](safe-engine-expanded-scope.md) records research, source examples, packaging alternatives, individual choices E1–E14, and proposed demonstrations. These requirements expand the initial build-plan scope; they do not approve its proposed 22-core-plus-2-later count, new names, or procedural recommendations. The capabilities are not implemented yet.

## Fast development and improvement requirements

Seif subsequently specified substantial development batches, with unit and E2E verification at meaningful boundaries instead of constant test runs. Do not use per-edit or per-function test execution as the default, and do not start test watchers by default. Test-first methods remain available for deliberately selected cases; the earlier E4 recommendation is superseded where it conflicts with this cadence.

Before the feature is pushed, inspect and apply worthwhile in-scope cleanup, reuse, refactoring, performance, security, and agent-navigability improvements. Then run QA appropriate to the resulting changes and obtain the already selected fresh independent assessment. Code should prioritize accurate, efficient maintenance by AI agents over individual human style preferences. Improvement claims require suitable evidence; function or file size alone does not justify refactoring.

The [fast feature delivery design](safe-engine-fast-delivery.md) compares the remaining choices F1–F4. The optional “scale button” remains a control proposal, with its meaning, labels, depth, and packaging unselected. These directions do not settle G6, G9, names, numerical limits, or skill count.

## Naming

| ID | Selection | Approved direction |
|---|---|---|
| N1 | Safe Engine | Use this exact engine name, chosen by Seif. Earlier suggested brand names are superseded. |
| N2 | A | One engine brand with descriptive, plain-language stage and component names. The final stage vocabulary and individual skill names remain open. |

## Confirmed gap decisions

| ID | Selection | Approved direction |
|---|---|---|
| G1 | B | A small executable controller with an entry skill. Existing skills provide expertise; the controller records progress and validates transitions. |
| G2 | B | Discover each target project's configuration and propose a profile that can be reviewed and corrected. Support varied project types; surface uncertainty instead of silently guessing. Discovery does not infer permission for external actions. |
| G3 | B | A validated task record with a readable view, preserving the original request, acceptance criteria, scope, decisions, and completion boundary. |
| G4 | A | Saved checkpoints with a small history. Recover interrupted work and reconcile uncertain external actions before repeating them. |
| G5 | B | Shared gate logic called by host adapters, commands, and independent delivery checks. |
| G6 | Pending | The spoken selection was “recommended D,” but the offered choices were A–C. Clarify the intended approach to evidence freshness. |
| G7 | B | Separately controlled acceptance checks plus fresh review. Independence requires a real permission boundary around decisive checks. |
| G8 | A | One correction budget for the entire run, including nested build and review loops. Numerical limits remain open. |
| G9 | Pending | No option was supplied for skill and dependency versioning. |
| G10 | B | Project-specific scenario adapters for repeatable UI, API, or command-line checks of user outcomes. |
| G11 | B | End-to-end fault scenarios for the QA system, including a successful valid run and failures involving skipped stages, stale evidence, hooks, interruption, and exhausted retries. |
| G12 | B | A protected repository workflow as the target merge boundary. Resolve private-repository feature availability and credential configuration before claiming enforcement. |
| G13 | B | A human-approved release procedure when deployment enters scope, with deployed-version verification, health checks, and explicitly defined recovery authority. |

## Further improvement decisions

| ID | Selection | Approved direction |
|---|---|---|
| I1 | B | Record UNKNOWN and block the affected decision while allowing independent work. N/A requires a supported reason. |
| I2 | B | Seif defines the exception policy: waivable project rules, authorized decision owners, scope, and records. An explanation alone does not authorize an exception. |
| I3 | B | Separate planning and implementation into two focused skills with a defined handoff. Their names remain open. |
| I4 | B | A reviewer may make bounded repairs for supported findings, followed by a fresh independent check of the corrected revision. A clean review can finish without edits. |
| I5 | A | Judge relevant performance against workload-specific targets. Use function and file size as inspection prompts rather than automatic reasons to split code. |
| I6 | B | Require appropriate evidence for each acceptance criterion, including failure-before and success-after demonstrations where applicable. |
| I7 | B | Compare baseline and changed-version results to classify failures. Preserve all results; inherited failures still follow the exception policy. |
| I8 | B | Reproducible workspaces plus integration rechecks when relevant environment inputs or the target branch change. |
| I9 | B | Track input authority and enforce action permissions. Retrieved content supplies evidence, not new permission to act or weaken checks. |
| I10 | B | A stable benchmark plus reserved cases to compare quality across factory versions. Track missed defects, false findings, unnecessary edits, acceptance, and recovery behavior. |

## Important connections

- G2 discovers and proposes the project profile; G3 preserves the particular task's requirements. They serve different purposes.
- G1, G4, and G5 describe the controller, its saved state, and its gates. They are parts of one execution system.
- I4 permits reviewer repairs, while G7 requires fresh independent acceptance of the resulting revision. The repairer cannot independently certify its own correction.
- G10 supplies reusable scenario execution; I6 determines the evidence each task must produce.
- G11 tests whether enforcement works; I10 measures whether factory versions make better decisions and deliver better results.
- G12 and G13 are design selections. They do not themselves authorize subscription purchases, permission changes, merges, releases, or deployment to a live project.

## Relationship to earlier proposals

The [QA gap analysis](qa-enforcement-gap-analysis.md) and [skill lifecycle map](skill-lifecycle-map.md) preserve the research and original source mapping. This decision record governs selected design directions where earlier proposals differ. Earlier labels such as `factory-qa` and `factory-run` are provisional role names, not approved skill or command names.

The [skill index](../.agents/skills/README.md) remains the record of actual imported skills. Design approval must stay distinct from implementation and demonstrated behavior.
