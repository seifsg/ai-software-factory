# AI Software Factory

Private home for Seif's software-delivery skills. We will import existing skills, improve them through real use, and build new skills together.

## Goal

Make skills work together as a repeatable delivery system: understand a request, prepare the work, implement it, verify the result, handle feedback, and return evidence. Connect release and monitoring when the target project supports them and the user authorizes them.

The factory runs against the customer's or team's project. This repository owns the reusable skills and their supporting resources, not client source code or credentials.

## Current state

Repository foundation and visual design. No skills have been imported yet. No runtime, unattended workflow, integrations, or deployment behavior has been implemented or verified.

## Start here

Open [the visual introduction](preview/index.html) in a browser. It explains the factory in plain language: understand, build, check, approve. It is our living guide to the goal, the existing skill collection, and the next milestone. It works locally without installation or external dependencies.

Its interactive architecture map shows the named skills, their handoffs, the five review lenses, correction and observation loops, human approval, and proposed orchestration/release capabilities. Select a node for its inputs and outputs, or explore all 38 skills in the library view. Keep the HTML, stylesheet, and script together in `preview/` when copying it.

The [skill lifecycle map](docs/skill-lifecycle-map.md) maps the 38 supplied RepairCheck skills to delivery stages, review checks, system adapters and business workflows. It records existing instructions separately from proposed factory connections.

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

Start with actual skills and working use cases. Choose orchestration after we understand their inputs, outputs, and dependencies.

## Working principles

- A skill describes a procedure; it does not grant access or authorize external actions.
- Preserve human decisions at the agreed review and release boundaries.
- Distinguish implemented, tested, accepted, and deployed states.
- Use observable evidence for completion. A generated summary alone is insufficient.
- Keep retries and spend bounded for unattended execution. Return a blocker when the workflow cannot progress.
- Keep secrets, client data, local runtime state, and generated run artifacts out of version control.

Project skills live in `.agents/skills`. Discovery and invocation depend on the host and its repository context. Personal installation or use from another project requires a separate installation step; creating this repository does not install its skills globally.
