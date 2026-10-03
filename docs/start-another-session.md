# Start Safe Engine in another session

The first thing to give the agent is the Safe Engine entry skill and your actual task. The agent then runs the controller commands. There is no `safe-engine start` daemon or one shell command that independently builds an app.

## Regular skill: recommended entry

Install [Safe Engine itself](install-safe-engine.md) from GitHub `main`, path `skills/safe-engine`, once per host. Then call `$safe-engine Build [my app or feature] in [absolute project directory]` in Codex, or `/safe-engine` after personal Claude Code installation. The adapter loads the complete factory and saves the target's selected bundle for safe resume. `improve-factory` is for changing the factory; it is not required as a separate installation for app delivery.

## Manual bundle: paste this first on this computer

Start a Codex chat in the target project. Replace the two bracketed fields below. The factory bundle already exists at `C:/work/ai-software-factory`.

```text
Read and follow C:/work/ai-software-factory/.agents/skills/safe-engine/SKILL.md
and its linked usage guide. Use that existing factory bundle.

Target project: [absolute project directory]
Task: [the app or feature I want, and what success looks like]

First inspect the real project and any .factory/state.json. Resume an existing
run instead of initializing it again. For a new run, discover the project,
prepare the acceptance criteria and real check commands, and show me the brief
and any product or design decisions that still need my choice.

Follow analyze-start, including the ASCII charts, then get-ready-to-code and
the per-todo 0–4 loop. Work autonomously within the agreed scope and recorded session contract.
Ask essential preferences once only when not already answered. Under delegated
autonomy, continue until the agreed verified outcome without artificial credits,
correction allowances, fixed retry ceilings or session deadlines. Honor my explicit stops.
Read each complete skill and its references, not just its name. Before planning,
compare three strong approaches and recommend one with reasons. Preserve my
chosen direction and my delegated/reserved decision authority. For a new app,
save an original plan, research competitors/features/visuals using research-market,
then revise the plan before coding. Carry these methods,
decisions, real artifacts, diagnostic progress and actual constraints into every resume or delegation.
Batch completed capabilities; use affected feature checks as feedback, then full
version QA. Keep detailed method records durable and progress updates concise.
Inspect worthwhile improvements, validate final QA,
and obtain a fresh independent review before the checked handoff.
For any authorized PR, always execute how-to-make-a-pr, then the full
how-to-review-a-pr on a separate instance. Keep its task/owner handoff,
visual description, five review passes and detailed comment mandatory.
The local controller review does not replace the PR review. Missing required
project settings or access block PR completion after discovery; keep independent
local build, QA and owner-test delivery moving. Leave the PR draft for me.

Keep the work visible: show the plan before coding, give concise stage updates,
open the running app when available, and show actual browser results and the
final review. Continue without waiting at routine progress updates. Ask when
an owner-reserved decision, actual missing access or my explicit stop prevents dependent progress.
Do not choose a different example or change the product requirements for me.
```

If you start in the factory repository itself and Codex discovers the skill, the short form is `Use $safe-engine to implement [task] in [absolute project directory]`. The explicit file path above also tells a fresh session where the complete bundle lives. `$safe-engine` belongs in the chat; it is not a PowerShell command.

For the Codex CLI, launch it in your target project with `codex -C <target-path> --add-dir <bundle-path>`, then paste the starter. Replace both paths with real directories. The added directory makes the bundle accessible in the session; it does not make every skill globally installed. These flags were checked against the installed CLI's help.

Codex discovers repository skills in `.agents/skills` within the repository scope. A skill in a different project is not automatically global. [Official Codex skill documentation](https://learn.chatgpt.com/docs/build-skills).

## What the agent needs before it can proceed

- The complete factory bundle, Python 3.11+, Git, and access to the target project.
- An authenticated `codex` CLI on PATH for the current independent reviewer.
- The target project's actual test tools. Browser work needs a browser driver and runnable app.
- An agreed task, observable acceptance, protected check files, and recorded authority and completion boundaries. The first demo's finite allowance is historical and does not govern continuous execution; actual command watchdogs still detect stuck processes.

The [session contract](../.agents/skills/safe-engine/references/session-contract.md) preserves delegated and reserved choices. The agent makes in-scope delegated choices; unresolved owner-reserved choices stay yours. A prompt does not install missing dependencies or grant access outside the session's permissions. Keep the factory bundle unchanged during a target run; editing its instructions changes an acceptance input.

## Start a brand-new application

Add this to the first message when the target does not exist:

```text
This is a new application. Start with a minimal project baseline in the target
directory. Preserve any existing files. Inspect the repository before choosing
the stack; if it is empty and I have not chosen the stack, give me three options
with one recommendation. Choose within my explicit delegation; otherwise ask
for the required owner choice. Do not reopen choices I already made.

Define the agreed behavior and check commands before feature implementation.
Ignore .factory/, establish a clean Git baseline, then initialize Safe Engine.
Show what belongs to bootstrap setup and what belongs to the controlled build.
```

The controller requires a Git project with a clean baseline and real configured checks. An empty folder alone cannot pass initialization. The agent performs that setup before the controlled analysis/plan/build cycle. For large apps, plan bounded coherent capabilities; the pilot supports partial feature feedback and full version checkpoints but does not automatically select dependencies or schedule arbitrary projects.

## Start from another computer or cloud workspace

Obtain the private bundle using your normal authorized GitHub login. The complete factory is merged on `main`. Prefer the regular skill installation above, or clone the full bundle for manual use.

```sh
git clone --branch main --single-branch https://github.com/seifsg/ai-software-factory.git
```

Use a new destination; do not run this over an existing checkout. Replace the bundle path in the starter prompt with its actual absolute path there. Preserve the full directory structure: copying only `SKILL.md` omits the controller, seven adapted methods and references.

A remote workspace cannot read `C:/work/...` on this PC. It needs its own checkout, permissions, runtimes, browser tools and authenticated review route. Cloud delivery has not been demonstrated by this pilot; if its environment cannot run the reviewer, handoff remains blocked.

## Codex and Claude Code

| Session | First action | Current status |
|---|---|---|
| Codex, local | Paste the explicit-path starter, or invoke `$safe-engine` when discovered | The local delivery cycle was demonstrated on the recorded fixture. |
| Claude Code, local, with Codex CLI installed | Add the factory directory, then ask Claude to read the same entry skill by its path | Documented manual loading route. No complete Claude-builder run has been verified here. Review still uses Codex. |
| Claude Code without Codex CLI | Can read the methods, but the current controller cannot complete its independent review | A Claude-native review adapter is not implemented. |
| Cloud-hosted session | Provision both repositories and the required tools inside that environment | Not demonstrated; local installation does not establish cloud compatibility. |

For an installed Claude Code CLI, launch from your target project:

```powershell
# First Set-Location to your actual target project.
claude --add-dir 'C:\work\ai-software-factory'
```

Then paste the same explicit-path starter. For an existing Claude Code session, `/add-dir C:/work/ai-software-factory` grants access to the bundle. This repository uses `.agents/skills`, while Claude's native discovery uses `.claude/skills`; adding file access does not create a `/safe-engine` command from this bundle. Install the portable `skills/safe-engine` folder in Claude's skill directory to obtain that command. [Claude CLI reference](https://code.claude.com/docs/en/cli-reference), [Claude skills](https://code.claude.com/docs/en/skills).

Claude Code was not available on PATH when this guide was checked on 2 October 2026. These are official-documented launch instructions, not a claim that a Claude-only factory run passed.

## The first controller commands

On this Windows computer, these read-only commands are complete and runnable against the existing demonstration. They do not begin another build:

```powershell
Set-Location 'C:\work\ai-software-factory'
py -3 -m safe_engine --help
py -3 -m safe_engine --project 'C:\work\safe-engine-pilot-20261001\app' discover
```

For the selected target, the agent checks `status` when `.factory/state.json` exists; otherwise it discovers and prepares the new run. `discover` returns a proposal. It does not write a usable profile or execute the application. The [filled fixture commands](../examples/pilot-commands.md) show initialization and every subsequent operation with concrete paths.

To resume in a fresh chat, paste:

```text
Read C:/work/ai-software-factory/.agents/skills/safe-engine/SKILL.md.
Resume the existing Safe Engine run in [absolute target project directory].
Read the saved original task, profile, phase, history and artifacts. Check
evidence freshness and continue from the next valid step. Do not replace the
task record, reinitialize the run or treat old passing evidence as current.
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

Replace the path if the bundle lives elsewhere. If the host discovers the skill, `$improve-factory` is the shorter invocation. For a reusable personal installation, follow [Install Improve Factory from GitHub](install-improve-factory.md): its portable folder enables `$improve-factory` in Codex or `/improve-factory` in Claude Code after discovery. It loads the complete canonical bundle and preserves an active run's recorded version. The controller's broader host limitations above still apply.

The selected policy holds affected app work during repair; only demonstrably independent work may continue. The parent keeps app ownership and passes a durable context packet to delegates. Exact bundle versions and evidence matter: incompatible changes may require a new reviewed run in a fresh app worktree, preserving the old run. The [live-session procedure](../.agents/skills/improve-factory/references/live-session.md) explains actual 0.1.0 recovery limits. No automatic state migration or uninterrupted mid-run upgrade is claimed.

## Making the delivery coordinator invocation permanent

| Option | Benefit | Tradeoff |
|---|---|---|
| A — Explicit starter pointing to one bundle | Works without global changes; keeps one source of truth | Paste the starter in each new session; environment prerequisites still apply. |
| B — Personal host adapters pointing to the bundle | Short invocation across local projects | Requires installation for each host and machine; cloud is separate. |
| C — Per-project host adapters with a pinned bundle | Each repository carries a repeatable entrypoint | Adds configuration and version maintenance to every project. |

**Current selection, 3 October:** Seif requested the factory itself as a regular reusable skill, selecting B for this delivery under his implementation delegation. [Install Safe Engine](install-safe-engine.md) for the short invocation. Manual option A remains available; C is not selected. Maintenance installation is separate and optional.
