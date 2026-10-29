# UX basics: checks, outline, scan, judge

Contents: U1 Map · U2 Navigation · U3 Hierarchy · U4 Disclosure · U5 Labels · Page outline · Scan · Judge · Tree test

Read when writing the brief's Map, Hierarchy and Labels lines, and when auditing.
Check each screen in each state it can be in (empty, in progress, done; signed out, each role) and at each supported width.
`[auto]`: a script or the accessibility tree can check it. `[look]`: needs the rendered screen.

## U1 Map

- One map per audience and sign-in state: every screen, its parent, how a user reaches it. No orphan screens. No dead ends: every screen offers a next step or a way back. [auto]
- Each core object has one name, one list and one detail with its own address. Core destinations sit at most 2 levels below a top section; deeper data uses list and detail side by side, hubs or search. [auto]
- Categories do not overlap; each item has one parent. Every requested need has a screen, and every screen serves a journey. [look]

## U2 Navigation

- Where am I: a unique page title and the H1 repeat the label that led there. The active nav item is marked: `aria-current` plus a cue beyond color. [auto]
- Where can I go: the global nav keeps the same items in the same order on every screen of an audience. Items are destinations, never actions. Text labels stay on. [auto]
- Counts: a phone bottom bar holds 3 to 5 items, a side rail 3 to 7. Tablet and desktop nav stays visible, never only behind a menu button. A phone keeps every item, in a bar or a menu. [auto]
- Nav follows the user's state and role: no links to what they cannot use or have already done, such as sign in while signed in. [auto]
- How do I get back: every screen below the top level has a visible way up, a back link or breadcrumbs from 3 levels, never both. Back and reload restore the view; on web, tabs, filters, selection and page live in the URL. [auto]
- Large sets get search or filters. CLIs: help on every command; a bare run prints usage with an example. [auto]

## U3 Hierarchy

- One primary action per view and state: what most users need next in that state. It changes when the state changes. At most one filled button per view; the rest look quieter. [auto count, look]
- Items waiting on the user (a review, a reply, a payment) show that action on the item, not only a status. [look]
- Blur test (5 to 10 px): the primary content and action dominate; at most 2 large elements. [look]
- Order follows importance from the top and the leading edge. Gaps inside a group are smaller than gaps between groups. [look]
- One H1, no skipped heading levels, reading order equals visual order. [auto]
- Each fact shows once per item: no two badges or texts for the same state. Uniform items that users scan or compare go in a list or table; cards are for browsing mixed content. [look]

## U4 Disclosure

- The default view holds what most users need in the current state. Rare or advanced options sit one step away, behind a trigger that names what it reveals. [look]
- The primary task and must-have facts never live only behind hover, an overflow menu, a collapsed section or a non-default tab. [look]
- At most 2 disclosure levels; no disclosure inside a disclosure. [auto]
- Panels and controls for other states (before or after the current one) are hidden or shrink to a one-line status. They never take prime space. [look]
- Modals only for blocking or irreversible choices; one at a time; close and Escape both work. [auto]
- Wizards only for linear steps users rarely do. Show every step and the current one; back keeps input. [look]

## U5 Labels

- One glossary: one term per object, state, action and result ("Publish", "Published"). The same words in nav, headings, titles, buttons, URLs, messages and notifications. One term never names two things. [auto: compare the outline's labels]
- The users' words, not internal or invented ones. The first 1 or 2 words carry the meaning. Sibling labels do not overlap. [look]
- Buttons: a verb, plus a noun when needed. Links name the destination. Never "click here", a bare "Learn more" or "Submit". One name never leads to two places. [auto]
- Every field has a visible label outside the field, linked to it. A placeholder is a hint at most. [auto]
- Nav icons, and icons that are not near-universal, carry visible text. Each accessible name starts with the visible label. [auto]

## Page outline (web)

Run it in any browser tool that executes page scripts, on each audited screen and state. Compare across screens: nav set and order, the active item (`*`), title and H1 against the clicked label, labels against the glossary, empty action names, fields without labels.

```js
(() => {
  const name = e => (e.getAttribute("aria-label") || e.innerText || e.value || e.title || "").replace(/\s+/g, " ").trim().slice(0, 80);
  const shown = e => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== "hidden"; };
  const all = s => [...document.querySelectorAll(s)].filter(shown);
  const named = e => [...(e.labels || []), ...(e.getAttribute("aria-labelledby") || "").split(" ").map(id => document.getElementById(id))]
    .some(label => label && shown(label));  // a label people can see, not only aria-label or a visually hidden one
  const root = document.documentElement;
  return {
    title: document.title,
    headings: all("h1,h2,h3,h4,h5,h6").map(h => `${h.tagName} ${name(h)}`),
    landmarks: all("header,nav,main,aside,footer,[role=banner],[role=navigation],[role=main],[role=contentinfo]").map(e => e.getAttribute("role") || e.tagName.toLowerCase()),
    nav: all("nav a,[role=navigation] a").map(a => (a.getAttribute("aria-current") ? "* " : "") + name(a)),
    actions: all("button,a[href],[role=button]").map(name),
    unlabeled: all("input:not([type=hidden]),select,textarea").filter(e => !named(e)).map(e => e.placeholder || e.name || e.type),
    sideScroll: root.clientWidth ? root.scrollWidth > root.clientWidth : null  // null: hidden tab, no width
  };
})()
```

## Scan (web)

- axe-core through the project's browser automation, or injected into the page, with tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`, `best-practice`.
- Results feed the verdicts: `label`, `button-name`, `link-name`, `select-name` (U5); `page-has-heading-one`, `heading-order`, `empty-heading` (U3); `document-title`, `landmark-one-main`, `region`, `bypass` (U2); `color-contrast`, `target-size` and the rest (U8).
- Put the counts in the verdict line (`axe: 0 violations`). A clean scan is an automated pass, never proof of accessibility.
- Other platforms: the platform's accessibility inspector where one exists; otherwise the judge and manual use.

## Judge

- A mid-size model is enough. Prefer a different model family from the builder's when the host offers one.
- Inputs: the brief (Journeys, Map, Hierarchy, Labels), the shots of one journey together, each screen's outline and scan, and the use log. No other build notes or opinions.
- For each ID, answer its checks screen by screen, yes or no. Evidence only the use log holds is marked "per use log". No quotas: a clean rule is a PASS. Rules the change cannot touch: N/A with the reason.
- Many screens: one judge per journey in parallel, then one pass across all screens for U2, U5 and U9.
- Never loop until a judge finds nothing.
- Example lines: `U3 PASS schedule, roster (375, 1280): one filled button each` and `U5 FAIL checkout, phone: the note field shows only the placeholder "Add a note"`.
- The done-run's `**UX judge:**` line names the judge and its inputs.

## Tree test (before UI code)

- Walk the Map and Labels as a text tree against 3 to 5 top tasks; record where each starts. Use an independent reader when label ambiguity needs it.
- A missed task: rename or regroup before building. Record `tree test <passed>/<tasks>` in the Map line.
- Only failures count: models find items that people miss.
