# Safe Engine fast feature delivery

Seif's direction, recorded 1 October 2026: **build substantial parts of a feature, batch verification at meaningful boundaries, improve the completed design before pushing, then verify the improvements. Optimize the code for reliable future work by AI agents.** These requirements amend the [expanded capability plan](safe-engine-expanded-scope.md). The later [local pilot](pilot-verification.md) implements the first delivery loop; the broader choices below remain proposals.

The remaining choices below concern batch boundaries, improvement scope, agent-oriented structure, and an optional control. Each has three alternatives and one recommendation. Names, control design, numerical limits, and skill packaging remain Seif's decisions.

## Requested workflow

```text
Plan the feature and substantial development batches
                         |
               Build a coherent batch
          code + useful tests + required UI
                         |
               Run verification batch
        applicable unit / integration / E2E checks
                         |
         Repair supported failures as a batch
                         |
              Complete remaining feature
                         |
          Establish the working feature baseline
                         |
          Inspect improvement opportunities
       cleanup / reuse / design / performance / security
                         |
             Apply worthwhile improvements
                         |
       Recheck affected behavior and final user journeys
                         |
            Fresh independent final review
                         |
                 Ready for agreed push
```

Verification runs after substantial work, rather than after every edit, helper function, or save. Do not start unit or E2E watch loops by default. Existing compiler or editor diagnostics can inform development without becoming a repeated test-suite loop. A known failure that prevents further work can be investigated directly; the default batch policy must not be bypassed by classifying every edit as an exception.

The task can specify expected behavior and author tests during development while deferring their execution to the batch boundary. This is not strict per-function RED/GREEN TDD. TDD remains an available technique for deliberately chosen tasks, with its execution cadence made explicit. The earlier E4 recommendation does not override this newer instruction.

An E2E scenario becomes executable when its journey exists. If an intermediate batch lacks the required UI or backend, retain that scenario as pending and execute it when the full path is ready. Pending coverage is not a passing result. Documentation-only work uses relevant document checks rather than application test suites.

## F1 Verification batch boundaries

The user has already selected batching. These options concern how to define substantial batches, not whether to return to testing every small change.

| Option | Boundary | Benefit and tradeoff |
|---|---|---|
| A | Whole feature before the first test batch. | Fewest interruptions; several interacting defects can accumulate before diagnosis. |
| B | Planned, coherent capabilities within the feature, plus final feature verification. | Earlier feedback on meaningful outcomes; requires sensible boundaries instead of artificial microtasks. |
| C | Major implementation layers, such as backend complete, then frontend complete. | Fits some project structures; cross-layer integration failures may arrive later. |

**Recommend B.** A batch should produce an inspectable capability, such as creating and editing a saved item, rather than an arbitrary number of lines or minutes. A small feature can be one batch. An expanded feature can have several substantial capabilities. The planner proposes these boundaries before execution; exact sizing remains project-specific.

Within a batch run, select checks by changed behavior and affected dependencies. Reusing a shared component requires testing its relevant consumers, not only the file edited. Broaden coverage when dependency impact is uncertain or when shared configuration, schemas, authentication, or build inputs change. The project's required final acceptance suite still applies.

Nx demonstrates dependency-aware task selection using Git changes and the project graph; this is inspiration for adapters, not a requirement to install Nx. [Affected tasks](https://nx.dev/docs/features/ci-features/affected).

Avoid rerunning identical, still-valid checks solely because another stage starts. Caching is appropriate only when the result's relevant inputs and environment are controlled and its validity can be established. Backend-dependent browser results cannot be reused merely because source files did not change. G6 now selects exact declared-input binding for the pilot; safe result reuse remains future work. The initial pilot conservatively reruns its final batch, including after a no-change improvement pass; this is a known efficiency gap against this target. [Nx cache constraints](https://nx.dev/docs/features/cache-task-results).

## The improvement pass before push

The pass examines the completed feature and applies supported improvements within the agreed scope. It can conclude that no changes are warranted. Use the verified feature as the comparison baseline, then group related changes before the post-improvement QA batch.

| Opportunity | Basis for making the change | Evidence afterward |
|---|---|---|
| Remove unused code or dependencies | Check imports, entrypoints, registrations, generated references, dynamic loading, public exports, and supported consumers. | Relevant build and behavior checks; affected entrypoints still work. |
| Reuse duplicate components or logic | The copies implement the same responsibility and have compatible behavior. | All affected consumers retain their intended variants and interactions. |
| Split a function or module | Separate responsibilities, side effects, or dependencies make changes difficult to reason about. | Clear contracts and equivalent required behavior. |
| Combine functions or remove wrappers | Existing indirection or fragmentation adds navigation without a useful boundary. | Fewer unnecessary hops and preserved contracts. |
| Improve performance | Identify an actual bottleneck or unnecessary work against a relevant workload. | Comparable measurements before and after, plus correctness checks. |
| Improve security | Identify a concrete weakness, missing control, or inconsistent protection. | Relevant negative cases, supported control evidence, and normal-flow regression checks. |
| Improve agent navigation | Ambiguous names, hidden dependencies, duplicate sources of truth, or missing context cause avoidable investigation. | Clear ownership, discoverable contracts, and a more direct path to the next change. |

Source search alone is insufficient proof that an export is unused. Knip documents reachability gaps involving entrypoints, generated files, and dynamic imports. Use analysis findings as evidence to investigate, not automatic deletion authority. [Unused-code analysis limitations](https://knip.dev/guides/handling-issues).

Reuse is justified by shared meaning and behavior. Two similar-looking components can deserve separate implementations if combining them creates conditionals for unrelated products. Conversely, splitting every small function into another file can make an agent load more context to understand one operation. Preserve the selected I5 policy: function length and file length are inspection prompts, not automatic refactoring rules.

Performance, security, reuse, and navigability are separate outcomes. A cleanup can improve one while preserving the others. Do not claim universal improvement because tests pass or line count falls. A cache might reduce latency while introducing stale data or authorization risks; evaluate those tradeoffs before keeping it. Larger changes to product behavior or architecture remain explicit decisions.

## F2 Scope of the improvement pass

| Option | Scope | Benefit and tradeoff |
|---|---|---|
| A | Only directly changed files. | Fast and easy to contain; can miss duplicate logic or affected consumers nearby. |
| B | The feature, its relevant callers, and shared components it touches. | Finds useful design opportunities while keeping the feature deliverable. |
| C | The entire application. | Exposes broader debt and structural issues; can turn feature delivery into a large refactor. |

**Recommend B.** It covers the reuse and simplification opportunities Seif described. Keep separate opportunities outside the feature visible for a later decision. Required defect repairs remain part of acceptance; optional improvements stop when their expected value no longer justifies added change and verification work. The selected continuous session contract governs completion and actual owner boundaries; no artificial repair allowance or session deadline is introduced.

## Code optimized for AI agents

The target is for an agent to find the right code, understand its contract with limited context, make a localized change, and verify it accurately. Agent reasoning and maintenance take priority over individual human stylistic preferences. Correctness, security, and inspectable decisions remain part of the standard.

OpenAI's harness-engineering account emphasizes repository-local knowledge, a compact navigation entrypoint, explicit architectural boundaries, and executable feedback. This supports the direction; it does not demonstrate that our proposed structure will be faster in every project. [Primary source](https://openai.com/index/harness-engineering/).

Our proposed review criteria are:

| Criterion | Concrete application |
|---|---|
| Predictable locations | A feature's behavior, contracts, and tests have discoverable owners. |
| Explicit interfaces | Inputs, outputs, errors, validation, and side effects are easy to inspect. |
| Local reasoning | One behavior can be understood without following a chain of trivial wrappers. |
| Stable boundaries | Dependencies cross documented interfaces; unrelated domains remain decoupled. |
| Shared rules | Business invariants have one authoritative implementation when reuse is appropriate. |
| Useful names and rationale | Names describe domain intent; comments explain constraints and non-obvious decisions. |
| Small context entrypoint | A short repository map links to focused architecture and feature records. |
| Reliable feedback | Setup, checks, and diagnostics provide reproducible commands and actionable failures. |

Example: if two screens apply the same discount policy, centralize that policy behind an explicit contract and test both callers. Keep their different screen layouts separate. This reduces conflicting business logic without constructing a large configurable component that is harder for the next agent to understand.

## F3 How to improve agent friendliness

| Option | Approach | Benefit and tradeoff |
|---|---|---|
| A | Normalize naming, formatting, and comments within the current structure. | Low disruption; leaves deeper context and dependency problems untouched. |
| B | Improve feature ownership, contracts, navigation, and machine-checkable boundaries where the task exposes a problem. | Addresses how agents locate and change behavior; requires judgment and measurable trials. |
| C | Standardize applications around schema-generated modules and extensive machine metadata. | Can suit repetitive domains; adds generation tooling and architectural constraints. |

**Recommend B.** Apply it incrementally to the existing project. Measure whether agents locate the correct implementation, avoid duplicate rules, complete representative changes with fewer corrections, and preserve behavior. Record elapsed time and tool/context use alongside defect rates. A smaller source file alone is not evidence of improved agent performance.

## F4 Optional improvement control

Seif suggested a possible “scale button.” Its meaning and interface remain open pending clarification. This is a design proposal, not an implemented control, and no label is approved.

| Option | Control | Benefit and tradeoff |
|---|---|---|
| A | One action that runs the improvement pass at the agreed scope. | Simple invocation; limited variation between tasks. |
| B | Three depth settings: focused, feature-wide, and architecture-wide. | Makes scope clear without many settings; broader work needs an appropriate task boundary. |
| C | Separate controls for performance, reuse, security, cleanup, and inspection effort. | Fine control; more configuration and harder-to-predict interactions. |

**Recommend B if a depth control is wanted.** It controls optional improvement scope and effort. Required functional, security, regression, and browser acceptance stays in force at every setting. Expanding the setting must not silently authorize a repository-wide rewrite, release, or external action. Skill packaging and whether this appears as a command or UI are still open.

## Final verification and improvement evidence

The post-improvement batch covers the changed behavior, affected shared consumers, applicable security checks, and complete required user journeys. Browser QA includes fresh rendered inspection of changed UI, not just unit tests. Anthropic reports cases where code-level checks passed while the end-to-end feature remained broken, which supports retaining that final browser evidence. [Engineering account](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

Keep a concise comparison: what changed, why it was worth changing, what was measured or exercised, which results improved, which remained equivalent, and what remains unverified. A performance claim needs a representative measurement with comparable setup; a security claim needs evidence about the control; a reuse claim needs evidence that relevant consumers still behave correctly.

If the pass introduces a failure, repair or undo the responsible optimization and recheck the affected result. Preserve unrelated feature work. Fresh independent assessment follows repairs, as already selected in I4 and G7. Once required checks pass, run them again only when new changes, failures, or unresolved concerns justify it; an unchanged candidate does not need another identical local suite simply because it is about to be pushed. Existing required repository checks still apply.

## Acceptance work for this design

- Demonstrate a substantial feature batch without tests triggered by each file edit.
- Show that every required scenario is either executed at the appropriate boundary or explicitly pending, never silently omitted.
- Detect a regression in an unedited consumer of a shared component.
- Reject an unused-code finding when a supported dynamic entrypoint still needs the code.
- Keep a useful cleanup, and accept a sound feature without manufacturing cleanup work.
- Reproduce comparable performance measurements before claiming an optimization.
- Detect and recover from an optimization that breaks behavior or weakens a security control.
- Compare representative agent maintenance tasks before and after structural changes.
- Confirm that the optional control cannot weaken required acceptance or broaden authority silently.

These are evaluation targets for the full implementation. The [pilot verification record](pilot-verification.md) documents the subset actually exercised; no test watchers are used.
