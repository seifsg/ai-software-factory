<div align="center">

# 🏭 AI Software Factory

**Your coding agent, run like a software team. Idea in, proven draft PR out.**

Research, tickets, analysis, plan, build, QA, review and PR, in that order, every time.

![Agents](https://img.shields.io/badge/agents-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Cursor%20%C2%B7%20more-6E56CF)
![Modes](https://img.shields.io/badge/modes-Fast%20%C2%B7%20Lucky%20%C2%B7%20Safe-2EA44F)
![OS](https://img.shields.io/badge/OS-Windows%20%C2%B7%20macOS%20%C2%B7%20Linux-0A66C2)
![Python](https://img.shields.io/badge/python-3.9%2B-3776AB)

**[Quick start](#-quick-start) · [Use it](#-use-it) · [Update](#-update) · [Troubleshooting](#-troubleshooting) · [FAQ](#-faq)**

</div>

Coding agents jump straight to code. They skip the research, forget the ticket, test nothing and tell you it works. More instructions do not fix that, because an agent can ignore any instruction.

The factory **enforces** the process. Hooks block source edits until the ticket, analysis and plan are recorded. Every run ends in a draft pull request with before/after proof and a list of what is still unverified. You merge.

Plain progress reports show per-ticket spend, worth and checked PNG pictures: [report command](docs/owner-reports.md).
New requests take priority and may replace the objective. Answer or deliver with only the action's necessary checks; resume earlier work only if compatible. Preserve previews unless asked otherwise. [Delivery limits](docs/hosts.md#message-delivery).
Local run timing, observed task/helper spans, rework and attributable host-session usage analytics (distinct from owner reports): [run metrics](docs/run-metrics.md). Fast runs mark observed T-number boundaries with `fast_gate.py metrics task --key <run> --task-id T1 --state start|finish|fail|cancel|resume`; reused gate keys keep separate metrics instances.

## ⚡ Quick start

**You need:**

- A coding agent. Claude Code, Codex and Cursor get the installer and gate hooks; any agent that reads a `SKILL.md` file works ([hosts](docs/hosts.md)).
- Git and Python 3.9 or newer (`python`, `python3` or `py -3` on Windows). Missing ones: an agent given the install prompt below installs them from official sources.
- Read access to this repository and the GitHub CLI signed in (`gh auth login`). Git fetches the factory over HTTPS with those credentials, and runs use `gh` for GitHub tickets and draft PRs.
- Windows with Claude Code: Git Bash (part of Git for Windows), because its hooks run in a POSIX `sh`.

**Then:**

1. **Install.** Paste this to your coding agent, or use the [install options](#-install-options):

   ```text
   Install the AI Software Factory for this agent from https://github.com/seifsg/ai-software-factory.
   Clone it, follow docs/install.md and run its installer for this agent.
   ```

2. **Check it.** Start a new session. Your agent should list or autocomplete `safe-engine`. Not there: [troubleshooting](#-troubleshooting).
3. **Build.** Type this in your agent's chat, not in a terminal, as `/safe-engine ...` in Claude Code, `$safe-engine ...` in Codex, or "use safe-engine to build ..." in Cursor:

   ```text
   safe-engine Build [app or feature] in [absolute project directory]. Success means [observable outcome].
   ```

4. **Answer, watch, merge.** Answer its questions, follow the progress card, then review the draft PR and merge it.

Already have code? Point it at that directory. Feature runs analyze the existing code and every consumer before planning (`analyze-start`).

Optional polish is scored and collected in the epic's existing **Finishing touches** follow-ups. `fast_gate.py fix-round --file <report.json> --finding F1` selects worthwhile repairs; `--finishing-authority` records an explicit batch request. Selected work needs resolution evidence or owner cancellation before completion. Required quality stays mandatory. See [worth-it rounds](docs/worth-it.md) for the shared Fast/Safe report and commands.

## 🎬 What a run looks like

New runs use `fast_gate.py checks` to record reasoned hidden-check selection, actual runtime names and parsed/executed proof. Visual-only ports keep likeness plus the suite. See [hidden checks](docs/hidden-checks.md).

Record refusals collect independent problems with repair examples; explicit verdict fields distinguish a failed check from explanatory wording. See [record diagnostics](docs/record-diagnostics.md).

Browser journeys use a fixed instant and timezone before navigation. Each declared source calls `fixedBrowserPage` or `fixedBrowserClock`; run `node skills/safe-engine/scripts/journey_clock_lint.mjs <manifest.json>`. See [fixed browser time and affected tests](docs/journey-clock.md).

Illustrative example:

```text
safe-engine Build a habit tracker in /home/me/habits. Success means a signed-in user adds a habit and sees a streak.
```

1. Researches three competitors and writes a feature matrix with opportunities.
2. Asks you about size, features, approach and stack: one round for a POC, more for an MVP.
3. Reads the backlog, then opens an epic and outcome sub-issues in To do, each with a definition of done.
4. Analyzes requirements and consumers, then writes a plan whose todos become each ticket's checklist. Before each build wave, a fresh agent writes the hidden checks for the criteria that wave builds.
5. Writes the design brief and the schema decision.
6. Builds every checklist item through a check-change-check loop and ticks it once it works.
7. Runs the app through every requested journey and its most likely failure; the hidden checks decide each criterion.
8. Opens a draft PR with before and after for every outcome and what is unverified. Tickets wait in Ready for QA until you merge.

While it works, the gate shows a card after every step and finished todo (illustrative):

```text
🏭 portal-poc · 🔨 build · step 6/8 · ⏱️ 42m total, 5m in step
🎫 #12 Download & SEO   ▰▰▱ 2/3 · run 5/9
✅ SEO: title and description on every page
🔨 NOW  Download button
     → click it and the PDF saves
⏭️ NEXT Contact form
```

```mermaid
flowchart LR
  A[Request] --> B[Research] --> C[Questions] --> D[Tickets]
  D --> E[Analyze] --> F[Plan] --> G[Design and schema]
  G --> H[Build] --> I[Use it] --> J[Review] --> K[Draft PR] --> L[You merge]
```

## 🏆 Why it works

- 🔒 **Enforced, not suggested.** A gate and host hooks deny code edits until earlier steps pass, and push back when the agent tries to stop mid-run. The gate keeps its state outside your project, so nothing written there can switch it off.
- 🛑 **Destructive commands refused.** During a run, hooks deny recursive deletes outside the project, force pushes, `git clean -x`, `DROP` or `TRUNCATE`, database wipes and production migrations. You run those yourself or pick another approach.
- 📣 **Progress you can see.** The card above, once per change, plus any question waiting on you. When nothing changed, a hook spends under 0.1 ms on it.
- 🔎 **Research before code.** New products and big features start with competitors, a feature matrix, opportunities and stack options.
- ❓ **Questions that fit the size.** A POC builds exactly what you asked and asks only what the request leaves open. An MVP researches launch gaps, suggests features you did not think of and ships analytics and in-app feedback. Answers are recorded and binding.
- 🎫 **A living backlog.** Every run reads it, cleans up issues after merged or closed PRs, and opens an epic with outcome sub-issues; follow-ups update existing tickets instead. Each ticket has a definition of done and a checklist; an item is ticked only after it works. Tickets move through To do, In progress, Dev done and Ready for QA; your merge makes them Done.
- 💸 **The cheapest model that can do the job.** Delegated work runs on its role's tier: light jobs (commands, comparisons) on a small model, building and review on a larger one; a job that fails its gates twice moves one tier up. On Claude Code these are the plugin's `safe-engine:<role>` agents; ask in chat to override the model or effort ([delegation](docs/hosts.md#delegation)).
- 🎚️ **Right-sized.** Fast by default, Lucky for quick tries, Safe for work that must not break. Small tasks and follow-ups take a light lane: no analysis step, a short plan, the same checks.
- ⚡ **Bounded Fast work.** Plan required proof and useful helper jobs, keep short tasks local, pass compact context, preflight fragile tools and batch repairs before final capture. Reuse intact same-candidate evidence; stop speculative expansion once required checks pass. Time savings never waive acceptance, security, independent checks or owner stops ([proof](docs/show-first.md), [repair batches](docs/worth-it.md)).
- 📖 **Conditional detail.** The common product bar remains in every run. Logging/security implementation detail and visual PR capture instructions load when their named situation applies; the pointers in the owning methods keep those obligations visible. Preflight and delegate handbacks retain complete command, session and exit receipts.

The gate loads optional command parsers only for the requested command; help and invalid input retain the complete CLI. State checks and pinned routing still run. Host test setup is documented in [hosts](docs/hosts.md#local-test-hosts).
- 🧪 **Proof, not promises.** Every requested item traces to a criterion, a checklist item and proof. In product and feature runs, a fresh agent writes a check for every criterion before the build, from the tickets and plan alone; the builder never sees them, and any FAIL sends the work back. Then a done-run with real controls and logs, and a PR showing before and after for every outcome, which the gate reads before the run can finish. MVPs and production slices also record a secret scan, a dependency audit and static analysis. Safe adds manual QA, tests and an independent reviewer.
- 🩹 **Root causes, not patches.** A bug or edge case is fixed where it starts: impossible by design, or rejected loudly where data enters. No silent defaults. A big or risky refactor waits for your yes.
- 🎨 **A product bar.** Accessible, responsive UI, clear copy, public-page SEO and a designed schema. Every UI run gets a fresh agent's check against ten UX rules before the gate lets it finish. Non-production builds show their environment and label sample data.
- 🧑‍⚖️ **Humans stay in charge.** Draft PRs only. It never merges, releases or deploys.
- 🌍 **Any agent, any OS, any codebase.** Games, web, mobile and desktop apps, services, tools and libraries.

## ⚖️ Instructions alone vs the factory

| | Instructions alone | AI Software Factory |
|---|---|---|
| Skipping steps | The agent can skip any step | Code edits are denied until ticket, analysis and plan pass the gate |
| Stopping early | The agent can stop and say "done" | Stopping mid-run is blocked once, with the next step named; waiting on background agents costs no extra turn where the host reports them |
| Dangerous commands | The agent can run them | Deletes outside the project, force pushes and database wipes are denied during a run |
| Proof | The agent's word | Hidden checks the builder never saw, done-run results and logs; Safe adds QA, tests and independent review |
| Review | The same agent grades itself | Safe: a different agent reviews from raw evidence |
| Process size | One size for every task | Fast, Lucky or Safe |
| Output | Changes in your working tree | Ticket plus draft PR with before and after for every outcome |

## 🚀 Use it

Type requests in your agent's chat, in its syntax: `/safe-engine` in Claude Code, `$safe-engine` in Codex, "use safe-engine to ..." in Cursor. The examples below leave that prefix out.

**Pick a mode.** Add `lucky` or `safe` after the skill name; no mode means Fast.

| | 🏃 Fast (default) | 🍀 Lucky | 🛡️ Safe |
|---|---|---|---|
| Best for | Everyday features and products | Quick experiments | Work that must not break |
| Research and questions | New products and big features | Skipped, sensible defaults | Always |
| Planning | Full analysis and plan | One short pass | Full, plus a stop to review the file list |
| Enforcement | Gate and hooks | Gate and hooks | Python controller |
| Checks | Each checklist item, hidden checks, then a done-run | Each checklist item, hidden checks, then a done-run | Each item, manual QA, tests, verify, independent review |

```text
safe-engine Build [app or feature] in [absolute project directory]. Success means [observable outcome].
safe-engine lucky Fix [bug] in [absolute project directory].
safe-engine safe Add [feature] to [absolute project directory]. Success means [observable outcome].
safe-engine Resume [absolute project directory]
safe-engine Verify [absolute project directory]
safe-engine Promote [absolute project directory]
improve-factory The factory did [observed]; expected [result].
```

- **Resume** reads the ticket and the work record, then continues the first unfinished step.
- **Verify** adds manual QA and tests to a Fast or Lucky run. **Promote** moves it to Safe on the same epic.
- **improve-factory** repairs the factory itself when it skipped a step or misbehaved. Product bugs go back to `safe-engine`.
- **Watch it live:** once per run the agent starts `fast_gate.py view --project <dir>` and gives you a local link with the run's steps, todos, sessions and anything ready to try. `--all-projects` shows every project on this machine.
- **Unattended:** `fast_gate.py orchestrate paperclip --agent claude|codex --company <id> --project <dir>` sets up an orchestrator to start factory sessions from its tickets ([orchestrators](docs/orchestrators.md)).
- **Your part:** answer its questions (the run waits, and your answers bind it), review the draft PR and merge. Before a Fast or Lucky PR it offers an optional Safe check: manual QA, tests and an independent review.

## 📦 Install options

The installer, from a clone. Replace `claude` with `codex`, `cursor` or `other`, and `python` with `python3` or `py -3` where needed:

```bash
git clone https://github.com/seifsg/ai-software-factory.git
python ai-software-factory/skills/safe-engine/scripts/fast_gate.py install --host claude
```

- `claude` enables the plugin (skills and gate hooks) with auto-update, installs it with Claude Code's own CLI and checks `claude plugin list`. It follows release tags. Start a new session. No CLI found or the install failed: it exits 1 and names the fix. It looks on `PATH`, in `~/.local/bin` and in the Windows desktop app's `%APPDATA%\Claude\claude-code` folder; elsewhere, set `SAFE_ENGINE_CLAUDE` to the CLI's path.
- `codex` and `cursor` copy the `safe-engine` and `improve-factory` skills into `~/.agents/skills` and write the gate hooks. Codex asks you to trust them once in `/hooks`.
- `other` copies those skills only; wire the hooks by hand ([hosts](docs/hosts.md#other-agents)).
- `--project <dir>` installs into one project instead of your user folders.
- `--channel stable|edge` sets this machine's channel: `stable` (the default) follows the newest verified release, `edge` follows `main`.
- `--no-auto-update` turns the daily self-update off; `--codex-home <dir>` writes Codex hooks into that `CODEX_HOME` (an orchestrator's own Codex).

What gets installed, per host:

| Host | Skills | Gate hooks | Delegate agents |
|---|---|---|---|
| `claude` | plugin `safe-engine@ai-software-factory` (`safe-engine`, `improve-factory`) | plugin hooks | plugin agents `safe-engine:runner`, `analyst`, `maker`, `builder`, `reviewer` |
| `codex` | `~/.agents/skills/` | `~/.codex/hooks.json` (trust once in `/hooks`) | named in each brief |
| `cursor` | `~/.agents/skills/` | `~/.cursor/hooks.json` | named in each brief |
| `other` | `~/.agents/skills/` | by hand ([hosts](docs/hosts.md#other-agents)) | named in each brief |

Machine data lives in `~/.safe-engine/` (`install.json`, pinned bundles, run state, `logs/gate.log`); each project gets `.factory/`, kept out of Git.

Check what you run: `fast_gate.py version` prints the version, commit, channel, install route and release digest; `fast_gate.py verify` lists every file that differs from the release manifest. What changed: [CHANGELOG](CHANGELOG.md); what to do on upgrade: [UPGRADING](UPGRADING.md).

Claude Code without a clone. This route leaves auto-update off: turn it on in `/plugin` under Marketplaces, or [update by hand](#-update).

```bash
claude plugin marketplace add https://github.com/seifsg/ai-software-factory.git
claude plugin install safe-engine@ai-software-factory
```

Details: [install](docs/install.md) · [hosts](docs/hosts.md).

## 🔄 Update

Updates arrive as releases: a tag on `main` whose files are checked against its sha256 manifest before it is pushed. Clone installs and new projects check it again before taking it.

| Installed with | How it updates |
|---|---|
| Claude Code, through the installer | On its own: during a session Claude Code fetches a new release; `/reload-plugins` or a new session loads it |
| Claude Code, right now (any route) | `claude plugin marketplace update ai-software-factory`, then `claude plugin update safe-engine@ai-software-factory`, then a new session |
| Codex, Cursor, other, installed from a clone | On its own: at most once a day, the first session start moves your clone to the newest release that verifies (detached at its tag) and reruns your install. A failed install rolls back to the previous revision. A clone with local changes, on another branch, at a commit it did not install, used by an open run or offline is left alone and the gate log says why ([hosts](docs/hosts.md#updates)); to keep a hand-picked commit, install it with `--no-auto-update` |
| Codex, Cursor, other, right now or opted out | In your factory clone `git fetch --tags` and `git checkout vX.Y.Z` (the newest tag), then run the same `fast_gate.py install --host ...` again. It replaces only the factory's own files and hook entries |

After an update or a rollback, the next `start`, `status` or `version` shows one notice with the old and new version. Turn the daily update off with `SAFE_ENGINE_NO_UPDATE=1` in your environment, or install with `--no-auto-update`.

- **Switch channel:** rerun the install with `--channel edge` to follow `main`, or `--channel stable` to return to releases. Claude Code has no channels: edge changes what new projects pin ([hosts](docs/hosts.md#updates)).
- **Roll back by hand:** in your clone `git checkout vX.Y.Z` (the release you want), then rerun the install with `--no-auto-update` so the daily update keeps it there. Claude Code serves one version: run an older release with `claude --plugin-dir <clone at that tag>/skills`, the plugin disabled.

**Active runs stay pinned.** New automatic selections use the newest verified release (`main` on edge or before the first release). `resolve_bundle.py --project <dir> --new-run` refreshes only before a new run; ordinary resume stays offline. Explicit `--ref`/`--bundle` pins and older receipts with unknown pin intent stay fixed. `fast_gate.py start` prints selected/latest versions, reports failed release checks and executes the selected gate. Its project commands and hooks follow that run's saved identity, including session-bound or absolute-path work outside the project directory. Tool calls spanning different factory versions must be split. A Fast/Lucky run closed in the gate home permits the next selection even if its project mirror is missing or stale. A named Safe run with a confirmed cancellation or checked handoff releases selection for the next ticket. Receipt-less bare starts are legacy use, not a freshness guarantee. Pin changes need `improve-factory`; never edit an active receipt.

Factory maintenance uses an immutable selected runner and a separate editable candidate. The candidate can start from an explicitly approved unmerged dependency; that does not release or adopt it. Complete and commit planned changes before final candidate-bound proof. Use Prove when the selected runner supports it; otherwise run the required full suite directly on the committed candidate under its recorded gate workflow, retaining runner, commit, inputs, command, log and result. See `improve-factory` for the maintenance flow.

## 🧹 Uninstall

- **Claude Code:** `claude plugin marketplace remove ai-software-factory` removes the marketplace from your settings and uninstalls its plugin. The installer kept your earlier settings as `~/.claude/settings.json.bak-before-safe-engine`.
- **Codex, Cursor, other:** delete `safe-engine` and `improve-factory` from `~/.agents/skills` (or `<dir>/.agents/skills`), then remove the hook entries naming `run-gate` or `fast_gate` from `hooks.json` in `~/.codex` or `~/.cursor` (or `<dir>/.codex`, `<dir>/.cursor`). Delete your factory clone too.
- **Data:** `~/.safe-engine/` holds the pinned factory copies, the install record (`install.json`, with the channel) and the gate's run state; delete it once no project has an unfinished run. Each project keeps a `.factory/` folder with its work records, kept out of Git; delete it when you no longer need them.

## 🩺 Troubleshooting

| Symptom | Fix |
|---|---|
| `safe-engine` does not show up | Start a new session. Claude Code: `claude plugin list` must show `safe-engine@ai-software-factory`; enabled in settings is not installed. Missing: `claude plugin install safe-engine@ai-software-factory --scope user` (or `/plugin`), then a new session; the run card's `Hooks:` line names this too. Still missing: ask the agent to read the installed `safe-engine/SKILL.md` by path (Codex, Cursor: `~/.agents/skills/safe-engine/SKILL.md`) |
| Clone or install asks for a password or fails with "not found" | You need read access to this repository. Run `gh auth login` so Git uses your GitHub credentials over HTTPS |
| Claude Code on Windows: hooks fail | Install Git for Windows (the hooks run in its `sh`, Git Bash), then start a new session |
| Codex ignores the gate | Trust the factory's hooks once in `/hooks` |
| "Newer layout" or "Incomplete factory bundle" | Your install is older than the factory it fetched: [update](#-update) |
| Which factory am I on? Did my install change? | `fast_gate.py version`, then `fast_gate.py verify`: it names every changed, missing or extra file. The update's result is the last `update` line in `~/.safe-engine/logs/gate.log` |
| Updates stopped: "no release verifies", "not on main" or "would clobber existing tag" | A release tag failed its check or moved on the remote, so the update kept your copy. Report it ([issues](https://github.com/seifsg/ai-software-factory/issues)); never force-fetch tags |
| Claude Code: "Remote branch vX.Y.Z not found" | The release was merged but its tag is not pushed yet; your installed copy stays. It updates once the tag exists |
| An edit or command is refused during a run | Source edits wait until the ticket and plan pass. Destructive commands are yours: run them yourself or ask for another approach |
| The agent will not stop | A run blocks the first stop and names the next step; stopping again right after passes. To end a run early, ask the agent to close it with your reason |
| The agent's `gh` commands break in PowerShell | Have it run them in Git Bash: PowerShell 5.1 breaks `{owner}/{repo}` placeholders and nested quotes |
| Missing on another machine or in a cloud session | Install there too; cloud sessions load the skills committed to their repository |
| A run started on another machine reads as lost here | Bring the project with its `.factory/` and the run's bundle, then ask the agent to bring the run in, naming the folder it lived in (`fast_gate.py rehome --project <here> --from <old folder>`). Check the card against `status` on the old machine, then retire the copy there with `close --abandon` |
| The factory itself misbehaved | `improve-factory The factory did [observed]; expected [result].`, or [open an issue](https://github.com/seifsg/ai-software-factory/issues) |

## 🧰 Skills

| Skill | Job |
|---|---|
| `safe-engine` | Runs delivery in Fast, Lucky or Safe mode; holds the work rules and product bar |
| `research-market` | Competitors, feature matrix, opportunities, stack and architecture options |
| `analyze-start` | Understands the code and every consumer before changing it |
| `get-ready-to-code` | Files, critique, phases, todos and the whole plan |
| `ux-quality` | Ten UX rules (map, navigation, hierarchy, disclosure, labels, cost, states, access, look, speed) judged by fresh eyes; copy; public-page SEO |
| `database-schema` | Access patterns, three designs, chosen schema, indexes, migrations |
| `deep-review` | Bug hunt plus change-guard, compliance, security, performance and journey lenses |
| `ticketing` | Backlog upkeep: epic and outcome sub-issues with before/after, a definition of done, a checklist, status, priority and an activity timeline |
| `how-to-make-a-pr` | Draft PR with ticket link, before and after for every outcome, and what is unverified |
| `improve-factory` | Repairs or improves the factory itself without disturbing active runs |

Each skill lives in `.agents/skills/<name>/` and stands alone.

## 🤖 Supported agents

- **First-class** (installer, gate hooks, Safe reviewer): Claude Code, Codex, Cursor.
- **Supported:** GitHub Copilot, Gemini CLI, OpenCode, and any agent that can read a `SKILL.md` file.

Details per agent: [hosts](docs/hosts.md).

## ❓ FAQ

**Does it push to main, merge or deploy?**
No. It opens draft PRs. Humans mark them ready, merge and release.

**Does the gate judge quality?**
No. It proves each step was recorded, not that it was good. Quality comes from the methods, the hidden checks and the done-run; Safe adds tests and an independent review.

**Which tracker?**
GitHub Issues are checked online. Other trackers are recorded and marked unverified.

**Can hooks catch everything?**
No. They see tool calls, not intent: a command run from inside a script passes. The work record and the done-run carry the rest.

## 🛠️ Work on the factory

Design ports use `fast_gate.py start --design-port`, then `fast_gate.py design --input <coverage.json>` before plan. `fast_gate.py design --candidate` identifies the source for a fresh judge; `fast_gate.py design --review <review.json>` records matched screenshots and element observations. `fast_gate.py design` reports completed, partial, missing and approved-cut counts against the fixed original inventory ([usage](docs/design-coverage.md)).

Rules live in [AGENTS.md](AGENTS.md); changes go through `improve-factory`. Report problems as [issues](https://github.com/seifsg/ai-software-factory/issues).

```bash
python tests/run.py
```

- `python tests/run.py --changed` runs only the tests your diff touches; run the full suite before any push.
- Adding, moving or deleting a factory file: `python scripts/package_skill_entries.py`, then `--check` before pushing.
- Every PR adds a line to [CHANGELOG](CHANGELOG.md), and updates this README and `docs/` when it changes a command, flag, host, install or update step, release step, skill or folder; `tests/test_docs_sync.py` fails until they match.
- Releases are local, no CI: `python scripts/release.py cut X.Y.Z`, merge the release PR, `python scripts/release.py prove vX.Y.Z`, tag, then `python scripts/release.py publish vX.Y.Z`. Publish reuses intact matching suite proof or runs the complete suite ([releasing](docs/releasing.md)).
- Method byte budgets: `python scripts/token_report.py --against origin/main` compares file-text proxies for whole runs, overlapping phases and optional conditions. These are neither observed context nor billed model tokens.
- `python -m evals run` scores the factory against a plain agent ([evals](evals/README.md)). Windows evals require confirmed job ownership and descendant cleanup; isolated checks receive the same snapshotted ownership helper.

The gate loads command arguments from `fast_cli.py` only for CLI calls; tool hooks retain their direct fast path.

Parallel local stacks use `fast_gate.py lane start`, `lane status` and `lane stop` with explicit project, lane name and fixed ports. They retain owned descendants, confirm shutdown before reporting cleanup, isolate supported caches and use short browser profiles. Screenshot cleanup attempts every acquired process and preserves artifacts when shutdown is unconfirmed. Installed entries preserve child arguments after `--`; commands, cleanup retries and platform limits are in [hosts](docs/hosts.md#lane-resources).

## 🗂️ Layout

For finite helper work, [quiet waits](docs/waiting.md) records completion identities with `wait --add`, `wait --finish` and `wait --status`. Supported pending results release Stop; terminal or unknown work restores the reminder.

```text
.agents/skills/        the skills (canonical methods)
skills/                portable launchers, gate scripts and the Claude Code plugin root
skills/agents/         delegate roles as Claude Code agents (runner, analyst, maker, builder, reviewer)
skills/safe-engine/    VERSION and release-manifest.json (the release identity)
.claude-plugin/        the Claude Code marketplace, pinned to the release tag
safe_engine/           Safe mode controller (python -m safe_engine)
evals/                 factory vs plain agent scoring (repository only)
scripts/               launcher packaging, release.py and token_report.py
docs/                  docs/install.md, docs/hosts.md, docs/orchestrators.md, docs/releasing.md
tests/                 controller, gate, installer, budget, docs-sync and skill hygiene tests
CHANGELOG.md           what changed per release; UPGRADING.md: what to do
```

UI delivery uses [Look, Show, Prove, Ship](docs/show-first.md): `show --plan`, `show --candidate`, `show --prepare`, `show --shared`, `show --reply`, `done show`, then `prove --suite`. Only actual shared pictures start the owner-response window. Installed entries use the selected bundle runner; completion requires any retained suite pass to match current source. Humans retain merge authority.

POC/MVP visual work defaults to light mode on desktop, or light mode on phone for a mobile app. Extra themes, devices and responsive checks need an explicit request or existing requirement. Keep elegant visuals and polished motion; honor reduced-motion preferences. New Show plans freeze selected `variants`; ordinary reports show matched Before/After focused on the changed area. Design ports retain their design comparison and frozen coverage; existing plans keep their recorded scope.

New non-UI Fast runs declare `prove --plan <plan.json>` before plan completion. Intact matching complete-suite evidence returns before the machine-wide execution queue; misses join the queue and recheck. Each execution keeps its own log, so an intact earlier receipt can survive a later run with different inputs. Concurrent Fast proof completion preserves independent observations and owner controls; a conflicting state write fails visibly. `prove --suite --fresh` explicitly reruns diagnostics. Safe `check` uses the same behavior; new complete-cycle runs permit `feature-check --checks <ids> --file <json>` after completed-item use. See [complete suites](docs/suite-checks.md) for declarations, manual receipts, reuse and compatibility.
