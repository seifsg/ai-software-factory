---
name: recommend
description: "Compares three strong solutions for a change in one table and recommends exactly one, with reasons: correctness, simplicity, performance, fit to the original goal, coupling. Use after analysis and before planning, when reviewing a PR, or whenever a substantive choice comes up. No coding."
---

# Recommend: three solutions, one pick

Run after `analyze-start`, before planning. No code in this step.

1. **Restate the goal** in one line, from the original request and approved decisions.
2. **Find three strong alternatives.** Real, distinct approaches that each could ship. No padded weak options to make the pick look good. For an existing or already approved design, assess it against two credible alternatives; keeping it can be the best answer. Never manufacture a defect or a rewrite to justify this step.
3. **Compare them in one table**, best evidence first:

   | Option | Approach | Correct | Simple | Performance | Fits goal | Coupling / cycles | Cost |
   |---|---|---|---|---|---|---|---|
   | A | ... | ... | ... | ... | ... | ... | ... |

   Fill each cell with a fact or a short reason, not a score alone. Performance is judged against the real workload, not a universal target.
4. **Pick exactly one** and say why in two or three lines: what it wins, what it costs, why the others lose.
5. **Who decides.** In-scope choices already delegated to you: pick and record the reason. A new product, design, naming or other owner-reserved choice: present the pick as a recommendation, set `Waiting: owner: <question>` in the run file and keep independent work moving.

A change with only one sane path (a typo, a one-line fix): say "one path: <why>" and name the two rejected ideas in a line each. Never skip the step.

## Output contract

The block `## 2 Recommend` holds:

- [ ] **Goal:** one line, traceable to the request
- [ ] **Table:** three options with every column filled, or "one path" with two rejected ideas
- [ ] **Pick:** exactly one option, with reasons
- [ ] **Decider:** "picked (delegated)" or "waiting on the owner: <question>"
- [ ] No file changed during this step
