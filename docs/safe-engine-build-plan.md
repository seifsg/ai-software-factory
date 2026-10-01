# Safe Engine build plan

**Initial baseline, retained for its core workflow and checklist.** Seif subsequently expanded the required scope to include specialist engineering, product, design, security, and autonomous browser capabilities. Use the [expanded capability plan](safe-engine-expanded-scope.md) for the current scope and count alternatives; the numbers below describe the earlier proposal.

The later [fast feature delivery design](safe-engine-fast-delivery.md) governs test batching, the improvement pass before push, and the priority for accurate maintenance by AI agents.

The initial recommendation was **11 core skill entry files**, followed by **2 release and observation skills when deployment enters scope**. The full count, role boundaries, and individual names were not approved. The later selected pilot packages five existing procedures and one coordinator; see [pilot scope and verification](pilot-verification.md). The checklist below still tracks the broader design.

Seif writes the procedures. The assistant helps structure, challenge, refine, and test them. Eight proposed core entry files adapt Seif's existing procedures; three core roles need new instructions. Splitting the existing planning and implementation procedure accounts for two of the eight adapted files.

## Choose the scope

| Option | Core and later skills | Advantage | Tradeoff |
|---|---|---|---|
| A | 8 core + 2 later = 10 | A compact library with the quality, regression, and compliance rubrics held as references within the review skill. | Those three checks lose independently invokable skill entrypoints. |
| B | 11 core + 2 later = 13 | Preserves the existing review skills and separates the already approved planning and implementation phases. | Requires clear contracts between the entrypoints. |
| C | 15 core + 2 later = 17 | Adds distinct intake, defect investigation, UX investigation, and factory evaluation routes for frequent specialist work. | More authoring and routing decisions before the first delivery loop is proven. |

**Recommendation: B.** It preserves the useful boundaries in Seif's work and adds only the missing core roles. The other source skills remain available for later adaptation when a concrete project needs them. The 38-source-skill inventory is not a requirement to import all 38 into the factory core.

## Proposed skill inventory

These are role descriptions, not approved skill or folder names. One skill means one required `SKILL.md` entrypoint. Supporting references, optional helpers, and engine code are additional files whose count depends on the design.

| No. | Role | Starting material | Main result |
|---|---|---|---|
| 1 | Enter or resume a factory task | New procedure | Route the task using the controller's permitted next step. |
| 2 | Discover the project | New procedure | A proposed project profile that Seif can inspect and correct. |
| 3 | Understand the request and system | Adapt `analyze-start` | Grounded analysis and a task contract with scope and acceptance criteria. |
| 4 | Prepare the plan | Adapt the planning portion of `get-ready-to-code` | A concrete plan with explicit handoffs and prerequisites. |
| 5 | Implement the plan | Adapt the execution portion of `get-ready-to-code` | A scoped change and evidence from the change-and-check loop. |
| 6 | Verify the changed result | New procedure | Select and run applicable checks and scenarios; report actual evidence. |
| 7 | Review implementation quality | Adapt `deep-review` and its existing lens references | Findings from security, performance, and user-journey review where applicable. |
| 8 | Check existing behavior | Adapt `change-guard` | Findings about regressions and broken contracts or callers. |
| 9 | Check requirements and rules | Adapt `compliance-check` | Acceptance traceability, unresolved uncertainty, and rule compliance. |
| 10 | Coordinate a fresh review | Adapt `how-to-review-a-pr` | Synthesize checks 7–9, make permitted bounded repairs, and request independent verification afterward. |
| 11 | Prepare the PR and human handoff | Adapt `how-to-make-a-pr` | An accurate draft PR, review evidence, remaining blockers, and the agreed handoff. |
| 12 | Execute an approved release | New procedure, later | Verified deployed revision and health, or a recovery decision under agreed authority. |
| 13 | Inspect the released outcome | New procedure, later | Evidence of the observed outcome and proposed follow-up work. Recurring monitoring needs separate authorization. |

Skills 7–9 preserve their existing distinct responsibilities. Their detailed review lenses remain supporting references; a lens does not automatically need another skill. Skill 10 coordinates them without duplicating their rubrics. The profile and task determine which checks apply.

## Proposed architecture

```text
SEIF WRITES THE PROCEDURES
        |
        +--> Assistant helps structure, critique, refine, and test
        |
        v
APPROVED SKILLS                           TARGET PROJECT
        |                                      |
        |                        [2] Discover -> review/correct profile
        |                                      |
        +--------------------+-----------------+
                             |
Request ----------------> [1] Enter / resume
                             |
                    [3] Understand + task contract
                             |
                         [4] Plan
                             |
                         [5] Build <---------------------+
                             |                          |
                         [6] Verify -- failed check ----+ bounded
                             |                            repair
                    [11] Prepare draft PR                 budget
                             |
                     [10] Fresh review
                             |
                  +----------+-----------+
                  |          |           |
              [7] Quality [8] Regression [9] Requirements
                  |          |           |
                  +----------+-----------+
                             |
                     Synthesize findings
                             |
              +--------------+----------------+
              |                               |
      Bounded reviewer repairs          Current evidence
              |                               |
      [6] Recheck + fresh                [11] Human handoff
      independent review                      |
              |                          SEIF DECIDES
              +--> updated verdict            |
                                      [12] Approved release
                                              |
                                      [13] Observe outcome
                                              |
                                      Evidence -> new intake

SAFE ENGINE CODE SUPPORTS EVERY STAGE
  Controller | checkpoints | shared gates | permission checks
  Evidence records | correction budget | cancellation / recovery
        |                                  |
  Host hook adapters             Independent repository checks

  Skills describe judgment and procedure.
  Code validates state, records evidence, and enforces covered gates.
```

The diagram shows the normal draft-PR delivery path. Stages can return a blocker or an explicit handoff when dependencies, evidence, or authority are missing. A clean review can finish without edits. Reviewer repairs are followed by fresh independent assessment, as selected in I4 and G7. Release and observation are conditional on the task's agreed delivery scope.

## How we write each skill together

1. Seif describes or writes how he wants the work done, starting from his existing skill where applicable.
2. The assistant compares the relevant examples and identifies concrete gaps, contradictions, or unclear handoffs. New design choices receive three alternatives and one recommendation.
3. Seif selects the behavior and refines the wording. The assistant formats or edits the selected material when requested.
4. Together we establish the trigger, inputs, procedure, outputs, evidence, and stopping conditions that the particular skill needs.
5. Validate its structure and references, then exercise representative behavior and revise from observed results.

## Completion checklist

### Agree the first version

- [x] Choose the engine name: Safe Engine.
- [x] Establish Seif as primary skill author, with assisted editing and validation.
- [x] Record 23 clear architecture and quality selections.
- [x] Resolve G6, evidence freshness, and G9, skill versioning for the pilot.
- [ ] Select the current skill count and role boundaries from the expanded capability plan.
- [ ] Choose the actual skill and stage names.
- [x] Select the first host, implementation language, record formats, pilot project, and delivery boundary: local Codex, Python, JSON, disposable browser app, checked local handoff.

### Author the core together

- [ ] Review the seven existing source entrypoints and their needed resources before adaptation.
- [ ] Adapt the eight core files derived from those sources, preserving intent and separating planning from implementation.
- [ ] Write the three new core procedures: entry/resume, project discovery, and verification.
- [ ] Remove project-specific assumptions and declare actual tools and dependencies.
- [ ] Define each skill's inputs, outputs, required evidence, failure behavior, and routing boundary.
- [x] Validate the six pilot entrypoints and register them in the index; validate later additions separately.

### Implement the selected engine design

- [x] Implement the local controller, validated task record, checkpoints, cancellation, and resume; wider crash recovery remains to exercise.
- [x] Implement discovery that produces a reviewable and correctable project profile.
- [x] Implement local shared gates, evidence freshness according to G6, and an explicit run-wide correction budget.
- [ ] Connect the chosen host's hooks and verify their real coverage and failure behavior.
- [ ] Implement scenario adapters, baseline comparison, and reproducible project setup where applicable.
- [ ] Protect acceptance criteria and action authority; resolve the private-repository feature prerequisite for merge enforcement.

### Prove the factory works

- [ ] Complete one real task through a checked draft PR and human handoff.
- [ ] Detect a missing requirement, a regression, stale evidence, a failed critical check, and exhausted retries.
- [ ] Interrupt, resume, and cancel without losing requirements or duplicating external actions.
- [ ] Verify unknown applicability, exception authority, misleading retrieved instructions, and independent review after reviewer repairs.
- [ ] Confirm that a good change can pass review without unnecessary edits.
- [ ] Compare skill versions using a representative benchmark and reserved cases.
- [ ] Repeat the delivery loop in a second materially different project to demonstrate portability without changing core procedures.

### Package and document the demonstrated system

- [x] Package controller, skills, adapters and version in one repository bundle; global installation remains separate.
- [x] Document pilot setup, dependencies, recovery, and known limitations.
- [x] Update the preview and skill index to distinguish the pilot from the wider target.

### Extend to release when needed

- [ ] Coauthor the conditional release and observation skills; their numbering depends on the selected expanded inventory.
- [ ] Connect an explicitly authorized release procedure and verify the deployed revision and relevant health signals.
- [ ] Exercise the agreed recovery path and route observed defects back into intake.

A first delivery version is complete when the selected core skills and engine can repeatedly deliver the agreed checked handoff, reject insufficient evidence, recover safely, and demonstrate portability. The release extension has its own acceptance work. Supporting additional projects remains an ongoing compatibility effort rather than a claim that every possible project is already supported.
