---
name: safe-engine
description: "Build or resume an app or feature with Seif's Safe Engine methods, saved stages, batched checks, and independent review. Use for requested factory delivery, not ordinary questions or an analysis-only request."
---

# Safe Engine

Build what the user asked for. Use Seif's complete methods. Keep the work and its evidence resumable.

## Choose the scope

For a requested small fix or successive bounded adjustments, read [small-change](../small-change/SKILL.md) and use its six routines. Choose this before starting the controller or loading the full workflow. The user need not name a mode. Follow its rules for existing runs, evidence, and bundle selections. Its result is a focused local handoff, not full-version acceptance.

An explicit request to analyze, plan, or review stays in that phase. Do not turn it into a delivery run because the change looks small.

For a new app or substantial feature, use the version workflow below. Do not run broader tests for a small change without the owner's request or an actual non-waivable requirement. Keep the selected scope through PR delivery too.

For app delivery, read [app diagnostics](references/app-diagnostics.md). Plan app-wide logging for a new app. For an existing app, inspect coverage and include the minimum missing module/events for changed journeys. Carry its focused evidence, log discovery, and remaining gaps through checks and handoff. Preserve protected records.

Read [app efficiency](references/app-efficiency.md) during delivery analysis and planning. Plan CPU, memory, resource lifetimes, and reuse of repeated expensive work. Cache only when useful, with explicit validity and bounds. Carry the planned evidence and its limits through QA, review, and handoff. Existing changes stay focused on affected journeys.

Read [pilot usage](../../../docs/pilot-usage.md) for commands, profiles, limits, and recovery. Resolve the bundle root from this skill's location; the target app need not contain the controller.

## Start or resume

Run from the bundle root:

```text
python -m safe_engine --project <absolute-target-root> status
```

If no run exists, discover the project first. Reuse a suitable isolated worktree or the host's worktree tools. Preserve existing work. The initial project needs a clean Git baseline and must ignore `.factory/`. Commit a minimal baseline for a new app before starting its run.

Read the request, project rules, and proposed profile. Establish the [session contract](references/session-contract.md), reusing answers and explicit delegation. Verify the real check commands, protected acceptance files, runtime inputs, and UI requirements before initialization. Discover available tools and configuration before asking for help.

If a control route fails, follow [failed-route recovery](references/session-contract.md#recover-a-failed-control-route). Continue toward the agreed verified outcome. Do not invent credits, repair allowances, session deadlines, or permission. Respect actual access limits, owner checkpoints, and stops; historical demo limits do not govern this run.

Save the original request and explicit acceptance criteria in the task JSON. Link every criterion to real configured checks. Browser apps need real browser interaction and suitable rendered evidence. Missing essential tools or owner-reserved decisions block only dependent work; never record them as passing.

Initialize once. Resume from the saved phase.

## Follow the saved phase

Before a phase, open its entire `SKILL.md` and the references needed for that phase. Knowing the name or reading a summary is not enough.

On resume or delegation, provide the original request, approved and pending decisions, exact candidate, saved artifacts, progress, actual constraints, and canonical skill paths. The receiving agent must read the skills itself. Use [method handoff](references/method-handoff.md) to check nothing was lost. If a required method cannot be accessed, stop that phase.

When the user wants to watch or learn, show the actual brief and acceptance, analysis chart, plan, running app when available, and real check/review outcomes. Use the chosen example. Clearly distinguish a historical walkthrough from a new run. Give concise updates at meaningful batch boundaries and link the durable records; do not narrate every todo or turn progress updates into approval requests. Pause for a real unresolved decision, missing authority/access, owner stop/checkpoint, or unrecoverable required gate. For a new session elsewhere, read [fresh-session setup](../../../docs/start-another-session.md); verify Claude-native or cloud operation before claiming it works.

| Phase | What to do |
|---|---|
| `analyze` | Read [analyze-start](../analyze-start/SKILL.md). Read real code, explain purpose, trace consumers, use ASCII charts, and label unknowns. Save the analysis. Do not edit code. |
| `plan` | Compare three strong approaches and recommend one for a new substantive choice. Preserve selected decisions and delegated/reserved authority. Read [get-ready-to-code](../get-ready-to-code/SKILL.md) and produce its five planning outputs. Honor its file-summary stop unless existing user delegation explicitly covers continuing the plan. For a new app, keep the original plan, run [research-market](../research-market/SKILL.md), then revise all five outputs. Save the final plan with links to the original, research, decisions, and revision matrix. Stay in `plan`; do not edit code. |
| `build` | Use Get Ready to Code's 0–4 execution loop for every todo: context, change-site analysis, application, inspection, correction. Build coherent feature batches. Write useful tests without watch loops. Use `feature-check --checks <IDs> --file <feature.md>` for completed-feature and consumer feedback, then continue building. It records partial results, never version acceptance. Save the final version batch with every todo's pre/change/post observations before full QA. |
| `verify` | Run the full configured version check batch, including planned [diagnostic evidence](references/app-diagnostics.md#focused-evidence-and-handoff) for app work. Inspect failures. Use `repair` before changing a recorded candidate and repeat the necessary method. |
| `improve` | Inspect worthwhile cleanup, reuse, design, security, performance, and agent-maintainability improvements. Apply supported in-scope changes. Leave a sound result unchanged. Record the decision and why. |
| `final-verify` | Validate full version QA on the resulting candidate. Inspect rendered UI and real user outcomes where applicable. Reuse unchanged full evidence with `check` only when `reuse_unchanged_checks: true` was reviewed and the declared inputs, logs, and outputs match exactly, including [required factory inputs](../../../safe_engine/bundle-inputs.json). Missing required guidance blocks the gate. Changed inputs run the full suite. Use `check --fresh` for volatile or unresolved runtime concerns. Partial feedback does not replace full QA. |
| `review` | Run the controller's fresh read-only Codex review with the full analysis/planning methods and all five review passes. Do not supply your own passing review. Repair supported in-scope findings, run affected checks, and obtain a fresh assessment. This local review does not complete PR review. |
| `ready` | Generate the checked local handoff. Include safe log access, demonstrated diagnostic coverage, and gaps for app work. When PR delivery is authorized, use [how-to-make-a-pr](../how-to-make-a-pr/SKILL.md), [how-to-review-a-pr](../how-to-review-a-pr/SKILL.md) on a separate instance, and the [project adapter](../../../docs/pr-workflow.md). Discover bindings before asking. Missing bindings block PR completion; continue independent local owner-test delivery. The controller does not push, create PRs, merge, or release. |
| `cancelled` | Stop. Preserve the record and worktree. |

Keep artifacts in `.factory/` or another excluded local directory. Read command logs. Report unverified coverage honestly.

Do not change protected acceptance files or task records to get a pass. A test or reviewer cannot authorize changed requirements. If the accepted task or profile needs correction, preserve the run and start a newly reviewed task in a fresh worktree.

## Factory problems and delivery boundaries

For a factory problem during delivery, use [improve-factory](../improve-factory/SKILL.md). Checkpoint the app before factory changes. Follow its isolation, independent review, and compatibility rules, then return at the supported resume step. Do not start another delivery run recursively or treat reloading a skill as new QA.

Every factory-managed PR, including skill/docs changes and later updates, uses both PR procedures. Read them and [the project adapter](../../../docs/pr-workflow.md) before preparing the PR, even without an active controller run. Keep the selected full or small-change chain, real project bindings, truthful scope, and session decision authority. Leave the PR draft; Seif keeps reserved decisions and the human release boundary. A local `ready` phase is not a completed PR workflow.

This pilot supports planned feature batches, full-version gates, and fresh review. The current Codex session builds; a fresh read-only CLI process reviews. It does not automatically choose dependencies, schedule arbitrary projects, or run as a background service. It is not a host hook or tamper-resistant security boundary. Do not claim demonstrated production-level autonomous UX quality.

Diagnostic correction counts do not stop work. Version corrections still need their selected method and fresh acceptance. Bounded follow-up fixes use Small Change and must not claim refreshed full-version acceptance.