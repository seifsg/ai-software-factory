# Use the Safe Engine pilot

Safe Engine 0.1.0 is a local, agent-operated delivery loop. The current Codex session builds the feature using Seif's methods. Python records stages and executes checks; a fresh read-only Codex CLI process reviews the final candidate. The controller creates a checked local handoff. It does not push, merge, deploy, or run as an unattended daemon.

## Start through Codex

Open this repository as the Codex project and ask:

> Use $safe-engine to implement this feature in [absolute target project path]: [request]. Follow analyze-start and get-ready-to-code. Work in substantial batches and stop at a checked handoff.

From another project, explicitly reference this bundle's `.agents/skills/safe-engine/SKILL.md` by absolute path. Repository skills are not automatically installed globally or into other repositories. Codex normally discovers `.agents/skills` within its repository scope. [Official skill documentation](https://learn.chatgpt.com/docs/build-skills).

Requirements: Python 3.11+, Git, authenticated Codex CLI, and the target project's actual check dependencies. Browser work additionally requires a working browser driver and a runnable test application. Use a suitable existing isolated worktree or the host's worktree tool. The demo uses an explicitly created disposable Git worktree.

## Configure a task

Run commands from this bundle's root. On Windows, use the full path of the real Python executable if `python` resolves to the Windows Store launcher.

```text
python -m safe_engine --project <absolute-project-root> discover
```

Discovery reads Git and package scripts without executing them. Review the proposed interface and supply real commands. Add `.factory/` to the target project's ignore rules, preserve existing work, and establish a clean committed baseline. Runtime artifacts belong in `.factory/` or an excluded external directory, not in the source candidate.

Example profile for a web project; adjust it to installed tools and actual acceptance files:

```json
{
  "version": 1,
  "interface": "web",
  "checks": [
    {"id": "unit", "kind": "unit", "argv": ["node", "tests/unit.mjs"], "timeout_seconds": 60},
    {"id": "browser", "kind": "browser", "argv": ["node", "tests/browser.cjs"], "timeout_seconds": 120,
     "artifacts": [".factory/outputs/browser/mobile.png", ".factory/outputs/browser/mobile-complete.png", ".factory/outputs/browser/desktop.png"]}
  ],
  "environment_inputs": ["NODE_ENV"],
  "input_files": [],
  "protected_paths": ["tests/unit.mjs", "tests/browser.cjs"]
}
```

Commands are argument arrays, not shell strings. `{python}`, `{project}`, and `{run}` expand to the current interpreter, target root, and local runtime directory. Explicitly use the right executable for the platform; npm shell wrappers may need a platform-specific command. Commands are trusted configuration reviewed by the operator, not a sandbox for untrusted test code.

Declare relevant environment variables and ignored/external input files in the profile; their content is hashed, not copied into task records. Include meaningful dependency manifests, browser/runtime configuration, and test-data identity where applicable. Input discovery cannot infer every mutable service, database, or hidden runtime input. The pilot has no evidence cache: browser checks execute against a running app supplied by the configured check. Network service identity remains the adapter's responsibility.

`protected_paths` holds the accepted checks that cannot be changed during the run. Develop further tests in other files when needed. If requirements or protected checks genuinely need correction, preserve the current run and initialize a newly reviewed task in a fresh worktree. The same OS user can edit local records, so this is workflow integrity, not hostile-user protection.

Optional per-check `artifacts` list generated evidence files under `.factory/outputs/`. The runner removes only those declared output files before the command, requires fresh files afterwards, and verifies their hashes before review and handoff. Configure the check to actually write those paths; old screenshots cannot substitute for a new run.

Task JSON:

```json
{
  "request": "The original requested outcome",
  "acceptance": [
    {"id": "A1", "text": "An observable required outcome", "checks": ["unit", "browser"]}
  ]
}
```

Initialize with explicitly agreed limits. The numbers below illustrate the disposable demo, not universal settings:

```text
python -m safe_engine --project <project> init --task <task.json> --profile <profile.json> --max-repairs 3
python -m safe_engine --project <project> status
```

## Follow the stages

Use the actual procedures, then record their outputs. Artifacts can be Markdown with diagrams and tables; the controller validates presence and integrity, while the fresh reviewer assesses substance.

```text
record analysis --file <analysis.md>       analyze-start; no code changes
record plan --file <plan.md>               get-ready-to-code Part A; no code changes
record batch --file <batch.md>             Part B: complete the substantial batch
check                                     run configured checks together
record improvement --file <improvement.md> inspect/apply supported improvements
check                                     verify the resulting candidate
review --timeout 600                       fresh read-only Codex CLI process
handoff                                   validate evidence and write handoff.md
```

Prefix every line with `python -m safe_engine --project <project>`. A failed check or finding requires `repair --reason "..."`, implementation using the same method, a new batch record, checks, improvement record, final checks, and fresh review. The correction count is shared across the run. `cancel --reason "..."` stops future progression and preserves work. No operation deletes the worktree.

After interruption, use `status`. An incomplete check or review is not acceptance; rerun it on current inputs. A changed candidate after its batch record needs a repair cycle. File locks release when the process exits. To stop an active check or review, interrupt its foreground controller; it terminates its owned process tree. A concurrent cancel command does not bypass the active operation's lock.

The first pilot supports one feature batch and bounded correction batches. Final checks currently run again after the improvement stage, including when no changes were made. Avoiding that duplicate work for provably unchanged controlled inputs is a remaining optimization; this pilot never runs tests on each edit or save.

## What is enforced

- Original task and profile are fixed for the run; criterion IDs and required checks are validated.
- Source changes during the analysis or planning phase prevent progression.
- Required acceptance files and recorded artifacts cannot change unnoticed through ordinary controller use.
- Evidence includes exact source contents, check definitions, declared inputs, executables, and the factory bundle. A commit that only records unchanged contents does not itself invalidate evidence.
- Passing commands, current logs, an improvement artifact, and a fresh successful review are necessary for handoff.
- Corrections share the explicitly supplied budget; cancelled runs cannot continue.

## Remaining gaps

The controller does not intercept arbitrary agent actions, install host hooks, or protect GitHub merges. Its local records are not signed or isolated from the builder's OS identity. A fresh read-only reviewer supplies context and permission separation, but is not a separately administered acceptance service. Model judgments and tests can miss defects.

PR delivery always uses [how-to-make-a-pr](../.agents/skills/how-to-make-a-pr/SKILL.md) followed by the **complete separate-instance** [how-to-review-a-pr](../.agents/skills/how-to-review-a-pr/SKILL.md). This is mandatory for every factory-managed project, including docs/skills and subsequent updates. A successful local `handoff` does not certify those PR steps. Resolve real tracker, human owner, notifications and project check bindings; missing required bindings block PR completion. See [PR workflow status](pr-workflow.md). The paired skills are instruction-level requirements, not executable GitHub/host enforcement.

The full architecture, UX, security, idea-assessment, TDD, skill-writing, and worktree-management modules are not implemented as independent specialist skills. General review lenses cover only part of those responsibilities. Planning and execution are separate controller phases but still share the original `get-ready-to-code` entrypoint; the selected modular split remains future packaging work.

The browser demo proves specified interactions, rendering checks, and a repair on one fixture. It does not demonstrate autonomous aesthetic judgment, broad project portability, remote state isolation, or production readiness. Python controller tests, skill structural validation, actual browser execution, and independent review are reported separately.

Fresh review uses `codex exec --sandbox read-only --ephemeral --output-schema ...`. Its completion and structured content are checked; an unavailable CLI or failed review blocks handoff. [Official non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode).
