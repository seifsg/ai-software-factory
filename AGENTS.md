# AI Software Factory — repository rules

## Scope selection — owner correction, 3 October 2026

Use [small-change](.agents/skills/small-change/SKILL.md) for small direct fixes. Its six lightweight routines override the full analysis/planning/review and repeated QA requirements below for that scope, including both PR procedures. Correct code, focused affected-behavior verification and a narrow independent assessment remain required. Do not automatically run broad regression or full suites; offer an affected-area batch when cumulative changes justify it and wait for the user's request before running it. Preserve actual protected gates and honest evidence. Version work keeps the full procedure. This is Seif's explicit selected change, not a new exception to request repeatedly.

## Scope

This private repository owns Seif's reusable software-factory skills. Read `README.md` and `.agents/skills/README.md` before changing the system. Follow the user's current instructions and preserve existing skill behavior unless the requested change requires altering it.

## Quality standard

Our motto: **give 100% minimum; aim to give more through the quality of the work.**

- Put extra effort into correctness, clarity, polish, usability, and appropriate verification.
- Review and refine the output before calling it finished. Iterate further when doing so materially improves the result.
- Overdeliver through useful improvements that are needed within the agreed scope. Preserve the user's intent and avoid adding unsolicited deliverables or unrelated features.
- Judge success by the quality and usefulness of the outcome, rather than the amount of material produced.
- For app work, apply [app efficiency](.agents/skills/safe-engine/references/app-efficiency.md) from analysis/planning through the selected scoped handoff: design CPU/memory/resource lifetimes, implement useful safe caching/reuse and verify relevant costs and correctness. Keep small changes focused and preserve necessary costs; a factory instruction is not proof of an optimized app.

## Skill development

The engine is named **Safe Engine**. Read `docs/safe-engine-decisions.md` before designing or changing the factory. Preserve Seif's selected options; keep pending choices unresolved. For new improvement or design decisions, compare three credible alternatives and recommend exactly one with reasons. Follow the canonical decision-ownership policy and session contract: Seif may explicitly delegate in-scope choices for a run; owner-reserved choices stay pending. Recommendations alone are not authority. Preserve selected names; descriptive working names may be chosen within explicit delegation.

Seif is the primary author of the skills. Help him express his procedures, compare relevant examples, identify gaps or contradictions, refine wording, structure files, and validate behavior. Preserve his intent and voice. Do not independently draft most of the skill library or create placeholder skills. New procedures and substantive rewrites should develop from Seif's writing or an explicit request for a particular draft. Examples from other factories are inspiration, not approved names or procedures. Skill counts, boundaries, and build plans remain proposals until selected.

- Use the available Skill Creator workflow when creating or substantially updating a skill.
- Read an imported skill and its relevant resources before adapting it. Record provenance where known; do not invent authorship or copy rights.
- Store each skill in `.agents/skills/<skill-name>/SKILL.md`, with YAML `name` and `description`. Match the name to the folder.
- Describe when the skill applies, what context it needs, and what it returns. Add exclusions when they prevent likely misrouting.
- Keep procedures self-contained where practical. Declare real dependencies; do not assume tools or integrations exist.
- Keep reusable content in one canonical owner. Link supporting references from the skill entrypoint.
- Do not create placeholder skills or claim that a skill is operational because its instructions exist.
- Update the skill index after adding, removing, or materially changing a skill.

## Connected workflows

### Mandatory PR creation and review

For every factory-managed project and every PR, read and execute [.agents/skills/how-to-make-a-pr/SKILL.md](.agents/skills/how-to-make-a-pr/SKILL.md), then [.agents/skills/how-to-review-a-pr/SKILL.md](.agents/skills/how-to-review-a-pr/SKILL.md) on a separate instance. This also applies to documentation, skills, existing-PR corrections and updates; no size- or project-based bypass. The paired skill explicitly authorizes delegation for that review. Preserve the full procedure, not only its formatting or five review lenses.

Keep the task links/status, truthful human attribution, Why-first visual body, adjustment history, human handoff, supported in-scope fixes, actual checks and detailed review comment. Use real project bindings for tracker, owners, notifications, stack and branches; missing required settings/access are blockers. Read [this repository's bindings](docs/pr-workflow.md). Never invent or silently omit them.

The local controller's read-only candidate review and `handoff` do not constitute PR creation or full PR review. Every changed PR candidate needs a fresh separate assessment. Leave PRs draft; the human owns ready/merge/release. These instructions do not claim host-hook or protected remote enforcement.

Keep `preview/index.html`, our plain-language visual introduction, accurate as the factory changes. Explain outcomes before implementation details. Clearly distinguish skills available in the source collection, skills imported here, and workflows demonstrated in a real run.

When connecting skills, make the handoff explicit: inputs, output artifact, acceptance condition, failure state, and next responsible step. Keep task state durable where the target environment supports it. Do not mark a ticket complete when work only reached a review or deployment handoff.

For unattended workflows, follow the [session contract](.agents/skills/safe-engine/references/session-contract.md) to record delegated authority, completion boundaries, diagnostic progress and actual constraints. Continue authorized work without artificial credits, repair allowances, fixed retry limits or session deadlines; honor explicit owner stops. Avoid duplicate actions on retries. Keep independent acceptance checks outside the builder's unrestricted control when their integrity matters.

Before handing a runtime-control problem back to the owner, follow the contract's [failed-route recovery](.agents/skills/safe-engine/references/session-contract.md#recover-a-failed-control-route). A missing UI window does not establish that every permitted CLI/API route is unavailable. Preserve exact-target authority, state and tool restrictions; report actual recovery evidence. Review app exit and failure feedback through the existing user-journey lens.

## Verification and changes

- For application development, batch unit and E2E runs after substantial planned work; do not run tests after every edit or start test watchers by default. Before pushing a feature, inspect worthwhile in-scope design, cleanup, reuse, performance, security, and agent-navigability improvements, then verify the affected result. Read `docs/safe-engine-fast-delivery.md`; its broader option recommendations remain unselected. The 2 October owner-selected cadence supports completed feature feedback and comprehensive version checkpoints; see the canonical usage guide. User updates should be concise and outcome-focused, with complete method evidence in durable linked artifacts.
- Validate skill frontmatter, names, references, and any executable helpers.
- Test observable behavior when warranted. Report checks not run and their limits honestly.
- Keep changes focused and preserve unrelated work. Use a branch for substantive changes to an established repository.
- Do not merge, release, contact others, spend money, or change a target project's live systems without applicable user authorization.
- Never commit credentials, client source/data, transcripts containing sensitive information, or local runtime state.
