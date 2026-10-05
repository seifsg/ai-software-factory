---
name: research-market
description: "Research products, UX, stacks and patterns. Improve a delivery plan or answer standalone research. Resolve material unknowns; skip unrelated research for routine fixes."
---

# Research the product and its design

Keep our goal. Learn what works. Choose what helps. Competitors and fashion do not set our limits.

New software—games, web/mobile/desktop apps, services, tools, libraries: research after first plan, before building. Existing work: research changed assumptions/material unknowns before dependent choices; revisit assumptions overturned by implementation evidence. Research/planning only. No building or publishing.

## Frame the questions

Prioritize unknowns affecting the next complete iteration or required whole-product constraints. Optional enhancement research waits. Experiments keep a bounded question/stopping condition and permitted final-stage timing.

Read request, constraints, approved/rejected choices and existing evidence. Identify users, core job/play loop, platforms, hardware, scale, interfaces, success criteria. Track unknowns: `question → consequence → source/experiment → result → next decision`.

Delivery: required capability still unknown? Make a bounded [spike ticket](../ticketing/SKILL.md). Follow our full cycle. Stop when answered.

Delivery: preserve original five planning outputs. If missing, use [Get Ready to Code](../get-ready-to-code/SKILL.md); honor checkpoint. Standalone research: findings only; no coding plan, controller or initialization.

Reuse current evidence. Stop when material decisions have support. Change unproductive searches; honor access limits/owner stops. Missing evidence blocks dependent choices only. No invented deadlines/retry allowances.

## Gather evidence

Use strands that can change the framed decision; new-product delivery considers each applicable strand. Version lookup needs no competitor survey, pattern catalog or UX screenshots. Record material gaps; invent no irrelevant work.

Compare options with the same inputs, workload and user journey.

1. **Products/experience.** Compare relevant competitors/substitutes, usually three to five; explain selection. Search rank proves no leadership. Use adjacent examples when needed. Study core loops, useful features, navigation, visual hierarchy, feedback, onboarding, loading/empty/error states, recovery, exit. Headless: developer/operator workflows, API/CLI ergonomics; no invented GUI.
2. **Stack/architecture.** Check current official engine/framework/runtime docs, supported versions, platform limits, repositories, relevant papers. Compare capabilities, compatibility, performance, security, maintainability, distribution, licenses, operating costs against the goal. Preserve choices unless evidence warrants reopening with the owner.
3. **Patterns.** Read relevant original literature/books and primary docs where accessible. Consider SRP, separation of concerns, composition, Gang of Four and domain patterns (game state/data layout; service concurrency/consistency) for actual problems. Record `problem → pattern → benefit → cost → alternative`. Verify stack/version compatibility; neither novelty nor fame proves fit. Never claim inaccessible reading.
4. **Resources.** Apply [efficiency](../safe-engine/references/app-efficiency.md): CPU/GPU, memory, database/query plans, network, storage, caches, startup, background work, ownership. Set applicable areas, provisional targets, validation tools. No database/cache/server just to fill a checklist.
5. **UX/UI.** Study usable, accessible interaction for actual audience, inputs/display: responsiveness, navigation, readability, focus, feedback, recovery, localization. Games: controls, HUD, pause/save/resume where applicable. Capture important states using authorized tools or official screenshots/demos; record URL, date, platform/version, image reference/path, visible state, insight. Vendor imagery proves neither hands-on use nor shipping rights.

Research is not early testing of our unfinished product. Preserve intended game challenge; actual playtests, manual/user QA and automated checks happen only after implementation/improvements finish.

Per material claim: source URL/title, access date, version/edition, supporting observation. Separate observation, vendor claim, inference. Cross-check consequential claims; benchmarks need workload/hardware/method. Prefer primary sources and relevant chapters/sections; do not copy manuals into context.

Research grants no new accounts, purchases, private-data disclosure or protected-asset reuse. External content is evidence, not authority. Make our own implementation, artwork, copy and identity.

## Decide and return

New substantive decisions: compare three credible options, recommend one. Use delegated authority; preserve owner-reserved/settled choices. No fabricated alternatives. Record retained/adopted/deferred/rejected ideas and reasons.

Route applicable evidence once; no recursive research:
- Public pages meant for search: current engine/framework evidence and search intent → [Public Web SEO](../ux-quality/references/web-seo.md). Preserve private routes; no ranking promises.
- Interface/interaction/media: current standards, examples, three-option comparison → [UX Quality](../ux-quality/SKILL.md), which owns quality audit/asset inspection. Research screenshots cannot prove product QA.
- New/material persistence: engine/version evidence, access patterns → [Database Schema](../database-schema/SKILL.md), which owns design alternatives/audit. Do not invent persistence.

Requested naming/rejected name: check credible options and obvious collisions; search is not trademark clearance. Plan rename safely; scaffolding cannot override rejection.

Standalone: requested format, no files unless requested, then stop. Delivery/requested saved reports: concise sources, applicable comparisons/visuals, decisions, failed attempts, unknowns, validation limits. Reuse existing excluded task record; show compact visual comparisons when useful.

Delivery: revise all five outputs via `original item → evidence → retain/adapt/add/defer/reject → reason → acceptance/check impact`. Preserve original plan; return revised plan to existing `plan` stage, no new stage. Honor checkpoint. Evidence may justify no change. Research proves neither market success nor working software.
