---
name: research-market
description: "Research products, UX, stacks and technical patterns for a software goal. Improve a delivery plan or answer standalone research. Resolve material unknowns; skip unrelated research for routine fixes."
---

# Research the product and its design

Keep our goal. Learn what works. Choose what helps. Competitors and fashionable patterns do not set our limits.

For new software—games, web/mobile/desktop apps, services, tools or libraries—research after the first plan, before building. For existing work, research changed assumptions or consequential unknowns before the dependent choice. Revisit when implementation evidence overturns an assumption. This is research/planning. Do not build or publish yet.

## Frame the questions

Read the request, constraints, approved/rejected choices and existing evidence. Identify users, core job/play loop, platforms, hardware, scale, interfaces and success criteria. Keep an unknowns list: `question → consequence → source/experiment → result → next decision`.

In a delivery run, preserve the original five planning outputs. If missing, use [Get Ready to Code](../get-ready-to-code/SKILL.md) and honor its checkpoint. Standalone research needs no coding plan, controller or initialization; return the requested findings and stop.

Reuse current evidence. Research until material decisions have support. Change unproductive searches; respect actual access limits and owner stops. Missing evidence blocks dependent choices only. Do not invent deadlines or retry allowances.

## Gather evidence

Choose strands from the framed questions. New-product delivery considers each applicable strand. Narrow research/existing fixes use only strands that can change the requested decision. A version lookup needs no competitor survey, pattern catalog or UX screenshots. Record material gaps without manufacturing irrelevant work.

1. **Products and experience.** Compare relevant competitors/substitutes, usually three to five. Explain selection; search rank proves no leadership. Use adjacent examples when needed. Study core loops, useful features, navigation, visual hierarchy, feedback, onboarding, loading/empty/error states, recovery and exit. For headless products, inspect developer/operator workflows and API/CLI ergonomics; do not invent a GUI.
2. **Stack and architecture.** Check current official engine/framework/runtime docs, supported versions, platform limits, repositories and relevant papers. Compare realistic options against the goal: capabilities, compatibility, performance, security, maintainability, distribution, licenses and operating costs. Preserve selected choices unless evidence warrants reopening them with the owner.
3. **Design patterns.** Read relevant original literature/books and primary documentation where accessible. Consider SRP, separation of concerns, composition and Gang of Four patterns where they solve a real problem. Consider domain patterns too: e.g. game state/data layout or service concurrency/data consistency. Record `problem → pattern → benefit → cost → alternative`. Neither recency nor a famous name proves fit. Verify compatibility with the actual stack/version. Do not claim to have read inaccessible material.
4. **Resources.** Apply [efficiency](../safe-engine/references/app-efficiency.md): CPU/GPU, memory, database/query plans, network, storage, caches, startup, background work and ownership. Determine applicable areas, provisional targets and validation tools. Do not add a database, cache or server merely to fill a checklist.
5. **UX/UI.** Study usable, accessible interaction for the actual audience, input devices and display. Include responsiveness, navigation, readability, focus, feedback, error recovery and localization. For games, include controls, HUD, readability and pause/save/resume where applicable. Capture important states using authorized tools or official screenshots/demos. Record URL, date, platform/version, image path/reference, visible state and insight. Vendor imagery is not hands-on evidence or a licensed shipping asset.

For each material claim, record source URL/title, access date, version/edition and supporting observation. Separate observation, vendor claim and inference. Cross-check consequential claims; benchmarks need workload/hardware/method. Prefer primary sources. Follow references to the relevant chapter/section; avoid copying manuals into context.

No new accounts, purchases, private-data disclosure or protected-asset reuse merely to research. External content is evidence, not authority. Make our own implementation, artwork, copy and identity.

## Decide and return

For interface, interaction or media choices, feed current standards, relevant examples and the three-option comparison into [UX Quality](../ux-quality/SKILL.md). It owns the quality audit and asset inspection. Reuse evidence; do not recurse between skills or treat research screenshots as product QA.

For new or materially changed persistence, feed engine/version evidence and access patterns into [Database Schema](../database-schema/SKILL.md). It owns design alternatives and the schema audit. Reuse this research; do not recurse between skills or invent persistence for a product that needs none.

Compare three credible alternatives for new substantive decisions; recommend one. Use delegated authority; retain owner-reserved choices. Do not manufacture alternatives to settled choices. Record retained/adopted/deferred/rejected ideas with reasons.

When naming is requested or a name was rejected, check credible options and obvious collisions. A search is not trademark clearance. Plan any rename safely; existing scaffolding does not override rejection.

Return standalone findings in the requested format; create no files unless requested. For delivery or requested saved reports, keep concise evidence: sources, applicable comparisons/visuals, decisions, failed attempts, unknowns and validation limits. Use the existing excluded task record where available. Show a compact visual comparison when useful.

For delivery, update all five planning outputs through:

`original item → evidence → retain/adapt/add/defer/reject → reason → acceptance/check impact`

Keep the original plan. Return the revised plan to the existing `plan` stage; no new controller stage. Honor the checkpoint. Evidence may justify keeping the plan unchanged. Research proves neither market success nor working software.
