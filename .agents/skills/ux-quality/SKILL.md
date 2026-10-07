---
name: ux-quality
description: "Plans and audits the user experience of any UI or interaction change: flows, interaction cost, states, accessibility, responsiveness, visuals, icons, images and sound. Use when building, changing or reviewing anything a person sees, hears or operates, including small fixes."
---

# UX Quality

Make the user's job easy. Simple. Familiar. Fast. Accessible.
No confusing or needless steps. No unfinished graphics or sounds sold as finished work.

Covers every UI or interaction change: games, web, mobile, desktop, tools a person operates. Tiny fix, tiny pass. Headless internals need no invented UI or audio.
Review and design requests stay read-only. Do not code unless told.

## 1. Understand the job

- Read the request, the design system, the actual interface and settled choices.
- Record audience, goal, devices and inputs, accessibility needs, success and failure states.
- Map each core journey: `intent → entry → actions/decisions/waits → outcome → recovery/exit`. Count its actions (clicks, taps, submits) and page or screen loads for the most common case. The minimum is the fewest actions the job itself needs, whatever the design. Above it needs a reason. Find repeated entry, confusion, dead ends, lost work.
- Remove accidental effort. Keep intended game challenge, consent, safety and comprehension. No deceptive defaults, no hidden costs.
- New UI or new look: fix the design brief before UI code. `**UI kit:**`, palette as hex tokens (≥4, AA contrast), `**Font:**`, `**Logo:**`, `**Icons:**`, `**Layout:**` (header, content, footer, phone to desktop), `**Theme:**` (light by default), `**Journeys:**` (per core journey: `<journey>: <n> actions, <n> loads, min <n>`, plus the reason for any gap). Use the project's visual defaults when it has them.
- Any user-facing text (labels, buttons, empty states, errors, pages): read `references/copy.md`.
- Icons, images, motion, sound: read `references/assets.md`.
- Public pages meant for search: read `references/web-seo.md`. Private screens stay out.

## 2. Research. Compare. Choose.

Uncertain interaction, layout, icon, image or sound? Research before choosing.

- Current official platform, design-system and accessibility guidance.
- 3 to 5 leading products doing the same job. Say why each. Popularity proves no fit.
- Record URL, version, what you observed. Vendor claims and marketing shots are not hands-on evidence.
- Substantive choice: compare three credible options on clarity, steps, familiarity, accessibility, visual or audio fit, runtime cost, compatibility, rights. Show samples. Recommend one: why, tradeoff, what would change it. Fewer than three viable: say why. Invent none.
- Settled choices stay. Adequate assets stay. Do not replace them just to compare.
- Owner-specified UX that adds interaction cost or breaks step 3: name the cost, show the better option, ask once before building. Until the answer, the brief records both options' counts. Build what the owner confirms.
- Delegated in-scope choices are yours. Ask the owner only for reserved decisions, missing access or consequential ambiguity. No implied purchase, account, rights exception or release.
- Source you cannot reach stays unverified. Find a permitted alternative.

## 3. Apply the quality rules

| Area | Require |
|---|---|
| Simplicity | One clear primary action. Plain language. Useful defaults. No duplicate entry. Advanced work reachable, not in the way. |
| Interaction cost | Fewest actions and loads from entry to outcome. Primary content and the next action show where the user lands. No page whose only job is one link. Design collections for 0, 1, few and many: one item shows in place (no list of one), a few stay in place too (tabs, sections, cards with their actions), many get search, sort or list and detail side by side. Defer only rare or advanced features, never the primary task. Deliberate friction stays: consent, destructive confirms, intended challenge. |
| Familiarity | Follow platform and design-system navigation, back, selection, editing, shortcuts, symbols. Depart only for evidenced benefit. |
| States | Loading. Empty, with the next action. Error, with retry. Success. Plus validation, offline, permission where they apply. Explain disabled actions. Block double submit. Keep input. Cancel, back, undo reachable. |
| Accessibility | Semantic controls, labels, logical focus order, keyboard and assistive access, contrast, scaling and reflow, usable targets. Never rely on color, sound, hover or gesture alone. Reduced motion. Alternative to dragging. WCAG 2.2 AA for web, or the project's stricter rule. |
| Responsive | Phone to desktop. No horizontal scroll, clipped labels or unreachable controls. Every supported input works: keyboard, pointer, touch, controller. |
| Visuals | Coherent hierarchy, type, spacing, alignment, color, density. One icon family. Light mode default. No blurry scaling, mismatched styles, unexplained symbols or placeholders. |
| Interaction | Immediate, truthful feedback. Predictable focus and navigation. Motion explains, never delays. Saves and drafts survive interruption. Games and browsers: focus loss, tab hide, resize, rotation, pause, resume, audio focus. Games: controls, HUD, remapping. |
| Performance | Set response, load and animation targets for the weakest supported device. Check asset, decode, memory and network cost. No polish-induced stalls. |

## 4. Use it. Audit it.

1. Finish implementation first. No product testing before then.
2. Use it by hand through the real browser, native app, game or CLI. Complete the journey, its failure and recovery states, each supported input and display variant. Recount each core journey; above its recorded minimum without the reason is a FAIL.
3. Read the logs. Inspect rendered assets at real size and theme. Listen to sounds in context. Screenshots cannot prove interaction. Filenames and waveforms cannot prove sound quality.
4. Record `criterion → action/device/state → evidence → PASS / FAIL / UNKNOWN / N/A with reason`.
5. Fix in-scope failures. Re-run the affected paths.
6. No hearing, device, assistive tool or runtime available? UNKNOWN. Name the check needed. A walkthrough of the instructions proves no real-user usability.
7. After manual use passes, write and run the accessibility, interaction and other final checks. Automation proves neither aesthetics nor manual use.

Handoff: choices, asset sources and rights, findings and fixes, limits.
No UX-ready claim with open in-scope failures or required UNKNOWNs. Unrelated findings stay proposals.
