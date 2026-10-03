# Skill sources and adaptations

## Current source map — 3 October 2026

Seif requested a repository-wide pass: use his originals, with RepairCheck Mobile first, and write skills without originals in the same direct style. These are the current sources. Earlier adaptation records below are history where this selection supersedes them.

| Factory file | Original in RepairCheck Mobile |
|---|---|
| `analyze-start/SKILL.md` | `.cursor/rules/analyze-start.mdc` + the three approved purpose/evidence/PR-wiring lines |
| `get-ready-to-code/SKILL.md` | `.cursor/rules/get-ready-to-code.mdc` |
| `deep-review/SKILL.md` | `.cursor/skills/deep-review/SKILL.md` |
| `change-guard/SKILL.md` | `.cursor/skills/change-guard/SKILL.md` |
| `compliance-check/SKILL.md` | `.cursor/skills/compliance-check/SKILL.md` |
| `how-to-review-a-pr/SKILL.md` | `.cursor/skills/pr-review/SKILL.md`; existing factory name retained for callers |

Factory paths above are relative to `.agents/skills/`. Mobile source: `Repaircheck/repaircheck_mobile`, commit `8ed32a10034bd78660f761685b81cdd881188c85`, branch `main`.

`how-to-make-a-pr` uses `Repaircheck/claude-routines`, commit `cbd252632f0218fa2a12161e91282da013c73839`, `.claude/skills/how-to-make-a-pr/SKILL.md`. Mobile's `release-pr` was inspected first: it prepares production release rollups, bumps versions and consolidates changelogs. It is a different task from ordinary feature-draft creation, so it was not substituted into that route.

### Packaging changes only

- Keep valid Codex metadata. Cursor rule files receive `name` and `description`; the Mobile PR skill keeps its body under the existing factory name.
- Analyze Start retains its three explicitly approved additions. No Small Change redirect, app-default requirements or provenance link is appended.
- Compliance gets a short adapter note for actual target rule locations. Each PR entry links the project-binding adapter. Original company/stack wording stays visible; it does not become the target project's settings.
- Replace Cursor `mdc:` links with bundled relative paths. PR analysis and execution links use canonical Analyze Start and Get Ready to Code.
- Mobile's performance, security and user-journey rubrics stay at the existing `deep-review/references/` paths. Its change-guard, synthesis and comment references live under `how-to-review-a-pr/references/`.
- Copy the four required Mobile rule files unchanged into `how-to-review-a-pr/references/mobile-rules/`. These are source-project context; actual target rules take precedence through the adapter.
- The separate PR body reference points to the original creation skill's template instead of maintaining a second rewritten template.

The Mobile PR workflow has four themed reviewers, synthesis, a question gate, scoped fixes and push/comment checkpoints. It does not contain the old routines review's three-option phase or retry-once rule. Any old summary inside the restored creation original is superseded by the actual Mobile review file and the [PR adapter](pr-workflow.md). The local controller's five acceptance passes remain a separate workflow.

### Skills without originals

`safe-engine`, `improve-factory`, `research-market` and `small-change` are factory-specific procedures based on Seif's requests. Their bodies, six factory references, two portable loading entries and project adapter were rewritten in direct instructions. Keep the task, priorities, outputs, necessary steps/checks and stopping point. Preserve commands, authority, evidence and recovery requirements.

Source checkouts stay unchanged. The remaining source library is not imported by this pass. Current docs and callers are reconciled; dated design records, tests, example apps and recorded screenshots are retained according to their actual purpose. This local revision is not a new release or refreshed historical app QA.

## Mobile original wording — 3 October 2026

Seif selected the originals in `Repaircheck/repaircheck_mobile` as the drafting baseline for `analyze-start`, `get-ready-to-code` and `deep-review`. The source checkout is at `8ed32a10034bd78660f761685b81cdd881188c85` (`main`); the three files also match the fetched `dev` tip. Analysis and planning originate in `.cursor/rules/analyze-start.mdc` and `.cursor/rules/get-ready-to-code.mdc`; review originates in `.cursor/skills/deep-review/SKILL.md`, mirrored unchanged under `.claude/skills/`.

The first revision changed only `analyze-start`, retaining the Mobile body and three approved lines. Seif then removed its Small Change, diagnostics, efficiency and provenance links. The whole-repository pass above now extends source restoration to the other skills. The earlier routines-based draft and the adaptation history below do not override the current source map.

## Earlier factory history

On 2 October Seif explicitly requested that `improve-factory` be reusable from GitHub in other agent sessions, pushed, and announced to him through an authorized notification. The assistant added `skills/improve-factory` as a portable loading adapter plus a standard-library resolver; the complete procedure remains under `.agents/skills/improve-factory`. No source skill was replaced or copied into a second procedure. The resolver and installation layout are new implementation under that request; native Claude/cloud execution still requires separate demonstration.

Seif identifies the source collection as his own work, with AI assistance in writing and committing. Source: `Repaircheck/claude-routines`, commit `449e1110104b6ac27aed3a940c5ed6d1bf671f11`, under `.claude/skills/`.

The pilot adapts `analyze-start`, `get-ready-to-code`, `deep-review`, `change-guard`, and `compliance-check`. On 2 October Seif explicitly required the complete `how-to-make-a-pr` and `how-to-review-a-pr` procedures for every project, authorizing their generic adaptation. Those two entrypoints and their body/comment/synthesis resources are now packaged. The three lens references remain canonically under `deep-review/references/`, originating from `how-to-review-a-pr/references/`; both reviewers link them rather than duplicate them. The original source checkout has not been modified.

The assistant-authored addition is the small `safe-engine` coordinator authorized for this pilot. The substantive analysis, planning, execution, and review methods remain Seif's work. The wider specialist library is still to be coauthored.

On 2 October Seif authorized a dedicated factory-maintenance skill, selected the name `improve-factory`, and selected checkpoint → isolated repair → independent review → resume, with parallel app work only when demonstrably independent. The assistant drafted this specific requested skill from that discussion, reusing the canonical methods rather than replacing them. Its live-session reference records the provider documentation consulted and the current controller's actual recovery constraints. Structural/behavioral validation, an actual app adoption, and complete PR delivery are distinct evidence categories; creation alone proves none of the latter outcomes.

Adaptations implement selected decisions: real project context replaces fixed repository/language assumptions; unknown applicability cannot silently become N/A; exceptions need authority; correction loops follow Seif's 2 October continuous-progress correction, retaining diagnostic history and actual boundaries; performance depends on the workload rather than universal O(1); file/function lengths prompt inspection rather than forced splits; tests run in substantial batches; reviewer repairs require fresh assessment. A clean review is valid.

Frontmatter descriptions are shortened and YAML-quoted for reliable discovery. The original five planning artifacts, no-code analysis phase, ASCII charts, consumer mapping, per-todo 0–4 loop, and complementary quality/regression/requirements reviews remain.

## PR procedure preservation

| Source behavior | Factory adaptation |
|---|---|
| Dev-default remote discovery; no-dev fallback; explicit paired hotfix | Preserved; actual project topology replaces RepairCheck repository names and precedent PR numbers |
| Recovery from a wrong PR base | Retarget only after verifying a focused diff, or fresh correct-base branch with selective cherry-picks and a cross-linked replacement; no force-push; closure needs authority |
| Task dedup on two axes, reverse links, exact Development done status | Preserved through a resolved tracker/status binding; not silently replaced by local state or made optional |
| Narrow routine-only task exception | Preserved only for a proven designated routine repository and routine-only diff; controller/app/docs work is not automatically exempt |
| Named reviewer, immediate GitHub request and notification, urgent reminders | Preserved outcomes; actual owner/destination/authority replaces company names, accounts and channel IDs; missing binding stays blocked |
| Attribution, Why, visual-first full context, before/after, adjustment history, observability | Preserved in generic body template; headings follow the target project's professional style; no fabricated originating threads |
| Separate reviewer; original goal → analysis → three options → plan → execute → five passes → verdict → retry once → build → additive push → detailed comment | All ordered methods are assessed even when no repair is warranted; the source retry-once ceiling is superseded by Seif's explicit 2 October no-exhaustion instruction |
| Three options automatically chosen by autonomous reviewer | Seif's decision-ownership/session-contract rule governs: explicitly delegated in-scope choices and authorized repairs can proceed; owner-reserved choices stay pending |
| `~O(1)` and unrestricted repair loops | Approved workload targets and batched QA govern; Seif explicitly removed numerical retry/repair/session ceilings on 2 October. Meaningful diagnosis, fresh acceptance and actual authority remain required |
| Security/performance/journey rubrics | Existing generic rubrics reused; locale and technology examples are contextual, not fixed project requirements |
| Fixing reviewer produces final verdict | Seif's selected fresh-assessment requirement applies after repairs; a repairer cannot independently certify its own changes |
| No force-push; sign if required; draft remains human-owned | Preserved; retrospective corrections do not rewrite earlier commits |

The English adaptation removes product-specific bindings, not the workflow. A host that cannot execute the separate review reports a blocker. No universal hook, global installation, protected merge gate or completed external integration is implied.

On the same day Seif emphasized that his complete routines must be supplied and followed across sessions. A direct source-versus-factory diff of the five earlier imports confirmed that their substantive analysis, planning and review bodies remain, with the approved changes described above. The coordinator now explicitly requires reading each full file, preserves the three-alternative comparison before planning, and carries decisions/artifacts/limits into resumes and delegates. Its [method handoff](../.agents/skills/safe-engine/references/method-handoff.md) links every canonical owner. The local review prompt now supplies `get-ready-to-code` as well as the analysis/review skills and explicitly requests all five review passes. These changes do not retroactively re-certify the first demonstration.

On 2 October Seif explicitly requested persistent session autonomy and a new-application original plan → market research → revised plan sequence, including competitors, strong features and visual evidence. The assistant drafted the focused `research-market` skill from that request using Skill Creator and corrected canonical autonomy instructions plus actual consumers. Its name is a descriptive working choice under delegation. No external skill or competitor asset was imported. Controller stages, schema, acceptance and paired PR procedures are preserved. Structural, independent behavioral, actual app adoption and PR evidence must still be reported separately.

On 2 October Seif requested concise progress and complete feature batches with affected feedback followed by comprehensive version QA. The assistant used Skill Creator to update the existing coordinator and execution cadence from that request; no new skill/source assets were imported. Partial feedback does not weaken version acceptance. Explicit controlled unchanged full-gate reuse, default-conservative legacy profiles, immutable contracts and complete independent/PR review are documented in pilot usage. Writer verification, fresh assessment and actual adoption are distinct evidence categories.

Independent assessment of that maintenance candidate found that changed mandatory decisions could leave the old procedural fingerprint unchanged. The supported correction adds one required-input contract shared by the controller and portable resolver, including current operative guidance and discovery of added code/guidance in declared areas. Skill Creator was used for the existing entry/index guidance; no new skill or source collection was imported. The earlier request-changes verdict remains historical evidence. Corrected writer checks, a fresh separate assessment, app compatibility/adoption and paired PR delivery remain separate outcomes.

## Portable delivery entry — 3 October 2026

Seif explicitly requested the app-building factory as an ordinary reusable skill after the maintenance-only guide. `skills/safe-engine` adapts installation/loading of the existing canonical Safe Engine coordinator; it introduces no new authored method or imported competitor procedure. Both portable helper copies are generated from `safe_engine/distribution.py` and checked for equality. [Factory installation](install-safe-engine.md) documents actual prerequisites and host verification limits. The ten canonical entrypoints remain ten; two installation adapters are packaged separately.

## Runtime recovery guidance

On 3 October Seif requested untrapped, explainable app exit and recovery through computer use or Windows commands after a UI-control lookup failed, plus durable skills/rules and continued research. The assistant used Skill Creator for a narrow existing session-contract/entry update, repository routing and the existing user-journey lens, with the owner's decision preserved. No external skill, OS-control helper, new controller mechanism or installed global-memory synchronization was added. Microsoft process-close/stop documentation informed the distinction between graceful cleanup and authorized termination; it grants no tool/owner permission. Structural checks, realistic independent instruction exercises, separate assessment, actual app repair/adoption and full PR delivery remain distinct evidence.

## Small-change alternatives — 3 October 2026

Seif supplied the six-stage lightweight intent directly after the input-fix audit. The assistant used Skill Creator to structure that specific request into `small-change` and precedence routes in its real callers. No external skill or new controller was imported. The earlier preserved full-method statements describe version mode; the owner explicitly superseded their application to bounded small fixes, including narrow PR updates. Structural validation, realistic instruction exercises and independent scoped assessment are distinct from a production app repair.

## Default app diagnostics — 3 October 2026

Seif supplied the requirement that app-wide logs be a critical default component for new apps and that missing diagnostics be added autonomously during smaller features. The assistant used Improve Factory and Skill Creator to structure that request into the canonical Safe Engine `app-diagnostics` reference and its real delivery consumers, retaining the selected lightweight scope. No new skill, external procedure or logger library was imported. OWASP's Logging Cheat Sheet and the OpenTelemetry Logs Data Model informed safe event context, exclusions, correlation and failure verification; neither a collector nor telemetry service is required. The candidate's required-input contract includes the guidance and is consumed by both unchanged generated resolvers; older pins keep their own contract. The portable entry documents an optional owner-authorized, independently reviewed local trial without claiming the candidate merged or editing an existing controller pin. Focused structural/helper checks, realistic instruction exercises, fresh independent assessment, app coverage/adoption and paired PR delivery are distinct evidence; historical pilot QA is not re-certified.

## Early app efficiency — 3 October 2026

Seif supplied the requirement to optimize CPU/memory, reuse repeated work and consider caching from initial app design, repairing the factory before the app. Improve Factory and Skill Creator structure that request into one `app-efficiency` reference with early analysis/planning, implementation, full/light QA/review and handoff routes. Microsoft Learn memory-caching guidance and AWS Builders' Library caching strategies informed explicit bounds/fallback, coalescing and measured cache behavior; primary links and checked date are in the reference. No external skill, cache library or optimizer is imported. The new contract declares this reference without changing legacy resolver requirements. Local trial routing retains its existing record filename, explicit authority, exact candidate review and rollback; old pins and diagnostics defaults remain. Focused input/structural checks and independent instruction application do not prove current-app performance or refresh its historical QA.
