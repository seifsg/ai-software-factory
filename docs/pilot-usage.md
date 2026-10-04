# Use the Safe Engine pilot

## Small direct changes

This route is for requested implementation. An explicit analysis, planning or review request stays in that phase.

Seif selected [small-change](../.agents/skills/small-change/SKILL.md) on 3 October: six lightweight routines, careful implementation, focused checks and one narrow independent assessment. This route precedes the full version workflow described below. No automatic broad regression, full-suite reruns or five-artifact planning for a small fix. Accumulated changes may prompt an offer of affected-area validation; execution waits for the user. It is an agent-operated scoped handoff, not a new controller command or whole-version acceptance. Existing pinned runs retain their bundle/state; see the method for explicit local trials and evidence limits.

Safe Engine 0.1.0 is a local, agent-operated delivery loop. The current Codex session builds the feature using Seif's methods. Python records stages and executes checks; a fresh read-only Codex CLI process reviews the final candidate. The controller creates a checked local handoff. It does not push, merge, deploy, or run as an unattended daemon.

## Start through Codex

Open this repository as the Codex project and ask:

> Use $safe-engine to implement this feature in [absolute target project path]: [request]. Follow analyze-start and get-ready-to-code. Work in substantial batches and stop at a checked handoff.

From another project, [install the portable Safe Engine skill](install-safe-engine.md) and invoke `$safe-engine`. You can also explicitly reference this bundle's `.agents/skills/safe-engine/SKILL.md` by absolute path. Repository skills are not automatically installed globally or into other repositories. Codex normally discovers `.agents/skills` within its repository scope. [Official skill documentation](https://learn.chatgpt.com/docs/build-skills).

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

Declare relevant environment variables and ignored/external input files in the profile; their content is hashed, not copied into task records. Include meaningful dependency manifests, browser/runtime configuration, and test-data identity where applicable. Input discovery cannot infer every mutable service, database, or hidden runtime input. The pilot can revalidate a whole unchanged full gate after improvement only when the immutable reviewed profile explicitly sets `reuse_unchanged_checks: true`. Default false preserves fresh final execution for existing profiles. Enable it only when every relevant runtime/service/test-data identity is controlled and declared; volatile backend, clock, hardware or permission state otherwise needs fresh execution. Browser checks use a running app supplied by the configured check. Network service identity remains the adapter's responsibility; source equality alone cannot establish it.

`protected_paths` holds existing accepted checks that cannot be changed during the run. Read them during development; execution and further test authoring wait until implementation and manual QA are complete. Add final tests only within the reviewed check contract, in unprotected files. If requirements, commands or protected checks need correction, preserve the run and use a newly reviewed task in a fresh worktree. The same OS user can edit local records, so this is workflow integrity, not hostile-user protection.

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

For new projects, resolve acceptance-shaping research before freezing task/profile where possible. Prepared analysis/plans may then be recorded in stage order. Once initialized, implementation plans may evolve within accepted criteria; changed task/profile/protected checks require a newly reviewed run in a fresh worktree. Preserve old records and lineage.

Initialize with the completion boundary and authority recorded in the [session contract](../.agents/skills/safe-engine/references/session-contract.md). No numerical correction allowance or session deadline is required or invented. Keep actual owner stop/checkpoint and provider/access constraints. Individual check/review timeouts diagnose hung commands; they are not a whole-session limit:

```text
python -m safe_engine --project <project> init --task <task.json> --profile <profile.json>
python -m safe_engine --project <project> status
```

## Follow the stages

Supported interfaces: `web`, `cli`, `library`, `desktop`, `mobile`, `game`, `service`. Web requires a `browser` check; desktop/mobile/game require an `interaction` check; service requires `api` or `integration`. Choose by the actual delivery interface: a browser game may use `web`, a headless game server `service`. Supported check kinds also include `unit`, `build`, `security`, and `performance`. Configure real commands/tools and evidence paths; labels alone prove nothing. These profiles do not install a browser, game driver, emulator or native automation tool. Inspect mixed surfaces and configure all relevant checks.

Use the actual procedures, then record their outputs. Honor Get Ready to Code's file-summary stop unless existing user instructions explicitly authorize continuing. Read the Mobile-priority [source map](skill-provenance.md#current-source-map--3-october-2026). For new software, the existing `plan` phase contains original plan → [research-market](../.agents/skills/research-market/SKILL.md) → revised plan; retain and link all three before recording the final plan. Research covers product/UX, current stack/architecture and fitting patterns; inspect applicable resource costs and resolve material unknowns during delivery. Standalone research needs no run. No new CLI stage is introduced. Artifacts can be Markdown with diagrams and tables; the controller validates presence and integrity, while the fresh reviewer assesses substance.

```text
record analysis --file <analysis.md>       analyze-start; no code changes
record plan --file <plan.md>               get-ready-to-code planning outputs; no code changes
record batch --file <batch.md>             finished implementation/improvements, manual QA, then final test authoring
check                                     run ALL configured version checks together
record improvement --file <improvement.md> record the pre-test improvement assessment; no planned development here
check                                     validate full final QA; eligible unchanged reuse or full rerun
review --timeout 600                       fresh read-only Codex CLI process
handoff                                   validate evidence and write handoff.md
```

Prefix every line with `python -m safe_engine --project <project>`. A failed check or finding requires `repair --reason "..."`, a completed surgical correction, manual QA, final test work, a new batch record, checks, improvement record, final checks and fresh review. The correction count is diagnostic history, not a stop condition. `cancel --reason "..."` stops future progression and preserves work. No operation deletes the worktree.

After interruption, use `status`. An incomplete check or review is not acceptance; rerun it on current inputs. A changed candidate after its batch record needs a repair cycle. File locks release when the process exits. To stop an active check or review, interrupt its foreground controller; it terminates its owned process tree. A concurrent cancel command does not bypass the active operation's lock.

## Feature feedback and version checkpoints

Current policy is [finish work → manual action QA → final test authoring/execution](current-decisions.md#finish-work-use-it-then-automate-tests). Apply it across the whole requested task, not per capability. During `build`, finish implementation and worthwhile improvements, exercise the real behavior manually, then author/polish tests at the final stage. Include candidate identity, actual actions/results and chronology in the batch artifact. Reviewers inspect adherence; the controller has no manual-QA receipt gate.

The legacy `feature-check --checks <IDs> --file <feature.md>` command still executes partial checks in `build`. Do not use it under current policy. Its availability is not permission; partial results never certify a version. Existing historical feedback remains evidence of its recorded candidate only.

Failed feature feedback is preserved and requires `repair --reason ...` before another feature or version batch. Repair from build is allowed only for actual failed feedback; diagnostic counters remain continuous. Interrupted operations remain incomplete, cannot be recorded as a finished version, and need reconciliation/rerun. Cancellation stays terminal.

After implementation, manual QA and final test authoring, `record batch` then `check` executes **every configured check**. The later `improve` stage records the assessment already completed before manual QA. New production changes require `repair`, renewed manual QA and final tests. At final QA, `check` either executes every command again or, with reviewed `reuse_unchanged_checks: true`, validates the unchanged full gate's exact source, fixed task/profile, declared files/environment, executable and operative factory-input fingerprints plus every required command, log and output hash. It records `checks_reused: true` without replacing original logs. Missing/modified evidence rejects reuse. `check --fresh` forces execution for volatile/runtime concerns. Partial subsets never count as acceptance; fresh independent review follows.

Initialization still requires existing protected acceptance files. If a new project lacks them, do not author tests early, add placeholders or invent completed stages. Continue authorized agent-led analysis/planning/implementation and manual QA with the same methods and durable records; write tests only at the final stage. Report that this delivery lacks controller acceptance. A later controller run needs an honestly scoped, reviewed task and preserved lineage; it cannot retroactively certify development performed outside it. Existing runs keep their pins and immutable contracts.

The factory input owner is [bundle-inputs.json](../safe_engine/bundle-inputs.json). Its required files cover the controller/schema, root rules and README, canonical methods/references/index, portable entry/resolver and guidance docs, including approved decisions and delivery cadence. The fingerprint also discovers `.py`, `.md`, `.json`, `.yaml` and `.yml` additions in its declared source trees. Missing required files, the contract or a source tree block the gate; content changes invalidate previous QA. Update the required list when adding mandatory procedural inputs so deletion cannot silently omit them. Guidance context is hashed conservatively; inclusion does not turn historical proposals into approved requirements.

This procedural boundary excludes the factory's own tests, examples, preview and media. When such a resource is an input to a target's acceptance, declare it in that target's profile. An installed launcher outside the selected bundle, external tools/services and hidden runtime state are not inferred; preserve their identity and declare operative files/environment inputs or require fresh checks. The target project's own source fingerprint still includes its tracked and nonignored untracked files. A clean Git revision or portable completeness inspection alone is not QA.

Do not add the reuse flag to a saved profile: the contract is immutable. Older profiles/runs remain supported and default to fresh final commands. A newly reviewed run may opt in when its environment control warrants reuse. This is local workflow integrity, not an administered cache/security boundary or automatic dependency scheduler.

## What is enforced

- Original task and profile are fixed for the run; criterion IDs and required checks are validated.
- Source changes during the analysis or planning phase prevent progression.
- Required acceptance files and recorded artifacts cannot change unnoticed through ordinary controller use.
- Evidence includes exact source contents, check definitions, declared inputs, executables, and the operative factory inputs defined above. A commit that only records unchanged contents does not itself invalidate evidence.
- Passing commands, current logs, an improvement artifact, and a fresh successful review are necessary for handoff.
- Corrections continue with supported diagnosis and fresh acceptance; cancelled runs cannot continue. New init defaults to continuous; deprecated `--max-repairs` and old saved integers remain historical metadata, never active caps. `status` exposes `repair_policy: continuous`, `max_repairs: null`, `historical_max_repairs`, and preserved `repairs_used`. Compatible old post-QA runs use normal `repair --reason ...`; no manual state edit or acceptance carry-over.

## Remaining gaps

The controller does not intercept arbitrary agent actions, install host hooks, or protect GitHub merges. Its local records are not signed or isolated from the builder's OS identity. A fresh read-only reviewer supplies context and permission separation, but is not a separately administered acceptance service. Model judgments and tests can miss defects.

PR delivery always uses [how-to-make-a-pr](../.agents/skills/how-to-make-a-pr/SKILL.md) with the [project adapter](pr-workflow.md), followed by the **complete separate-instance** [how-to-review-a-pr](../.agents/skills/how-to-review-a-pr/SKILL.md). This is mandatory for every factory-managed project, including docs/skills and subsequent updates. A successful local `handoff` does not certify those PR steps. Resolve real tracker, human owner, notifications and project check bindings; discover bindings first; missing required bindings block PR completion while independent local owner-test delivery continues. See [PR workflow status](pr-workflow.md). The paired skills are instruction-level requirements, not executable GitHub/host enforcement.

The full architecture, UX research beyond the implemented [quality audit](../.agents/skills/ux-quality/SKILL.md), security, idea-assessment, test-quality review, skill-writing, and worktree-management modules are not implemented as independent specialist skills. General review lenses cover only part of those responsibilities. Planning and execution are separate controller phases but still share the original `get-ready-to-code` entrypoint; the selected modular split remains future packaging work.

The browser demo proves specified interactions, rendering checks, and a repair on one fixture. It does not demonstrate autonomous aesthetic judgment, broad project portability, remote state isolation, or production readiness. Python controller tests, skill structural validation, actual browser execution, and independent review are reported separately.

Fresh review uses `codex exec --sandbox read-only --ephemeral --output-schema ...`. Its completion and structured content are checked; an unavailable CLI or failed review blocks handoff. [Official non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode).
