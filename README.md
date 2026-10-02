# AI Software Factory

Private home for Seif's software-delivery skills and **Safe Engine 0.1.0**, the first local factory pilot.

## Goal

Make skills work together as a repeatable delivery system: understand a request, prepare the work, implement it, verify the result, handle feedback, and return evidence. Connect release and monitoring when the target project supports them and the user authorizes them.

The factory runs against the customer's or team's project. This repository owns the reusable skills and their supporting resources, not client source code or credentials.

The engine is named **Safe Engine**. The [design decision record](docs/safe-engine-decisions.md) captures Seif's selected architecture and quality procedures, with unresolved choices kept explicit. The selected project onboarding approach discovers configuration and offers a profile for review and correction.

Seif leads skill authorship; the assistant helps structure, review, refine, and validate his procedures. The [expanded capability plan](docs/safe-engine-expanded-scope.md) covers worktrees, skill writing, TDD, debugging, architecture, UX, idea assessment, security, and autonomous browser inspection and repair. It includes source comparisons, three alternatives for each design choice, an ASCII architecture, and acceptance cases. Skill counts, boundaries, and new procedures await selection. The [initial build plan](docs/safe-engine-build-plan.md) preserves the core delivery workflow and engine checklist.

Development should proceed in substantial batches, followed by relevant verification. Before a feature is pushed, inspect worthwhile cleanup, reuse, design, performance, and security improvements, then verify the changes. The [fast feature delivery design](docs/safe-engine-fast-delivery.md) records this cadence and the proposed criteria for code that AI agents can navigate and change accurately.

## Current state

The demonstrated local pilot connects five of Seif's existing skills through one new coordinator. It saves task progress, enforces stage order and records corrections without a numerical repair ceiling, runs affected feature checks as feedback and full version QA, rejects stale evidence, and launches a fresh read-only Codex review before producing a checked handoff. Two further Seif-authored skills now govern every PR: `how-to-make-a-pr` and the complete separate-instance `how-to-review-a-pr`. Their project bindings and enforcement limits are recorded in the [PR workflow](docs/pr-workflow.md).

```text
analyze-start → original plan → market research (new app) → revised plan
    → build with the 0–4 loop
    → feature feedback (continue build) → full version QA → worthwhile improvement
    → full final-QA validation (controlled unchanged reuse only)
    → fresh local review → checked local handoff
    → how-to-make-a-pr → full separate how-to-review-a-pr → human
                     findings → supported repair ↗
```

The current Codex session does the building; Python controls the gates. This is a local agent-operated pilot, not an unattended production service. Browser QA uses the target project's real browser checks. The broader specialist library, host hooks, protected remote acceptance, general project adapters, and deployment remain ahead. See the [verification record](docs/pilot-verification.md) for actual results and limits.

QA fingerprints bind the controller and declared operative guidance, including approved decisions, cadence and the portable entry. Missing mandatory inputs block acceptance; guidance changes invalidate older evidence. [Pilot usage](docs/pilot-usage.md) defines the enforced boundary and the runtime inputs that a project must declare.

## Start here

For a new chat or another project, use the [pasteable fresh-session starter](docs/start-another-session.md). To see the first run, open the [recorded walkthrough](examples/pilot-walkthrough.md), including before/after images and the actual repair. [Complete example commands](examples/pilot-commands.md) show setup and every controller step. Claude Code and cloud limitations are explicit in the starter guide.

Read [pilot setup and usage](docs/pilot-usage.md), then ask Codex in this repository:

> Use $safe-engine to implement [feature] in [absolute target project path].

This retains Seif's analysis charts, planning critique, per-todo inspection, batched verification, and improvement pass. The [session contract](.agents/skills/safe-engine/references/session-contract.md) preserves delegated autonomy and continuous progress to the verified handoff without repeat questions. New applications use [research-market](.agents/skills/research-market/SKILL.md) between their original and revised plans; evidence includes current competitors and visual experiences. These are agent instructions, not a background service or a claim of a demonstrated market outcome. The [skill index](.agents/skills/README.md) lists ten packaged entrypoints; [provenance](docs/skill-provenance.md) records the seven adapted sources. Seif continues to lead authorship of the wider library.

When the factory itself needs correction, use [improve-factory](.agents/skills/improve-factory/SKILL.md), including during an app build. It preserves the app checkpoint, coordinates an isolated repair and independent assessment, then checks whether the current run can adopt it. This is an agent-operated procedure; automatic hooks, bundle migration, and uninterrupted upgrades are not implemented.

To call it from other projects, [install the reusable skill from GitHub](docs/install-improve-factory.md). Install **`skills/improve-factory`**: this portable entry loads the complete versioned factory and preserves an active app's recorded bundle. Invoke `$improve-factory` in Codex or `/improve-factory` after installation in Claude Code. Private GitHub access and the documented host prerequisites apply; native Claude execution remains unverified.

Open [the visual introduction](preview/index.html) in a browser. Its concise first screen explains the goal and the process: understand, build, check, approve. A single status line shows where we are today. It works locally without installation or external dependencies.

Expand “Explore the full factory” for the detailed map, handoffs, five review lenses, correction loops, proposed capabilities, and all 38 source skills. Select a node for its inputs and outputs. Keep the HTML, stylesheet, and script together in `preview/` when copying it.

The [skill lifecycle map](docs/skill-lifecycle-map.md) maps the 38 supplied RepairCheck skills to delivery stages, review checks, system adapters and business workflows. It records existing instructions separately from proposed factory connections.

The [QA entry point and gap analysis](docs/qa-enforcement-gap-analysis.md) is the earlier research baseline. Its 24 improvements describe the broader target; the pilot verification record identifies the subset now implemented and exercised.

Seif identifies this supplied collection as his own work, with AI assistance in writing and committing some skills. Commit author metadata does not determine design authorship; source history is preserved.

## Structure

```text
AGENTS.md                 Repository working rules
safe_engine/             Python controller, version and review schema
tests/                   Controller fault scenarios
examples/pilot-app/       Deliberately broken disposable demo fixture
docs/pilot-usage.md       Setup, commands, recovery and limits
.agents/skills/           Skill folders and their index
  <skill-name>/
    SKILL.md              Purpose, trigger, workflow, and outputs
    agents/openai.yaml    Optional Codex metadata
    scripts/              Helpers when needed
    references/           Supporting instructions when needed
    assets/               Reusable output assets when needed
skills/improve-factory/   Installable entry loading the complete canonical bundle
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
- Continue meaningful authorized work until the agreed verified outcome or an explicit owner stop. Diagnose stalled progress, research alternatives, reconcile uncertain actions and report actual access/authority obstacles; do not invent credits or exhaustion stops.
- Keep secrets, client data, local runtime state, and generated run artifacts out of version control.

Project skills live in `.agents/skills`. Discovery depends on the host and repository context. From another project, explicitly reference this bundle's coordinator by absolute path or install it separately; creating this repository does not install its skills globally.
