# AI Software Factory: repository rules

Skill library. Must work for any owner, coding agent, OS and codebase.

Factory changes use `improve-factory` (`.agents/skills/improve-factory/SKILL.md`). Fast by default; Safe on request. Analysis, planning or review requests stay in that phase.

## Work rules

`## Work rules` section of `.agents/skills/safe-factory/SKILL.md` applies to every change here, code and prose.

## Writing skills

1. One folder per skill: `.agents/skills/<name>/SKILL.md`. `name` = folder. `description`: what it does and when to use it, third person, under 1024 characters, no process summary.
2. Write like `analyze-start` and `get-ready-to-code`: short imperative lines, numbered steps when order matters, explicit stops. Only what an agent would get wrong without it.
3. Self-contained: link only to files in the skill's own folder, one level deep. Name other skills in backticks; never link them. Phase skills never name the coordinator.
4. No person, company or product names. No dates, history, decision logs or provenance. Git keeps history (tag `history-archive`); release history only in `CHANGELOG.md` and `UPGRADING.md` at root.
5. No agent, OS or tracker specifics in methods. They live in `docs/hosts.md`, the adapters (`.agents/.claude-plugin/`, `.agents/agents/`, `.agents/hooks/`) and reference files named for one tool (`references/github.md`).
6. Step skill ends with its `## Output contract`: the block it writes and a checklist the checker can verify.
7. Size: every SKILL.md under 17,000 bytes (under 5k tokens: Claude Code keeps only that much of a skill after compaction), aim for 150 lines. References under 200 lines; over 100 lines starts with a contents line. Methods a run's main agent reads (read-set command below) stay under 105 KB; all methods together under 170 KB. Both numbers only go down. Detail needed only in a rare situation goes to a reference behind a pointer that names the situation.
8. Each operative rule lives once per skill that needs it. Merge duplicates; cut filler. Never cut examples or ordering rules to save bytes.
9. English. No em dashes, stock phrases or invented claims.

## Keep it working

No Python, test suite or build. Checks are commands and a fresh agent. Byte counts come from Git blobs, same on every checkout and line ending: commit first, or name the base (`origin/main`) in place of `HEAD`.

```text
sh scripts/check.sh                    # every check: prints nothing, exit 0; else one FAIL line each, exit 1
sh scripts/check.sh HEAD origin/main    # also fails any method byte growth against the base
sh scripts/check.sh bytes origin/main   # "<all methods> <read set>" for the PR line (run for base and head)
```

It checks: links stay in a skill folder, SKILL.md under 17000, no media in Git, methods under 170000 and read set under 105000 (Git blobs), manifests agree, update check offline (newer tells, older quiet, curl fallback), doctor moves only old-only files, guard wiring (Stop in the skill, portable file for other hosts), session binding.

- Changed `run-guard.sh` runs on fixture run files (`improve-factory`, Proof). Stays POSIX `sh` with LF endings and one `awk` pass.
- Changed `gh` or `git` command form in a method: update night templates (`.agents/hooks/claude-settings.json` allow list, `codex.rules`) to match.
- Every changed method gets a fresh-agent walkthrough before review.
- Skill, reference, role or hook moved, added or deleted: update `README.md` and `docs/` in same PR. Keep what they say (commands, paths, defaults) true by hand.
- Each PR states method bytes before and after (`bytes` for base and head). Net growth needs owner's OK with the reason.
- Keep secrets, client data, transcripts and `.factory/` run files out of Git.

## PRs

Draft PRs, through `how-to-make-a-pr`, linked to their ticket, unless owner says push direct. Every PR gets `how-to-review-a-pr` from a fresh agent. Humans decide ready, merge and release. No AI attribution lines in commits. PR bodies end with the factory credit line (`how-to-make-a-pr`).

## Releases

- Every PR a reader notices adds its lines under `## [Unreleased]` in `CHANGELOG.md` per [releasing](docs/releasing.md#changelog), and steps under `## Unreleased` in `UPGRADING.md` when installs or open runs must act.
- One canonical version: `version` in `.agents/.claude-plugin/plugin.json`, SemVer by the bump table in [releasing](docs/releasing.md#versions); `.agents/.codex-plugin/plugin.json` and `.agents/.cursor-plugin/plugin.json` match it. Humans cut, tag and publish releases ([releasing](docs/releasing.md)); never move or re-publish a tag.
