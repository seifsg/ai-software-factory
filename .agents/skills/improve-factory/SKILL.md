---
name: improve-factory
description: "Repairs or improves the factory's own skills, hooks and adapters when factory instructions or behavior fail, in an isolated factory checkout, while any app run keeps going. Use when the factory misbehaved or needs a change. Product bugs go back to delivery."
---

# Improve Factory

Fix the factory, never the product. Any app run keeps using its installed factory; the repair never writes the app's files.

Run it as a factory run of kind `change` on its maintenance ticket: the ten steps of `safe-engine`, in a factory repository checkout, never the installed copy. Fast by default; Safe on request (the owner's OK after the plan). An analysis or planning request stops at that phase. The sections below add only what factory work needs.

## Understand the report (steps 0 and 1)

1. Record in the ticket: observed behavior, expected result, example, artifacts, commands and factory version.
2. Resolve the factory checkout and the target project separately. Read both projects' rules and working status.
3. Ask only the gaps that change the outcome.
4. Classify the cause:

| Cause | Action |
|---|---|
| Instruction skipped | Recover the step. Check how the method was loaded and handed off before adding rules. |
| Skill unclear or incomplete | Fix the skill that owns the rule, then its callers. |
| Hook or adapter fault | Diagnose from the script and the run file that triggered it. Fix that layer. |
| Missing tool, access or decision | Record the blocker. Invent nothing. |
| Product bug | Back to delivery, unless evidence also shows a factory defect. |
| Working as designed | Explain the rule that applied and where it lives. Change it only on the owner's request. |

## Isolate

- Repair in its own branch or worktree of the factory repository. One writer per file.
- Never edit an installed factory copy, an app's files or global settings. Never silently stash, reset or switch anything.
- Factory repair grants no product scope change. Keep the app ticket and the maintenance ticket separate.
- Independent tickets run in parallel, each in its own worktree.

## Plan the smallest correction (steps 2 and 3)

- Record the invariants: project goal, selected decisions, complete methods, owner stops, human release. Changing one needs the owner. Never weaken a check that failed.
- Exclude unrelated improvements. A new skill, hook, rule or reference needs a demonstrated gap; no universal rule for an isolated complaint.
- Shorter and faster is the goal. The plan states method bytes before and after for each changed file and in total, from Git blobs (`git ls-tree -l <ref>`). Net growth needs the owner's OK with the reason.
- Lasting rules go in the skill that owns them, once. Remove stale or duplicate prose.

## Proof (steps 4 to 6)

Capture Before at step 4: the old behavior in the same form as the After.

| Change | Proof |
|---|---|
| Instructions | A fresh agent gets the changed skill, a realistic request and raw fixtures, never the expected outcome. Judge its decisions and artifacts, not word matches. |
| Hook script | Run it on fixture run files: no run, open, waiting, idle after a nudge, closed with a gate missing, finished. |
| Both | Both, each proves only itself. |

- Pick the cases the change touches: the domain it governs (game, mobile, desktop, server, CLI) with its real tooling; an interrupted run; a compaction; a broken output contract the checker must catch.
- Isolate fixtures from real project work and secrets.
- Then run the repository checks listed in its `AGENTS.md`.

## Review and deliver (steps 7 and 8)

- No factory change reaches the main branch without `how-to-review-a-pr` from a fresh agent.
- Draft PR through `how-to-make-a-pr`, with the repository's changelog and upgrade notes.
- Humans mark ready, merge and release. Installs get the change only after a release.
- Report separately: change, manual use, checks, review, PR. Brief before/after. Name what is unverified.
- Never run `improve-factory` on its own repair.
