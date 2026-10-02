# Pilot skill provenance

Seif identifies the source collection as his own work, with AI assistance in writing and committing. Source: `Repaircheck/claude-routines`, commit `449e1110104b6ac27aed3a940c5ed6d1bf671f11`, under `.claude/skills/`.

The pilot adapts `analyze-start`, `get-ready-to-code`, `deep-review`, `change-guard`, and `compliance-check`. On 2 October Seif explicitly required the complete `how-to-make-a-pr` and `how-to-review-a-pr` procedures for every project, authorizing their generic adaptation. Those two entrypoints and their body/comment/synthesis resources are now packaged. The three lens references remain canonically under `deep-review/references/`, originating from `how-to-review-a-pr/references/`; both reviewers link them rather than duplicate them. The original source checkout has not been modified.

The assistant-authored addition is the small `safe-engine` coordinator authorized for this pilot. The substantive analysis, planning, execution, and review methods remain Seif's work. The wider specialist library is still to be coauthored.

Adaptations implement selected decisions: real project context replaces fixed repository/language assumptions; unknown applicability cannot silently become N/A; exceptions need authority; correction loops use an explicit run-wide budget; performance depends on the workload rather than universal O(1); file/function lengths prompt inspection rather than forced splits; tests run in substantial batches; reviewer repairs require fresh assessment. A clean review is valid.

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
| Separate reviewer; original goal → analysis → three options → plan → execute → five passes → verdict → retry once → build → additive push → detailed comment | Preserved in full; all steps assessed even when no repair is warranted |
| Three options automatically chosen by autonomous reviewer | Seif's later decision-ownership rule governs new substantive choices; already authorized narrow repairs can proceed |
| `~O(1)` and unrestricted repair loops | Existing approved workload targets, batched QA and shared finite limits govern; each failed step has at most one retry |
| Security/performance/journey rubrics | Existing generic rubrics reused; locale and technology examples are contextual, not fixed project requirements |
| Fixing reviewer produces final verdict | Seif's selected fresh-assessment requirement applies after repairs; a repairer cannot independently certify its own changes |
| No force-push; sign if required; draft remains human-owned | Preserved; retrospective corrections do not rewrite earlier commits |

The English adaptation removes product-specific bindings, not the workflow. A host that cannot execute the separate review reports a blocker. No universal hook, global installation, protected merge gate or completed external integration is implied.

On the same day Seif emphasized that his complete routines must be supplied and followed across sessions. A direct source-versus-factory diff of the five earlier imports confirmed that their substantive analysis, planning and review bodies remain, with the approved changes described above. The coordinator now explicitly requires reading each full file, preserves the three-alternative comparison before planning, and carries decisions/artifacts/limits into resumes and delegates. Its [method handoff](../.agents/skills/safe-engine/references/method-handoff.md) links every canonical owner. The local review prompt now supplies `get-ready-to-code` as well as the analysis/review skills and explicitly requests all five review passes. These changes do not retroactively re-certify the first demonstration.
