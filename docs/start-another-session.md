# Start Safe Engine in another session

Carry current iteration, remaining outcome and exact context. Preserve active pins and authority.

## Small direct changes

This route is for requested implementation. Explicit analysis, planning and review stay in their phase.

Seif selected [small-change](../.agents/skills/small-change/SKILL.md) on 3 October. Its six light routines remain for legacy unticketed work. Fast is the default [speed mode](../.agents/skills/safe-engine/references/speed-modes.md). Safe implementation uses [Ticketing](../.agents/skills/ticketing/SKILL.md) and the complete cycle, even bugfixes; retain surgical scope and relevant checks. Preserve existing pins, state and historical evidence.

[Ticket usage](ticketing.md) owns confirmed scope, captures, dependencies and proof. Prefer the owner's authorized tracker MCP; GitHub Issues is the default and Seif's current choice. Dispatch a real dedicated builder session per ticket; a label or local record is insufficient. Use isolated worktrees for independent tickets, serial ownership for a shared epic. Commands use `--ticket <key>`; initialization records `--session <real-builder-session-id>`. Ticket state is `.factory/runs/<key>/state.json`; legacy `.factory/state.json` stays intact. No controller daemon, session provisioner or host automation is installed.

The first thing to give the agent is the Safe Engine entry skill and your actual task. The agent then runs the controller commands. There is no `safe-engine start` daemon or one shell command that independently builds an app.

## Regular skill: recommended entry

Install [Safe Engine](install-safe-engine.md) for your agent once per machine ([hosts](hosts.md)). Then ask for the skill in your host's syntax: `safe-engine Build [my app or feature] in [absolute project directory]`. The adapter loads the complete factory and saves the target's selected bundle for safe resume. `improve-factory` is for changing the factory; it is not required as a separate installation for app delivery.

## Manual bundle: paste this first on this computer

Start a session of your agent in the target project, with the factory checkout reachable ([hosts](hosts.md)). Replace the two bracketed fields below. The path below is an example. Use the actual absolute path of your complete factory checkout.

```text
Read and follow C:/work/ai-software-factory/.agents/skills/safe-engine/SKILL.md
and its linked usage guide. Use that existing factory bundle.

Target project: [absolute project directory]
Task: [the app or feature I want, and what success looks like]

First inspect the real project, selected bundle, legacy .factory/state.json
and ticket state in .factory/runs/<key>/state.json. Resume the recorded run.
For Safe implementation, use ticketing: preserve owner input, inspect actual before,
confirm expected after/criteria and refresh the canonical tracker. Work one ticket
per dedicated builder session; record its actual ID with --session at init and
use --ticket <key> throughout. Prepare real checks without authoring/running tests.
Show the brief and only unresolved owner choices. Never mix legacy/ticket state
or silently upgrade its pin.

Follow analyze-start, including the ASCII charts, then get-ready-to-code and
the per-todo 0–4 loop. Work autonomously within the agreed scope and recorded session contract.
Ask essential preferences once only when not already answered. Under delegated
autonomy, continue until the agreed verified outcome per
.agents/skills/safe-engine/references/session-contract.md (including #review-rounds).
Honor my explicit stops.
Read each complete skill and its applicable references, not just its name. Honor
Get Ready to Code's file-summary stop (speed-modes.md#safe). Follow
docs/current-decisions.md#decision-ownership for new substantive choices. For new software,
save an original plan, research product/UX plus current stack, architecture and useful
patterns using research-market, then revise the plan before coding. Resolve material
unknowns during work. Plan applicable CPU/GPU, memory, queries/database, network,
storage and caching. Use actual browser/native/game/API/CLI evidence.
For new/material persistence design, use database-schema; no universal O(1) claim.
Carry these methods, decisions, real artifacts, diagnostic progress and actual constraints
into every resume or delegation.
Finish the complete outcome iteration and its required improvements. Keep the whole requested product visible. Optional polish/enhancement follows in later complete outcome tickets.
Follow the tests-last order in docs/current-decisions.md#finish-work-use-it-then-automate-tests.
Keep fixes surgical; no unrequested product pilots/simulations.
Keep method records durable, then obtain fresh independent review before handoff.
For any authorized PR, always execute how-to-make-a-pr, then how-to-review-a-pr as
docs/pr-workflow.md directs (remote/cloud review). Keep its task/owner handoff,
visual description and detailed comment. Read the PR project adapter first.
Missing required
project settings or access block PR completion after discovery; keep independent
local build, QA and owner-test delivery moving. Leave the PR draft for me.

Keep the work visible: show the plan before coding, give concise stage updates,
open the running app at final QA, and show actual browser results and the
final review. Continue without waiting at routine progress updates. Ask when
an owner-reserved decision, actual missing access or my explicit stop prevents dependent progress.
Do not choose a different example or change the product requirements for me.
```

If you start in the factory repository itself and your agent discovers the skill, the short form is `use safe-engine to implement [task] in [absolute project directory]`. The explicit file path above also tells a fresh session where the complete bundle lives. The skill call belongs in the chat; it is not a shell command.

To reach the bundle from another folder, add it to the session: Claude Code `claude --add-dir <bundle>` or `/add-dir`, Codex `codex -C <target> --add-dir <bundle>`, Cursor by adding the folder to the workspace. Added access does not install skills or hooks; [hosts](hosts.md) does.

Agents discover repository skills in `.agents/skills` (Claude Code: `.claude/skills` or its plugin). A skill in a different project is not automatically global.

## What the agent needs before it can proceed

- The complete factory bundle, Python 3.9+, Git, and access to the target project. The launcher installs missing Git/Python from official sources.
- One authenticated agent CLI for the Safe reviewer (Claude Code, Codex or Cursor, preferably not the builder), or the fallback: `review-packet` to a fresh read-only subagent, then `review --report`.
- The target project's actual test tools. Browser work needs a browser driver and runnable app.
- An agreed task, observable manual/automated/mixed acceptance, recorded authority and completion boundaries. Version 2 starts with draft checks; independently seal them at final testing. Real command watchdogs detect stuck processes; historical repair limits do not govern.
- For new delivery: canonical tracker access, confirmed ticket revision and a real dedicated builder session/workspace. Preserve missing capability as a dependent blocker; labels do not dispatch sessions.
- A remote/cloud agent route for [PR review](pr-workflow.md#cloud-pr-review); record missing access before dependent delivery.

The [session contract](../.agents/skills/safe-engine/references/session-contract.md) preserves delegated and reserved choices. The agent makes in-scope delegated choices; unresolved owner-reserved choices stay yours. A prompt does not install missing dependencies or grant access outside the session's permissions. Keep the factory bundle unchanged during a target run; editing its instructions changes an acceptance input.

## Start a brand-new application

Add this to the first message when the target does not exist:

```text
This is a new application. Start with a minimal project baseline in the target
directory. Preserve any existing files. Inspect the repository before choosing
the stack; if it is empty and I have not chosen the stack, give me three options
with one recommendation. Choose within my explicit delegation; otherwise ask
for the required owner choice. Do not reopen choices I already made.

Define agreed behavior and planned manual/automated evidence before implementation.
Ignore .factory/, establish a clean Git baseline, then initialize version-2 draft
acceptance without early tests. Seal independently reviewed checks at the final stage.
Show what belongs to bootstrap setup and what belongs to the controlled build.
```

The controller requires a Git project with a clean baseline. New version-2 runs need no existing tests; draft acceptance proceeds through finished implementation, final manual receipt, test authoring and independent sealing. Existing version-1 runs keep their limitations. Follow [current usage](pilot-usage.md#feature-feedback-and-version-checkpoints); no automatic dependency selection, scheduling or product pilot is implied.

## Start from another computer or cloud workspace

Obtain the private bundle using your normal authorized GitHub login. `main` contains the published factory, not unmerged candidate changes. Prefer regular skill installation above, or clone the full bundle for manual use.

```sh
git clone --branch main --single-branch https://github.com/seifsg/ai-software-factory.git
```

Use a new destination; do not run this over an existing checkout. Replace the bundle path in the starter prompt with its actual absolute path there. Preserve the full directory structure: copying only `SKILL.md` omits the controller, seven adapted methods and references.

A remote workspace cannot read `C:/work/...` on this PC. It needs its own checkout, permissions, runtimes, browser tools and authenticated review route. Cloud delivery has not been demonstrated by this pilot; if its environment cannot run the reviewer, handoff remains blocked.

## Hosts

[Hosts](hosts.md) owns per-host install routes, skill syntax, hooks, reviewers and what was checked where. A cloud-hosted session needs both repositories and the required tools provisioned inside that environment; cloud delivery has not been demonstrated.

## The first controller commands

These Windows commands are read-only examples. Replace both paths with your actual factory checkout and target project; the historical demonstration paths need not exist on your computer. They do not begin another build:

```powershell
Set-Location 'C:\work\ai-software-factory'
py -3 -m safe_engine --help
py -3 -m safe_engine --project 'C:\work\safe-engine-pilot-20261001\app' discover
```

For the selected target, check `status` when a run exists; add `--ticket <key>` for its namespaced state. Otherwise discover and prepare it. `discover` returns a proposal; `preflight --profile <profile.json>` inspects capabilities without launching tests or the app. [Current usage](pilot-usage.md) and [ticket usage](ticketing.md) own version-2 commands; [fixture commands](../examples/pilot-commands.md) remain a historical version-1 demonstration.

To resume in a fresh chat, paste:

```text
Read C:/work/ai-software-factory/.agents/skills/safe-engine/SKILL.md.
Resume the existing Safe Engine run in [absolute target project directory].
Read the saved original task, profile, phase, history and artifacts. Check
evidence freshness and continue from the next valid step. Do not replace the
task record, reinitialize the run or treat old passing evidence as current.
When ticketed, select its key/session and refresh canonical scope/activity;
compare the confirmed revision before dependent work. Preserve legacy pins/state.
Show me the saved progress and remaining work before continuing.
```

## Improve the factory during a build

Stay in the app-building chat and explain the behavior you want corrected:

```text
Read C:/work/ai-software-factory/.agents/skills/improve-factory/SKILL.md.
The factory did [what happened]. It should do [expected behavior].
Preserve this app's progress. Checkpoint it, repair the factory in isolation,
get an independent assessment, and resume through the supported workflow.
```

Replace the path if the bundle lives elsewhere. If your agent discovers the skill, ask for improve-factory directly in its syntax ([hosts](hosts.md)). For a reusable personal installation, follow [Install Improve Factory](install-improve-factory.md). It loads the complete canonical bundle and preserves an active run's recorded version. The controller's broader host limitations above still apply.

The selected policy holds affected app work during repair; only demonstrably independent work may continue. The parent keeps app ownership and passes a durable context packet to delegates. Exact bundle versions and evidence matter: incompatible changes may require a new reviewed run in a fresh app worktree, preserving the old run. The [live-session procedure](../.agents/skills/improve-factory/references/live-session.md) explains actual 0.1.0 recovery limits. No automatic state migration or uninterrupted mid-run upgrade is claimed.

## Making the delivery coordinator invocation permanent

| Option | Benefit | Tradeoff |
|---|---|---|
| A — Explicit starter pointing to one bundle | Works without global changes; keeps one source of truth | Paste the starter in each new session; environment prerequisites still apply. |
| B — Personal host adapters pointing to the bundle | Short invocation across local projects | Requires installation for each host and machine; cloud is separate. |
| C — Per-project host adapters with a pinned bundle | Each repository carries a repeatable entrypoint | Adds configuration and version maintenance to every project. |

**Current selection, 3 October:** Seif requested the factory itself as a regular reusable skill, selecting B for this delivery under his implementation delegation. [Install Safe Engine](install-safe-engine.md) for the short invocation. Manual option A remains available; C is not selected. Maintenance installation is separate and optional.
