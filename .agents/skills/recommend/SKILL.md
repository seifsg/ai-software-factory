---
name: recommend
description: "Compares three strong solutions for a change in one table and recommends exactly one, with reasons: correctness, simplicity, performance, fit to the original goal, coupling. Use after analysis and before planning, when reviewing a PR, or whenever a substantive choice comes up. No coding."
---

# Recommend: three solutions, one pick

Run after `analyze-start`, before planning. No code in this step.

1. **Restate the goal** in one line, from original request and approved decisions.
2. **Find three strong alternatives.** Real, distinct, each could ship. No padded weak options. Existing or approved design: assess against two credible alternatives; keeping it can be best. Never manufacture a defect or rewrite to justify this step.
3. **Compare them in one table**, best evidence first:

   | Option | Approach | Correct | Simple | Performance | UX / look | Fits goal | Coupling / cycles | Cost |
   |---|---|---|---|---|---|---|---|---|
   | A | ... | ... | ... | ... | ... | ... | ... | ... |

   Each cell: a fact or short reason, not a score alone. Judge performance against real workload, not a universal target. UI: look beats simple.
   New UI (product, feature, new view) in a factory run: second table, 3 looks (type, color, layout, motion, refs). Pick best, delegated, no owner wait. Bar: best in class, any size. Existing look kept: `Look: existing`.
4. **Pick exactly one**, why in two or three lines: what it wins, what it costs, why others lose.
5. **Who decides.** In-scope choices already delegated to you: pick, record reason. New product, design (except look above), naming or other owner-reserved choice: present pick as recommendation, set `Waiting: owner: <question>` in run file, keep independent work moving.

Only one sane path (typo, one-line fix): say "one path: <why>", name two rejected ideas, a line each. Never skip the step.

## Challenge (step 2b)

Challenge's own pass, after step 2's block: "I don't think this is the best we could do. Do better. Make no mistake." Redo steps 2 to 4 against it: missed option, wrong cell, underrated cost. Keep pick only if it survives.

## Output contract

Block `## 2 Recommend` holds:

- [ ] **Goal:** one line, traceable to the request
- [ ] **Table:** three options, every column filled, or "one path" with two rejected ideas
- [ ] **Pick:** exactly one option, with reasons
- [ ] **Look:** new UI: 3 looks, one pick; `existing` or `no UI`
- [ ] **Decider:** "picked (delegated)" or "waiting on the owner: <question>"
- [ ] No file changed during this step

Block `## 2b Challenge` holds:

- [ ] **Challenge:** the sentence above, verbatim
- [ ] **Found:** each new option, wrong cell or missed cost, or "nothing new" with what was rechecked
- [ ] **Result:** `kept <pick>` or `changed <old> → <new>` and why
