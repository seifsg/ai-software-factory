# PR layout

Contents: sections · building blocks · writing rules · example

Brief words, full meaning: a human or fresh agent must understand the PR without the chat or the diff. Priority: complete first (every relevant behavior, decision, file, guard, proof and gap), visual second (tables and ASCII before prose), fewest words third (one line where a table or diagram does not fit).

**Title:** concrete change + outcome, as `<type>(<scope>): <subject>`, in the reader's language; explain needed jargon.

## Sections

Fill the project's PR template first, then use these blocks inside it. Skip what does not apply. Never bury purpose, context or progress inside Before.

```text
<header: requester, deciders, who wrote it, original vs adaptation>
## 🎯 Purpose & goal      short problem, intended result and clickable ticket link
## 🎬 Before & after      one ### per outcome: what it was, what it is, proof the reviewer can open
## 📍 Context             base/branch, code and sources, prior work; facts and unknowns
## 🔧 What & why          approach and reason
## 🔀 Flow                states and branches, failure and recovery
## 🧩 Design / files      options and reason; NEW <path> <purpose>, M <path> <change>, D <path> <why removed>
## 🧱 Guards / scope      severity → problem → status; limits; follow-ups
## ✅ Verification        criterion → actual change → exact-candidate proof → gap
## 🚦 Progress / next     done, left, blockers, review state, human step
## 📝 Adjustment history  WHAT / WHY / WHO / result
---
<credit line>           the last line, exactly as in credit.md
```

- **Header:** credit the requester and deciders and say who wrote the code (a person, or the factory run for its owner); separate original work from a port or adaptation.
- **Context:** link the discussion that triggered the PR; the ticket link stays visible, not hidden in a comment.
- **Before & after:** never skipped; right after purpose, ahead of implementation detail. One `### <outcome>` per changed view/state or touched journey, named by its effect (`### 🧾 Invoice totals include tax`, never `### invoice.ts`). Every inventory item maps here; reuse shared proof with captions or timestamps.
- **Outcome declarations:** each outcome has `**Visual:** yes` or `**Visual:** no (<reason>)`, and `**Journey:** yes` or `**Journey:** no (<reason>)`, in these exact forms; extra explanation on the next line. A UI run needs a visual outcome. Never call a real user journey nonvisual merely because the diff changes shared logic.
- **Screenshots:** Visual yes requires `**Before:**` and `**After:**`, each with a different screenshot or a `pane:` observation (what the built-in browser showed: view, state, viewport, time) when the host cannot save the image, or `**Before → After:**` with a two-column image table. Captions identify state, base/head and criterion. A new surface's Before is `**Before:** did not exist`, with no image or observation. Prose, video or a code block never replaces a screenshot pair.
- **Video:** optional. Journey yes needs the journey's steps shown: screenshots, a GIF or a `**Video:**` link, as the owner asks; a shared clip gives that journey's start/end timestamps.
- **Media waiver:** scoped to this outcome: `**Media waiver:** screenshots | <exact owner request> | <source>` (`screenshots`, `video` or `all`), only where that request applies; a screenshot waiver does not waive video. It waives that media, not the truthful description of both states or other proof.
- **Nonvisual proof:** matched request/response JSON, status, logs or command results: `**Before:**` then `**After:**` with fenced output, or `**Before → After:** <same input>, base <sha> → head <sha> (<criterion>)` and a `diff` block. Server-only, infrastructure or internal work with no affected interactive UI journey needs no media waiver.
- **Demo context:** base and demonstrated candidate, isolated empty slot or seed/reset recipe, viewport/environment, covered journeys and limitations.
- **Cold start:** the original request and why, decisions with reasons, facts (IDs, paths, repos), current state, remaining steps and blockers. Links are an audit trail, not a substitute.
- **Verification:** one row per confirmed criterion, plus the ticket's checklist state: every item ticked, or the gap. Ticketed work: the ticket's confirmed criteria, dependencies and integration status. Proof is bound to the exact pushed candidate. Name what is **unverified**.
- **Adjustment history:** append an entry per requested change; keep it for the PR's whole life.
- **Progress:** checked, reviewed, merged and released stay separate; name the next visible result. Overall acceptance stays open.

## Building blocks

```text
<trigger> ─▶ <step> ─┬─▶ <result A>
                     └─▶ <result B / escalation>

<check command>   <actual result>
```

```text
### <emoji> <outcome, named by its effect>
**Visual:** yes
**Journey:** yes
**Before:** <what was observed> (base <sha>)
![before](https://<host>/<outcome>-before.png)
**After:** <what is observed now> (head <sha>, A1)
![after](https://<host>/<outcome>-after.png)
**Video:** [<journey through its result, 00:00-00:35>](https://<host>/<journey>.mp4)
```

- Compare variants across dimensions in a table; mark what is new.
- Put monospace diagrams in code blocks. Bold only key terms.
- Never copy claimed results from a template or example.

## Writing rules

- No em dashes. Use a period, comma, colon or parentheses.
- Cut generic openers, canned summaries, buzzwords, inflated adjectives, filler transitions, "not X, but Y" and slogans. State the point, key facts first.
- Specific nouns, active verbs, consistent terms, short bullets, narrow tables. Emojis only to label sections and aid scanning.
- No invented facts, metrics, benefits, tests, visuals, authorship or consent; charts need measured values; screenshots show real, relevant proof. Label illustrative examples. Verify names, numbers, units, dates.
- Fold long machine data; keep purpose, outcome, proof, gaps and next action visible.
- Finishing pass: can a cold reader say what, why, before, after and next, open every outcome's proof, and find every requested detail?

## Example

Illustration only.

**Title: fix(settings): keep chosen theme after reload**

### 🎯 Purpose & goal

- **Purpose:** Theme resets on reload.
- **Goal:** Reload keeps the chosen theme.
- Ticket: #12 (confirmed rev 1). Base `main`, branch `fix/theme-save`.

### 🎬 Before & after

#### 🎨 Settings: chosen theme survives a reload

**Visual:** yes
**Journey:** yes
**Before → After:** dark chosen, page reloaded, 1280×800 (base `a1b2c3d` → head `d4e5f6a`, A1)

| Before | After |
|---|---|
| ![before: light after reload](https://example.com/b.png) | ![after: dark after reload](https://example.com/a.png) |

**Video:** [Choose dark, reload, force save failure, retry](https://example.com/theme.mp4)

#### 🔌 GET /api/settings: returns the saved theme

**Visual:** no (endpoint response)
**Journey:** no (journey shown above)
**Before → After:** same request after saving dark, base `a1b2c3d` → head `d4e5f6a` (A1)

```diff
  200 OK
- {"theme": "light"}
+ {"theme": "dark"}
```

### 📍 Context

- Theme store had no save path. Demo: isolated empty profile, same viewport.

### 🔧 What & why

- **Approach:** reuse settings storage, one save path.

### 🧩 Files

```text
 M  settings/theme-store    save on change, load on start
NEW settings/theme-save     single save path, returns error result
```

### ✅ Verification

| Criterion | Change | Proof | Gap |
|---|---|---|---|
| A1 save, reload | store saves and loads | screenshot pair | none |
| A2 save fails | error shown, choice kept | forced failure, screenshot | mobile retry unchecked |

### 🚦 Progress / next

- Draft; tests and independent review pending. A human decides ready and merge.

---
<the credit line from credit.md>
