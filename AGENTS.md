# AI Software Factory — repository rules

## Scope

This private repository owns Seif's reusable software-factory skills. Read `README.md` and `.agents/skills/README.md` before changing the system. Follow the user's current instructions and preserve existing skill behavior unless the requested change requires altering it.

## Quality standard

Our motto: **give 100% minimum; aim to give more through the quality of the work.**

- Put extra effort into correctness, clarity, polish, usability, and appropriate verification.
- Review and refine the output before calling it finished. Iterate further when doing so materially improves the result.
- Overdeliver through useful improvements that are needed within the agreed scope. Preserve the user's intent and avoid adding unsolicited deliverables or unrelated features.
- Judge success by the quality and usefulness of the outcome, rather than the amount of material produced.

## Skill development

The engine is named **Safe Engine**. Read `docs/safe-engine-decisions.md` before designing or changing the factory. Preserve Seif's selected options; keep pending choices unresolved. For new improvement or design decisions, present three credible alternatives in a comparison table, recommend one with reasons, and leave the selection to Seif. Recommendations do not become approved defaults. Exact stage and skill names remain open unless explicitly selected.

Seif is the primary author of the skills. Help him express his procedures, compare relevant examples, identify gaps or contradictions, refine wording, structure files, and validate behavior. Preserve his intent and voice. Do not independently draft most of the skill library or create placeholder skills. New procedures and substantive rewrites should develop from Seif's writing or an explicit request for a particular draft. Examples from other factories are inspiration, not approved names or procedures. Skill counts, boundaries, and build plans remain proposals until selected.

- Use the available Skill Creator workflow when creating or substantially updating a skill.
- Read an imported skill and its relevant resources before adapting it. Record provenance where known; do not invent authorship or copy rights.
- Store each skill in `.agents/skills/<skill-name>/SKILL.md`, with YAML `name` and `description`. Match the name to the folder.
- Describe when the skill applies, what context it needs, and what it returns. Add exclusions when they prevent likely misrouting.
- Keep procedures self-contained where practical. Declare real dependencies; do not assume tools or integrations exist.
- Keep reusable content in one canonical owner. Link supporting references from the skill entrypoint.
- Do not create placeholder skills or claim that a skill is operational because its instructions exist.
- Update the skill index after adding, removing, or materially changing a skill.

## Connected workflows

Keep `preview/index.html`, our plain-language visual introduction, accurate as the factory changes. Explain outcomes before implementation details. Clearly distinguish skills available in the source collection, skills imported here, and workflows demonstrated in a real run.

When connecting skills, make the handoff explicit: inputs, output artifact, acceptance condition, failure state, and next responsible step. Keep task state durable where the target environment supports it. Do not mark a ticket complete when work only reached a review or deployment handoff.

For unattended workflows, define retry, time, and cost limits appropriate to the task. Avoid duplicate actions on retries. Keep independent acceptance checks outside the builder's unrestricted control when their integrity matters.

## Verification and changes

- Validate skill frontmatter, names, references, and any executable helpers.
- Test observable behavior when warranted. Report checks not run and their limits honestly.
- Keep changes focused and preserve unrelated work. Use a branch for substantive changes to an established repository.
- Do not merge, release, contact others, spend money, or change a target project's live systems without applicable user authorization.
- Never commit credentials, client source/data, transcripts containing sensitive information, or local runtime state.
