---
name: get-ready-to-code
description: "Plans the build from a finished analysis and recommendation: files to change, self-critique, phases, the full todo list and the whole plan, then runs every todo through the 0-4 loop. The todo list becomes each ticket's checklist. Use after analysis and before coding. No coding during planning."
---

# Get Ready To Code: plan first, self-critique, then execute the loop

Prepare build from analysis (`analyze-start`) and picked option (`recommend`). Part A: the plan. Part B: the loop every change goes through.

Keep required quality. Complete working iterations, tiny bug or full product. Never downgrade the result because the correct change takes more work.

## Part A: the plan (in order; stop where noted)

1. **Summary of files about to change.** List them, then stop and look at the list. Continue only when your instructions already authorize it.
2. **Self-critique that set.** Is this file set optimal, the best path for the plan? Can it be smaller, cleaner, more reusable? Revise it before going on.
3. **Steps or phases.** Ordered by user value: first the smallest real journey someone can see and use. Before dependent work, settle the shared state owner, invariants and who enforces them, entry points, limits, compatibility and failure behavior. Root fix, not patch; big or risky ones go to the owner.
4. **The entire todo list.** Every todo concrete and checkable, and it becomes the ticket's checklist. Order never drops scope: every requested item maps to a todo, or stays open in its ticket when the owner narrowed this iteration.
5. **The entire plan.** The whole thing written out, so no agent guesses: interfaces and this checkout's dev ports.
6. **Proof and tests.** The proof list for the PR's Before and After: one short id per changed view, state, journey or command; interactive elements share their journey's id, never one id each. The test map: the command that runs the tests covering each changed file, and the project's full-suite command for verify.

Do no coding while producing the plan.

### Todos

- Each todo reads as an outcome the owner understands, then its ticket and criteria. Example: `T4 Download button → click it and the PDF saves (#12, A2)`. Not `T4 add store_true option`.
- Each todo has a pre-step, the step and a post-step, so the loop applies.
- A todo that depends on an unproven capability (platform API, device, third-party access) goes first as a bounded spike: one question, one stop condition. A failed spike blocks only that item.
- Group useful parallel jobs by files and dependencies; keep tasks shorter than their delegation overhead local. A delegated todo names the lowest tier that can pass its checks: light (commands with a pass/fail, search; no edits), standard (planned edits, research, walkthroughs) or deep (architecture, schema, security, unclear bugs).

## Part B: the 0–4 loop (absolute for every todo)

```
0  Prepare full context to advance: read the relevant code, facts and details.
1  Analyze where the change is about to happen and its affected consumers.
2  Apply the change.
3  Analyze the applied change:
     - Applied correctly? Double-check.
     - Circular dependency? NEVER introduce one.
     - Any extra code we did not need? Over-engineered? (Logic only; UI: best look.)
     - More optimal: less code, fewer functions, less CPU and memory for the real workload?
     - Root cause handled, edge cases asserted once, no silent defaults?
     - Critical gaps?
     - Does it satisfy the USER JOURNEY end to end? Use the real screen, endpoint,
       command or logs before ticking.
4  Step 3 found an issue → back to step 1.
```

- After each todo's real use: only tests covering its changed files. Full suite waits for verify.
- Tick the todo in the ticket and write its log line once its own use-check passes: `T3 pre: <before> do: <change> post: <check>`.
- Second related failure or edge case: find the shared cause and why the previous fix failed, fix the cause and its consumers, state what prevents recurrence. No endless symptom patches.
- Ticket finished: every item ticked, definition of done proven. Until then the loop continues.

## Light plan

A small `change` or follow-up, when your instructions ask for one: files with a one-line critique, the todo list, one success line, the proof list and the test map. It meets the same output contract, whose product-only lines it omits. The 0–4 loop stays.


## Output contract

The block `## 3 Plan` holds:

- [ ] **Files:** the summary, then the critique and what it changed
- [ ] **Phases:** ordered, smallest real journey first (product, feature or new UI; a `change` omits it)
- [ ] **Todos:** `T1..Tn`, each an outcome with ticket and criteria; every criterion maps to at least one todo; the ticket checklist matches
- [ ] **Plan:** interfaces and ports (product, feature, new UI or delegated work; a `change` omits it)
- [ ] **Proof list:** every changed view, state, journey or command with an id
- [ ] **Test map:** per-file test command and the full-suite command, or `none (<reason>)`: no logic, or owner-named POC
- [ ] No source file changed during this step

The block `## 5 Build` holds:

- [ ] The ticket moved to In progress before T1
- [ ] One `Tn pre: … do: … post: …` line per todo, each ticked, e.g. `T2 pre: reload lost the theme do: save it on change post: npm test theme: 4 passed; reload kept dark ✔`
- [ ] Every todo ticked in the ticket checklist after its use-check
- [ ] Only mapped tests ran; their commands and results are named
- [ ] Commits staged by name, each `<type>(<scope>): <subject>`
