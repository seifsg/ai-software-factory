# PR layout

Brief words. Full meaning. A human or fresh agent must understand the PR without the chat or the diff.

Order of priority: complete first (every relevant behavior, decision, file, guard, proof and gap), visual second (tables and ASCII before prose), fewest words third (one line where a table or diagram does not fit).

**Title:** concrete change + outcome, as `<type>(<scope>): <subject>`. Use the reader's language; explain needed jargon.

## Sections

Fill the project's PR template first, then use these blocks inside it. Skip what does not apply. Never bury purpose, context or progress inside Before.

```text
<header: requester, deciders, real author, original vs adaptation>
## 🎯 Purpose & goal      problem, who is affected, consequence, why needed; exact success
## 📍 Context             base/branch, ticket link, code and sources, prior work; facts and unknowns
## 🔧 What & why          Before → After (behavior only); approach and reason
## 🔀 Flow                states and branches, failure and recovery
## 🧩 Design / files      options and reason; NEW / M / D + path + purpose
## 🧱 Guards / scope      severity → problem → status; limits; follow-ups
## ✅ Verification        criterion → actual change → exact-candidate proof → gap
## 🚦 Progress / next     done, left, blockers, review state, human step
## 📝 Adjustment history  WHAT / WHY / WHO / result
```

- **Header:** credit the requester, the deciders and the real human author. Separate original work from a port or adaptation. No invented authorship or tests. No AI or tool trailers.
- **Context:** the ticket link is clickable and visible, not hidden in a comment. Discussion that triggered the PR is linked too.
- **Cold start:** the PR states the original request and why, decisions with reasons, facts (IDs, paths, repos), current state, remaining steps and blockers. Links are an audit trail, not a substitute.
- **Verification:** one row per confirmed criterion. Ticketed work: include the ticket's confirmed revision and digest, dependencies and integration status. Proof is bound to the exact pushed candidate. Name what is **unverified**.
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
- One finishing pass: can a cold reader say what, why, before, after and next? Does every requested detail have a home?

## Example

Illustration only. Real PRs need real code, proof and sources.

**Title: fix(settings): keep chosen theme after reload**

### 🎯 Purpose & goal

- **Purpose:** Theme resets on reload. Users redo setup.
- **Goal:** Reload keeps the chosen theme.

### 📍 Context

- Ticket: #12 (confirmed rev 1). Base `main`, branch `fix/theme-save`.
- Settings screen calls the theme store, which had no save path.

### 🔧 What & why

| Before | After |
|---|---|
| Reload restores default | Reload restores saved choice |

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
