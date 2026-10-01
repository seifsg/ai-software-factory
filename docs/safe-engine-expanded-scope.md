# Safe Engine: expanded capability plan

Research and proposal, 1 October 2026. **The capabilities below are requested by Seif. Their packaging, names, and new procedural choices remain proposals.** The later Safe Engine 0.1.0 local pilot implements a narrow delivery loop with six entrypoints; see its [verification record](pilot-verification.md). This broader plan is not a claim that every capability is implemented.

The target is a factory that can understand a task, build it, use the resulting application, notice defects and poor experiences, repair them, and produce fresh evidence without Seif repeatedly pointing out what is broken. Seif remains the primary skill author and owns product and design decisions.

This expands the [initial build plan](safe-engine-build-plan.md). It preserves the [selected engine decisions](safe-engine-decisions.md), including project discovery with review/correction, separate planning and execution, bounded reviewer repairs followed by independent verification, and the agreed human delivery/release boundaries. G6 now binds evidence to exact declared inputs; G9 versions the controller, skills and adapters as one repository bundle.

Seif subsequently specified **substantial development batches, verification at batch boundaries, and an improvement pass before pushing followed by QA**. The [fast feature delivery design](safe-engine-fast-delivery.md) governs that cadence and records the requested priority for code that AI agents can maintain accurately. The updated E4 below preserves TDD as a capability without prescribing tests after every edit.

## What must be covered

| Requested capability | What a useful result must demonstrate | Starting material to examine together |
|---|---|---|
| Worktrees | Select or create an isolated workspace, establish its baseline, track ownership, and recover or clean up without losing work. | [Superpowers worktrees][sp-worktrees]; selected I8. |
| Skill writing | Help Seif turn his method into a usable skill, then test its routing and behavior. | [Superpowers skill authoring][sp-writing]; Seif's existing procedures. |
| Planning | Translate the request into executable steps, dependencies, interfaces, and observable acceptance. | Seif's `analyze-start` and `get-ready-to-code`; [Superpowers plans][sp-plans]; [BMAD product requirements][bmad-prd]. |
| Execution | Follow the current plan, check real outcomes, retain progress and deviations, and continue through in-scope repairs. | Seif's pre/change/post method; [Superpowers execution][sp-execution]. |
| Debugging | Reproduce a defect, discriminate between causes, repair the cause, and verify the original failure and regressions. | Seif's `bug-investigation`; [Superpowers debugging][sp-debug]. |
| TDD and TDD review | Support test-first methods when explicitly chosen and review whether tests detect intended defects. Default feature development batches test execution after substantial work. | [Superpowers TDD][sp-tdd] and [test-quality guidance][sp-test-quality], adapted to Seif's cadence. |
| Architecture | Ground decisions in existing code; define boundaries, data ownership, interfaces, and relevant deployment constraints. | [BMAD architecture][bmad-architecture] and its [decision template][bmad-spine]. |
| UX design | Define the intended journeys, content, interactions, screen states, responsive behavior, and design language. | Seif's `ux-investigation`; [BMAD UX][bmad-ux]; [gstack design consultation][gs-consult]. |
| Product design review | Assess whether the proposed and rendered experience serves its users, makes the next action clear, and meets the agreed standard. | [gstack plan design review][gs-plan-design] and [rendered design review][gs-design]. |
| Idea assessment | Investigate the problem and alternatives, label assumptions, and recommend whether to proceed, clarify, or stop; Seif decides. | [Spec Kit assessment][sk-assess]; [BMAD idea assessment][bmad-idea]. |
| Browser QA | Open the real app, navigate and interact, exercise relevant states, and report reproducible functional and visual findings. | [gstack QA][gs-qa], [exploration][gs-explore], and [Playwright practices][pw-practices]. |
| UI repair | Correct supported layout, interaction, responsive, and visual defects; rerender and replay the affected journey. | [gstack browser verification][gs-browser-verify] and [design repair][gs-design]. |
| Security | Review relevant threats and controls, distinguish suspicion from demonstrated findings, and verify fixes. | Seif's security review lens; [gstack security][gs-security]; [OWASP ASVS][asvs]. |

The existing quality, regression, requirements, review coordination, and PR/handoff responsibilities remain. A capability can be required without becoming a separate entrypoint or running on every task.

## Sources and what they actually contribute

These are source-code and documentation findings, not comparative performance measurements. We have not executed these external factories as part of this research.

| Source | Useful contribution | Adaptation or limit |
|---|---|---|
| [Seif's 38 source skills][seif-skills] | Request grounding, pre/change/post inspection, multiple review lenses, defect investigation, and human handoffs. | Preserve the method; replace project-specific assumptions with explicit adapters and resolve the recorded contradictions. |
| Superpowers | Workspaces, plans, test-first development, debugging, and evaluating skill behavior. | Keep Seif's authorship, proportionate verification, and fresh review after repairs. The inspected execution instructions omit that final re-review. |
| BMAD | Architecture decisions, product definition, UX journeys and state coverage. | Its UX validation concerns design artifacts and is optional; our browser acceptance must exercise the running application. [Validation source][bmad-ux-validation]. |
| gstack | Concrete browser tooling, exploration, QA repairs, rendered design inspection, and security review. | Preserve evidence and rechecks; avoid copying arbitrary taste rules, treating CSS changes as harmless, or treating a model's score as proof. |
| Spec Kit | Explicit requirements and an optional staged idea-assessment extension. | Its assessment procedures are not runtime enforcement; route them only to tasks that need product assessment. |
| Cole's factory / pinned Archon | Candidate-bound runtime evidence, lifecycle control, separate acceptance, and correction before delivery. | Strengthen our selected controller and gates; do not import its workflow or names wholesale. [Policy][cole-policy], [derivation][cole-derivation]. |
| StrongDM | Published use of scenario-based acceptance, held-out evaluations, and simulated dependencies. | Useful evaluation inspiration; its autonomous operating policy differs from our selected human release boundary. These are the company's reported practices. [Source][strongdm]. |
| Playwright and OWASP | Browser testing techniques and structured security requirements. | They support execution and review; neither replaces product judgment or supplies a complete factory. |

Inspection snapshots: Superpowers `8ca22dba9a94f28898bbce59f2537ff4d87c747d`; BMAD `1cbcfa272fe65787c06a1fa164a901f46117cca7`; gstack `96764e80a641e28141ec8297223768029f5bf483`; Spec Kit `838f1184d1b2ed254a99e8b818dbc23aa80a7f1f`; Cole `2b851d76c557fa7ed33a8d47b6870585a41a29ce`, whose inspected Archon pin is `24796870605b0fd576734b79a8d5c781f2b1c1e1`. Seif's source collection was inspected at `449e1110104b6ac27aed3a940c5ed6d1bf671f11`. Public documentation links describe their retrieved state on the research date.

## E1 — How many skill entrypoints?

These options replace the earlier count comparison for the expanded scope. They all cover the requested capabilities. The letters apply only to this table; no earlier choice silently approves E1.

| Option | Proposed count | Organization | Tradeoff |
|---|---|---|---|
| A | 18 core + 2 later = **20** | Include TDD within implementation; combine UX with product design review and browser QA with repair; retain security within quality review. | Less routing and authoring overhead, but fewer separately invokable specialist roles. |
| B | 22 core + 2 later = **24** | Retain the original 11 core roles and add 11 specialist roles listed below. | Clear ownership and reuse; requires explicit handoffs and a single owner for each shared rubric. |
| C | 26 core + 2 later = **28** | Further split idea research/decision, architecture design/review, TDD creation/audit, and browser exploration/regression execution. | Finer invocation and specialization, with more coordination before the first useful run. |

**Recommend B.** It gives each requested specialty a clear home while preserving the existing planning, execution, and review system. A fresh review is a separate assessment, not necessarily another skill file. The skill count is a packaging choice, not a quality measure.

Under B, the original core roles remain 1–11: enter/resume, discover project, understand, plan, implement, verify, quality review, regression review, requirements review, review coordination, and PR/handoff. The additions are:

| No. | Proposed responsibility, not an approved name | Boundary |
|---|---|---|
| 12 | Workspace and worktree management | Own workspace preparation, baseline, ownership, and recovery. |
| 13 | Assisted skill authoring and evaluation | Factory maintenance; Seif supplies the procedure. |
| 14 | Test-driven implementation | Own the optional TDD method and test-quality rubric; respect the default batch cadence. Quality review invokes the rubric independently. |
| 15 | Systematic debugging | Own evidence-driven defect investigation; execution and QA can invoke it. |
| 16 | Architecture design and review | Own shared structural decisions and their conformance criteria. |
| 17 | UX design | Own intended journeys, states, content, and visual rules. |
| 18 | Product design review | Independently assess the proposed or implemented experience against that design record. |
| 19 | Idea assessment | Research uncertain product opportunities; return a recommendation for Seif. |
| 20 | Browser QA | Observe and reproduce; run scenarios and exploration; retain evidence. |
| 21 | UI repair | Apply supported corrections and request reinspection. |
| 22 | Security review | Own the detailed security rubric; general quality review delegates applicable depth to it. |
| 23 | Approved release, later | Existing conditional release responsibility. |
| 24 | Released outcome observation, later | Existing conditional observation responsibility. |

All 22 are core library capabilities; a task uses the relevant subset. Skill 13 improves the factory itself. A routine defect need not pass through idea assessment or fresh product strategy. Supporting references, fixtures, adapters, and engine code are additional files, not additional skills.

## Individual design choices

Every choice below is **open**. Recommendations are research conclusions for Seif to accept or revise. They do not authorize implementation of a particular option.

### E2 — Worktree strategy

| Option | Approach | Benefit and cost |
|---|---|---|
| A | One managed worktree per run; reuse suitable existing isolation. | Clear ownership and recovery; tasks primarily edit sequentially. |
| B | One worktree per independent implementation task. | Parallel edits; requires conflict handling and integration checks. |
| C | A pool of reusable worktrees leased to workers. | Faster repeated setup; more residual-state and cleanup complexity. |

**Recommend A.** It provides an understandable first isolation model. Track the base revision, branch, owned processes, ports, and baseline. A worktree does not isolate databases, credentials, or downstream services by itself. Inspiration: [workspace procedure][sp-worktrees].

### E3 — How to support Seif's skill writing

| Option | Approach | Benefit and cost |
|---|---|---|
| A | Seif drafts freely; the assistant critiques afterward. | Maximum writing freedom; structural gaps may emerge late. |
| B | Agree purpose and examples; Seif writes the method; the assistant probes, edits, and validates it. | Preserves authorship and finds ambiguity early; requires collaboration. |
| C | Seif fills a structured authoring form; tools generate packaging. | Consistent structure; a rigid form can flatten useful differences. |

**Recommend B.** Test whether the skill activates appropriately, follows Seif's method under pressure, retrieves needed references, and declines unrelated tasks. Structural validation alone does not demonstrate these behaviors. Inspiration: [skill evaluation][sp-writing].

### E4 — TDD and test review

Seif's later instruction settles the default execution cadence: batch tests after substantial development. The remaining alternatives concern when to author tests and how to retain TDD as a deliberate technique. This replaces the earlier strict test-first options.

| Option | Approach | Benefit and cost |
|---|---|---|
| A | Author acceptance tests before coding; execute them at substantial batch boundaries. | Keeps expected behavior independent of implementation; some details need revision during discovery. |
| B | Batch development and verification by default; use explicit test-first work only for deliberately chosen tasks. | Preserves speed and access to TDD where wanted; the task must make that choice clear. |
| C | Implement each substantial batch, then author and execute its tests. | Least interruption to implementation; requires stronger review against tests mirroring the code. |

**Recommend B.** Review whether plausible defects would fail the tests and whether expected results come from requirements. For selected TDD work, observe the intended failure and later success; do not label unobserved execution as RED/GREEN evidence. Use rendered inspection for visual judgment. The [batch-boundary options](safe-engine-fast-delivery.md#f1-verification-batch-boundaries) remain open. Sources: [TDD][sp-tdd], [test quality][sp-test-quality].

### E5 — Debugging

| Option | Approach | Benefit and cost |
|---|---|---|
| A | A fixed full investigation sequence for every defect. | Easy to teach; excessive for localized problems. |
| B | Evidence-driven investigation scaled to the defect. | Fast when the cause is clear, deeper when needed; requires disciplined reasoning. |
| C | Competing independent investigations before repair. | Useful for ambiguous cross-system failures; costs more and needs synthesis. |

**Recommend B.** Keep one investigation record: reproduction, hypothesis, discriminating experiment, result, fix, and recheck. Repeated failure triggers reassessment under the shared run budget. It does not prove an architectural flaw. Combine Seif's existing investigation method with [Superpowers debugging][sp-debug].

### E6 — Architecture

| Option | Approach | Benefit and cost |
|---|---|---|
| A | A comprehensive architecture document before implementation. | Broad shared view; can become stale and burden small changes. |
| B | Decision-led architecture, diagrams, and checked boundaries. | Focuses on decisions builders must share; requires judgment about significance. |
| C | Prototype-first architecture. | Resolves feasibility with working evidence; prototypes can become accidental production choices. |

**Recommend B.** Inspect the existing system, compare consequential alternatives, and record Seif's decisions with affected components and verifiable constraints. Use experiments when a particular decision needs evidence. Sources: [architecture][bmad-architecture], [decision structure][bmad-spine], [review gate][bmad-architecture-review].

### E7 — UX design

| Option | Approach | Benefit and cost |
|---|---|---|
| A | Extend the existing design system with a compact screen/state checklist. | Efficient for a mature product; weak when the intended experience is unclear. |
| B | A right-sized experience brief covering users, journeys, states, content, and visual rules. | Gives builders and reviewers a shared target across different projects; needs initial clarification. |
| C | Explore several interactive prototypes before choosing a direction. | Makes uncertain choices tangible; adds iteration and still needs a decision. |

**Recommend B.** Capture the existing direction first, including references and rejected preferences. Expand only where the task introduces uncertainty. The result supplies browser QA with expected journeys and states. Sources: [BMAD UX][bmad-ux], [gstack design consultation][gs-consult].

### E8 — Product design review

| Option | Approach | Benefit and cost |
|---|---|---|
| A | The designer reviews its own result against a shared checklist. | Low overhead; greater risk of defending its own assumptions. |
| B | Fresh critique against the approved brief, rendered screens, and observed journeys. | Independent assessment grounded in this product; needs a current design record. |
| C | Representative-user evaluation of alternative designs. | Direct evidence for disputed usability choices; needs access to users or reliable behavioral data. |

**Recommend B.** Review task clarity, information hierarchy, content, consistency, responsive behavior, and state feedback. Tie each finding to a user problem and evidence. It may make bounded repairs under I4, followed by another fresh assessment. A clean result can pass unchanged. Source: [gstack's design review passes][gs-plan-design].

### E9 — Idea assessment

| Option | Approach | Benefit and cost |
|---|---|---|
| A | One concise evidence-backed assessment brief. | Fast for small reversible ideas; may miss deeper uncertainty. |
| B | Staged assessment with explicit evidence and decision criteria. | Connects problem, alternatives, risks, unknowns, and recommendation; needs selective routing. |
| C | Validate important assumptions through experiments before recommending a build. | Stronger evidence for uncertain demand or feasibility; requires time and appropriate access. |

**Recommend B.** Keep the stages as one coherent skill with supporting resources unless independent invocation becomes useful. It can recommend an experiment where research is insufficient. Seif decides; simulated personas do not count as real customer evidence. Sources: [assessment overview][sk-assess], [research][sk-research], [decision criteria][sk-decide], [idea pressure testing][bmad-idea].

### E10 — Browser QA

| Option | Approach | Benefit and cost |
|---|---|---|
| A | Autonomous exploratory browser inspection. | Discovers unexpected problems with little prewritten coverage; coverage varies between runs. |
| B | Executable journeys plus exploratory browser and visual inspection. | Repeatability plus discovery of unscripted defects; requires controlled state and maintained scenarios. |
| C | A dedicated managed browser-testing service. | Broad browser execution and retained artifacts; adds provider or service operations. |

**Recommend B.** The browser adapter must expose real navigation, interaction, screenshots, and diagnostic evidence. Scenarios protect known journeys; exploration looks for what the script omitted. Useful reproductions become regression coverage when appropriate. Sources: [exploration][gs-explore], [QA scope][gs-scope], [Playwright practices][pw-practices].

### E11 — UI repair

| Option | Approach | Benefit and cost |
|---|---|---|
| A | One browser worker inspects, edits, and self-checks before the existing final review. | Short feedback cycle; debugging and visual judgment share the same context. |
| B | Browser findings drive scoped UI repair, followed by fresh browser and design assessment. | Clear evidence and accountability; requires precise findings and handoffs. |
| C | Generate several repair variants and select through comparison. | Useful for ambiguous layout problems; greater cost and risk of unintended redesign. |

**Recommend B.** Routine repairs proceed autonomously within the approved task and design direction. Reopen the app, repeat the failed interaction, inspect the new render, and check adjacent behavior. Preserve approved requirements and visual baselines; changing them to obtain a pass is a separate decision. Sources: [QA repair][gs-qa], [browser recheck][gs-browser-verify], [design review][gs-design].

### E12 — Security

| Option | Approach | Benefit and cost |
|---|---|---|
| A | Automated scanners plus a standard checklist. | Repeatable breadth; misses business logic and project-specific trust boundaries. |
| B | Threat-informed review plus applicable automated checks and targeted verification. | Connects controls to real assets, actors, and entrypoints; requires project context. |
| C | A specialist assessment with deeper adversarial testing. | More assurance for high-risk systems; greater effort and a separately defined test scope. |

**Recommend B.** Cover relevant authorization, authentication, data handling, secrets, dependencies, and exposed inputs. Use versioned requirements where useful; distinguish confirmed findings from hypotheses and residual uncertainty. Preserve one security rubric shared with quality review. Sources: [gstack security][gs-security], [OWASP ASVS][asvs].

### E13 — Improve the existing planning role

| Option | Approach | Benefit and cost |
|---|---|---|
| A | A short ordered checklist. | Fast for simple work; leaves complex dependencies implicit. |
| B | A right-sized task contract with interfaces, dependencies, and acceptance evidence. | Gives execution a verifiable target; needs enough repository investigation. |
| C | A complete implementation specification before coding. | Useful for constrained or multi-team delivery; risks false precision and unnecessary detail. |

**Recommend B.** Strengthen Seif's planning role with concrete files or components, interfaces between tasks, checks, expected outcomes, and unresolved decisions. Do not add a duplicate planner. Sources: [Superpowers planning][sp-plans], [BMAD requirements][bmad-prd].

### E14 — Improve the existing execution role

| Option | Approach | Benefit and cost |
|---|---|---|
| A | Execute one plan step and hand back control each time. | Clear checkpoints; frequent coordination interrupts otherwise routine progress. |
| B | Continue through dependent steps and in-scope repairs using durable checkpoints. | Fits autonomous delivery while retaining evidence and recovery; depends on the selected controller. |
| C | Dispatch independent tasks concurrently and integrate their results. | Can reduce elapsed time; requires stable interfaces, resource isolation, and integration review. |

**Recommend B.** Preserve the existing pre/change/post inspection, batch test execution after substantial work, record actual results, and follow the run-wide budget. Continue authorized work without repeated permission requests; surface genuine unresolved choices or blockers. Include the requested improvement pass before push and verify the result. Fresh independent verification remains required after reviewer repairs. Inspiration: [execution procedure][sp-execution], adapted to our selected G4, G8, I3, and I4.

## How the pieces connect

```text
SEIF + ASSISTED SKILL AUTHORING
                 |
          Approved procedures
                 v
REQUEST --> SAFE ENGINE: enter / resume
                 |
      Discover project + prepare workspace
                 |
           Understand task
                 |
       +---------+----------------------+
       |         |                      |
    Assess    Architecture         UX direction
     idea     when needed          when needed
       |         |                      |
       +---------+----------------------+
                 |
            Concrete plan
                 |
            Implement <---------------------------+
           TDD as applicable                       |
                 |                                 |
         Verify actual result                      |
                 |                                 |
      +----------+------------+                    |
      |                       |                    |
  Code / regression       Browser QA               |
  requirements /          + product design         |
  security checks         inspection               |
      |                       |                    |
      +----------+------------+                    |
                 |                                 |
       Supported defect? -- yes --> Debug / UI repair
                 |                    shared budget
                 |
       Fresh independent assessment
                 |
      Evidence-backed human handoff
                 |
       Approved release, when in scope

CONTROLLER SUPPORT THROUGHOUT
  Current task and decisions | checkpoints | gates | evidence
  Workspace and browser adapters | permissions | retry budget
```

The diagram groups responsibilities, not mandatory sequential invocations. Development and related repairs are grouped into meaningful batches, followed by affected verification and a fresh final assessment. The improvement pass before push follows the newer fast-delivery design. Independent work can continue when only one decision is blocked. A browser is not required for a project without a browser interface.

## The autonomous browser quality loop

```text
Approved task + experience brief + project profile
                         |
        Identify running candidate and test state
                         |
         OPEN --> NAVIGATE --> CLICK / TYPE / TAB
                         |
     Inspect rendered UI + task outcome + diagnostics
                         |
      Supported issue? -- no --> Fresh assessment
                         |                |
                        yes         Checked handoff
                         |
     Record failure, expected result, and reproduction
                         |
                  REPAIR IN SCOPE
                         |
       Reopen + replay + inspect fresh screenshots
                         |
         Check adjacent flows and required viewports
                         |
             Fresh independent assessment
                 /                     \
         Still unresolved        Required evidence passes
                 |                     |
       Next bounded attempt        Checked handoff
       or explicit blocker
```

The entrypoint can support quick diagnosis and repair, but the report must state its coverage. A quick smoke check cannot satisfy omitted requirements. Gstack's [Quick mode][gs-modes] deliberately omits its detailed checklist; we should not mistake that mode for complete acceptance.

For a visual finding, retain the route, viewport, initial state, user role where relevant, observed and expected result, reproduction, source candidate, and before/after render. For a behavioral finding, add the executed assertion or trace. Evidence must correspond to the candidate being reviewed; the selected G6 pilot binds code, definitions and declared environment inputs and checks generated artifact hashes.

The factory needs all three kinds of inspection:

| Inspection | Answers | Example |
|---|---|---|
| Functional | Can the person complete the intended task? | The submit button produces the correct result and avoids duplicate submission. |
| Visual | Is the actual render broken or inconsistent with the agreed design? | Mobile content clips the primary action; spacing or layering hides a field. |
| Experience | Does the flow communicate what to do and what happened? | Validation explains how to recover; loading, empty, and error states give useful next steps. |

Visual snapshots detect changes against a baseline, not whether that baseline is good design. [Playwright visual comparison][pw-snapshots]. Automated accessibility scans also need keyboard/focus checks and appropriate human evaluation; passing a scan alone cannot establish accessibility conformance. [Playwright accessibility][pw-accessibility], [W3C evaluation guidance][wai-evaluation].

The required browser backend, supported hosts, test-data strategy, and numeric budgets still need concrete choices. Worktrees need separate ports and runtime ownership where applicable. Browser state and downstream services must belong to the intended test environment. A missing browser, unavailable login, or unidentified running build yields an unverified result, not a pass.

## What must be demonstrated before calling this autonomous

The following are proposed acceptance cases for the selected G11 and I10 evaluation approach. They are not already implemented tests.

| Case | Required observable result |
|---|---|
| Narrow viewport hides a primary action | Detect the actual clipping, repair it, rerender, and complete the action at affected widths. |
| Visible button has no working behavior | Reproduce the failed interaction, fix it, and verify the intended result. |
| Required journey or state is missing | Compare the app with the task and UX record; identify the omission and verify the completed flow. |
| Validation, loading, empty, or error feedback is unusable | Exercise the relevant state; repair supported defects and demonstrate understandable feedback. |
| Keyboard focus is lost or trapped | Reproduce using the keyboard; repair and verify navigation and focus recovery. |
| A request can be submitted twice | Demonstrate the duplicate behavior with controlled data, then verify the correction. |
| UI correction breaks an adjacent flow | Detect the regression and repair or recover before issuing a passing handoff. |
| Browser is showing an older candidate | Reject stale evidence and inspect the intended candidate. |
| Browser or authentication is unavailable | Preserve the missing coverage and report the affected blocker. |
| A page already meets the agreed standard | Accept it without manufactured findings or unnecessary edits. |
| A reviewer makes a repair | Obtain fresh independent evidence for the resulting revision. |

Measure detection, repair success, missed defects, false findings, introduced regressions, unnecessary edits, and recovery. Use representative projects and reserved cases. High quality must be demonstrated across runs; instruction length, skill count, and confidence language do not establish it.

## Work ahead

- [x] Record Seif's expanded capability requirements.
- [x] Inspect relevant external procedures and identify useful mechanisms and limits.
- [ ] Seif selects packaging E1 and procedural choices E2–E14; choose actual names afterward.
- [x] Resolve G6 and G9 and choose the local Codex/Python/JSON pilot with a disposable browser app. General adapters remain future work.
- [ ] Agree a small experience brief and objective defects for the first browser-quality demonstration.
- [ ] Seif writes the first procedures; the assistant supports source comparison, structure, critique, editing, and behavioral trials.
- [ ] Adapt the existing planning, implementation, and review methods with one canonical owner per shared rubric.
- [ ] Build the smallest connected controller path that runs browser QA, repairs a reproduced defect, and obtains independent verification.
- [ ] Demonstrate both a broken-UI repair and an already-good page that needs no changes.
- [ ] Add the remaining selected modules and test their individual routing, outputs, and handoffs.
- [ ] Exercise interrupted runs, exhausted budgets, stale evidence, missing dependencies, security findings, and regression recovery.
- [ ] Demonstrate portability in another materially different project.
- [ ] Update the skill index and preview only as capabilities become implemented and demonstrated.

Recommended first demonstration: a controlled application with a hidden mobile action and a failing form flow. Have Safe Engine find and fix both, replay the journey, and pass fresh review. This is a concrete test of the user's central requirement; it does not replace completion of the wider capability set.

[sp-worktrees]: https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/using-git-worktrees/SKILL.md
[sp-writing]: https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/writing-skills/SKILL.md
[sp-plans]: https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/writing-plans/SKILL.md
[sp-execution]: https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/executing-plans/SKILL.md
[sp-debug]: https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/systematic-debugging/SKILL.md
[sp-tdd]: https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/test-driven-development/SKILL.md
[sp-test-quality]: https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/test-driven-development/writing-good-tests.md
[bmad-architecture]: https://github.com/bmad-code-org/BMAD-METHOD/blob/1cbcfa272fe65787c06a1fa164a901f46117cca7/skills/bmad-architecture/SKILL.md
[bmad-spine]: https://github.com/bmad-code-org/BMAD-METHOD/blob/1cbcfa272fe65787c06a1fa164a901f46117cca7/skills/bmad-architecture/assets/spine-template.md
[bmad-architecture-review]: https://github.com/bmad-code-org/BMAD-METHOD/blob/1cbcfa272fe65787c06a1fa164a901f46117cca7/skills/bmad-architecture/references/reviewer-gate.md
[bmad-ux]: https://github.com/bmad-code-org/BMAD-METHOD/blob/1cbcfa272fe65787c06a1fa164a901f46117cca7/skills/bmad-ux/SKILL.md
[bmad-ux-validation]: https://github.com/bmad-code-org/BMAD-METHOD/blob/1cbcfa272fe65787c06a1fa164a901f46117cca7/skills/bmad-ux/references/validate.md
[bmad-prd]: https://github.com/bmad-code-org/BMAD-METHOD/blob/1cbcfa272fe65787c06a1fa164a901f46117cca7/skills/bmad-prd/SKILL.md
[bmad-idea]: https://github.com/bmad-code-org/BMAD-METHOD/blob/1cbcfa272fe65787c06a1fa164a901f46117cca7/skills/bmad-forge-idea/SKILL.md
[gs-qa]: https://github.com/garrytan/gstack/blob/96764e80a641e28141ec8297223768029f5bf483/qa/SKILL.md
[gs-explore]: https://github.com/garrytan/gstack/blob/96764e80a641e28141ec8297223768029f5bf483/qa/sections/exploratory.md
[gs-browser-verify]: https://github.com/garrytan/gstack/blob/96764e80a641e28141ec8297223768029f5bf483/qa/sections/browser-verify.md
[gs-modes]: https://github.com/garrytan/gstack/blob/96764e80a641e28141ec8297223768029f5bf483/qa/sections/qa-patterns.md
[gs-scope]: https://github.com/garrytan/gstack/blob/96764e80a641e28141ec8297223768029f5bf483/qa/sections/scope.md
[gs-design]: https://github.com/garrytan/gstack/blob/96764e80a641e28141ec8297223768029f5bf483/design-review/SKILL.md
[gs-plan-design]: https://github.com/garrytan/gstack/blob/96764e80a641e28141ec8297223768029f5bf483/plan-design-review/sections/review-sections.md
[gs-consult]: https://github.com/garrytan/gstack/blob/96764e80a641e28141ec8297223768029f5bf483/design-consultation/SKILL.md
[gs-security]: https://github.com/garrytan/gstack/blob/96764e80a641e28141ec8297223768029f5bf483/cso/SKILL.md
[sk-assess]: https://github.com/github/spec-kit/blob/838f1184d1b2ed254a99e8b818dbc23aa80a7f1f/extensions/assess/README.md
[sk-research]: https://github.com/github/spec-kit/blob/838f1184d1b2ed254a99e8b818dbc23aa80a7f1f/extensions/assess/commands/speckit.assess.research.md
[sk-decide]: https://github.com/github/spec-kit/blob/838f1184d1b2ed254a99e8b818dbc23aa80a7f1f/extensions/assess/commands/speckit.assess.decide.md
[cole-policy]: https://github.com/coleam00/ai-software-factory/blob/2b851d76c557fa7ed33a8d47b6870585a41a29ce/template/factory/WORKFLOW_POLICY.md
[cole-derivation]: https://github.com/coleam00/ai-software-factory/blob/2b851d76c557fa7ed33a8d47b6870585a41a29ce/docs/derivation.md
[strongdm]: https://factory.strongdm.ai/
[pw-practices]: https://playwright.dev/docs/best-practices
[pw-snapshots]: https://playwright.dev/docs/test-snapshots
[pw-accessibility]: https://playwright.dev/docs/accessibility-testing
[wai-evaluation]: https://www.w3.org/WAI/test-evaluate/
[asvs]: https://owasp.org/projects/asvs
[seif-skills]: https://github.com/Repaircheck/claude-routines/tree/449e1110104b6ac27aed3a940c5ed6d1bf671f11/.claude/skills
