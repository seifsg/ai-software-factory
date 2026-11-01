<div align="center">

# 🏭 AI Software Factory

**Your coding agent, run like a software team. Idea in, reviewed draft PR out.**

Ticket, analyze, recommend, plan, Before proof, build, verify, PR, review. In that order, every time, and you see every step.

![Agents](https://img.shields.io/badge/agents-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20more-6E56CF)
![Modes](https://img.shields.io/badge/modes-Fast%20%C2%B7%20Safe-2EA44F)
![OS](https://img.shields.io/badge/OS-Windows%20%C2%B7%20macOS%20%C2%B7%20Linux-0A66C2)

**[Quick start](#-quick-start) · [A run](#-a-run) · [How it stays on track](#-how-it-stays-on-track) · [Update](#-update) · [Troubleshooting](#-troubleshooting)**

</div>

Coding agents jump straight to code, forget the method as the context grows and tell you it works. The factory is a set of skills that gives your agent a team's process, plus one small hook script that keeps a run going until every step is done and checked. No runtime, no Python, nothing on every tool call.

## ⚡ Quick start

**You need:** a coding agent (Claude Code and Codex are first-class; any agent that reads `SKILL.md` works), Git, the GitHub CLI signed in (`gh auth login`) for tickets and draft PRs, and on Windows Git Bash (part of Git for Windows) for the hooks.

1. **Install:** [docs/install.md](docs/install.md). Claude Code:

   ```text
   claude plugin marketplace add https://github.com/seifsg/ai-software-factory.git
   claude plugin install safe-engine@ai-software-factory
   ```

2. **Check it:** start a new session; your agent should list `safe-engine`.
3. **Build:** in your agent's chat (`/safe-engine` in Claude Code, `$safe-engine` in Codex):

   ```text
   safe-engine Build [app or feature] in [absolute project directory, or leave it out for a new project]. Success means [observable outcome].
   ```

4. **Watch, answer, merge.** Every step prints its output. Answer its questions, review the draft PR, merge it.

## 🎬 A run

| Step | Skill | You see |
|---|---|---|
| 0 Ticket | `ticketing` | ticket link, criteria, checklist |
| 1 Analyze | `analyze-start` | purpose, ASCII flow, every consumer, claim vs code, unknowns |
| 2 Recommend | `recommend` | three options in one table, one pick |
| 3 Plan | `get-ready-to-code` | files, critique, phases, todos, proof list, test map |
| 4 Before | `how-to-make-a-pr` | Before screenshots and outputs, saved before the first edit |
| 5 Build | `get-ready-to-code` | one line per todo, through the 0–4 loop |
| 6 Verify | `deep-review` | findings, one full suite run, After captures |
| 7 PR | `how-to-make-a-pr` | draft PR with Before/After pairs |
| 8 Review | `how-to-review-a-pr` | a fresh agent's verdict comment |

Products and big features add `research-market` and kickoff questions before step 1; persistence adds `database-schema`. **Fast** (default) runs straight through; **Safe** also stops for your OK on the plan.

## 🛡️ How it stays on track

Long runs lose skill text when the host compacts context. The factory works around it instead of hoping:

```text
each step:  load its skill fresh → do it → write its block to .factory/run.md
gates:      after steps 3, 6, 8 a fresh light checker compares outputs with each skill's
            output contract and hands back Gate A/B/C: PASS @<commit>, or the missing items
turn ends:  Stop guard reads run.md + the host's subagent files → "Next: step N, load skill X"
compaction: compact hook reads run.md → re-injects the next step
```

- The run cannot close without step 8, three gates and a review, each proven by the host's record of that checker or reviewer on that commit; Gate C and the review on the pushed HEAD.
- Loops stop: rounds 1-3 run, 4-5 only with an open `CRITICAL:` line; then, or after 6 turns without progress, the guard halts the run with one packet for you. `sh run-guard.sh clear` resumes it.
- Waiting on you is allowed (`Waiting: owner:`); waiting on background jobs needs a deadline (`(max <n> min)`), past which the guard wakes the run.
- After two compactions the run moves to a fresh session that reads only the run file and the ticket.
- The guard reads the run file and the run's subagent files: about 0.4 s per turn end with a run on Windows, nothing per tool call.

### 🌙 Overnight runs

`night.sh` refuses to start unless the run can finish unattended (guard wired, deny rules, own branch, `pre-push` hook, push dry run, tracker sign-in), then starts a session that denies instead of prompting. Owner questions get recorded defaults, owner-only items are parked, nothing leaves the machine but the run's branch, draft PR and tickets. A watchdog from the OS scheduler resumes a stalled run, waits out usage limits, starts relays and tells you once how it ended. Setup: [install](docs/install.md#overnight-runs).

Details: [run file](.agents/skills/safe-engine/references/run-file.md), [checker](.agents/skills/safe-engine/references/checker.md), [night mode](.agents/skills/safe-engine/references/night.md), [hosts](docs/hosts.md).

## 🔄 Update

- **Claude Code:** `claude plugin marketplace update ai-software-factory`, then `/plugin` to update `safe-engine`, or keep auto-update on.
- **Codex and others:** `git -C <clone> pull`, then copy the skills again ([install](docs/install.md)).
- What changed: [CHANGELOG.md](CHANGELOG.md). What to do: [UPGRADING.md](UPGRADING.md).

## 🧹 Uninstall

Claude Code: `claude plugin uninstall safe-engine@ai-software-factory`. Codex: delete the copied skill folders and the two hook entries from `~/.codex/hooks.json`. Projects keep their `.factory/` folders until you delete them.

## 🩺 Troubleshooting

| Symptom | Fix |
|---|---|
| `safe-engine` not listed | Start a new session; check `/plugin` (Claude Code) or the copied folder under `~/.agents/skills` (Codex) |
| Agent stops mid-run | Check the hooks are installed and trusted (Codex: `/hooks`); read `.factory/run.md`; say "resume" |
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
| `recommend` | three solutions, one pick |
| `get-ready-to-code` | the plan and the 0–4 build loop |
| `deep-review` | verify: bug hunt and review lenses |
| `how-to-make-a-pr` | Before/After proof and the draft PR |
| `how-to-review-a-pr` | the fresh-agent PR review |
| `database-schema`, `research-market` | specialists the steps call when needed |
| `improve-factory` | repairs the factory itself |

## 🛠️ Work on the factory

Rules: [AGENTS.md](AGENTS.md). Changes go through `improve-factory`. Releases: [docs/releasing.md](docs/releasing.md). Report problems as [issues](https://github.com/seifsg/ai-software-factory/issues).

```text
.agents/skills/                  the skills (canonical methods)
.agents/agents/                  delegate roles for Claude Code (runner, analyst, maker, builder, reviewer, checker)
.agents/hooks/hooks.json         the Stop guard and compact hook for Claude Code
.agents/.claude-plugin/          the plugin manifest; the plugin root is .agents/
.claude-plugin/marketplace.json  the marketplace, pinned to the release tag
docs/                            install, hosts, releasing
CHANGELOG.md, UPGRADING.md       what changed per release, and what to do
```
