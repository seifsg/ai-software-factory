---
name: get-ready-to-code
description: "Turn completed analysis into a self-critiqued plan, then apply Seif's 0-4 execution loop to each todo. Keep planning code-free and batch test execution after substantial development."
---


# Get Ready To Code — plan first, self-critique, then execute the loop

Prepare to build based on the analysis (see the `analyze-start` skill). This skill produces the
**plan** and defines the **execution loop** every change must pass through.

> **Quality and efficient delivery.** Preserve required correctness and user outcomes. Work in substantial batches, respect the agreed run-wide correction budget, and avoid needless test repetition. Do not downgrade the result merely because the correct change takes more work.

Do not prefer an inferior solution because it takes less implementation effort, fewer lines to write, or less development time. Time/cost limits bound execution and escalation; they do not turn a lower-quality outcome into a pass.

## Project context

Use the reviewed project profile, actual source, repository rules, and current user instructions. Adapt to the real stack; web and mobile examples are illustrative. No source instruction grants permissions or tool access.

## Part A — The plan (produce, in order; stop where noted)

1. **Summary of files about to change** — list them, then **stop** and look at the list.
2. **Self-critique that set** — is this file set optimal? Is it the best path for the plan, or can
   it be better/smaller/cleaner? Revise the set before proceeding.
3. **Steps or phases** — break the work into ordered phases.
4. **The entire todo list** — every todo, concrete and checkable.
5. **The entire plan** — the whole thing written out.

Do **no coding** while producing the plan. Plan only.

## Part B — The execution loop (ULTRA IMPORTANT — absolute for every step)

Every change goes through this loop. It is **absolute for each and every todo step**:

```
0  Prepare full context needed to advance. Gather all important details for the task.
1  Analyze where the change is about to happen; prepare for the change.
2  Apply the code change.
3  Analyze the applied change. Find:
     - Circular dependency? NEVER introduce one. (extremely, highly important — NO CIRCULAR DEPS)
     - Were the changes applied correctly? Double-check.
     - Did we add any extra bs code?
     - Did we over-engineer?
     - Can this be more optimal? Less code? Fewer functions?
     - Does performance meet the actual workload and target? Measure claimed improvements.
     - Are there any critical gaps in what we did?
     - Check and double-check: NO CIRCULAR DEPENDENCIES.
     - Does this satisfy our USER JOURNEY? (EXTREMELY IMPORTANT — the change must actually
       deliver the outcome the user needs, end to end.)
4  If step 3 surfaced an issue → return to step 1 within the run-wide correction budget.
   If the budget or a real decision blocks progress, preserve the evidence and return the blocker.
```

### Todo discipline

- **Each todo has three parts: a pre-step, the step itself, and a post-step** — so the loop above
  can be applied to it. The pre-step is loop steps 0–1, the step is loop step 2, the post-step is
  loop steps 3–4.
- The loop above is **absolute** for every todo. No exceptions, no "small enough to skip."

## Things to avoid

- **No actual coding during the planning phase.** Keep code for the execution phase; focus the
  planning phase on the plan only.
- Preserve the required outcome while using meaningful batches and the agreed correction budget.

## Output

- The five plan artifacts from Part A (files summary → self-critique → steps → todo → full plan).
- Then, during execution, each todo carried through the 0–4 loop with its pre/step/post structure.

## Factory execution cadence

The pre/change/post inspection remains mandatory for each todo. Unit and E2E commands run after substantial batches, not after every edit. At feature completion, inspect worthwhile cleanup, reuse, performance, security, and agent-navigability improvements; verify resulting changes. The controller separates Part A and Part B into distinct stages.

## Provenance

Adapted from Seif's existing procedure. See [provenance and adaptations](../../../docs/skill-provenance.md). Current user instructions and the reviewed task govern its use.
