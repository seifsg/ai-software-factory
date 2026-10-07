# AI Software Factory — repository rules

Read [README](README.md), the [skill index](.agents/skills/README.md) and [current decisions](docs/current-decisions.md) before changing this factory.

## Write in Seif's words

Apply [Clear Writing](.agents/skills/safe-engine/references/clear-writing.md) to authored prose: brief, specific, natural, evidenced. No em dashes or stock rhetorical formulas. Use one finishing pass; preserve source originals and useful details.

Tickets/PRs use the shared [work layout](.agents/skills/safe-engine/references/work-writing.md): clear title; purpose/goal, context, behavior change/reason, proof and progress separate. Brief bullets, useful emojis, narrow tables and fitting flows. Before is actual behavior only; never bury purpose or context there. Complete detail, no decoration quota or added writing gate.

Use the original when one exists. RepairCheck Mobile is the first source; use another original only when Mobile has no equivalent for that task. [Provenance](docs/skill-provenance.md) records the mapping. Preserve Seif's wording, order, emphasis, checkpoints and deliberate repetition: reminders protect against context loss. Analyze Start keeps its owner-approved additions. Remove source-project assumptions from operative methods; discover the actual target's stack, rules, users and integrations. Record adaptations; preserve source checkouts. Where an original conflicts with a decision in current decisions, speed modes or the PR adapter, that decision governs; originals stay unedited.

No original? Use Seif's brief, direct wording: task, priorities, outputs, necessary steps/checks, stop. No gimmicky voice, filler or explanations the agent already knows. Number ordered steps. Compare requirements before/after; lose no detail or behavior. Links must not quietly import another workflow.

Seif is the primary author. Compress AI prose; preserve his deliberate reminders. Keep bindings/coordination explicit. No invented library or placeholders. Generic methods and product/technical research are authorized.

Spend steps where they change decisions, results or evidence. Reuse valid analysis, choices, records and checks. Read each method fully once when its phase starts; delegates get only their role's methods plus the agent-routing brief. Reread changed/lost context, not every cross-link. Load conditional references only when needed. Reassess changed inputs, failures or unresolved material concerns; no recursive skills, duplicate reports, repeated votes or busywork. Preserve required gates, independent review and original checkpoints/0–4 corrections.

## Stay agent-agnostic

Seif, 7 October: the factory runs on any coding agent. Methods and docs say "your agent"; host-specific commands, paths and flags live only in [hosts](docs/hosts.md) and the host adapters (plugin manifest, `fast_hosts.py`, `fast_install.py`, `safe_engine/reviewers.py`). Never make a step depend on one agent.

## Keep the requested scope

An analysis, planning or review request stays in that phase. A small subject does not authorize coding. File-summary stop: [speed modes](.agents/skills/safe-engine/references/speed-modes.md#safe).

Every factory activity (delivery, tickets, PRs, factory maintenance) uses [speed modes](.agents/skills/safe-engine/references/speed-modes.md): **Fast** by default, Lucky or Safe on request. In Fast and Lucky that file overrides any conflicting rule here or in linked methods. Fast and Lucky still create tickets and record every step through [Fast run](.agents/skills/safe-engine/references/fast-run.md) and its gate. In every mode, delegate independent work to parallel subagents on fitting models by [agent routing](.agents/skills/safe-engine/references/agent-routing.md).

Safe implementation uses [Ticketing](.agents/skills/ticketing/SKILL.md): canonical tracker, owner-confirmed before/after, one complete delivery unit and its own builder session. Prefer the owner's chosen MCP; GitHub Issues is the default and Seif's current choice. Phase-only requests grant no coding or tracker-write authority; explicitly requested ticket intake still applies.

Default ticket intake derives complete, brief, visual context from the request/code/prior work and continues within authority. No detailed-ticket questionnaire or repeated vote on delegated scope. New products and big features get one [kickoff question round](.agents/skills/safe-engine/references/fast-run.md#kickoff-questions) after quick research. Preserve explicit stops and reserved choices; record progress/PRs and a clear cold-agent handoff under the ticket contract.

Every Safe ticket runs full analysis, planning, 0–4 implementation, final manual QA, final tests and independent review; Fast and Lucky tickets follow their mode. Choose checks prospectively by effect/consumers, not file extension. One compact work record; immutable controller snapshots/raw proof remain. [Small Change](.agents/skills/small-change/SKILL.md) supplies surgical tactics; its six shortcuts apply only to legacy unticketed work. Keep fix scope narrow, checks relevant and unrelated refactors deferred. Separate worktrees for independent tickets; a shared epic checkout has one writer at a time. Preserve ticket/run history and active pins.

For larger factory changes, use [Improve Factory](.agents/skills/improve-factory/SKILL.md). Preserve existing work and active app state. Use a suitable branch or isolated worktree. Keep one writer per file; subagents do not have automatic filesystem isolation.

## Decisions and quality

Build in complete working iterations: next useful outcome ticket first, required quality intact. Keep overall acceptance open. Optional follow-ups tracked; repeated failure needs shared-cause diagnosis.

Give 100% minimum. Aim higher through correct, useful work within scope.

Preserve selected options. New substantive choices follow [decision ownership](docs/current-decisions.md#decision-ownership).

Use the [session contract](.agents/skills/safe-engine/references/session-contract.md) for authority, continuation, recovery and the [review round cap](.agents/skills/safe-engine/references/session-contract.md#review-rounds). Honor access limits, protected gates and owner stops. Discover permitted alternatives when a UI/control route fails.

Delivery uses [diagnostics](.agents/skills/safe-engine/references/app-diagnostics.md) and [efficiency](.agents/skills/safe-engine/references/app-efficiency.md). Every app/game needs working shared logging, including small fixes.

Use applicable [Delivery Readiness](.agents/skills/safe-engine/references/delivery-readiness.md): capabilities, criterion evidence, game/browser lifecycle, durable integrations and release/operations. Preserve intended game challenge. Product pilots/simulations are deferred until specifically requested; no app/game/mobile build or simulation as a factory check this iteration.

The factory serves games, mobile/desktop/web software, servers, tools and libraries. For new products, preserve the first plan, research current product/UX and technical options, then revise it. Resolve material unknowns as work proceeds. Use [research](.agents/skills/research-market/SKILL.md) for stack, architecture and fitting design patterns; apply SRP/GoF where useful, not ceremonially. Plan applicable CPU/GPU, memory, queries/database, network, storage, caching and interaction costs. Unknowns need evidence or a disclosed limit; do not assume a GUI or fixed stack.

## Files and verification

Use [Application Security](.agents/skills/safe-engine/references/app-security.md): cheap relevant protections from the start, actual exposure checks before production. Local MVPs stay simple; existing security review owns the assessment.

Public pages meant for search use [Public Web SEO](.agents/skills/ux-quality/references/web-seo.md) in planning and final review. Preserve private/staging exclusions; verify actual production state within authority. Keep the checklist scoped.

Every app meets the [product bar](.agents/skills/safe-engine/references/product-bar.md): best-fit TypeScript stack, polished light-mode UI, dev sign-in; POCs are never throwaway. Every UI/interaction change uses [UX Quality](.agents/skills/ux-quality/SKILL.md): simple, familiar, accessible, responsive. Research uncertain design/assets and choose per decision ownership. Inspect visuals; audition sounds. No poor placeholders or unsupported claims. Reuse the reviewer; keep surgical scope.

For new or materially changed persistence, use [Database Schema](.agents/skills/database-schema/SKILL.md). Every structure needs a purpose. Optimize measured workloads, not universal O(1) claims. Preserve original Get Ready wording, settled decisions and surgical scope.

- Use Skill Creator for new or substantially revised skills.
- Keep canonical skills in `.agents/skills/<name>/SKILL.md`, with matching YAML `name` and useful `description`.
- Read an original and its resources before importing it. Record repository, revision, path and deviations.
- Keep each procedure in one canonical place. Declare real dependencies and preserve links.
- Update affected callers, index, source records and current usage/preview statements together. Preserve dated evidence as history.
- Check frontmatter, references and changed helpers. Exercise realistic behavior when instructions or executable behavior change. Wording checks alone do not prove method adherence.
- Follow [tests-last order](docs/current-decisions.md#finish-work-use-it-then-automate-tests), including delegates and reviewer fixes.
- Distinguish implemented, checked, independently reviewed, adopted and released. Report incomplete or unverified work plainly.
- Keep secrets, client data, transcripts and runtime artifacts out of Git. Preserve unrelated edits.

## PRs and external actions

For every authorized PR or update, use the original [creation](.agents/skills/how-to-make-a-pr/SKILL.md) and [review](.agents/skills/how-to-review-a-pr/SKILL.md) procedures with the [project adapter](docs/pr-workflow.md). The adapter owns [remote/cloud PR review](docs/pr-workflow.md#cloud-pr-review). Self-review of our own draft PR is [pre-authorized](docs/pr-workflow.md#self-review-of-our-own-draft-pr).

Source company names, accounts, channels, tracker lists and tool names are not this project's settings. Discover actual bindings before asking. Missing bindings block the affected external action; keep authorized local work moving. Local review and controller `ready` do not complete the PR workflow.

For ticketed work, refresh the canonical ticket before PR completion ([cheap refresh](.agents/skills/ticketing/SKILL.md#execute-and-keep-the-contract-current)). Compare its latest confirmed criteria with actual changes, journey proof and limits; unresolved scope drift or failed refresh blocks dependent acceptance. Keep original input, revisions, owner authority and decision activity. Local records cache context/evidence; they never become a second tracker.

Keep task links, truthful attribution, visual context, adjustment history and human handoff. Leave PRs draft unless explicitly authorized otherwise. Do not infer authority to notify, merge, release, deploy or spend money. Factory publication to main follows the adapter's [enforcement](docs/pr-workflow.md#enforcement-and-evidence); preserve installed/active pins.
