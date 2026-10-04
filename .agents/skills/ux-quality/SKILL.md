---
name: ux-quality
description: "Plan and audit every UI change, including small fixes: interactions, visuals and audio. Research uncertain choices, compare three options and verify the experience. Review-only stays read-only."
---

# UX Quality

Make the user's job easy. Clean. Familiar. Fast. No confusing steps or unfinished graphics/sounds sold as finished work.

Every UI/interaction change: games, web/mobile/desktop apps and human-facing tools. Cover the affected journey and shared consumers. Tiny fixes stay tiny; headless internals need no invented UI/audio. Analysis/design/review keeps its phase.

## 1. Understand the job

Apply [Clear Writing](../safe-engine/references/clear-writing.md) to UI/page copy: specific headlines, supported claims, clear actions. Inspect text in the real layout.

Read request, design system, actual interface and settled choices. Reuse original analysis/planning; preserve the file-summary checkpoint and 0–4 loop. Record audience, goal, supported devices/inputs, accessibility needs and success/failure states.

Map `intent → entry → actions/decisions/waits → outcome → recovery/exit`. Count steps/repeated entry; find confusion, dead ends and lost work. Minimize total effort, not clicks alone. Preserve consent, safety and comprehension. No deceptive defaults or hidden costs.

## 2. Research. Compare. Choose.

Before an uncertain interaction, visual, icon, sound or tool choice, use [Research Market](../research-market/SKILL.md): current official platform/design/accessibility guidance and relevant leading products. Record URLs, date, versions and observations. Verify leadership claims; popularity or novelty alone proves no fit. Keep useful proven patterns; no frozen year.

Compare three credible options: clarity, steps/effort, familiarity, accessibility, visual/audio fit, runtime cost, compatibility and rights. Show available samples/demos; distinguish inspected evidence from hearsay. Fewer viable options? Explain why. No fake contenders, reopened settled choices or replacement of adequate assets just to compare.

Recommend one; explain the win, tradeoff and evidence that would change it. Use delegated authority. Ask only for reserved decisions, missing access or consequential ambiguity. No implied purchase, account, rights exception or release. Inaccessible sources stay unverified; seek permitted alternatives.

## 3. Apply the quality rules

| Area | Require |
|---|---|
| Simplicity | Clear primary action, plain user language, useful defaults; no duplicate entry or needless screens. Reveal detail when needed; keep advanced work reachable. |
| Familiarity | Follow platform/design-system navigation, back, selection, editing, shortcuts and symbols. Depart only with evidenced user benefit. |
| State/recovery | Relevant loading, empty, success, validation, error, offline and permission states. Explain disabled actions. Prevent double submission; preserve input. Reachable cancel/back/undo/retry and truthful exit. |
| Accessibility | Semantic controls, meaningful labels, logical focus/order, keyboard/assistive access, contrast, scaling/reflow, usable targets. Never rely solely on color/sound/hover/gesture. Reduced motion; dragging alternatives. Current platform guidance; WCAG 2.2 AA for web or stricter project requirements. |
| Visuals | Coherent hierarchy, typography, spacing, alignment, color, density, imagery and icon family. Inspect actual sizes, themes, languages and small/large displays. No blurry scaling, clipped labels, mismatched styles, unexplained symbols or unfinished placeholders. |
| Interaction | Immediate truthful feedback; predictable focus/navigation and interruption handling. Motion explains, never delays. Preserve saves/drafts; applicable game controls, HUD, pause/resume and remapping. |
| Performance | Set device/workload targets for response/loading/animation. Check low-end target behavior and asset/decode/memory/network costs, including reduced-motion paths, through [efficiency](../safe-engine/references/app-efficiency.md). No polish-induced stalls. |

For visuals/audio, read [asset quality](references/assets-and-sources.md). Best fit beats price/file size. Silence may serve better. Intentional stylization/simple sounds can be excellent; inspect them.

## 4. Use it. Audit it.

Finish implementation. Manually complete the journey through actual browser/native/game/CLI controls: relevant failure/recovery states and supported input/display variants. Read [logs](../safe-engine/references/app-diagnostics.md); capture safe before/after evidence, steps, delays, mistakes and ambiguity. Inspect rendered assets; listen in context. Screenshots cannot prove interaction; filenames/waveforms cannot prove sound quality.

Record `criterion → action/device/state → observation/evidence → PASS / FAIL / UNKNOWN / justified N/A`. Fix in-scope failures; re-exercise affected paths. Missing hearing/device/assistive tools/runtime stays UNKNOWN; request that check. Instruction walkthroughs do not prove real-user usability.

After passing manual QA, author/polish/run applicable accessibility/interaction and other final checks under [tests-last order](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests). Automation proves neither aesthetics nor manual use.

Reuse the independent reviewer; no extra fleet. Handoff: choices, asset provenance, findings/fixes and limits. No UX-ready claim with unresolved in-scope failures or required unknowns. Unrelated opportunities stay proposals.
