---
name: get-ready-to-code
description: "Plans the build from a finished analysis: summary of files to change, self-critique, phases, full todo list and whole plan, plus the 0-4 loop every todo runs through. Use after analysis and before coding. No coding during planning."
---

Prepare to start building based on our plan and analysis.
Important: We do not care about effort time or code that would take to build. We only care about quality. Do not factor code effort or time to develop at all within the plan. AI will develop and write it.
The next steps are the following:

Build in complete working iterations. Tiny bug or full product, same logic.

- First: smallest real user journey we can see and use. Order by user value; explain required blockers.
- Before dependent work: shared state owner, limits, compatibility and failure behavior.
- Required quality stays. Optional polish/enhancements later: owner, ticket, acceptance condition.
- Complete outcome ticket -> finish iteration -> manual QA -> relevant final tests/review. Full requested outcome stays open until delivered.
- Map every original requirement to an outcome ticket, criterion, planned implementation and final proof. Iterations order that work; they do not cut POC or MVP scope. A later focused slice leaves earlier requirements active unless the owner explicitly changes them.

Prepare a :
- summary of files about to change then stop. (Continue without stopping only when your instructions already authorize it.)
- next step, criticize our suggested summary of files, is it optimal, is that the best path for our plan
- steps or phases.
- The entire list of to do.
- The entire plan.

Keep these five outputs in one compact work record. Full depth, the file-summary stop and every 0–4 step stay. Reuse source/decisions; link proof. Within step 3, finish affected callers, counts and links before recording completion. No extra finishing gate.

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
4- if we detect issues from step 3, start our processes over again from step 1 and follow steps again.

Second related failure? Find the shared cause. Why did the previous fix fail? Fix the cause and affected consumers. State what prevents recurrence. Preserve failures; no endless symptom patches or retry cap.

Important: We do not care about effort time or code that would take to build. We only care about quality. Do not factor code effort or time to develop at all within the plan. AI will develop and write it.

To do steps:
- Each to do step will have a pre-step, the step itself, and post-step. And that is so that we can apply the logic above.
- The logic above is absolute for every and each step.

things to avoid:
- Actual coding during our planning phases. Keep code for later focus on plan only.
