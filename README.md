<div align="center">

# 🏭 AI Software Factory

### Your coding agent, run like a software team.
**One request in. Ten checked steps. A reviewed draft PR out.**

<a href="https://github.com/seifsg/ai-software-factory/releases/latest"><img src="https://img.shields.io/github/v/release/seifsg/ai-software-factory?label=version&color=6E56CF&style=flat-square" alt="Latest version" height="28"></a> <img src="docs/assets/badges.svg" alt="Claude Code live · Codex plugin and Cursor not yet run live · Fast and Safe modes · any OS with Git and sh, no runtime" height="28">

**[Quick start](#-quick-start) · [A run](#-a-run) · [How it stays on track](#%EF%B8%8F-how-it-stays-on-track) · [Update](#-update) · [Troubleshooting](#-troubleshooting)**

<img src="docs/assets/hero.svg" alt="A run: ticket, analyze, recommend, challenge, plan, Before, build, verify, PR, review, with checker gates A, B and C after plan, verify and review, ending in a reviewed draft PR" width="100%">

</div>

Coding agents jump straight to code, forget the method as context grows, and tell you it works. The factory is a set of skills that gives your agent a team's process, plus one small hook script that keeps the run going until every step is done and checked. No runtime, no Python, nothing on every tool call.

<table>
<tr>
<td width="33%" valign="top">

### 🧭 A process, not a prompt
Ten steps in order, every time. Each step loads its skill fresh, prints its block to you and writes it to `.factory/run.md`.

</td>
<td width="33%" valign="top">

### 🔒 Gates it cannot skip
After plan, verify and review, a fresh checker compares the outputs with each skill's contract. The run cannot close until all three pass on the commit, or you waive one.

</td>
<td width="33%" valign="top">

### 📸 Proof, not claims
Before is captured before the first edit, After during verify, and both land in the draft PR. A fresh agent that did not build it reviews the PR.

</td>
</tr>
</table>

## ⚡ Quick start

**1. Install** in your agent ([all options](docs/install.md)):

| Agent | Install |
|---|---|
| **Claude Code** | `claude plugin marketplace add https://github.com/seifsg/ai-software-factory.git`<br>`claude plugin install safe-engine@ai-software-factory` |
| **Codex** (plugin, not yet run live) | `codex plugin marketplace add seifsg/ai-software-factory`, then `/plugins`, install `safe-engine`, trust its hooks in `/hooks` |
| **Cursor** (plugin, not yet run live; no hooks yet, so say go per step) | Customize, Plugins, add marketplace `https://github.com/seifsg/ai-software-factory`, install `safe-engine` |

Start a new session; your agent should list `safe-engine`. Other agents: copy the skills ([other agents](docs/install.md#other-agents)). You need Git, the GitHub CLI signed in (`gh auth login`) for tickets and draft PRs, and on Windows Git Bash (part of Git for Windows) for the hooks. To try unreleased `main`, run `claude --plugin-dir <clone>/.agents`.

**2. Ask** (`/safe-engine` in Claude Code, `$safe-engine` in Codex):

```text
safe-engine Build [app or feature] in [absolute project directory, or leave it out for a new project]. Success means [observable outcome].
```

**3. Watch, answer, merge.** A ticket link comes first, then one block per step. Answer questions when asked. You end with a draft PR that carries Before/After proof and a reviewer's verdict: review it and merge it.

```text
safe-engine Resume [absolute project directory].
```

## 🎬 A run

| Step | Skill | You see |
|---|---|---|
| 0 Ticket | `ticketing` | ticket link, criteria, checklist |
| 1 Analyze | `analyze-start` | purpose, ASCII flow, every consumer, claim vs code, unknowns |
| 2 Recommend | `recommend` | three options in one table, one pick; new UI also gets three looks, one pick |
| 2b Challenge | `recommend` | the pick rechecked against "do better": kept or changed, and why |
| 3 Plan | `get-ready-to-code` | files, critique, phases, todos, proof list, test map, then **Gate A** |
| 4 Before | `how-to-make-a-pr` | Before screenshots and outputs, saved before the first edit |
| 5 Build | `get-ready-to-code` | one line per todo, through the 0–4 loop |
| 6 Verify | `deep-review` | findings, UI pass, one full suite run, After captures, then **Gate B** |
| 7 PR | `how-to-make-a-pr` | draft PR with Before/After pairs |
| 8 Review | `how-to-review-a-pr` | a fresh agent's verdict, then **Gate C** |

Products and big features add `research-market` and kickoff questions at step 0; persistence adds `database-schema`. **Fast** (default) runs straight through; **Safe** also stops for your OK on the plan.

## 🛡️ How it stays on track

<img src="docs/assets/guard.svg" alt="Load the step's skill fresh, do the step, write its block to .factory/run.md, then the Stop guard sends the next step on the next turn. After compaction the compact hook re-injects Next. Gates A, B and C need a fresh checker's pass on the commit." width="100%">

Long runs lose skill text when the host compacts context. The factory works around it instead of hoping:

- The run cannot close without step 8, three gates and a review, each proven by the host's record of that checker or reviewer on that commit; Gate C and the review on the pushed HEAD.
- Loops never stall: after 3 failed rounds with no open `CRITICAL:` line the gate or review passes by cap (`Gate X: PASS (cap, 3 rounds, no CRITICAL)`) and leftovers go to follow-ups; rounds 4-5 only while a `CRITICAL:` is open. After round 5, or 6 turns without progress, the guard halts the run with one packet for you. `sh run-guard.sh clear` resumes it.
- Waiting on you is allowed (`Waiting: owner:`); waiting on background jobs needs a deadline (`(max <n> min)`), past which the guard wakes the run.
- After two compactions the run moves to a fresh session that reads only the run file and the ticket.
- The guard reads the run file and the run's subagent files: about 0.4 s per turn end with a run on Windows, nothing per tool call.

### 🌙 Overnight runs

`night.sh` refuses to start unless the run can finish unattended (guard wired, deny rules, own branch, `pre-push` hook, push dry run, tracker sign-in), then starts a session that denies instead of prompting. Owner questions get recorded defaults, owner-only items are parked, and nothing leaves the machine but the run's branch, draft PR and tickets. A watchdog from the OS scheduler resumes a stalled run, waits out usage limits, starts relays and tells you once how it ended. Setup: [install](docs/install.md#overnight-runs).

Details: [run file](.agents/skills/safe-engine/references/run-file.md), [checker](.agents/skills/safe-engine/references/checker.md), [night mode](.agents/skills/safe-engine/references/night.md), [hosts](docs/hosts.md).

## 🔄 Update

- Each session start checks for a newer release (cached, about 0.1 s) and says so before a run ([update check](docs/install.md#update-check)).
- **Claude Code:** `claude plugin marketplace update ai-software-factory`, then `/plugin` to update `safe-engine`, or keep auto-update on.
- **Codex:** `codex plugin marketplace upgrade ai-software-factory`; copied skills: `git -C <clone> pull`, copy again.
- **Cursor:** reinstall `safe-engine` from Customize, Plugins when a new version shows.
- What changed: [CHANGELOG.md](CHANGELOG.md). What to do: [UPGRADING.md](UPGRADING.md).

## 🧹 Uninstall

Claude Code: `claude plugin uninstall safe-engine@ai-software-factory`. Codex: delete the copied skill folders and the two hook entries from `~/.codex/hooks.json`. Projects keep `.factory/` folders until you delete them.

## 🩺 Troubleshooting

| Symptom | Fix |
|---|---|
| `safe-engine` not listed | Start a new session; check `/plugin` (Claude Code) or the copied folder under `~/.agents/skills` (Codex) |
| Agent stops mid-run | Check hooks are installed and trusted (Codex: `/hooks`); read `.factory/run.md`; say "resume" |
| Run will not stop | `Waiting:` must name what you wait for; to abandon, set `Status: stopped (<reason>)` |
| Run halted | Read the packet under the current step in `.factory/run.md`, decide, then run the guard with `clear` |
| Gate line "has not passed" | Paste the checker's line with its id and commit; Gate C needs the pushed HEAD |
| Hook errors on Windows | Install Git for Windows; hooks need its `sh` |

## 🧰 Skills

| Skill | What it does |
|---|---|
| `safe-engine` | the ten-step coordinator, run file and gates |
| `ticketing` | backlog, epics, tickets, checklists and statuses |
| `analyze-start` | analysis before any code |
| `recommend` | three solutions, one pick, and the step 2b challenge |
| `get-ready-to-code` | the plan and the 0–4 build loop |
| `deep-review` | verify: bug hunt and review lenses |
| `how-to-make-a-pr` | Before/After proof and the draft PR |
| `how-to-review-a-pr` | the fresh-agent PR review |
| `database-schema`, `research-market` | specialists the steps call when needed |
| `improve-factory` | repairs the factory itself: `improve-factory The factory did [observed]; expected [result].` |

## 🛠️ Work on the factory

Rules: [AGENTS.md](AGENTS.md). Changes go through `improve-factory`. Releases: [docs/releasing.md](docs/releasing.md). Report problems as [issues](https://github.com/seifsg/ai-software-factory/issues).

```text
.agents/skills/                  the skills (canonical methods)
.agents/agents/                  delegate roles for Claude Code (runner, analyst, maker, builder, reviewer, checker)
.agents/hooks/hooks.json         the Stop guard, compact hook and update check (Claude Code, Codex)
.agents/.claude-plugin/          plugin manifests (also .codex-plugin/, .cursor-plugin/); the plugin root is .agents/
.claude-plugin/marketplace.json  the marketplace (Claude Code, Codex), pinned to the release tag
.cursor-plugin/marketplace.json  the Cursor marketplace
docs/                            install, hosts, releasing; docs/assets/ holds the README images
CHANGELOG.md, UPGRADING.md       what changed per release, and what to do
```
