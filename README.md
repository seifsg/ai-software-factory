# AI Software Factory

Private home for Seif's software-delivery skills. We will import existing skills, improve them through real use, and build new skills together.

## Goal

Make skills work together as a repeatable delivery system: understand a request, prepare the work, implement it, verify the result, handle feedback, and return evidence. Connect release and monitoring when the target project supports them and the user authorizes them.

The factory runs against the customer's or team's project. This repository owns the reusable skills and their supporting resources, not client source code or credentials.

The engine is named **Safe Engine**. The [design decision record](docs/safe-engine-decisions.md) captures Seif's selected architecture and quality procedures, with unresolved choices kept explicit. The selected project onboarding approach discovers configuration and offers a profile for review and correction.

Seif leads skill authorship; the assistant helps structure, review, refine, and validate his procedures. The [expanded capability plan](docs/safe-engine-expanded-scope.md) covers worktrees, skill writing, TDD, debugging, architecture, UX, idea assessment, security, and autonomous browser inspection and repair. It includes source comparisons, three alternatives for each design choice, an ASCII architecture, and acceptance cases. Skill counts, boundaries, and new procedures await selection. The [initial build plan](docs/safe-engine-build-plan.md) preserves the core delivery workflow and engine checklist.

Development should proceed in substantial batches, followed by relevant verification. Before a feature is pushed, inspect worthwhile cleanup, reuse, design, performance, and security improvements, then verify the changes. The [fast feature delivery design](docs/safe-engine-fast-delivery.md) records this cadence and the proposed criteria for code that AI agents can navigate and change accurately.

## Current state

Repository foundation and visual design. No skills have been imported yet. No runtime, unattended workflow, integrations, or deployment behavior has been implemented or verified.

## Start here

Open [the visual introduction](preview/index.html) in a browser. Its concise first screen explains the goal and the process: understand, build, check, approve. A single status line shows where we are today. It works locally without installation or external dependencies.

Expand “Explore the full factory” for the detailed map, handoffs, five review lenses, correction loops, proposed capabilities, and all 38 source skills. Select a node for its inputs and outputs. Keep the HTML, stylesheet, and script together in `preview/` when copying it.

The [skill lifecycle map](docs/skill-lifecycle-map.md) maps the 38 supplied RepairCheck skills to delivery stages, review checks, system adapters and business workflows. It records existing instructions separately from proposed factory connections.

The [QA entry point and gap analysis](docs/qa-enforcement-gap-analysis.md) proposes how an entry skill, saved state, hooks, executable gates, and independent checks can make those procedures reliable. It includes 24 prioritized improvements and a first-run acceptance plan; these mechanisms are not implemented yet.

Seif identifies this supplied collection as his own work, with AI assistance in writing and committing some skills. Commit author metadata does not determine design authorship; source history is preserved.

## Structure

```text
AGENTS.md                 Repository working rules
.agents/skills/           Skill folders and their index
  <skill-name>/
    SKILL.md              Purpose, trigger, workflow, and outputs
    agents/openai.yaml    Optional Codex metadata
    scripts/              Helpers when needed
    references/           Supporting instructions when needed
    assets/               Reusable output assets when needed
```

Create supporting folders only when a skill needs them. Keep skill names lowercase with hyphens. A skill's frontmatter name must match its folder name.

## Building together

1. Supply an existing skill or describe a concrete workflow we need.
2. Read its instructions and supporting files. Preserve useful behavior and identify assumptions about tools, access, and target projects.
3. Add or adapt it under `.agents/skills/<skill-name>/` and register it in the index.
4. Validate its structure and references. Exercise meaningful behavior where the environment permits.
5. Record what was tested, what remains unknown, and how it connects to other skills.

Start with actual skills and working use cases. Implement the selected Safe Engine architecture around explicit inputs, outputs, and dependencies.

## Working principles

- A skill describes a procedure; it does not grant access or authorize external actions.
- Preserve human decisions at the agreed review and release boundaries.
- Distinguish implemented, tested, accepted, and deployed states.
- Use observable evidence for completion. A generated summary alone is insufficient.
- Keep retries and spend bounded for unattended execution. Return a blocker when the workflow cannot progress.
- Keep secrets, client data, local runtime state, and generated run artifacts out of version control.

Project skills live in `.agents/skills`. Discovery and invocation depend on the host and its repository context. Personal installation or use from another project requires a separate installation step; creating this repository does not install its skills globally.
