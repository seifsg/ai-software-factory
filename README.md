# AI Software Factory

Agent skills that take software from idea to reviewed handoff: research, tickets, analysis, plan, build, QA, review and PR. Any owner, any coding agent, any OS, any codebase. Games, web, mobile and desktop apps, services, tools and libraries.

## Skills

| Skill | Job |
|---|---|
| `safe-engine` | Coordinates delivery in Fast, Lucky or Safe mode; holds the work rules and product bar |
| `research-market` | Competitors, feature matrix, opportunities, stack and architecture options |
| `analyze-start` | Understand the code and every consumer before changing it; ASCII charts; no coding |
| `get-ready-to-code` | Files, critique, phases, todos, whole plan; the 0–4 loop for every todo |
| `ux-quality` | Simple, familiar, accessible, responsive UI; copy; public-page SEO |
| `database-schema` | Access patterns, three designs, chosen schema, indexes, migrations |
| `deep-review` | Bug hunt plus change-guard, compliance, security, performance and journey lenses; PR review |
| `ticketing` | Epic and outcome sub-issues, confirmed before/after, criteria, activity |
| `how-to-make-a-pr` | Draft PR with ticket link, before/after proof and what is unverified |
| `improve-factory` | Repair or improve the factory itself without disturbing active runs |

Each skill lives in `.agents/skills/<name>/` and stands alone: it links only to its own `references/`.

## Modes

| | 🏃 Fast (default) | 🍀 Lucky | 🛡️ Safe |
|---|---|---|---|
| Tickets | epic + sub-issues | same | ticket contract |
| Research + owner questions | new products, big features | no | yes |
| Methods | full analyze, plan, 0–4 | one short pass | full, with file-summary stop |
| Enforcement | gate + hooks | gate + hooks | Python controller |
| Checks | one done-run | none until `verify` | manual QA, tests, verify, independent review |

```text
request → research → kickoff questions → tickets → analyze → plan → design/schema
        → build (0–4 per todo) → use it → tests → review → handoff → draft PR → human
```

## Start

[Install](docs/install.md) for your agent, then:

```text
safe-engine Build [app or feature] in [absolute project directory]. Success means [observable outcome].
```

Add `lucky` or `safe` after the skill name for those modes. Resume with `safe-engine Resume [absolute project directory]`. Each agent's skill syntax and hooks: [hosts](docs/hosts.md).

## Layout

```text
.agents/skills/        the skills (canonical methods)
skills/                portable launchers, gate scripts and the Claude Code plugin root
safe_engine/           Safe mode controller (python -m safe_engine)
docs/                  install and hosts
tests/                 controller, gate, installer and skill hygiene tests
```

The gate checks that each step was recorded, not that it was good. The controller records stages and launches independent review; it never pushes, merges or deploys.
