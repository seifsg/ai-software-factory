---
name: safe-engine
description: "Run or resume a Safe Engine app-development task using Seif's analysis, planning, and 0-4 coding method, saved stages, batched checks, and fresh review. Use for a requested factory delivery run; ordinary questions do not start a run."
---

# Safe Engine

This is the small coordinator for the local pilot. Seif's procedures own analysis, planning, implementation, and review. Read [pilot usage](../../../docs/pilot-usage.md) for the real CLI, profile, limitations, and recovery. Resolve the bundle root from this skill's location; do not assume the target project contains the controller.

## Start or resume

Run the controller from the bundle root with `python -m safe_engine --project <absolute-target-root> status`. If no run exists, discover the project first. Use an existing suitable isolated worktree or the host's worktree tools; preserve existing work. The initial project must have a clean Git baseline and ignore `.factory/`. A new application needs a minimal committed baseline before the run.

Read the user's request, project rules, and proposed profile. Verify the actual check commands, protected acceptance files, runtime inputs, browser requirements, and finite budgets before initialization. Discovery proposes configuration; it does not execute scripts or infer authority. Use the user's selected limits; the demo's limits are fixture values, not a global policy.

Capture the original request and explicit acceptance criteria in the task JSON. Each criterion links to real configured checks. For a browser app, include actual browser interaction and appropriate rendered evidence. Missing tools or a needed product decision are blockers, not passing results. Initialize once; then let the saved phase determine the next action.

## Follow the saved phase

When the user wants to watch or learn from a run, make the execution visible: show the actual brief and acceptance before building, the analysis chart and plan, concise stage updates, the running app when available, and real check/review outcomes. Link the recorded artifacts. Distinguish a historical walkthrough from a new execution. Progress updates do not require another approval; pause only for a real unresolved decision, missing authority/access, or exhausted limit. Use the user's selected example, not a substitute demo. For starting elsewhere, read [fresh-session setup](../../../docs/start-another-session.md); Claude-native and cloud operation must not be claimed without verification.

| Phase | Action |
|---|---|
| `analyze` | Use [analyze-start](../analyze-start/SKILL.md). Read real code, explain why, map consumers, draw ASCII flow/architecture charts, and label unknowns. No code edits. Record the analysis artifact. |
| `plan` | Use Part A of [get-ready-to-code](../get-ready-to-code/SKILL.md): file list, critique, phases, all todos, full plan. No code edits. Record the plan. |
| `build` | Use Part B of the same method. Every todo has context, change-site analysis, application, inspection, and correction. Build a substantial batch; write useful tests without starting watch loops. Record the batch and its pre/change/post observations. |
| `verify` | Run one configured check batch. Inspect real failures; use `repair` before changing a recorded candidate and then repeat the necessary method. |
| `improve` | Inspect the completed feature for worthwhile cleanup, reuse, design, security, performance, and agent-maintainability improvements. Apply only supported in-scope changes. A sound result can remain unchanged. Record what changed and why, or why no changes were warranted. |
| `final-verify` | Run the final check batch on the resulting candidate; inspect rendered UI and actual user outcomes where applicable. |
| `review` | Run the controller's fresh read-only Codex review. Do not write your own passing review in its place. Findings lead to a bounded repair, affected checks, and another fresh assessment. |
| `ready` | Generate the checked handoff. Push, PR, merge, and release follow the task's actual authorization; this controller performs none of them automatically. |
| `cancelled` | Stop. Preserve the record and worktree for the user. |

Keep artifacts in `.factory/` or another excluded local location. Read command logs and report unverified coverage honestly. A reviewer or test saying “pass” does not authorize changed requirements. Never alter protected acceptance files or task records to make a gate pass. If the accepted task or profile needs correction, preserve this run and start a newly reviewed task in a fresh worktree.

## Operating boundaries

The pilot supports one coherent feature batch per normal cycle; corrections use the shared budget. Broader multi-batch scheduling remains an extension. It uses the current Codex session as its builder and a fresh read-only CLI process as reviewer. It is not a background app-building service, host hook, or tamper-resistant security boundary. Do not claim production-level autonomous UX quality from this pilot demonstration.
