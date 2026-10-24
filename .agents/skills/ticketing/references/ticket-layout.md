# Ticket layout

Brief words, full meaning. A human or fresh agent must understand the ticket without the chat.

**Title:** concrete change + outcome, in the reader's language; explain needed jargon.

## Sections

Skip what does not apply. Keep each block separate. Never bury purpose, context or progress inside Before.

| Section | Put here |
|---|---|
| 📥 Request | The owner's original words, verbatim; why, examples, supplied evidence, source, date, who decided. Later corrections are appended, never overwritten. |
| 🎯 Purpose & goal | **Purpose:** problem, who is affected, consequence, why now. **Goal:** exact success. |
| 📍 Context | Code and consumers (paths), baseline, sources, prior work and PRs. Label fact, inference, unknown. |
| 🔧 Before → after | Behavior only, in a table or paired blocks. **Before** = actual current behavior, from code and existing evidence. New capability: what does not exist yet. Non-visual work: the real consumer and output. **Approach:** the choice and its reason. |
| 🔀 Flow | Entry → action → effect → result, plus relevant failure and recovery. ASCII for branches and state. |
| ✅ Definition of done | One observable result per criterion, stable ID (A1, A2). A criterion that delivers a requested item names it: `**A1 (R2):**`. Cover success, failure, recovery, preserved behavior. No "works", "best" or "optimized" without a check. |
| ☑️ Checklist | The plan's todos as task items in build order: `- [ ] T1 <todo> (A1)`, plus `needs #11 T1` when an item waits on another ticket's item. Every criterion has at least one item that names its ID; no ranges. Ticked `- [x]` with a short proof. Never deleted; an added or changed item records why. |
| 🧱 Scope & guardrails | In, out, constraints, dependencies, decisions (approved, rejected, pending), optional wants, finish boundary. Each deferral of requested work: owner, destination ticket, revisit condition. POC skips: one list, in the epic. |
| 🚦 Progress / next | Status, priority, assignee. Done, left, phase, next action, blockers, linked PR or branch. Checked, reviewed, merged, released stay separate. |
| 📝 Activity | The ticket's lifetime timeline, entries per the skill's Activity rules. Trackers with comments: one comment per entry. |

- **Epic:** overall outcome, shared constraints and decisions, one line per sub-issue (outcome + link), integration criteria as its definition of done. Checklist: one item per in-scope sub-issue (follow-ups stay out) plus the integration checks.
- **Sub-issue:** one outcome, its own definition of done and checklist, link to the epic.

## Writing rules

- No em dashes: use a period, comma, colon or parentheses.
- Cut generic openers, canned summaries, buzzwords, inflated adjectives, filler transitions, "not X, but Y" and slogans. State the point.
- Specific nouns, active verbs, consistent terms, key facts first.
- Short bullets, narrow tables, flow diagrams. Emojis only to label sections and help scanning.
- No invented facts, metrics, benefits, quotes, tests or consent. Label illustrative examples. Verify names, numbers, units, dates.
- Keep the owner's words, reasons and examples; never compress away context. Fold long machine data; keep purpose, outcome, proof, gaps and next action visible.
- One finishing pass: can a cold reader say what, why, before, after and next? Does every requested detail have a home?

## Example

Illustration only.

### 📥 Request
> "Theme resets every time I reload." (owner, chat)

### 🔧 Before → after
| Before | After |
|---|---|
| Reload restores default | Reload restores saved choice |

### 🔀 Flow
```text
save -> reload -> restore
 | fail -> error, keep choice, retry
```

### ☑️ Checklist
- [x] T1 Save on change, restore on start (A1). Proof: reload showed dark.
- [ ] T2 Error with retry on a failed save (A2)

### 🚦 Progress / next
- **Status:** In progress. **Priority:** P2. Next: T2.

### 📝 Activity
- `<date>`, agent: To do → In progress, assigned. Why: build started. Proof: branch link.
