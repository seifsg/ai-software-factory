# Safe Engine design decisions

Seif selected these directions on 1 October 2026. **Safe Engine** is the engine name. The repository remains AI Software Factory. Safe Engine 0.1.0 implements the selected local pilot subset; the [verification record](pilot-verification.md) distinguishes demonstrated behavior from the wider approved design.

The decision IDs refer to the 25-option discussion: N1–N2 cover naming, G1–G13 cover confirmed gaps, and I1–I10 cover further improvements. They do not match the numbering in the earlier 24-gap research document.

## Decision ownership

Seif owns the outcome and may explicitly delegate in-scope product, design, technical and working-name choices for a session. Preserve approved and rejected choices; delegation does not silently reopen them. For new choices, present three credible alternatives, recommend exactly one and explain why. Under explicit delegation, record the evidence and agent selection and continue; otherwise a new substantive owner decision remains pending. A recommendation alone is not authority.

Read and apply the [session contract](../.agents/skills/safe-engine/references/session-contract.md) once at intake and on handoff. Reuse answers across the whole workflow. Full autonomy means continue to the agreed testable handoff, without artificial credits, repair allowances or session deadlines. It does not expand permissions or authorize deployment, ready/merge/release, purchases or a guessed recipient. Block only dependent work for real missing authority/evidence; continue independent authorized work.

## Skill authorship

Seif is the primary skill author. He supplies the working method in his own words and owns the final procedures. The assistant helps him examine examples, structure his writing, expose gaps and contradictions, refine wording, and test the resulting skills. Existing Seif-authored skills are the starting material; external examples provide inspiration. The assistant may prepare a specific draft when asked, but should not independently write the majority of the skill library.

Plans for broader skill counts, boundaries and names remain pending unless selected or explicitly delegated. A request to create a specific procedure authorizes that focused draft and a descriptive working name within delegation. No new skill files are created merely to reserve proposed roles.

## Expanded capability requirements

Seif explicitly requested worktree management, assisted skill writing, planning, execution, debugging, TDD and TDD review, architecture, UX, browser QA with quick diagnosis and repair, security, product design review, and idea assessment. The TDD applicability policy remains open; the requested capability and its review must be considered in the design.

The factory must be designed to open and navigate the actual application, identify broken UI and poor user experiences, make authorized in-scope repairs autonomously, and verify the result without Seif repeatedly identifying defects. High quality includes the rendered experience and complete user journeys. Preserve Seif's product decisions and the selected human handoff/release boundaries.

The [expanded capability plan](safe-engine-expanded-scope.md) records research, source examples, packaging alternatives, individual choices E1–E14, and proposed demonstrations. These requirements expand the initial build-plan scope; they do not approve its proposed 22-core-plus-2-later count, new names, or procedural recommendations. The broader specialist library remains to be coauthored and verified.

## Fast development and improvement requirements

Seif subsequently specified substantial development batches, with unit and E2E verification at meaningful boundaries instead of constant test runs. Do not use per-edit or per-function test execution as the default, and do not start test watchers by default. Test-first methods remain available for deliberately selected cases; the earlier E4 recommendation is superseded where it conflicts with this cadence.

Before the feature is pushed, inspect and apply worthwhile in-scope cleanup, reuse, refactoring, performance, security, and agent-navigability improvements. Then run QA appropriate to the resulting changes and obtain the already selected fresh independent assessment. Code should prioritize accurate, efficient maintenance by AI agents over individual human style preferences. Improvement claims require suitable evidence; function or file size alone does not justify refactoring.

The [fast feature delivery design](safe-engine-fast-delivery.md) compares the remaining choices F1–F4. The optional “scale button” remains a control proposal, with its meaning, labels, depth, and packaging unselected. G6 and G9 were subsequently resolved for the pilot below; broader names, numerical limits, and skill counts remain separate decisions.

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
| G6 | A, pilot clarification | Bind evidence to exact project code, check definitions, and declared environment inputs. Invalidate it when those inputs change. Seif explicitly selected this pilot option on 1 October 2026, resolving the earlier ambiguous spoken answer. |
| G7 | B | Separately controlled acceptance checks plus fresh review. Independence requires a real permission boundary around decisive checks. |
| G8 | Superseded 2 October by Seif | Continuous progress through maintenance and nested build/review loops; no artificial credits, numerical correction allowance, fixed retry ceiling or overall session deadline. Keep diagnostic history and require meaningful corrections. Earlier finite-budget decisions and consumed counts remain historical. |
| G9 | A | One versioned repository bundle containing controller, skills, and adapters. Seif explicitly selected this option on 1 October 2026. |
| G10 | B | Project-specific scenario adapters for repeatable UI, API, or command-line checks of user outcomes. |
| G11 | B | End-to-end fault scenarios for the QA system, including a successful valid run and failures involving skipped stages, stale evidence, hooks, interruption, cancellation, continuous corrections and rejected unchanged rerolls. |
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

On 2 October Seif required **how-to-make-a-pr** and **how-to-review-a-pr** to execute for every factory-managed PR, in all projects, with no workflow bypass. Adapt project-specific content into real project bindings while preserving the full method. This explicitly authorizes importing those two existing procedures, not independently writing the wider skill library. The local candidate review is not a substitute for the full separate-instance PR review. Missing bindings/access remain blockers. See [PR workflow and pending bindings](pr-workflow.md).

Seif selected an initial local Codex pilot with a small Python controller, JSON task records, his existing methods, and one Safe Engine entry skill, demonstrated on a disposable web application. This authorizes the pilot implementation and its small coordinating skill; Seif remains the primary author of the wider library. The first bundle uses existing skill names and the selected Safe Engine brand. Detailed specialist modules and their names remain open.

- G2 discovers and proposes the project profile; G3 preserves the particular task's requirements. They serve different purposes.
- G1, G4, and G5 describe the controller, its saved state, and its gates. They are parts of one execution system.
- I4 permits reviewer repairs, while G7 requires fresh independent acceptance of the resulting revision. The repairer cannot independently certify its own correction.
- G10 supplies reusable scenario execution; I6 determines the evidence each task must produce.
- G11 tests whether enforcement works; I10 measures whether factory versions make better decisions and deliver better results.
- G12 and G13 are design selections. They do not themselves authorize subscription purchases, permission changes, merges, releases, or deployment to a live project.

## Factory maintenance — 2 October 2026

Seif authorized a dedicated skill to evolve the factory from his feedback while preserving its integrity, selected **`improve-factory`**, and selected mid-build option **A**. He remains the author of the intended procedures; this request authorizes this specific draft, not independent expansion of the library.

| Decision | Alternatives compared | Selection and reason |
|---|---|---|
| Structure | A dedicated maintenance skill; B maintenance mode in Safe Engine; C hook-triggered maintenance | A, authorized after the recommendation: focused scope, reuse of existing methods, explicit handback |
| Name | `maintain-factory`; `repair-factory`; `improve-factory` | `improve-factory`, explicitly selected by Seif, emphasizing evolving the workflow |
| Mid-build behavior | A checkpoint and isolated repair, independent work only; B continue with pinned old bundle until later adoption; C sequential parent repair with separate review | A, explicitly selected: checkpoint → isolated repair → review → compatible resume |

The procedure preserves dirty app/bundle state, reads full routines, delegates with an explicit context packet where available, and treats adoption as a compatibility/evidence decision. The current controller has no pause or migration command. New schemas/contracts or invalidated analysis can require a reviewed run in a fresh app worktree; acceptance and cancellation cannot be reset to bypass a failure. Human ready/merge/release remains unchanged.

Model routing is not newly configured by this skill. It preserves existing user/host settings and records actual capabilities. For a future routing change, compare these options; no new routing policy is selected here:

| Option | Benefit | Tradeoff |
|---|---|---|
| A — recommended: inherit the configured session model | Preserves the user's current choice; straightforward first version | Does not optimize each role separately |
| B — user-approved models by role | Can balance diagnosis/review quality and bounded lookup cost | Requires available-model checks and representative evaluations |
| C — user chooses a model for each maintenance case | Maximum direct control for unusual cases | Interrupts routine repairs and adds repeated decisions |

Recommendation: A for the first version. Capability comes from observed tools, context and verification, not an assumed model name. Existing host instructions still govern actual spawning; there is no provider switch, installed model router or guarantee of the same model across hosts.

## Autonomous execution and market research — 2 October 2026

Seif reported that the factory stopped unnecessarily and explicitly requested autonomous execution for this session through a finished local application with factory QA and independent review, ready for his initial testing. Deployment remains excluded; human ready/merge/release stays reserved. He asked for essential preferences once at intake when needed, persistent decisions, discovery and researched options before escalation. This clarification supersedes earlier wording that every numerical limit or substantive choice needs a new owner answer even after delegation.

For new applications he selected **original plan → market/competitor research → revised plan** before implementation, protecting original creativity while learning from existing products, features and visual experiences. He authorized creation of the missing focused skill now. `research-market` is its descriptive working name under that delegation, not a user-selected permanent brand. Research evidence and names must support the product; the rejected app name stays rejected. All three steps fit inside the existing controller `plan` phase; no new stage/schema or autonomous service is implemented.

## Continuous execution correction — 2 October 2026

Seif explicitly corrected the allowance/exhaustion premise: “There are no allowances, no credits, and AI should prompt as long as it needs to achieve something.” This supersedes earlier G8 finite safeguards and the source PR retry-once ceiling for current operation. Keep former counts/limits in history; never ask to replenish them. Continue authorized meaningful corrections to the agreed verified handoff, honor explicit owner checkpoints/cancellation, and preserve fresh QA, separate review and human ready/merge/release. Actual provider quotas, unavailable access and individual process watchdogs remain real constraints; no unlimited compute, daemon or host enforcement is claimed. The canonical session contract owns discovery, stalled-progress diagnosis and reconciliation before uncertain external actions are retried.

## Reusable maintenance entry — 2 October 2026

Seif explicitly requested a GitHub-installable `improve-factory`, commit/push of the latest work, and a completion notification to himself through Slack or Zoho. This authorizes packaging and delivery within the existing maintenance scope. Three approaches were compared: A, a small portable launcher loading the complete pinned bundle; B, embedding a second complete factory copy; C, host-specific plugin packaging. A is selected under the request's implementation delegation because it preserves one canonical procedure and supports ordinary skill installation. Existing active runs retain their recorded bundle; new cases resolve one revision and keep it through repair. No automatic upgrade, hook, merge, release or universal cloud compatibility is implied. Seif's Slack DM is authorized for this completion notification; permanent project tracker and formal review bindings remain unresolved.

## Feature batches and version checkpoints — 2 October 2026

Seif requested less running prose, substantial completed feature batches with feature-focused tests, and comprehensive version checkpoint QA. Under his existing full autonomy, the maintenance design compares external ad-hoc subset commands, additive controller feedback/version gates, and a dependency scheduler; the additive approach is recommended and selected within scope. `feature-check` remains in build and cannot satisfy version acceptance. The full configured version suite, complete improvement method, fresh independent review and both PR procedures remain mandatory. Exact unchanged full-gate reuse is an explicit immutable reviewed-profile opt-in for controlled declared runtime inputs; legacy profiles remain uncached. No automatic dependency graph, watcher, model router, depth control, ready/merge/release or deployment authority is introduced. Complete methods stay durable; owner updates focus on outcomes and meaningful boundaries. Independent assessment/adoption/PR evidence remains separate from implementation.

## Runtime control recovery and exit UX — 3 October 2026

Seif reported that Wispdock's unsent thought blocked Quit and that the factory handed him a UI window-discovery problem. He explicitly authorized Windows commands or computer use to stop this app and fix it, and requested the lesson be preserved in skills/rules with continued research when stuck. This authority is specific to the app/task; it does not authorize unrelated process termination, security changes, evading tool restrictions or silent loss of other private work.

Three approaches were compared: A, clarify recovery in the existing session contract and route the entry/rules plus existing UX lens; B, add a platform recovery skill; C, implement a controller process registry/stop command. A is recommended and selected under this repair delegation: the observed gap is instruction routing and an application exit journey, with no demonstrated controller defect. The canonical contract now distinguishes one failed route from the outcome, discovers permitted CLI/API alternatives, preserves exact-target/state/authority checks, requires observed exit/resource release and meaningful researched corrections. The existing user-journey lens covers explainable preservation failures and accessible exit. No new skill, global memory synchronization, automated stop service or guarantee of recovery is introduced. Current app progress, complete methods, fresh acceptance, paired PR procedures and human ready/merge/release/deployment remain preserved.

## Relationship to earlier proposals

The [QA gap analysis](qa-enforcement-gap-analysis.md) and [skill lifecycle map](skill-lifecycle-map.md) preserve the research and original source mapping. This decision record governs selected design directions where earlier proposals differ. Earlier labels such as `factory-qa` and `factory-run` are provisional role names, not approved skill or command names.

The [skill index](../.agents/skills/README.md) remains the record of actual imported skills. Design approval must stay distinct from implementation and demonstrated behavior.

## Reusable factory entry — 3 October 2026

Seif clarified that the emailed improvement guide did not install the app-building factory. He explicitly requested Safe Engine itself as a regular reusable skill. Under this packaging request, three alternatives were assessed: A, a standalone adapter resolving the complete immutable bundle; B, embedding the whole factory in each installation; C, host-specific plugin packaging. A is recommended and implemented because it preserves the existing canonical procedures, supports ordinary skill installation and avoids a second maintained library. The existing selected Safe Engine name is preserved.

Install `skills/safe-engine` from merged `main`; invoke `$safe-engine` in Codex or `/safe-engine` in a configured Claude Code installation. Both portable resolvers are derived from one owner, `safe_engine/distribution.py`, with a drift-check gate. New app selections are recorded separately in excluded `.factory/entry-bundle.json`; resume uses the established path/revision offline. Legacy runs without that record require their original bundle identity, not latest substitution. Receipt selection does not certify QA, authorize upgrades or migrate controller state. Older app pins and historical distribution references remain valid.

The earlier explicit-path recommendation remains an alternative, superseded for normal cross-project use by this authorized installation. The maintenance entry is optional as a separate install; the full bundle includes its canonical procedure. Native Claude-builder and cloud executions remain unverified; the current independent review requires Codex CLI. Direct merge/email instructions govern this delivery only; permanent task/formal-reviewer bindings remain unresolved.
