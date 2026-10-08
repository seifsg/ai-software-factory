# Ticket layout

Brief words. Full meaning. A human or fresh agent must understand the ticket without the chat.

**Title:** concrete change + outcome. Use the reader's language; explain needed jargon.

## Sections

Skip what does not apply. Keep each block separate. Never bury purpose, context or progress inside Before.

| Section | Put here |
|---|---|
| 📥 Request | The owner's original words, verbatim. Why, examples, supplied evidence, source, date, who decided. Later corrections are appended, never overwritten. |
| 🎯 Purpose & goal | **Purpose:** problem, who is affected, consequence, why now. **Goal:** exact success. |
| 📍 Context | Code and consumers (paths), baseline, sources, prior work and PRs. Label fact, inference, unknown. |
| 🔧 Before → after | Behavior only, in a table or paired blocks. **Before** = actual current behavior, read from code and existing evidence. New capability: say what does not exist yet. Non-visual work: name the real consumer and output. **Approach:** the choice and its reason. |
| 🔀 Flow | Entry → action → effect → result, plus relevant failure and recovery. ASCII for branches and state. |
| ✅ Done when | One observable result per criterion, stable ID (A1, A2). Cover success, failure, recovery, preserved behavior. No "works", "best" or "optimized" without a check. |
| 🧱 Scope & guardrails | In, out, constraints, dependencies, decisions (approved, rejected, pending), optional wants, finish boundary. Each deferral: owner, destination ticket, revisit condition. |
| 🚦 Progress / next | Status, priority, assignee. Done, left, phase, next action, blockers, linked PR or branch. Checked, reviewed, merged, released stay separate. |
| 📝 Activity | The ticket's lifetime timeline. One entry per change: date, who, old → new, why, proof link. Append only. Trackers with comments: one comment per entry. |

- **Epic:** overall outcome, shared constraints, one line per sub-issue (outcome + link), integration criteria.
- **Sub-issue:** one outcome, its own criteria, link to the epic.

## Writing rules

- No em dashes. Use a period, comma, colon or parentheses.
- Cut generic openers, canned summaries, buzzwords, inflated adjectives, filler transitions, "not X, but Y" and slogans. State the point.
- Specific nouns, active verbs, consistent terms. Key facts first.
- Short bullets, narrow tables, flow diagrams. Emojis only to label sections and help scanning.
- No invented facts, metrics, benefits, quotes, tests or consent. Label illustrative examples. Verify names, numbers, units, dates.
- Keep the owner's words, reasons and examples. Never compress away context. Fold long machine data; keep purpose, outcome, proof, gaps and next action visible.
- One finishing pass: can a cold reader say what, why, before, after and next? Does every requested detail have a home?

## Example

Illustration only. Real tickets need real code and sources.

**Title: Keep chosen theme after reload**

### 📥 Request

> "Theme resets every time I reload." (owner, chat)

### 🎯 Purpose & goal

- **Purpose:** Theme resets on reload. Users redo setup.
- **Goal:** Reload keeps the chosen theme.

### 📍 Context

- Settings screen calls the theme store. Code shows no save path; runtime unverified.

### 🔧 Before → after

| Before | After |
|---|---|
| Reload restores default | Reload restores saved choice |

- **Approach:** Reuse settings storage. One save path.

```text
choose theme -> save -> reload -> restore
                 | fail
                 v
            show error -> keep choice -> retry
```

### ✅ Done when

- **A1:** Save dark, reload, dark restored.
- **A2:** Save fails: show error, keep choice, allow retry.

### 🧱 Scope & guardrails

- Theme only. Keep defaults. No account sync. More themes: follow-up.

### 🚦 Progress / next

- **Status:** To do. **Priority:** P2. Next: inspect store and consumers.

### 📝 Activity

- `<date>`, agent: Backlog → To do, P2. Why: picked for this run. Proof: plan link.
