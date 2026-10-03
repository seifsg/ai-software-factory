# AI Software Factory

Seif's software-building skills and **Safe Engine 0.1.0**, the local controller that connects them.

Understand the request. Prepare the work. Build it. Check it. Return the result with evidence.

**Reading from your phone?** Start with the [factory status and skill links](docs/factory-status.md), then the [full audit](docs/factory-audit-2026-10-03.md). Both render directly on GitHub. Sign in with an account that can access this private repository.

## The skills

Use Seif's originals where they exist. RepairCheck Mobile comes first. Write the remaining skills in the same direct style. Keep real requirements; remove needless explanation and hidden workflow changes.

The [skill index](.agents/skills/README.md) lists eleven canonical skills: seven with originals and four factory-specific skills. Two portable entries load the complete factory from another project. [Provenance](docs/skill-provenance.md) records exact sources, task matches and packaging changes.

Ask for analysis and you get analysis. Ask for planning and you get planning. A small feature does not turn either request into permission to code. For a requested bounded fix, [Small Change](.agents/skills/small-change/SKILL.md) runs six light routines with focused checks and one independent review. Larger delivery follows the version workflow:

```text
analyze → original plan → market research for new apps → revised plan
        → build with the 0–4 loop → feature feedback
        → full version QA → useful improvements → final QA → fresh review
        → checked local handoff → authorized PR creation and review → human
```

The original planning checkpoint remains. Proceed through it only when the user's instructions already authorize that continuation.

## Start or resume

[Install Safe Engine](docs/install-safe-engine.md), then give it the task and target:

```text
$safe-engine Build [app or feature] in [absolute project directory].
Success means [observable outcomes].
```

To continue, ask it to resume the existing run. Keep the selected bundle, decisions and evidence. [Fresh-session setup](docs/start-another-session.md) covers manual loading and other hosts. [Pilot usage](docs/pilot-usage.md) contains actual commands and prerequisites.

To improve the factory, use [Improve Factory](.agents/skills/improve-factory/SKILL.md). It preserves an active app checkpoint, repairs separately, obtains independent review and checks whether the app can safely resume. [Install its portable entry](docs/install-improve-factory.md) when working elsewhere.

Use existing authorized GitHub access. A local installation does not install on another machine or grant new permissions.

## What works today

The current Codex session builds; Python saves stages, runs configured checks and rejects stale evidence. A fresh read-only Codex CLI process reviews the candidate before local handoff. The controller does not push, merge, deploy or run as a background service.

The [recorded pilot](docs/pilot-verification.md) demonstrates a local browser fixture and repair. It does not certify this revised wording, every host, or a production app. PR delivery needs actual project settings from the [PR adapter](docs/pr-workflow.md). Claude-native and cloud delivery are unverified.

During app delivery, the coordinator applies [diagnostics](.agents/skills/safe-engine/references/app-diagnostics.md) and [efficiency](.agents/skills/safe-engine/references/app-efficiency.md). New apps plan these from the start; existing changes address affected paths. Instructions alone do not prove useful logs or a faster app.

QA binds to declared code, guidance and runtime inputs. Changing a required skill invalidates old evidence. Preserve active pins and use the compatibility procedure before adopting a different factory.

## Repository layout

```text
.agents/skills/           Canonical skills, references and index
skills/                  Two installable entries and generated resolvers
safe_engine/             Python controller, schema and bundle input contract
scripts/                 Resolver packaging helper
tests/                   Controller and distribution checks
docs/                    Usage, sources, decisions and dated design records
preview/                 Visual factory map
examples/                Disposable fixture and recorded demonstration
```

Client source, credentials and runtime records belong outside this reusable bundle. Keep run records in ignored `.factory/` folders.

Both portable resolvers come from `safe_engine/distribution.py`. After editing it, run `python scripts/package_skill_entries.py`, then check with `--check`.

## Keep building together

Read [repository rules](AGENTS.md) and [selected decisions](docs/safe-engine-decisions.md) before editing. Restore originals faithfully. For a new procedure, start from Seif's actual request, compare requirements before and after editing, then verify affected behavior.

The [visual map](preview/index.html) explains the flow. The [lifecycle map](docs/skill-lifecycle-map.md) catalogs all 38 supplied source skills; seven source skills are imported here. The [expanded plan](docs/safe-engine-expanded-scope.md), [build plan](docs/safe-engine-build-plan.md) and [delivery design](docs/safe-engine-fast-delivery.md) preserve earlier proposals and choices. They do not authorize importing the rest of the library.
