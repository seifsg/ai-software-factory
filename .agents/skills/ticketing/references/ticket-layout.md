# Ticket layout

Brief words, full meaning. Human or fresh agent must understand ticket without chat.

**Title:** concrete change + outcome, reader's language; explain needed jargon.

## Sections

Skip what does not apply. Keep blocks separate. Never bury purpose, context or progress inside Before.

| Section | Put here |
|---|---|
| 📥 Request | Owner's original words, verbatim; why, examples, supplied evidence, source, date, who decided. Later corrections appended, never overwritten. |
| 🎯 Purpose & goal | **Purpose:** problem, who is affected, consequence, why now. **Goal:** exact success. |
| 📍 Context | Code and consumers (paths), baseline, sources, prior work and PRs. Label fact, inference, unknown. |
| 🔧 Before → after | Behavior only, table or paired blocks. **Before** = actual current behavior, from code and existing evidence. New capability: what does not exist yet. Non-visual work: real consumer and output. **Approach:** choice and reason. |
| 🔀 Flow | Entry → action → effect → result, plus relevant failure and recovery. ASCII for branches and state. |
| ✅ Definition of done | One observable result per criterion, stable ID (A1, A2). Criterion that delivers a requested item names it: `**A1 (R2):**`. Cover success, failure, recovery, preserved behavior. No "works", "best" or "optimized" without a check. |
| ☑️ Checklist | The plan's todos as task items in build order: `- [ ] T1 <todo> (A1)`, plus `needs #11 T1` when an item waits on another ticket's item. Every criterion has at least one item naming its ID; no ranges. Ticked `- [x]` with short proof. Never deleted; added or changed item records why. |
| 🧱 Scope & guardrails | In, out, constraints, dependencies, decisions (approved, rejected, pending), optional wants, finish boundary. Each deferral of requested work: owner, destination ticket, revisit condition. POC skips: one list, in the epic. |
| 🚦 Progress / next | Status, priority, assignee. Done, left, phase, next action, blockers, linked PR or branch. |
| 📝 Activity | Ticket's lifetime timeline, entries per the skill's Activity rules. Trackers with comments: one comment per entry. |

- **Epic:** overall outcome, shared constraints and decisions, one line per sub-issue (outcome + link), integration criteria as its definition of done. Checklist: one item per in-scope sub-issue (follow-ups stay out) plus integration checks.
- **Sub-issue:** one outcome, own definition of done and checklist, link to epic.

## Writing rules

- No em dashes: period, comma, colon or parentheses.
- Cut generic openers, canned summaries, buzzwords, inflated adjectives, filler transitions, "not X, but Y", slogans. State the point.
- Specific nouns, active verbs, consistent terms, key facts first.
- Short bullets, narrow tables, flow diagrams. Emojis only to label sections and help scanning.
- No invented facts, metrics, benefits, quotes, tests or consent. Label illustrative examples. Verify names, numbers, units, dates.
- Keep owner's words, reasons, examples; never compress away context. Fold long machine data; keep purpose, outcome, proof, gaps, next action visible.
- One finishing pass: can cold reader say what, why, before, after, next? Does every requested detail have a home?

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

### ✅ Definition of done
- **A1:** reload keeps the chosen theme.
- **A2:** a failed save shows an error with retry and keeps the choice.

### ☑️ Checklist
- [x] T1 Save on change, restore on start (A1). Proof: reload showed dark.
- [ ] T2 Error with retry on a failed save (A2)

### 🚦 Progress / next
- **Status:** In progress. **Priority:** P2. Next: T2.

### 📝 Activity
- `<date>`, agent: To do → In progress, assigned. Why: build started. Proof: branch link.
