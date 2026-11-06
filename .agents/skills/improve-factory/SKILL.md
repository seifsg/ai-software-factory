---
name: improve-factory
description: "Repairs or improves the factory's own skills, hooks and adapters when factory instructions or behavior fail, in an isolated factory checkout, while any app run keeps going. Use when the factory misbehaved or needs a change. Product bugs go back to delivery."
---

# Improve Factory

Fix factory, never product. Any app run keeps its installed factory; repair never writes app files.

Load `safe-factory`. Run as factory run of kind `change` on its maintenance ticket: its ten steps, in a factory checkout, never the installed copy. Fast by default; Safe on request (owner's OK after the plan). Analysis or planning request stops at that phase. Sections below add only what factory work needs.

## Understand the report (steps 0 and 1)

1. Record in ticket: observed behavior, expected result, example, artifacts, commands, factory version.
2. Resolve factory checkout and target project separately. Read both projects' rules and working status.
3. Ask only gaps that change the outcome.
4. Classify cause:

| Cause | Action |
|---|---|
| Instruction skipped | Recover the step. Check how method was loaded and handed off before adding rules. |
| Skill unclear or incomplete | Fix skill that owns the rule, then its callers. |
| Hook or adapter fault | Diagnose from script and the run file that triggered it. Fix that layer. |
| Missing tool, access or decision | Record blocker. Invent nothing. |
| Product bug | Back to delivery, unless evidence also shows a factory defect. |
| Working as designed | Explain rule that applied and where it lives. Change only on owner's request. |

## Isolate

- Repair in own branch or worktree of factory repository. One writer per file.
- Never edit installed factory copy, app files or global settings. Never silently stash, reset or switch anything.
- Factory repair grants no product scope change. Keep app ticket and maintenance ticket separate.
- Independent tickets run in parallel, each in own worktree.

## Plan the smallest correction (steps 2 and 3)

- Record invariants: project goal, selected decisions, complete methods, owner stops, human release. Changing one needs owner. Never weaken a check that failed.
- Exclude unrelated improvements. New skill, hook, rule or reference needs a demonstrated gap; no universal rule for an isolated complaint.
- Goal: shorter and faster. Plan states method bytes before and after per changed file and in total, from Git blobs (`git ls-tree -l <ref>`).
- Lasting rules go once in the skill that owns them. Remove stale or duplicate prose.

## Proof (steps 4 to 6)

Capture Before at step 4: old behavior, same form as After.

| Change | Proof |
|---|---|
| Instructions | Fresh agent gets changed skill, realistic request, raw fixtures, never expected outcome. Judge its decisions and artifacts, not word matches. |
| Hook script | Run on fixture run files: no run, open, waiting, idle after a nudge, closed with a gate missing, finished. Hook that drives this session: edit and test a copy, replace live file only once fixtures are green. |
| Both | Both, each proves only itself. |

- Pick cases the change touches: domain it governs (game, mobile, desktop, server, CLI) with real tooling; interrupted run; compaction; broken output contract the checker must catch.
- Isolate fixtures from real project work and secrets.
- Then run repository checks listed in its `AGENTS.md`.

## Review and deliver (steps 7 and 8)

- No factory change reaches main branch without `how-to-review-a-pr` from a fresh agent.
- Draft PR through `how-to-make-a-pr`, with repository's changelog and upgrade notes.
- Humans mark ready, merge, release. Installs get change only after a release.
- Report separately: change, manual use, checks, review, PR. Brief before/after. Name what is unverified.
- Never run `improve-factory` on its own repair.
