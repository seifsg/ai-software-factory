# Safe Engine pilot implementation

The first working version runs Seif's existing methods inside a local Codex session. A Python controller persists the task, advances explicit stages, runs batched checks, rejects stale evidence, and invokes a fresh read-only Codex review before preparing a local handoff. It does not merge, deploy, or operate live systems.

## Analysis of the starting repository

Before this implementation, the repository contained documentation and a static preview. The reusable method is in Seif's source repository at `449e1110104b6ac27aed3a940c5ed6d1bf671f11`. `analyze-start` defines code-grounded analysis, callers, ASCII diagrams, and no coding. `get-ready-to-code` defines five planning artifacts followed by the per-todo 0–4 inspection loop. `deep-review`, `change-guard`, and `compliance-check` supply the complementary review lenses. There was no runtime connecting them. The completed implementation's evidence is in [pilot verification](pilot-verification.md).

The pilot retains these five entrypoints and adds `safe-engine`. It adapts only the recorded user decisions: project-neutral language, bounded corrections, unknowns that block affected decisions, authorized exceptions, measured performance, batched tests, and fresh review. The selected eventual split of planning and execution into separate skills remains packaging work; the controller already separates those phases and preserves the original procedure.

```text
Codex + safe-engine skill
       |
       +-- analyze-start -> analysis artifact
       +-- get-ready-to-code Part A -> plan artifact
       +-- get-ready-to-code Part B -> substantial implementation batch
       |
Python controller -> recorded command results -> improvement -> final checks
       |
Fresh read-only Codex process -> quality / regression / requirements review
       |
Current evidence + complete criteria -> local handoff, human delivery boundary
```

The controller's callers will be the entry skill, a CLI user, and its fault tests. Target projects supply explicit check commands and declared runtime inputs. A deterministic runner verifies exit results and input freshness; it cannot prove that a test is meaningful or that a model's judgment is correct. The fresh reviewer assesses those matters. Local files and credentials are controlled by the same OS user, so this pilot is not a tamper-resistant acceptance service or a repository merge protection.

## Plan and file critique

Keep code in a small `safe_engine` Python package, with project input discovery, persistence, command execution, and workflow logic separated by responsibility. Use the standard library. A disposable web fixture and actual browser test exercise the complete handoff. Preserve source provenance next to the bundle, and keep run state out of Git. Avoid a web dashboard, database, autonomous deployment daemon, or imported third-party skill suite in this first version.

1. Import and adapt five source procedures, preserving the user's analysis and execution loop; add one coordinating entry skill.
2. Implement project discovery, JSON profile/task validation, atomic checkpoints, and input fingerprints.
3. Implement analysis/plan/build/check/improve/review/handoff transitions, cancellation, and a caller-supplied repair budget.
4. Execute real commands as batches; capture outcomes, reject changed inputs, and run fresh Codex review in read-only mode.
5. Exercise successful delivery plus failed checks, stale evidence, skipped phases, exhausted repairs, and cancelled runs.
6. Demonstrate a feature on a disposable Git worktree with unit and real browser checks, then independently review the pilot.
7. Publish accurate setup, scope, invocation, provenance, demonstrated results, and remaining gaps; update the preview's status.

Every implementation todo follows context gathering, change-site analysis, application, inspection, and correction. Tests run after coherent implementation batches. The final improvement pass checks unnecessary state, duplicated validation, process cleanup, stale-evidence paths, and whether diagnostics help the next agent.

## Acceptance

- A user can discover a project, initialize a task, follow the original methods, run a QA batch, record an improvement pass, obtain fresh review, and produce a readable handoff.
- Source edits during analysis/planning are rejected at the relevant transition.
- Failed commands, missing artifacts, incomplete criteria, stale inputs, missing review, and exhausted repairs prevent a ready handoff.
- A resumed process reads the saved task and next stage; concurrent mutation is refused.
- At least one real browser journey is verified in a disposable application, with actual tool results distinguished from fixture assertions.
- No runtime file, secret, installed dependency tree, or disposable worktree is committed.

The pilot demonstration uses explicit finite test budgets and timeout values as fixture configuration, not permanent defaults for customer projects. The wider factory still needs protected external acceptance, host hooks, more scenario adapters, the rest of the specialist library, and demonstrated portability.
