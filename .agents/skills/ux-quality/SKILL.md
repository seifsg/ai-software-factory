---
name: ux-quality
description: "Plans and audits the user experience of any UI or interaction change: map, navigation, hierarchy, disclosure, labels, flows, interaction cost, states, accessibility, responsiveness, visuals, icons, images and sound. Use when building, changing or reviewing anything a person sees, hears or operates, including small fixes."
---

# UX Quality

Make the user's job easy. Simple. Familiar. Fast. Accessible.
No confusing or needless steps. No unfinished graphics or sounds sold as finished work.

Covers every UI or interaction change: games, web, mobile, desktop, tools a person operates. Tiny fix, tiny pass. Headless internals need no invented UI or audio.
Review and design requests stay read-only. Do not code unless told.

## 1. Understand the job

- Read the request, the design system, the actual interface and settled choices.
- Record audience, goal, devices and inputs, accessibility needs, success and failure states.
- Map each core journey: `intent → entry → actions/decisions/waits → outcome → recovery/exit`. For the most common case, count its actions from entry (each click, tap, submit or filled field) and its loads (new pages or screens; dialogs, tabs and expands are not loads). The minimum is the fewest actions the job itself needs, whatever the design. Above it needs a reason, such as deliberate friction. Find repeated entry, confusion, dead ends, lost work.
- Remove accidental effort. Keep intended game challenge, consent, safety and comprehension. No deceptive defaults, no hidden costs.
- New UI or new look: fix the design brief before UI code. Use the project's visual defaults when it has them. A change records only what it touches.
  - Look: `**UI kit:**`, palette as hex tokens (≥4, AA contrast), `**Font:**`, `**Logo:**`, `**Icons:**`, `**Layout:**` (header, content, footer, phone to desktop), `**Theme:**` (light by default).
  - `**Journeys:**` per core journey: `<journey>: <n> actions, <n> loads, min <n> actions`, plus the reason for any gap.
  - `**Map:**` every screen per audience and sign-in state, its parent, the nav pattern per width (U1, U2). Tree test it first: `references/basics.md`.
  - `**Hierarchy:**` per key screen and state: the primary action, then secondary ones, then what is deferred (U3, U4).
  - `**Labels:**` the glossary: one term per object, state, action and result (U5).
- Map, Hierarchy, Labels and the rules below: read `references/basics.md`.
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
- Owner-specified UX that counts above the minimum without a reason, or breaks step 3: name the cost, show the better option, ask once before building. Until the answer, the brief records both options' counts. Build what the owner confirms.
- Delegated in-scope choices are yours. Ask the owner only for reserved decisions, missing access or consequential ambiguity. No implied purchase, account, rights exception or release.
- Source you cannot reach stays unverified. Find a permitted alternative.

## 3. Apply the quality rules

Every audit gives each ID a verdict. U1 to U5 are spelled out as checks in `references/basics.md`.

| ID | Area | Require |
|---|---|---|
| U1 | Map | One map per audience and sign-in state: every screen has a parent and a way in. No orphans, no dead ends. Each core object has one name, one list and one detail. Core destinations sit at most 2 levels below a top section. |
| U2 | Navigation | Where am I: a unique title and the H1 repeat the label that led there; the active item is marked beyond color. Where can I go: the same nav in the same order on every screen of an audience, destinations only, text labels on, nothing lost at a breakpoint. Nav follows state and role. A visible way up below the top level; back and reload restore the view. Platform and design-system navigation, back and shortcuts. |
| U3 | Hierarchy | One primary action per view and state: what most users need next there. At most one filled button. Items waiting on the user show that action on the item. The primary content and action dominate a blurred view. Order follows importance; related items group. One H1, no skipped heading levels. Each fact once per item. |
| U4 | Disclosure | The default view holds what most users need in this state. Rare or advanced work sits one named step away, never in the way. The primary task and must-have facts are never only behind hover, overflow, a collapsed section or another tab. At most 2 levels. Panels for other states shrink to a one-line status. Modals only for blocking or irreversible choices. |
| U5 | Labels | One glossary, the same in nav, headings, titles, buttons, URLs and messages; one term never names two things. Plain words the users use, front-loaded, distinct from their siblings. Buttons say what happens; links name where they go. Visible field labels; a placeholder never replaces one. Icons carry text unless near-universal. |
| U6 | Interaction cost | Fewest actions and loads from entry to outcome. Primary content and the next action show where the user lands. No page whose only job is one link. Useful defaults. No duplicate entry. Design collections for 0, 1, few and many: one item shows in place (no list of one), a few stay in place too (tabs, sections, cards with their actions), many (more than one screen) get search, sort or filter, and list and detail side by side on wide screens. Deliberate friction stays: consent, destructive confirms, intended challenge. |
| U7 | States and feedback | Loading. Empty, with the next action. Error, with retry. Success. Plus validation, offline, permission where they apply. Explain disabled actions. Block double submit. Keep input. Cancel, back, undo reachable. Immediate, truthful feedback. Predictable focus. Motion explains, never delays. Saves and drafts survive interruption. Games and browsers: focus loss, tab hide, resize, rotation, pause, resume, audio focus. Games: controls, HUD, remapping. |
| U8 | Access and devices | Semantic controls, labels, logical focus order, keyboard and assistive access, contrast, scaling and reflow, usable targets. Never rely on color, sound, hover or gesture alone. Reduced motion. Alternative to dragging. WCAG 2.2 AA for web, or the project's stricter rule. Phone to desktop: no horizontal scroll, clipped labels or unreachable controls. Every supported input works: keyboard, pointer, touch, controller. |
| U9 | Look and consistency | Coherent type, spacing, alignment, color, density. One icon family. Light mode default. No blurry scaling, mismatched styles, unexplained symbols or placeholders. The same component, place and label for the same job on every screen. Platform and design-system selection, editing and symbols; depart only for evidenced benefit. |
| U10 | Performance | Set response, load and animation targets for the weakest supported device. Check asset, decode, memory and network cost. No polish-induced stalls. |

## 4. Use it. Audit it.

1. Finish implementation first. No product testing before then.
2. Use it by hand through the real browser, native app, game or CLI. Complete the journey, its failure and recovery states, each supported input and display variant. Recount each core journey; above its recorded minimum without the reason is a FAIL.
3. Read the logs. Inspect rendered assets at real size and theme. Listen to sounds in context. Screenshots cannot prove interaction. Filenames and waveforms cannot prove sound quality.
4. Capture each core screen in each of its states at the main width, plus once at the other width (phone and desktop). First viewport and full page. Web: run the page outline and the scan from `references/basics.md` on each.
5. A fresh agent that did not build it judges, as `references/basics.md` sets out: one line per ID, `U3 FAIL <screen, state>: <element, quoted text>`, or PASS, or N/A or UNKNOWN with the reason. A FAIL names its rule, an in-scope screen and the visible evidence.
6. Fix in-scope FAILs, recapture, and the judge rechecks those IDs once. A FAIL the builder contests becomes UNKNOWN with both reasons, for the owner. Findings outside the change go to the follow-ups ticket.
7. No hearing, device, assistive tool or runtime available? UNKNOWN. Name the check needed. A walkthrough of the instructions proves no real-user usability.
8. After manual use passes, write and run the accessibility, interaction and other final checks. Automation proves neither aesthetics nor manual use.

Handoff: choices, asset sources and rights, findings and fixes, limits.
No UX-ready claim with open in-scope failures or required UNKNOWNs. Unrelated findings stay proposals.
