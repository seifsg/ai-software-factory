---
name: get-ready-to-code
description: "Plans the build from a finished analysis: summary of files to change, self-critique, phases, full todo list and whole plan, plus the 0-4 loop every todo runs through. The todo list becomes each ticket's checklist. Use after analysis and before coding. No coding during planning."
---

Prepare to build from our plan and analysis.
Keep required quality. Minimize total execution, context and repeated proof; use `deep-review` worth-it scores for optional polish. Retain scope, owner authority and unknown cost.

Build in complete working iterations. Tiny bug or full product, same logic.

- First: smallest real user journey we can see and use. Order by user value; explain required blockers. Order never drops scope: every requested item maps to todos, or stays open in its ticket when the owner narrowed this iteration.
- Before dependent work: shared state owner, invariants and their enforcers, entry points, limits, compatibility and failure behavior. Root fix, not patch; big or risky ones go to the owner.
- Design ports keep frozen coverage. Optional polish: owner, ticket, acceptance.
- Complete outcome ticket -> finish iteration -> manual QA -> relevant final tests/review.

Prepare:
- summary of files about to change, then stop (continue only when your instructions already authorize it).
- critique of that summary: is it optimal, the best path for our plan?
- steps or phases; UI: Look, Show, Prove, Ship.
- the entire to do list. It becomes each ticket's checklist.
- the entire plan, fixing what every brief carries so no agent guesses: Interface, this checkout's dev Ports and, for UI work, UX rules (safe-engine fast-run, Briefs).

Keep these five outputs in one compact work record. Full depth, the file-summary stop and every 0–4 step stay. Reuse source/decisions; link proof. Within step 3, finish affected callers, counts and links before recording completion. No extra finishing gate.

Fast plans bound journeys/checks, helpers, proof reuse and unexpected repetition. Overruns change the approach and report remaining work, never waive requirements or invent token limits. Preflight uncertain interpreters, wrapper guards and capture/publication with harmless actual probes, not an early full suite. Keep each complete tool return with command, session and exit result; pending or missing results never pass.

Light plan, when your instructions ask for one (a small change or follow-up): the to do list and one success line; the 0–4 loop stays. Otherwise all five outputs.

## 0–4 loop

Every plan executes this loop:

0- Read relevant context and facts.
1- Analyze the change and affected consumers.
2- Apply it.
3- Review correctness, root-cause edge cases, complexity and required journeys. Remove overengineering; forbid circular dependencies and silent defaults. Assert impossible states once. Use the real screen, endpoint, command or logs before ticking its ticket with proof.
4- Findings return to step 1.

Second related failure or edge case? Find the shared cause. Why did the previous fix fail? Fix the cause and affected consumers. State what prevents recurrence. Preserve failures; no endless symptom patches or retry cap.

To do steps:
- Each to do has a pre-step, the step and a post-step, so the loop applies. The loop is absolute for every step.
- Each to do is a checklist item in its ticket. Automated test suites still come last.
- Each to do reads as an outcome the owner understands: what it is → what they can do once it is done, then its ticket and criteria. Example: `T4 Download button → click it and the PDF saves (#12, A2)`. Not `T4 add store_true option`.
- Group useful parallel jobs by files and dependencies; keep tasks shorter than their delegation overhead local. Required independent checking stays separate. Tick each todo after its own use-check.
- Each to do names its model tier, the lowest that can pass its checks: light (commands with a pass/fail, search, inventory, comparison; no edits), standard (planned or mechanical edits, research, one-lens reviews, walkthroughs) or deep (design calls: architecture, schema, security, unclear bugs; final review). Its delegate's role follows from the tier and whether it edits.
- A ticket is finished when every item is ticked and its definition of done is proven. Until then the loop continues.
- A to do that depends on an unproven capability (platform API, device, third-party access) goes first as a bounded spike: one question, one stop condition. A failed spike blocks only that item; the rest continues.

Never code during planning. Plan only.
