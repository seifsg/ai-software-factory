---
name: get-ready-to-code
description: "Plans the build from a finished analysis: summary of files to change, self-critique, phases, full todo list and whole plan, plus the 0-4 loop every todo runs through. The todo list becomes each ticket's checklist. Use after analysis and before coding. No coding during planning."
---

Prepare to start building based on our plan and analysis.
Important: We do not care about effort time or code that would take to build. We only care about quality. Do not factor code effort or time to develop at all within the plan. AI will develop and write it.
The next steps are the following:

Build in complete working iterations. Tiny bug or full product, same logic.

- First: smallest real user journey we can see and use. Order by user value; explain required blockers. Order never drops scope: every requested item maps to todos, or stays open in its ticket when the owner narrowed this iteration.
- Before dependent work: shared state owner, limits, compatibility and failure behavior.
- Required quality stays. Optional polish/enhancements later: owner, ticket, acceptance condition.
- Complete outcome ticket -> finish iteration -> manual QA -> relevant final tests/review. Full requested outcome stays open until delivered.

Prepare a :
- summary of files about to change then stop. (Continue without stopping only when your instructions already authorize it.)
- next step, criticize our suggested summary of files, is it optimal, is that the best path for our plan
- steps or phases.
- The entire list of to do. It becomes each ticket's checklist.
- The entire plan.

Keep these five outputs in one compact work record. Full depth, the file-summary stop and every 0–4 step stay. Reuse source/decisions; link proof. Within step 3, finish affected callers, counts and links before recording completion. No extra finishing gate.

A small change or follow-up keeps the plan to the to do list and one success line; the 0–4 loop stays.

## ULTRA EXTRA IMPORTANT

The plan execution will be based on the following logic:

0- prepare our full context needed to advance forward. Gather all important details for the task.
1- analyze where we are about to do changes and prepare for next changes
2- apply our code changes
3- analyze our applied changes and try to find the following:
- Analyze and never ever have a circular dependency
- double check the changes were they applied correctly?
- did we add any extra bs code?
- did we over engineer?
- can this be more optimal? Less code? Less functions?
- Is this o(1) or as close?
- are there any critical gaps to what we did?
- Check and double check. Extremely and highly important: NO CIRCULAR DEPs!!!
- Does this satisfy our user journey? EXTREMELY IMPORTANT!!
- Use it: run the item's real effect (screen, endpoint, command, logs) and see it work. Only then tick it in its ticket, with the proof.
4- if we detect issues from step 3, start our processes over again from step 1 and follow steps again.

Second related failure? Find the shared cause. Why did the previous fix fail? Fix the cause and affected consumers. State what prevents recurrence. Preserve failures; no endless symptom patches or retry cap.

Important: We do not care about effort time or code that would take to build. We only care about quality. Do not factor code effort or time to develop at all within the plan. AI will develop and write it.

To do steps:
- Each to do step will have a pre-step, the step itself, and post-step. And that is so that we can apply the logic above.
- The logic above is absolute for every and each step.
- Each to do is a checklist item in its ticket. Automated test suites still come last.
- The plan groups independent to dos into waves by files and dependencies. Each wave runs at once, as many as capacity allows; each to do is ticked after its own check.
- Each to do names its model tier: light (search, inventory, mechanical edits), standard (planned implementation, one-lens reviews, research, walkthroughs) or deep (architecture, schema, security, unclear bugs, synthesis, final review).
- A ticket is finished when every item is ticked and its definition of done is proven. Until then the loop continues.
- A to do that depends on an unproven capability (platform API, device, third-party access) goes first as a bounded spike: one question, one stop condition. A failed spike blocks only that item; the rest continues.

things to avoid:
- Actual coding during our planning phases. Keep code for later focus on plan only.
