# QA entry point and enforcement gaps

Research and design, 30 September 2026. This document compares Seif's existing procedures with published factory patterns and proposes the next capabilities to build. It does not install a skill, hooks, a runner, or GitHub protections.

**Build a small `factory-qa` entry skill backed by saved task state, executable gates, host hooks, and independent delivery checks.** The skill chooses the process; the gates require evidence before the work advances. Instructions alone cannot guarantee that an agent follows every rule.

## What we already have

The [factory repository](../README.md) currently contains rules, a preview, and a [mapping of 38 source skills](skill-lifecycle-map.md). Its skill index explicitly says no skills are imported. No connected QA run has been demonstrated.

The supplied RepairCheck collection already describes analysis before implementation, review before and after each todo, five review lenses, finding deduplication, build checks, a fresh reviewer, draft PRs, and human approval. These are strengths to preserve. The source `.claude/settings.json` contains permission settings but no lifecycle hooks. Most gaps concern executing and connecting these procedures, rather than writing more quality instructions.

Audit baseline: factory commit `30a26e269c7d34a0df670d0958a4a60b9e916b70`; supplied collection snapshot `449e1110104b6ac27aed3a940c5ed6d1bf671f11`. The delivery core and review resources were examined; specialist business routines were not exhaustively exercised. Source routines were read as reference material and were not invoked.

## Patterns worth adopting

These are published mechanisms, not an independent audit of another company's results. The recommendations in the following sections are our design choices.

| Source | Published mechanism | Proposed use here |
|---|---|---|
| [Stripe Minions Part 2](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2), 19 February 2026 | Code-defined blueprints combine agent work with deterministic lint and push steps, isolated environments, and limited CI repair attempts. | Enforce required transitions in code while leaving the agent room to solve the problem. |
| [OpenAI Symphony specification](https://github.com/openai/symphony/blob/main/SPEC.md) | One scheduling authority coordinates claims, workspaces, retries, reconciliation, and versioned workflow configuration. `before_run` failure aborts an attempt; `after_run` failure is logged and ignored. | Reuse ownership and recovery ideas. A best-effort after-hook must not certify QA success. |
| [StrongDM factory](https://factory.strongdm.ai/), 6 February 2026 | Acceptance scenarios can live outside the editable codebase; dependency twins permit controlled integration failures. | Preserve acceptance independently of the builder. Start with fixtures and contract tests; richer twins need a demonstrated benefit. |
| [Uber factory](https://www.uber.com/gb/en/blog/efficient-software-factory/), 27 August 2026 | Centralized policy and authentication, selective tools, outcome-based cost measurement, and proposed improvements from traces. | Resolve real capabilities and measure accepted results. Automatic skill improvement remains a proposal in that account. |
| [Superpowers bootstrap](https://github.com/obra/superpowers/blob/main/hooks/session-start) and [configuration](https://github.com/obra/superpowers/blob/main/hooks/hooks.json) | A session hook injects its entry procedure. The checked-in matcher covers startup, clear, and compact. | Load a concise entry procedure, with explicitly tested resume and delegation coverage. Injection does not prove faithful execution. |

## How the entry point should work

The proposed `factory-qa` is a small router and supervisor. It resolves the target project, creates or resumes a run, selects the relevant canonical skills, and requests the controller's next permitted stage. It returns evidence, a review handoff, or a precise blocker.

It should not duplicate the review battery or load every domain skill. Adapt `analyze-start`, `get-ready-to-code`, `deep-review`, `change-guard`, `compliance-check`, and the PR procedures where applicable. The project profile supplies commands and integration context; source-specific permissions and messaging instructions do not transfer automatically.

```text
Request -> factory-qa -> relevant delivery skills -> verified review -> agreed handoff
               |                  |                       |
               +------------------+-----------------------+
                                  |
                    Controller checks stage prerequisites
                       |                       |
              Saved run and evidence     Independent CI checks
                       ^                       |
                 Lifecycle hooks        Protected merge boundary
```

The components have distinct jobs:

- **Skill:** explains the procedure and routes judgment work.
- **Project profile:** specifies commands, required checks, tools, scope, and authority.
- **Run record:** preserves the original request, decisions, stage, evidence, and next action.
- **Controller:** accepts a transition only when its required evidence is present and current.
- **Hooks:** load context and call checks at supported lifecycle events.
- **Independent checks:** protect acceptance and the merge or release boundary outside the agent's editable session.

The controller should use the same decision rules whether called manually, by a hook, or by CI. A raw tool event is not automatically a development stage: running a shell command may inspect files, mutate code, start a long-lived process, or perform an external action.

## Proposed lifecycle checkpoints

This is a design mapping, not installed hook configuration. The host adapter must prove its actual event coverage.

| Checkpoint | Intended action | Condition for advancement |
|---|---|---|
| Start or resume | Load the project profile and reconstruct the active run. | Required context and dependencies are resolved for the next action. |
| Before implementation | Check scope, acceptance criteria, and the preparation required for this change type. | A sufficient work contract exists; small edits need proportionate preparation. |
| After a mutation | Record changed content and invalidate affected verification or review evidence. | Previous passes cannot silently validate a changed result. |
| Before push or review handoff | Execute applicable checks and construct the review inputs. | Required local evidence is valid for the proposed revision. Draft diagnostics remain distinguishable from ready-for-review work. |
| Reviewer start and finish | Supply original requirements and the actual diff; record findings and a structured verdict. | Blocking findings are resolved or the run is explicitly blocked. Reviewer edits require renewed verification. |
| Before compaction or interruption | Save checkpoints continuously and at available lifecycle events. | Recovery does not depend on a final hook firing successfully. |
| Attempt to finish | Consult the recorded task state and required evidence. | The agreed acceptance boundary is reached, or an honest handoff/blocker is reported. |
| Merge or authorized release | Independently enforce repository checks and authority. | Required external checks and the applicable human decision are satisfied. |

[Codex hooks](https://learn.chatgpt.com/docs/hooks) currently support lifecycle and tool events with command/MCP handlers. Non-managed hooks require trust; prompt/agent handlers are skipped. Background hooks cannot block, coverage has exceptions, and some hook failures allow the tool to proceed. A post-tool hook cannot undo an action. These limits make a separate controller and repository gate necessary.

[Claude Code hooks](https://code.claude.com/docs/en/hooks) use different semantics and support additional handler types. Skill-scoped hooks activate only after invocation. Stop is a response boundary, not proof that the project is complete. Missing scripts and timeouts can be nonblocking. Hook scripts do not directly invoke skills; injected routing instructions still depend on model behavior. Neither host's installed version or hook setup has been validated in this project.

## Complete gap list

P0 means necessary for a dependable first delivery loop. P1 strengthens operation and quality after that loop works. P2 is conditional expansion, not a lower quality bar for work that requires it. These are proposed improvements, not claims that every other factory implements all of them.

### P0 Reliable entry and delivery

| No. | Addition | Existing foundation | Evidence that closes the gap |
|---|---|---|---|
| 1 | Import and validate the portable delivery core | The source skills exist and have been mapped. | Real entrypoints, references, dependencies, and host discovery validate; a representative invocation succeeds. Import only the required core first. |
| 2 | One concise QA entry point | A source chain links analysis, building, and review. | `factory-qa` initializes or resumes a run and routes the necessary procedures without duplicating them. |
| 3 | A validated project profile | Source procedures contain stack, tracker, branch, and access assumptions. | Commands, capabilities, credentials availability, required checks, and authorized side effects resolve explicitly. Missing access blocks the dependent action. |
| 4 | A preserved work contract | Reviews refer to the original request. | Original goal, acceptance criteria, allowed scope, and completion boundary survive handoffs. Requirement changes are explicit and reviewable. |
| 5 | Durable state and recovery | Our repository rules require durable handoffs. | Restart, resume, compaction, and interruption preserve stage, decisions, findings, evidence, and next action. State is saved before risky transitions, not only at shutdown. |
| 6 | Executable stage gates | Preparation and build requirements are mostly prose. | Missing required artifacts block the corresponding transition. The controller permits flexible implementation within those gates. |
| 7 | Installed hooks with a tested host adapter | No source lifecycle hooks were found. | Required events, trust, script installation, version support, timeout behavior, and supported denials are demonstrated. Hook failure becomes unknown/blocked evidence rather than a pass. |
| 8 | Verification tied to current content | Source skills request lint, typecheck, tests, and reviews. | Each result records command, exit status, revision/content identity, relevant inputs, and artifacts. Mutations invalidate affected results; completion also recomputes freshness. |
| 9 | Acceptance and checker integrity | A fresh reviewer and original-request check are described. | The builder cannot quietly weaken decisive criteria, tests, or gate configuration. Reviewable changes to checks remain possible; independence is enforced by access or protected configuration. |
| 10 | A fresh reviewer with structured findings | Five review lenses, deduplication, and severity synthesis exist. | Reviewer receives original requirements and exact changes directly. Findings retain severity, confidence, resolution, and decision owner. Reviewer fixes invalidate relevant evidence. |
| 11 | A truthful finalization gate | Draft review and human handoff are distinguished in the source. | Missing, failed, skipped, or unavailable required evidence cannot become passed. Checked, reviewed, awaiting approval, accepted, and released remain separate states. |
| 12 | Independent repository checks | Human review and no-red-gate instructions exist. | The agreed merge boundary requires checks on the correct revision from the expected source. The builder cannot silently weaken the workflow or bypass policy with its credentials. |
| 13 | A shared correction budget | Build and review each contain retry loops. | Nested loops share attempt/time limits and cost limits where available. Exhaustion preserves work and produces a blocker; it never lowers the acceptance bar. |

GitHub accepts `skipped` and `neutral` conclusions for some required-check purposes. A conditional job can appear successful, and dependent jobs can be skipped after a failure. Our proposed required aggregate check must explicitly verify that every applicable mandatory check actually passed, while representing a reviewed not-applicable outcome separately. Check freshness, expected source, and private-repository plan support before enabling protection. [GitHub required-check behavior](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)

Local Git hooks provide earlier feedback, but ordinary commit hooks can be bypassed with `--no-verify`. They should complement the external gate. [Git hook reference](https://git-scm.com/docs/githooks)

### P1 Stronger operation and quality

| No. | Addition | Why it helps | Evidence that closes the gap |
|---|---|---|---|
| 14 | Checks proportionate to change and risk | Preserves quality without running every specialist or full suite after every edit. | UI, API, dependency, schema, and documentation changes select appropriate checks. Expensive checks run at useful boundaries; the reason for exclusions is visible. |
| 15 | One owner and isolated workspaces | Prevents parallel agents from mixing edits or advancing the same run twice. | A run has a stable owner/claim, a known branch/workspace, reproducible setup, and controlled shared writes. Workspace isolation does not substitute for credential or network controls. |
| 16 | Duplicate prevention on retries | Avoids repeated PRs, tasks, comments, or other external effects after uncertain responses. | Stable operation IDs and remote readback reconcile ambiguous outcomes before retrying. Apply only to actions authorized for the task. |
| 17 | Cancellation and changed-request handling | Keeps automation aligned with the user's current intention. | A stop remains stopped; changed scope or remote task eligibility triggers reconciliation. Preserve the patch and report its state without silently resuming canceled work. |
| 18 | User-visible outcome checks | Adds evidence beyond code inspection and passing unit tests. | Relevant user journeys, failure paths, responsive layout/accessibility, or performance behavior are exercised where the task requires them. Screenshots support behavior checks rather than replacing them. |
| 19 | Realistic integration verification | Exposes failure conditions that local code checks miss. | Appropriate fixtures, contract tests, replayable failures, or staging demonstrate required integration behavior. A full dependency twin is optional and justified by recurring needs. |
| 20 | A concise execution trail and outcome measurements | Makes failures diagnosable and quality improvements measurable. | A human can see request, changes, check results, blockers, owner, and next action. Measure acceptance, rework, escaped defects, elapsed time, and cost where available; keep secrets out of records. |
| 21 | Tests of the QA system itself | Proves the enforcement works when the agent or tooling misbehaves. | Repeatable cases detect missing stages, unmet requirements, regressions, stale evidence, malformed hooks, timeouts, context loss, unauthorized transitions, and exhausted retries. |
| 22 | Versioned skills and controlled improvement | Prevents growing, conflicting prompts and unnoticed regressions. | Skills have clear routing boundaries and canonical owners. Proposed changes are compared on representative tasks before promotion; traces inform improvements rather than silently rewriting policy. |

OpenAI recommends checking actual skill execution traces as well as output quality through [skill evaluations](https://developers.openai.com/blog/eval-skills). Its current guidance also favors concise routing descriptions, supporting references loaded as needed, and instructions scoped to the task. [Skill and instruction guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)

### P2 Complete the lifecycle when release is in scope

| No. | Addition | Why it helps | Evidence that closes the gap |
|---|---|---|---|
| 23 | An authorized release and recovery path | Extends the source's draft-PR boundary into delivery. | The approved revision, deployment result, appropriate smoke checks, and rollback/recovery path are verified. Deployment follows the target project's authority model. |
| 24 | Observation and feedback routing | Confirms the deployed outcome and turns evidenced problems into new work. | Agreed health or user-outcome signals are checked. Defects return to intake; UX suggestions remain proposals for prioritization. Monitoring or recurring runs are configured only when requested. |

## First version to build

Begin in one target repository with one small real change and a draft-PR handoff. Adapt only the necessary source skills. Implement `factory-qa`, a project profile, a durable run record, a small gate/check runner, and one chosen host adapter. Add external required checks where the target repository's permissions and plan support them.

The initial run record needs the request and acceptance criteria, project/base revision, scope and authority, skill/profile versions, stage and owner, evidence references, unresolved findings, budget, and next action. Keep local execution state outside committed source. Reviewable schemas and harmless evaluation fixtures can live in the factory repository.

Proposed controller operations are `start`, `resume`, `checkpoint`, `verify`, `status`, and `finalize`. These are design labels, not existing executable commands or host slash commands. Avoid a database or background scheduler until the same loop works reliably with simple saved records.

The first acceptance demonstration should prove:

1. A clearly specified task reaches a checked draft-PR handoff.
2. An omitted requirement or introduced regression prevents advancement.
3. Passing checks followed by a code change makes the previous evidence stale.
4. Interrupting and resuming preserves requirements and avoids duplicate effects.
5. A missing or failing critical hook/check cannot be treated as a pass.
6. Retry exhaustion and unavailable dependencies return accurate blockers.
7. A human stop and the agreed merge/release boundary are respected.

The useful promise is observable compliance with required gates, current evidence, and recoverable progress. A claim that every instruction is always followed would exceed what skills, hooks, and model review can establish.
