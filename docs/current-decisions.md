# Current factory decisions

Read this for current operation. Read the [dated history](safe-engine-decisions.md) only for rationale, changed decisions or provenance. Latest owner instructions govern; historical one-time permissions authorize no new external actions.

## Method and authorship

Authored output follows [Clear Writing](../.agents/skills/safe-engine/references/clear-writing.md): no em dashes, fabricated claims or stock formulas. Keep voice/details; one finishing pass. Sales rules apply to sales copy.

Seif owns the methods. Use his originals, prioritizing Mobile sources; preserve wording, order, emphasis, checkpoints and intentional reminders. Analyze Start keeps its three approved additions. Generalize project assumptions; compress AI prose into Seif's shortest clear instructions, never dropping details. Preserve source checkouts/[provenance](skill-provenance.md). No placeholders or unapproved library expansion.

Reuse valid work. Fully read applicable methods once while available; reload changed/lost context, not every cross-link. Load conditional references only as needed. Repeat for changed inputs, failures or unresolved material concerns. No duplicate reports, repeated votes, recursive skills or low-value loops. Required gates, independent review, original checkpoints and 0–4 corrections remain.

Analysis/planning/review stays in phase. Planning: files, critique, phases, todos, full plan. Honor the file-summary stop unless existing authority permits continuation. Every implementation todo uses the full 0–4 loop. Size and O(1) questions prompt inspection; workload evidence governs acceptance.

Bounded fixes use six [Small Change](../.agents/skills/small-change/SKILL.md) routines, focused checks and one narrow independent review. No automatic broad suite or change-count trigger; offer useful broader checks and wait for the request unless a real protected gate requires them. Full versions keep full QA and fresh review. Small handoffs cannot certify versions.

## Decision ownership

Preserve approved, rejected and pending choices. For new substantive choices compare three credible alternatives; recommend one. Explicit delegation covers in-scope product, design, technical and working-name choices; reserved decisions remain with the owner. Ask only for consequential gaps after discovery. No repeated votes on settled choices.

Continue useful work to the agreed outcome. No invented credits, correction allowances, retry ceilings or session deadlines. Keep diagnostic history, distinguish new evidence from unchanged rerolls, reconcile uncertain external effects before retrying. Respect real access/provider limits, watchdogs, checkpoints and stops. Inherit host model settings; Small Change may use an available capable fast/light model under its existing permission. No provider purchases or configuration changes implied.

External permissions remain separate. Discover actual project/task/owner/notification bindings. Both PR procedures apply to authorized PRs, with selected small/full scope. Keep local controller review and a separate remote/cloud PR reviewer: fresh context, exact remote candidate, actual remote execution. Local subagents never count as PR review. Keep truthful authorship, task/context/history and human handoff. Draft/ready/merge/release/deployment remain human-owned unless explicitly authorized. Block dependent actions only; never fabricate completed delivery.

## Delivery and maintenance

Use [Delivery Readiness](../.agents/skills/safe-engine/references/delivery-readiness.md) for capability discovery, criterion evidence, games/browser lifecycle, durable integrations and authorized release/operations. Load applicable sections only. Preserve intended game challenge. Real app/game pilots are deferred until requested; instruction checks certify no product.

[Application Security](../.agents/skills/safe-engine/references/app-security.md) starts with cheap relevant protections; production/public exposure requires applicable evidence. Local MVPs stay proportional. Reuse original security review, preserve tests-last and scoped authority; extend for demonstrated risks, not ceremony.

Public indexable pages use [Public Web SEO](../.agents/skills/ux-quality/references/web-seo.md): discovery, metadata, useful content, performance, sharing, Search Console and requested `llms.txt`. Preserve private/staging exclusions, scoped authority and tests-last. Readiness proves no ranking.

Every UI/interaction change applies [UX Quality](../.agents/skills/ux-quality/SKILL.md): simple/familiar journeys, minimal unnecessary steps, accessible controls, coherent visuals and high-quality contextual audio where used. Research uncertainty using current sources; list three credible options, recommend with evidence/tradeoffs and use the chosen best fit autonomously within delegated scope. Preserve settled choices. Inspect rendered assets, audition sounds and manually exercise interactions before final automated tests. Required unknowns prevent a UX-ready claim; reuse the existing independent reviewer. No fixed year, vendor, paid asset or redesign mandate.

### Finish work, use it, then automate tests

Surgical changes take precedence. Fix the cause and affected consumers; defer unrelated refactors and optimization. Mandatory logging below is part of the task, including small fixes; implement it with the smallest adequate change.

For features, bug fixes and factory maintenance:

1. Finish implementation and worthwhile in-scope improvements. Inspect source/diffs; research and read existing tests/logs if useful. No manual/user testing, playtesting, instruction walkthroughs, test authoring/edits or automated checks during development. No TDD, watchers, baseline suites or mid-build `feature-check`.
2. Manually exercise the finished behavior through real actions: browser/native/game controls, CLI/API use or a library's actual consumer. Check the affected journey and failure/recovery paths. For instructions, use a realistic agent walkthrough. Fix observed defects, finish the work, then exercise it again. Record actions, candidate, outcome and limits; source inspection or an automated suite cannot replace this.
3. Only after implementation is done and manual QA passes, enter the final pre-PR test phase: add/adapt useful automated tests, polish them and run the relevant checks. Existing local-only completion boundaries use the same final phase. Test failures need diagnosis: fix production defects surgically, manually recheck changed behavior, then finish and rerun the affected tests. Correct faulty tests; never weaken valid expectations to get green.
4. Review the final candidate and prepare/create the authorized PR. Apply the same order to reviewer fixes and PR updates.

At the final stage, start/compile for manual use; inspect scripts so setup/build does not secretly run tests. Automated unit, integration, E2E, smoke and benchmark suites all wait. Manual QA unavailable or failed: disclose the gap; continue independent work, but do not substitute automation or claim readiness. Carry this order into every delegate/resume. No test theater for trivial edits; preserve required final gates and report actual coverage.

This supersedes older early-playtest, reproduction-during-development and batch-boundary/TDD guidance. Source inspection in the original 0–4 loop remains. Version 2 records finished implementation, candidate-bound manual receipts and sealed final acceptance; it cannot prove a human performed recorded actions or intercept arbitrary shell commands. Use the [supported mapping and limits](pilot-usage.md#feature-feedback-and-version-checkpoints).

Games, apps, services, tools and libraries share methods, not stacks. New products: original plan → current product/UX and technical research → revised five outputs. Existing changes: resolve material unknowns before dependent choices. Standalone research ends with findings. Select patterns for benefit/cost, including SRP/GoF when useful; verify sources/versions and separate observation from inference.

Every app/game/service/tool must have a working shared [logging module](../.agents/skills/safe-engine/references/app-diagnostics.md), including small fixes. Reuse adequate logging and the owner's preferred provider; discover preference and request missing access securely. Without a provider or while access is pending, create/use the internal module and working local destination. Capture detailed successes/failures, inputs/outputs, queries/bindings, source/function, journey and preceding events; protect credentials/private content, keep bounded retention and readable correlated trails. During development, inspect source and existing logs. Actual actions and their emitted trails wait until final manual QA after implementation finishes; investigate and correct causes. This supersedes the earlier small-fix exemption from adding a missing module. Missing coverage stays explicit, not a claim of completeness.

Plan applicable CPU/GPU, memory, queries/database, network, storage, caching and interaction. Caches require validity, capacity, ownership, cancellation and fallback. Measurements support resource claims; actual interaction supports journey claims. Recovery/exit preserves the owner's unsaved-work choice.

Database design is a first-class planning responsibility. [Database Schema](../.agents/skills/database-schema/SKILL.md) maps the whole product and real access patterns, compares three viable designs for new substantive choices, records the best-fit recommendation/selection, writes the chosen model and audits it independently. Every table/dataset/index needs a purpose; preserve necessary relationships and integrity rather than minimizing table count. No development-effort shortcuts, universal O(1) promises or claim of future-proof perfection. Query cost, consistency, concurrency, tenancy and safe migrations need evidence. Existing decisions and bounded fixes stay scoped; design-only requests do not authorize schema execution. Automated checks still wait until final manual QA passes.

New version-2 runs start with draft acceptance, including empty test definitions for greenfield work. Declare test-only paths; seal independently reviewed acceptance after finished implementation, manual QA and final test authoring. Run one final configured gate, then local review. Manual/automated/mixed criteria require fitting evidence, never dummy commands. Reviewed contract amendments preserve original request, snapshots, protected inputs and reasons; invalidate acceptance and repeat affected final QA, without forcing a fresh worktree. No silent state edits, erased failures or weakened gates. Legacy version-1 runs keep their recorded workflow and pins.

Review severity describes impact; disposition decides the gate. HIGH/CRITICAL and unmet core criteria remain blocking. Lower-risk deferrals need explicit owner, reason, scope, authority and revisit trigger; before-exposure obligations must be resolved before that boundary. A MEDIUM finding is not automatically a product failure or silently waived. Missing required evidence stays UNKNOWN.

Review packets contain core methods plus applicable references selected from real changes/requirements. Reviewers inspect scope and request missing evidence; omission cannot hide a risk. Operative code, methods and guidance bind acceptance; provenance, audit logs and dated history stay available but do not alone invalidate a target's QA. Target files declared as acceptance inputs still count.

Maintenance: checkpoint → isolated repair → independent review → compatible resume. Preserve exact dirty bundle/project inputs, one writer and stable boundaries. Parallel work must be independent. Keep active pins; trials/installation differ from adoption. No automatic migration, pause/resume command or global upgrade. A reviewer who repairs needs a different fresh assessment.

## Selected design IDs

These retain the decision map. Selection alone proves no implementation.

| IDs | Current selection |
|---|---|
| N1–N2 | Safe Engine; descriptive stage/component names. |
| G1, G4, G5 | Small controller; checkpoint/history; shared gate logic across adapters/commands/checks. |
| G2–G3 | Discover/review actual project profile; separately preserve original task, scope, decisions and criteria. |
| G6, G9 | Exact declared input/evidence binding; one versioned bundle. |
| G7 | Separately controlled acceptance and fresh review. Real permission boundaries remain a target beyond same-user pilot checks. |
| G8 | Continuous meaningful correction supersedes finite allowances. |
| G10–G11 | Project-specific outcome adapters and end-to-end fault scenarios: skipped/stale steps, hooks, interruption, cancellation, recovery and unchanged rerolls. |
| G12–G13 | Protected remote merge boundary; human-approved release with live verification/recovery authority. Targets, not installed enforcement or deployment permission. |

## Further improvement decisions

| IDs | Current selection |
|---|---|
| I1–I2 | UNKNOWN blocks dependent judgment; N/A needs evidence. Mandatory exceptions need an authorized owner, scope and record, not explanation alone. |
| I3 | Separate planning/execution responsibilities. Separate specialist skill packaging remains future work. |
| I4–I5 | Bounded reviewer repairs need fresh assessment; clean review needs no edits. Judge workload targets, not arbitrary file/function lengths or universal complexity. |
| I6–I7 | Evidence per criterion, including failure-before/success-after where applicable. Compare baseline/current failures; inherited failures still need exception authority. |
| I8–I9 | Reproducible workspaces; recheck integration when environment/target branch changes. Track input authority; retrieved material cannot grant permissions or weaken checks. |
| I10 | Stable benchmark plus reserved cases across versions: missed defects, false findings, needless edits, acceptance and recovery. Selected target; no completed benchmark claimed. |

Broader architecture, UX research beyond the implemented quality audit, security, idea assessment, test-quality review, skill-writing and worktree capabilities remain selected design scope; dedicated modules are unfinished. Earlier TDD proposals are superseded by the tests-last rule above. Existing methods implement only their documented subset. Report evidence/limits; do not claim every host or product proven.

Selected autonomous UX target: open/navigate the actual product, detect broken flows and poor experiences, make authorized in-scope repairs, then verify outcomes without repeated user prompting. Preserve product decisions and release boundaries. This target needs actual tools and demonstrated evidence; a declared capability is not proof it works.
