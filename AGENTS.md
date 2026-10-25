# AI Software Factory: repository rules

This repository is a skill library. It must work for any owner, coding agent, OS and codebase.

Changes to the factory use `improve-factory` (`.agents/skills/improve-factory/SKILL.md`). Fast by default; Safe on request. Analysis, planning or review requests stay in that phase.

## Work rules

The `## Work rules` section of `.agents/skills/safe-engine/SKILL.md` applies to every change here, code and prose.

## Writing skills

1. One folder per skill: `.agents/skills/<name>/SKILL.md`. `name` equals the folder. `description` says what it does and when to use it, third person, under 1024 characters, no process summary.
2. Write like `analyze-start` and `get-ready-to-code`: short imperative lines, numbered steps when order matters, explicit stops. Only what an agent would get wrong without it.
3. Self-contained: link only to files in the skill's own folder, one level deep. Name other skills in backticks; never link them. Phase skills never name the coordinator.
4. No person, company or product names. No dates, history, decision logs or provenance. Git keeps history (tag `history-archive`); release history lives only in `CHANGELOG.md` and `UPGRADING.md` at the root.
5. No agent, OS or tracker specifics in methods. They live in `docs/hosts.md`, the adapters (`skills/.claude-plugin/plugin.json`, `skills/agents/`, `fast_hosts.py`, `fast_install.py`, `safe_engine/reviewers.py`) and reference files named for one tool (`references/github.md`).
6. SKILL.md under 500 lines (aim for 150). References under 200; over 100 lines starts with a contents line. Each method file stays within its byte budget in `tests/budgets.json`: every run re-sends its methods each turn. Raise a budget only with the reason in the PR; `python scripts/token_report.py [--gate] --against origin/main` shows the change. Detail needed only in a rare situation goes to a reference behind a pointer that names the situation.
7. Every operative rule lives once per skill that needs it. Merge duplicates; cut filler.
8. English. No em dashes, stock phrases or invented claims.

## Keep the machinery working

- Moving, adding or deleting a factory file: update `safe_engine/bundle-inputs.json`, `safe_engine/distribution.py`, then `python scripts/package_skill_entries.py` (it regenerates both launcher resolvers; `--check` before pushing).
- Manual use first, tests last. For method changes, manual use means a fresh agent walking through the changed skill.
- Tests run in parallel: `python tests/run.py` (the same tests as `python -m unittest discover -s tests`). While iterating, `python tests/run.py --changed` runs only the modules your diff touches. Before any PR or push, run the full `python tests/run.py`, prose-only changes included (about 40 s). The hygiene and budget tests enforce rules 1, 3, 4 and 6.
- Keep secrets, client data, transcripts and `.factory/` run records out of Git.

## PRs

Draft PRs, through `how-to-make-a-pr`, linked to their ticket, unless the owner says push direct. Humans decide ready, merge and release. No AI attribution lines in commits. PR bodies end with the factory credit line (`how-to-make-a-pr`).

## Releases

- Every PR adds a line under `## [Unreleased]` in `CHANGELOG.md` (Keep a Changelog), and steps under the next version in `UPGRADING.md` when installs or active runs must act.
- One canonical version, `skills/safe-engine/VERSION`, SemVer. Humans cut, tag and publish releases with `scripts/release.py` ([releasing](docs/releasing.md)); never move or re-publish a tag.
