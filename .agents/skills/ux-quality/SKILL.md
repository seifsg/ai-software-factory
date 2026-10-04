---
name: ux-quality
description: "Plan and audit user-facing interfaces, interactions, visuals and audio. Apply to every UI change, including small fixes; research uncertain choices, compare three credible options and verify the actual experience. Review-only stays read-only."
---

# UX Quality

Make the user's job easy. Clean. Familiar. Fast. No confusing steps. No throwaway graphics or sounds passed off as finished work.

Use for every UI or interaction change, including games, web/mobile/desktop apps and human-facing tools. Cover the affected journey and shared consumers; a tiny fix does not authorize a redesign. Headless internals need no invented screen or sound. Analysis/design/review-only requests keep their phase.

## 1. Understand the job

Read the request, existing design system, real interface and settled choices. Reuse original analysis/planning; keep the existing file-summary checkpoint and 0–4 loop. Record audience, goal, supported devices/inputs, accessibility needs and success/failure states.

Map `intent → entry → actions/decisions/waits → outcome → recovery/exit`. Count steps and repeated entry; identify confusion, dead ends and lost work. Optimize total effort and successful completion, not click count alone. Keep necessary consent, safety and comprehension. No deceptive defaults or hidden costs.

## 2. Research. Compare. Choose.

Before choosing an uncertain interaction, visual, icon, sound or tool, look it up. Use [Research Market](../research-market/SKILL.md) for current official platform/design/accessibility guidance and relevant leading products. Record URLs, checked date, applicable versions and actual observations. Verify leadership claims; popularity is not proof of fit. Use today's evidence, not a frozen year or remembered trend. Keep proven patterns when they serve users better.

List the three strongest credible options for the actual choice. Compare task clarity, steps/effort, platform familiarity, accessibility, visual/audio fit, runtime cost, compatibility and asset rights. Show samples or demos when available; distinguish inspected examples from hearsay. If fewer options are viable, explain why; no fake third contender. Preserve settled choices and adequate existing assets; do not reopen every icon in a small fix.

Recommend one. Explain why it wins, the tradeoff and evidence that could change the choice. Then use it under delegated authority. Do useful work autonomously; ask only for reserved decisions, missing access or consequential ambiguity. No purchase, new account, rights exception or production release is implied. An inaccessible source stays unverified; find a permitted alternative.

## 3. Apply the quality rules

| Area | Required result |
|---|---|
| Simplicity | Clear primary action, plain user language, useful defaults, no duplicate entry or unnecessary screens. Reveal detail when needed; keep advanced work reachable. |
| Familiarity | Follow the target platform and existing coherent design system: navigation, back, selection, editing, shortcuts and common symbols. Depart only with a user benefit and evidence. |
| State and recovery | Complete loading, empty, success, validation, error, offline and permission states where relevant. Explain disabled actions. Prevent double submission; preserve input. Reachable cancel/back/undo/retry and truthful exit. |
| Accessibility | Semantic controls, meaningful labels, logical focus/order, keyboard/assistive access, readable contrast, text scaling/reflow and usable targets. Never rely only on color, sound, hover or a gesture. Respect reduced motion; offer alternatives to dragging. Apply current platform guidance and WCAG 2.2 AA for web unless a stricter project requirement governs. |
| Visual craft | Consistent hierarchy, typography, spacing, alignment, color, density, imagery and icon family. Inspect actual sizes, themes, supported languages and small/large displays. No blurry scaling, clipped labels, mismatched styles, unexplained symbols or unfinished placeholders. |
| Interaction | Immediate truthful feedback, predictable focus/navigation and interruption handling. Motion explains change; it does not delay work. Preserve saves/drafts and relevant game controls, HUD, pause/resume and input remapping. |
| Performance | Set workload/device targets for response, loading and animation. Check actual low-end target behavior, asset/decode/memory/network costs and reduced-motion paths through [efficiency](../safe-engine/references/app-efficiency.md). Visual polish cannot justify stalls. |

For visual or audio assets, read [asset quality and source selection](references/assets-and-sources.md). Pick the best fit, not the most expensive or largest file. No audio is needed where silence serves the task. Intentional stylization or a simple sound can be excellent; uninspected placeholders cannot.

## 4. Use it. Audit it.

Finish implementation first. Then manually complete the changed journey through actual browser/native/game/CLI controls. Include relevant failure/recovery states and supported input/display variants. Inspect [logs](../safe-engine/references/app-diagnostics.md); capture safe before/after evidence and steps, delays, mistakes or ambiguity observed. Inspect rendered assets and listen to actual audio in context. A screenshot cannot prove interaction; filenames and waveforms cannot prove sound quality.

Record `criterion → action/device/state → observation/evidence → PASS / FAIL / UNKNOWN / justified N/A`. Fix supported in-scope failures and exercise again. Unavailable hearing, device, assistive tool or runtime access stays UNKNOWN; request the missing check rather than certify unseen/unheard quality. An agent walkthrough validates instructions, not product usability with real users.

After passing manual QA, author/polish/run relevant automated checks at the final stage under [tests-last order](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests). Include accessibility/interaction checks when applicable; automation cannot establish aesthetic quality or replace manual use.

Use the existing independent reviewer to assess this UX evidence; no extra fleet for a small change. Carry selected options, asset provenance, findings/fixes and unverified limits into the normal handoff. No UX-ready claim with unresolved in-scope failures or unknown required evidence. New unrelated opportunities remain proposals; do not quietly expand the build.
