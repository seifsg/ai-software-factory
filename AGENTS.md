# AI Software Factory — repository rules

Read [README](README.md), the [skill index](.agents/skills/README.md) and [current decisions](docs/safe-engine-decisions.md) before changing this factory.

## Write in Seif's words

Use the original when one exists. RepairCheck Mobile is the first source; use another original only when Mobile has no equivalent for that task. [Provenance](docs/skill-provenance.md) records the mapping. Preserve wording, order, emphasis and checkpoints. Analyze Start keeps its three approved additions.

For skills without originals, write direct instructions: the task, priorities, outputs, necessary steps and checks, and where to stop. Keep instructions short without reducing the work. Number steps when order matters. Compare requirements before and after rewriting. Do not quietly drop behavior or import another workflow through a link.

Seif is the primary author. Keep project bindings and coordination outside original bodies. Record necessary packaging changes. Do not invent the rest of the library or create placeholders. The current request authorizes this whole-repository restoration and writing pass.

## Keep the requested scope

An analysis, planning or review request stays in that phase. A small subject does not authorize coding. Honor the original file-summary stop unless existing user instructions explicitly authorize continuing through it.

For a requested small implementation or fix, use [Small Change](.agents/skills/small-change/SKILL.md). Its six light routines replace full version procedures for that change. Keep the 0–4 discipline, focused checks and one narrow independent assessment. Offer broader affected-area checks when useful; run them only when requested or required by a real protected gate.

For larger factory changes, use [Improve Factory](.agents/skills/improve-factory/SKILL.md). Preserve existing work and active app state. Use a suitable branch or isolated worktree. Keep one writer per file; subagents do not have automatic filesystem isolation.

## Decisions and quality

Give 100% minimum. Aim higher through correct, useful work within scope.

Preserve selected options. For a new substantive choice, compare three credible alternatives and recommend one. Choose when delegated; ask only for an unresolved owner choice. Do not reopen settled decisions.

Use the [session contract](.agents/skills/safe-engine/references/session-contract.md) for authority, continuation and recovery. Continue to the agreed outcome without invented correction credits, retry ceilings or session deadlines. Honor access limits, protected gates and owner stops. Discover permitted alternatives when a UI/control route fails.

For app delivery, Safe Engine owns [diagnostics](.agents/skills/safe-engine/references/app-diagnostics.md) and [efficiency](.agents/skills/safe-engine/references/app-efficiency.md). Standalone analysis does not authorize instrumentation or optimization work.

## Files and verification

- Use Skill Creator for new or substantially revised skills.
- Keep canonical skills in `.agents/skills/<name>/SKILL.md`, with matching YAML `name` and useful `description`.
- Read an original and its resources before importing it. Record repository, revision, path and deviations.
- Keep each procedure in one canonical place. Declare real dependencies and preserve links.
- Update affected callers, index, source records and current usage/preview statements together. Preserve dated evidence as history.
- Check frontmatter, references and changed helpers. Exercise realistic behavior when instructions or executable behavior change. Wording checks alone do not prove method adherence.
- Batch relevant checks after coherent work. Inspect worthwhile in-scope improvements before delivery. Reuse valid evidence; rerun when a change or concrete concern warrants it.
- Distinguish implemented, checked, independently reviewed, adopted and released. Report incomplete or unverified work plainly.
- Keep secrets, client data, transcripts and runtime artifacts out of Git. Preserve unrelated edits.

## PRs and external actions

For every authorized PR or update, use the original [creation](.agents/skills/how-to-make-a-pr/SKILL.md) and [review](.agents/skills/how-to-review-a-pr/SKILL.md) procedures with the [project adapter](docs/pr-workflow.md). Run PR review on a separate instance. The adapter records actual settings, selected small-change scope and current recovery/review rules.

Source company names, accounts, channels, tracker lists and tool names are not this project's settings. Discover actual bindings before asking. Missing bindings block the affected external action; keep authorized local work moving. Local review and controller `ready` do not complete the PR workflow.

Keep task links, truthful attribution, visual context, adjustment history and human handoff. Leave PRs draft. Do not infer authority to notify, merge, release, deploy or spend money. No host hook or protected remote gate is installed by these instructions.
