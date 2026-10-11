---
name: improve-factory
description: "Repairs or improves the factory itself: its skills, gate, controller and host adapters. Use when the factory skipped a step, gave unclear or wrong instructions, or when its gate, controller or an adapter misbehaved. Not for product bugs; those go back to delivery."
---

# Improve Factory

Fix the factory, never the product.
Keep any active app run safe. The repair never writes the app's source; pausing its gate is allowed.

## Mode

- Fast by default: a light-lane `change` run on its maintenance ticket (the one it follows up, or a new one), with recorded steps, gated by `skills/safe-engine/scripts/fast_gate.py`, started once the maintenance worktree exists. The gate itself blocks the repair: pause the blocking run's gate first. Its done-run is step 5 below.
  - A small repair (wording, one rule) uses the light lane as is: step 3 keeps the cause, a success line and the todos.
  - A method, gate or controller change runs step 3 in full and records it in the Plan section, since the light lane has no Analysis section.
- Safe on request: the full `ticketing` cycle in its own builder session, the file-summary stop and the review in step 6.
- An analysis or planning request stops at that phase. Do not code.

## 1. Understand the report

1. Record in the ticket: observed behavior, expected result, example, artifacts, commands and factory revision.
2. Resolve the factory root and the target project root separately. Read both projects' rules and working status.
3. Ask only the gaps that change the outcome.
4. Classify the cause:

| Cause | Action |
|---|---|
| Instruction skipped | Recover the step. Check how the method was invoked and handed off before adding rules. |
| Skill unclear or incomplete | Fix the skill that owns the rule, then its callers. |
| Gate, controller or adapter fault | Diagnose from source and existing evidence. Fix that layer. Reproduction tests wait for step 5. |
| Missing tool, access or decision | Record the blocker. Invent nothing. |
| Product bug | Back to delivery, unless evidence also shows a factory defect. |
| Working as designed | Explain the rule that applied and where it lives. Change it only on the owner's request. |

## 2. Isolate

- Repair in its own branch or worktree. One writer per file in the candidate.
- Active app run: follow `references/live-session.md` before any workspace change or delegation. Checkpoint → isolated repair → independent review → compatible resume.
- Never silently stash, reset, switch or upgrade a target, its bundle or global settings.
- Factory repair grants no product scope change. Keep the app ticket and the maintenance ticket separate.
- Run independent tickets in parallel, each in its own worktree: a checkout holds one open gate run.
- Work for another session (a parallel ticket, a finding, a suggestion) launches the factory, never a bare task. A product bug during an active app run goes to its coordinator, who records it (`references/live-session.md`). Otherwise record it first in its ticket (`ticketing`): a maintenance ticket, or the product's ticket for a product bug. Its prompt opens with your agent's invoke form (the factory's `docs/hosts.md`) and the launcher's absolute skill path: `improve-factory`, or `safe-engine` for a product bug. Then mode, kind (`safe-engine` only), project root, a worktree the new session creates, the report and authority limited to that ticket.
- Worktrees separate files only. Give delegates absolute paths. Isolate shared ports, databases, caches and services.

## 3. Analyze and plan

1. Run `analyze-start`: source, consumers, flow, evidence versus claims, unknowns and the final reproduction you plan. An unobserved failure stays unverified.
2. Record the invariants: project goal, selected decisions, complete methods, owner stops, human release. Changing one needs the owner. Never weaken a failed check. A proposal is not approval.
3. Plan the smallest complete correction. Exclude unrelated improvements. A new skill, gate, helper or report needs a demonstrated gap. No universal rule for an isolated complaint.
4. Run `get-ready-to-code`: all five outputs. Include reproduction, behavioral checks, consumers, before/after evidence, compatibility and the resume step.
5. Choose the proof now. Instruction change: a fresh agent walks through the changed method. Code or config change: run the affected behavior. Mixed: both.

Do not code before the plan is recorded.

## 4. Repair

- Every todo is a checklist item in the maintenance ticket: the full 0–4 loop with pre, change and post notes, ticked after its check.
- Keep the owner posted:
  - the gate's card after each step (relay it where your agent does not show it);
  - one line per wave of delegates;
  - the question first when waiting.
- Fix the owning cause and every affected caller and link. Remove stale or duplicate prose.
- Write lasting rules into the skill that owns them.
- Edit skills with your agent's skill-authoring tool when it has one.
- Research unfamiliar platform or API behavior from current primary sources. Keep scope.
- Factory files added, moved or deleted:
  1. Update `safe_engine/bundle-inputs.json`. Required files catch deletion; source trees catch additions.
  2. Update the required paths in `safe_engine/distribution.py`.
  3. Run `python scripts/package_skill_entries.py` to refresh the launcher resolvers.
  4. Fix tests that name old paths.
- Never run `improve-factory` on its own repair.

## 5. Check: manual first, tests last

1. Use it first. Instructions: give a fresh agent the changed skill, a realistic request and raw fixtures, without the expected outcome. Judge its decisions and artifacts, not word matches. Code: run the changed command or flow on a realistic case.
2. Pick the cases the change touches:
   - Domain rule: exercise that domain (game, mobile, desktop, server, CLI) with its real tooling. Never import another project's bindings.
   - Live-session or adoption rule: dirty bundle, running operation, inputs changed during plan, change after QA, owner stop, cancellation, lost context.
   - Evidence reuse: both reuse and rejection (changed inputs, tampered proof, pending operations).
3. Isolate fixtures from real project work and secrets. No product pilot or simulation unless the owner asks.
4. Check every changed skill stays self-contained: links only inside its own folder; no names, dates or host specifics.
5. Run the full test suite: `python tests/run.py`, in parallel, the same tests as `python -m unittest discover -s tests`. It must pass. While iterating, `--changed` runs only what the diff touches. Write or fix tests only after step 1.
6. Each check proves only itself. A walkthrough does not prove a code repair; a passing suite does not prove a walkthrough.

## 6. Independent review

- Safe runs this locally. Fast skips it. In every mode, no factory change reaches the main branch without an independent PR review.
- A fresh agent, never the writer, runs `deep-review` on the exact candidate from raw evidence. Give it no verdict.
- A reviewer who repairs needs a different fresh review.
- A changed gate needs its old rule, a reproduction and independent review. Its own pass proves too little.
- One round: review, fixes, fresh review. After round 3, only open high or critical findings keep it going; medium and below are appended to the epic's one open follow-ups ticket in Backlog, never one ticket per finding. At most 6 failed rounds. Then stop that loop and ask the owner once: findings per round, shared cause, options (extend, defer, amend scope, cancel). Keep independent work moving.
- No reviewer available: name the blocker. Never self-approve.

## 7. Deliver

1. Refresh the maintenance ticket. Compare its confirmed criteria with the change, preserved behavior, proof and limits. Drift or a failed refresh blocks acceptance.
2. PRs always, as drafts, through `how-to-make-a-pr`. Missing PR bindings block the PR, not local repair or checks.
3. Humans mark ready, merge and release. Installed copies and active runs never auto-upgrade. A launcher, gate or hook fix reaches agents only after publishing and a plugin update or a fresh `fast_gate.py install`.
4. Active app run: adopt and resume per `references/live-session.md`.
5. Report separately: structure, manual use, tests, review, adoption, PR. Brief before/after. Name what is unverified.

## Record

One Git-ignored record: the Fast work record, or `.factory/maintenance/<id>/` in Safe. Keep:

- Report, expected result, cause or unknown.
- Ticket, confirmed scope, owner source, latest refresh.
- Invariants, choices, analysis, plan, 0–4 notes.
- Checkpoint, old and new commits, dirty manifest.
- Checks, limits, reviewer identity, PR links.
- Adoption, rollback target, exact resume step.

No secrets. Share only sanitized evidence.
