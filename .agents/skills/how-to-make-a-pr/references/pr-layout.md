# PR layout

Contents: sections · building blocks · writing rules · example

Brief words. Full meaning. A human or fresh agent must understand the PR without the chat or the diff.

Order of priority: complete first (every relevant behavior, decision, file, guard, proof and gap), visual second (tables and ASCII before prose), fewest words third (one line where a table or diagram does not fit).

**Title:** concrete change + outcome, as `<type>(<scope>): <subject>`. Use the reader's language; explain needed jargon.

## Sections

Fill the project's PR template first, then use these blocks inside it. Skip what does not apply. Never bury purpose, context or progress inside Before.

```text
<header: requester, deciders, real author, original vs adaptation>
## 🎯 Purpose & goal      short problem, intended result and clickable ticket link
## 🎬 Before & after      one ### per outcome: what it was, what it is, proof the reviewer can open
## 📍 Context             base/branch, code and sources, prior work; facts and unknowns
## 🔧 What & why          approach and reason
## 🔀 Flow                states and branches, failure and recovery
## 🧩 Design / files      options and reason; NEW / M / D + path + purpose
## 🧱 Guards / scope      severity → problem → status; limits; follow-ups
## ✅ Verification        criterion → actual change → exact-candidate proof → gap
## 🚦 Progress / next     done, left, blockers, review state, human step
## 📝 Adjustment history  WHAT / WHY / WHO / result
---
<credit line>           the last line, exactly as in credit.md
```

- **Header:** credit the requester, the deciders and the real human author. Separate original work from a port or adaptation. No invented authorship or tests. No AI or tool trailers: the body ends with the [credit line](credit.md).
- **Context:** the ticket link is clickable and visible, not hidden in a comment. Discussion that triggered the PR is linked too.
- **Before & after:** never skipped; immediately after purpose, ahead of implementation detail. One `### <outcome>` per changed view/state or touched journey, named by its effect (`### 🧾 Invoice totals include tax`, never `### invoice.ts`). Every inventory item maps here; shared proof can be reused with captions or timestamps. Use the capture and recovery procedure in SKILL.md.
- **Outcome declarations:** each outcome has `**Visual:** yes` or `**Visual:** no (<reason>)`, and `**Journey:** yes` or `**Journey:** no (<reason>)`. Use these exact line forms; extra explanation goes on the next line. Nonvisual methods/commands can say no with their concrete reason. A UI run needs a visual outcome. Do not call a real user journey nonvisual merely because the diff changes shared logic.
- **Screenshots:** Visual yes requires `**Before:**` and `**After:**`, each with a different screenshot, or `**Before → After:**` with a two-column image table. Captions identify the state, base/head and criterion. New UI includes the prior entry/empty-state screenshot labeled "did not exist". Neither prose, video nor a code block replaces a screenshot pair.
- **Video:** Journey yes requires `**Video:** [<journey and result>](https://<host>/<clip>.mp4)` (also webm/mov or an HTML video element for an extensionless upload). One outcome per journey; a shared clip must give that journey's start/end timestamps. Show actions, result and relevant changed error/recovery cases. A GIF or still image is only a preview.
- **Media waiver:** only on explicit owner request, scoped to this outcome: `**Media waiver:** screenshots | <exact owner request> | <source>` (first field `screenshots`, `video` or `all`). Repeat only where that request applies; a screenshot waiver does not waive video. It waives that media, not truthful before/after descriptions or other proof. Tool failure or a deadline is no waiver.
- **Nonvisual proof:** `**Before:**` then `**After:**` with fenced output, or `**Before → After:**` and a `diff` block. Server-only work with no affected interactive UI journey needs no media waiver: use matched request/response JSON, status, logs or command results. Explain the observed owner benefit with a short schema, table or labeled flow when useful. Prose or an illustrative diagram alone is no behavioral proof. A waived media-only outcome still describes both states; the explicit waiver explains the absent evidence.
- **Demo context:** state the base and demonstrated candidate, isolated empty slot or seed/reset recipe, viewport/environment, covered journeys and limitations. Record setup/capture/upload duration in the work record, summarize material delay in the PR. Later code changes require a fresh After demonstration; never present failed or stale media as final proof.
- **Cold start:** the PR states the original request and why, decisions with reasons, facts (IDs, paths, repos), current state, remaining steps and blockers. Links are an audit trail, not a substitute.
- **Verification:** one row per confirmed criterion, plus the ticket's checklist state: every item ticked, or the gap. Ticketed work: include the ticket's confirmed revision and digest, dependencies and integration status. Proof is bound to the exact pushed candidate. Name what is **unverified**.
- **Adjustment history:** when changes are requested, append WHAT, WHY, WHO and what was done. Keep it for the PR's whole life.
- **Progress:** checked, reviewed, merged, released stay separate. State what works now, what is missing, the next visible result, and the exact demo context (build, environment, data). Overall acceptance stays open.

## Building blocks

```text
BEFORE                       AFTER
──────────────────────────   ──────────────────────────
<old state>                  <new state>
<failure case>               <success case>

<trigger> ─▶ <step> ─┬─▶ <result A>
                     └─▶ <result B / escalation>

NEW <path>   <purpose>
 M  <path>   <change>
 D  <path>   <why removed>

<check command>   <actual result>
```

````text
### <emoji> <outcome, named by its effect>
**Visual:** yes
**Journey:** yes
**Before:** <what was observed> (base <sha>)
![before](https://github.com/<owner>/<repo>/blob/<proof commit>/<outcome>-before.png?raw=true)
**After:** <what is observed now> (head <sha>, A1)
![after](https://github.com/<owner>/<repo>/blob/<proof commit>/<outcome>-after.png?raw=true)
**Video:** [<journey through its result, 00:00-00:35>](https://github.com/<owner>/<repo>/blob/<proof commit>/<journey>.mp4?raw=true)

### <emoji> <endpoint or command>: <effect>
**Visual:** no (command output only)
**Journey:** no (internal validation, no product interaction changed)
**Before → After:** same request, base <sha> → head <sha> (A2)
```diff
- <old line of output>
+ <new line of output>
```
````

| Criterion | Change | Proof | Gap |
|---|---|---|---|
| A1 | what changed | exact evidence | what is not shown |

- Compare variants across dimensions in a table; mark what is new.
- Put monospace diagrams in code blocks. Bold only key terms.
- Never copy claimed results from a template or example.

## Writing rules

- No em dashes. Use a period, comma, colon or parentheses.
- Cut generic openers, canned summaries, buzzwords, inflated adjectives, filler transitions, "not X, but Y" and slogans. State the point.
- Specific nouns, active verbs, consistent terms. Key facts first.
- Short bullets, narrow tables, flow diagrams. Emojis only to label sections and help scanning.
- No invented facts, metrics, benefits, tests, visuals or consent. Label illustrative examples. Verify names, numbers, units, dates.
- Charts need measured values. Screenshots show real, relevant proof.
- Fold long machine data; keep purpose, outcome, proof, gaps and next action visible.
- One finishing pass: can a cold reader say what, why, before, after and next? Does every outcome show proof they can open? Does every requested detail have a home?

## Example

Illustration only. Real PRs need real code, proof and sources.

**Title: fix(settings): keep chosen theme after reload**

### 🎯 Purpose & goal

- **Purpose:** Theme resets on reload. Users redo setup.
- **Goal:** Reload keeps the chosen theme.
- Ticket: #12 (confirmed rev 1). Base `main`, branch `fix/theme-save`.

### 🎬 Before & after

#### 🎨 Settings: chosen theme survives a reload

**Visual:** yes
**Journey:** yes
**Before → After:** dark theme chosen, page reloaded, 1280×800 (base `a1b2c3d` → head `d4e5f6a`, A1)

| Before | After |
|---|---|
| ![before: light theme after reload](https://example.com/proof/theme-before.png) | ![after: dark theme after reload](https://example.com/proof/theme-after.png) |
**Video:** [Choose dark, reload, force save failure and retry](https://example.com/proof/theme.mp4)

#### 🔌 GET /api/settings: returns the saved theme

**Visual:** no (endpoint response)
**Journey:** no (same settings journey demonstrated above)
**Before → After:** same request after saving dark (A1)

```diff
  200 OK
- {"theme": "light"}
+ {"theme": "dark"}
```

### 📍 Context

- Settings screen calls the theme store, which had no save path. Demo: isolated empty profile, same viewport; capture on the candidate above.

### 🔧 What & why

- **Approach:** Reuse settings storage. One save path.

### 🧩 Files

```text
 M  settings/theme-store    save on change, load on start
NEW settings/theme-save     single save path, returns error result
```

### ✅ Verification

| Criterion | Change | Proof | Gap |
|---|---|---|---|
| A1 save, reload | store saves and loads | before/after screenshots, same viewport | none |
| A2 save fails | error shown, choice kept | forced failure, screenshot | retry on mobile unchecked |

### 🚦 Progress / next

- Draft. Tests and independent review pending. A human decides ready and merge.

---
<the credit line from credit.md>
