# Write tickets and PRs

Brief words. Full meaning. A human or fresh agent must understand without chat.

**Title:** concrete change + outcome. Attribution/source link when required. Use the reader's language; explain necessary jargon.

| Section | Put here |
|---|---|
| 🎯 Purpose & goal | **Purpose:** problem, affected reader/user, consequence, why needed. **Goal:** exact success. |
| 📍 Context | Actual code/consumers, paths, baseline, sources, prior work, unknowns. No rationale or progress buried in Before. |
| 🔧 What & why | Behavior-only Before/After table or paired blocks. Approach/decision + reason. Benefit must follow from the change. |
| 🔀 Journey / flow | Entry → action → effect → result; relevant failure/recovery. ASCII for branches/state. |
| ✅ Done when / proof | Ticket: stable criterion + observable result. PR: criterion → actual change → exact-candidate evidence → gap. |
| 🧱 Scope & guardrails | Required, avoid/out, constraints, dependencies, optional wants and finish boundary. |
| 🚦 Progress / next | Done, left, owner/phase, next action, blockers, linked PR/branch/candidate. Separate checked, reviewed, merged, released. |
| 📝 Activity / adjustment history | Date/who → changed what → reason/decision → result/next. Keep meaningful history. |

Use labeled emojis, short bullets and narrow tables. Diagram flows; table comparisons/files/checks. Charts need measured values. Screenshots need real relevant proof. Reuse existing evidence; follow baseline/final-QA rules. Fit the project's template; skip inapplicable blocks. No decoration quota, copied workflow, new media chore or extra vote.

Keep original words, reasons, examples and deliberate reminders. Fold machine data/long supporting evidence; keep purpose, outcome, proof/gaps and next action visible. Never compress away context. Label facts, inference, unknowns and illustrative examples. No fabricated benefits, tests, visuals or consent.

One finishing pass: can a cold reader say what, why, before, after and next? Does every requested detail have a home? Use existing review; no writing loop.

## Example: settings change

Illustration only; code/proof/authority bindings needed for real work.

**Title: Keep chosen theme after reload**

### 🎯 Purpose & goal

- **Purpose:** Theme resets. User repeats setup.
- **Goal:** Reload keeps the chosen theme.

### 📍 Context

- Settings screen calls theme store. Source shows no save path; runtime unverified.

### 🔧 What & why

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

- **A1:** Save dark → reload → dark restored.
- **A2:** Save fails → show error; keep choice; allow retry.

### 🧱 Scope & guardrails

- Theme only. Keep defaults. No account sync. Extra themes: follow-up.
- **Finish:** Checked PR; merge stays with owner.

### 🚦 Progress

- Not started; no PR. Next: inspect store/consumers, then plan.
