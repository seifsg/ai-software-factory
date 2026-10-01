# Pilot skill provenance

Seif identifies the source collection as his own work, with AI assistance in writing and committing. Source: `Repaircheck/claude-routines`, commit `449e1110104b6ac27aed3a940c5ed6d1bf671f11`, under `.claude/skills/`.

The pilot adapts `analyze-start`, `get-ready-to-code`, `deep-review`, `change-guard`, and `compliance-check`. The three lens references under `deep-review/references/` originate from `how-to-review-a-pr/references/`. The original source checkout has not been modified.

The assistant-authored addition is the small `safe-engine` coordinator authorized for this pilot. The substantive analysis, planning, execution, and review methods remain Seif's work. The wider specialist library is still to be coauthored.

Adaptations implement selected decisions: real project context replaces fixed repository/language assumptions; unknown applicability cannot silently become N/A; exceptions need authority; correction loops use an explicit run-wide budget; performance depends on the workload rather than universal O(1); file/function lengths prompt inspection rather than forced splits; tests run in substantial batches; reviewer repairs require fresh assessment. A clean review is valid.

Frontmatter descriptions are shortened and YAML-quoted for reliable discovery. The original five planning artifacts, no-code analysis phase, ASCII charts, consumer mapping, per-todo 0–4 loop, and complementary quality/regression/requirements reviews remain.
