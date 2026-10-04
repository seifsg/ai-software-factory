# AI Software Factory — repository rules

Read [README](README.md), the [skill index](.agents/skills/README.md) and [current decisions](docs/current-decisions.md) before changing this factory.

## Write in Seif's words

Apply [Clear Writing](.agents/skills/safe-engine/references/clear-writing.md) to authored prose: brief, specific, natural, evidenced. No em dashes or stock rhetorical formulas. Use one finishing pass; preserve source originals and useful details.

Use the original when one exists. RepairCheck Mobile is the first source; use another original only when Mobile has no equivalent for that task. [Provenance](docs/skill-provenance.md) records the mapping. Preserve Seif's wording, order, emphasis, checkpoints and deliberate repetition: reminders protect against context loss. Analyze Start keeps its three approved additions. Remove source-project assumptions from operative methods; discover the actual target's stack, rules, users and integrations. Record adaptations; preserve source checkouts.

No original? Use Seif's brief, direct wording: task, priorities, outputs, necessary steps/checks, stop. No gimmicky voice, filler or explanations the agent already knows. Number ordered steps. Compare requirements before/after; lose no detail or behavior. Links must not quietly import another workflow.

Seif is the primary author. Compress AI prose; preserve his deliberate reminders. Keep bindings/coordination explicit. No invented library or placeholders. Generic methods and product/technical research are authorized.

Spend steps where they change decisions, results or evidence. Reuse valid analysis, choices, records and checks. Read applicable methods fully once while available; reread changed/lost context, not every cross-link. Load conditional references only when needed. Reassess changed inputs, failures or unresolved material concerns; no recursive skills, duplicate reports, repeated votes or busywork. Preserve required gates, independent review and original checkpoints/0–4 corrections.

## Keep the requested scope

An analysis, planning or review request stays in that phase. A small subject does not authorize coding. Honor the original file-summary stop unless existing user instructions explicitly authorize continuing through it.

For a requested small implementation or fix, use [Small Change](.agents/skills/small-change/SKILL.md). Surgical changes take precedence; defer unrelated refactors, instrumentation and optimization. Its six light routines replace full version procedures for that change. Keep the 0–4 discipline, focused checks and one narrow independent assessment. Offer broader affected-area checks when useful; run them only at the final stage when requested or required by a real protected gate.

For larger factory changes, use [Improve Factory](.agents/skills/improve-factory/SKILL.md). Preserve existing work and active app state. Use a suitable branch or isolated worktree. Keep one writer per file; subagents do not have automatic filesystem isolation.

## Decisions and quality

Give 100% minimum. Aim higher through correct, useful work within scope.

Preserve selected options. For a new substantive choice, compare three credible alternatives and recommend one. Choose when delegated; ask only for an unresolved owner choice. Do not reopen settled decisions.

Use the [session contract](.agents/skills/safe-engine/references/session-contract.md) for authority, continuation and recovery. Continue to the agreed outcome without invented correction credits, retry ceilings or session deadlines. Honor access limits, protected gates and owner stops. Discover permitted alternatives when a UI/control route fails.

Delivery uses [diagnostics](.agents/skills/safe-engine/references/app-diagnostics.md) and [efficiency](.agents/skills/safe-engine/references/app-efficiency.md). Every app/game needs working shared logging, including small fixes: preferred provider/access or internal module/local sink. Log/read detailed success/failure journeys, safe parameters/queries/outputs/source while debugging. Never credentials. Required logging stays surgical; analysis stays read-only.

The factory serves games, mobile/desktop/web software, servers, tools and libraries. For new products, preserve the first plan, research current product/UX and technical options, then revise it. Resolve material unknowns as work proceeds. Use [research](.agents/skills/research-market/SKILL.md) for stack, architecture and fitting design patterns; apply SRP/GoF where useful, not ceremonially. Plan applicable CPU/GPU, memory, queries/database, network, storage, caching and interaction costs. Unknowns need evidence or a disclosed limit; do not assume a GUI or fixed stack.

## Files and verification

Every UI/interaction change uses [UX Quality](.agents/skills/ux-quality/SKILL.md): simple, familiar, accessible, responsive. Research uncertain design/assets; compare three credible options, justify/choose within delegation. Inspect visuals; audition sounds. No poor placeholders or unsupported claims. Reuse the reviewer; keep surgical scope and tests-last.

For new or materially changed persistence, use [Database Schema](.agents/skills/database-schema/SKILL.md): whole-product journeys/invariants → three viable designs → reasoned choice → written schema → fresh audit. Every structure needs a purpose. Optimize measured workloads, not universal O(1) claims. Preserve original Get Ready wording, settled decisions, surgical scope and tests-last order.

- Use Skill Creator for new or substantially revised skills.
- Keep canonical skills in `.agents/skills/<name>/SKILL.md`, with matching YAML `name` and useful `description`.
- Read an original and its resources before importing it. Record repository, revision, path and deviations.
- Keep each procedure in one canonical place. Declare real dependencies and preserve links.
- Update affected callers, index, source records and current usage/preview statements together. Preserve dated evidence as history.
- Check frontmatter, references and changed helpers. Exercise realistic behavior when instructions or executable behavior change. Wording checks alone do not prove method adherence.
- Follow [tests-last order](docs/current-decisions.md#finish-work-use-it-then-automate-tests): finish implementation/improvements → manual action QA → author/polish/run automated tests → final review/PR. Never write, change or run automated tests during development, including existing suites, TDD and feature checks. Apply to delegates and reviewer fixes. Manual QA gaps stay unverified; automation cannot replace them.
- Distinguish implemented, checked, independently reviewed, adopted and released. Report incomplete or unverified work plainly.
- Keep secrets, client data, transcripts and runtime artifacts out of Git. Preserve unrelated edits.

## PRs and external actions

For every authorized PR or update, use the original [creation](.agents/skills/how-to-make-a-pr/SKILL.md) and [review](.agents/skills/how-to-review-a-pr/SKILL.md) procedures with the [project adapter](docs/pr-workflow.md). Run PR review on a separate instance. The adapter records actual settings, selected small-change scope and current recovery/review rules.

Source company names, accounts, channels, tracker lists and tool names are not this project's settings. Discover actual bindings before asking. Missing bindings block the affected external action; keep authorized local work moving. Local review and controller `ready` do not complete the PR workflow.

Keep task links, truthful attribution, visual context, adjustment history and human handoff. Leave PRs draft. Do not infer authority to notify, merge, release, deploy or spend money. No host hook or protected remote gate is installed by these instructions.
