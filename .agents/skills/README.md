# Skill index

Six real entrypoints are packaged in Safe Engine 0.1.0: five adapted from Seif's supplied collection and one authorized coordinator. All six pass structural validation. That validates their packaging, not every possible workflow outcome. See the [pilot verification record](../../docs/pilot-verification.md) for observed behavior and limits.

| Skill | Purpose | Dependencies |
|---|---|---|
| [safe-engine](safe-engine/SKILL.md) | Start/resume a local delivery cycle and checked handoff | Python controller, Git, Codex CLI, actual project check tools, the five methods below |
| [analyze-start](analyze-start/SKILL.md) | Read code, explain purpose, map consumers, draw ASCII charts; no edits | Actual source and read/search tools |
| [get-ready-to-code](get-ready-to-code/SKILL.md) | Five planning artifacts followed by the per-todo 0–4 loop | Completed analysis, source editing, configured checks |
| [deep-review](deep-review/SKILL.md) | Review logic, boundaries, security, performance and user journey | Candidate source, diff, applicable bundled review references |
| [change-guard](change-guard/SKILL.md) | Inspect consumers and regressions after substantial changes | Consumer map, source/diff and check evidence |
| [compliance-check](compliance-check/SKILL.md) | Trace original requirements to supported outcomes | Original task, acceptance criteria and actual evidence |

Existing skills supplied by Seif are the starting point. The [expanded capability plan](../../docs/safe-engine-expanded-scope.md) records the requested specialist capabilities and proposed boundaries. Seif leads authorship; counts, names, and new procedures remain open until selected.

The wider collection contains 38 source entrypoints; five have been imported here. [Provenance and adaptations](../../docs/skill-provenance.md) records the exact source revision. Planning and execution remain two parts of Seif's original file in this pilot, with distinct controller phases; the proposed larger modular library is still ahead.
