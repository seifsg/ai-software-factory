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
5. No agent, OS or tracker specifics in methods. They live in `docs/hosts.md`, the adapters (`.agents/.claude-plugin/`, `.agents/agents/`, `.agents/hooks/`) and reference files named for one tool (`references/github.md`).
6. A step skill ends with its `## Output contract`: the block it writes and a checklist the checker can verify.
7. Size: every SKILL.md under 17,000 bytes (under 5k tokens: Claude Code keeps only that much of a skill after compaction), aim for 150 lines. References under 200 lines; over 100 lines starts with a contents line. The methods a run's main agent reads (the read-set command below) stay under 115 KB; all methods together under 220 KB. Both numbers only go down. Detail needed only in a rare situation goes to a reference behind a pointer that names the situation.
8. Every operative rule lives once per skill that needs it. Merge duplicates; cut filler. Never cut examples or ordering rules to save bytes.
9. English. No em dashes, stock phrases or invented claims.

## Keep it working

No Python, test suite or build. The checks are commands and a fresh agent:

```text
grep -rnE '\]\(\.\./' .agents/skills                 # no links out of a skill's folder: expect nothing
wc -c .agents/skills/*/SKILL.md                      # each under 17000
cat .agents/skills/*/SKILL.md .agents/skills/*/references/*.md | wc -c   # under 220000
(cd .agents/skills && cat safe-engine/SKILL.md safe-engine/references/run-file.md safe-engine/references/checker.md safe-engine/references/product-bar.md safe-engine/references/sizes.md safe-engine/references/delegate.md safe-engine/references/owner-reports.md safe-engine/references/worth-it.md ticketing/SKILL.md ticketing/references/ticket-layout.md analyze-start/SKILL.md recommend/SKILL.md get-ready-to-code/SKILL.md how-to-make-a-pr/SKILL.md how-to-make-a-pr/references/media-proof.md how-to-make-a-pr/references/pr-layout.md how-to-make-a-pr/references/github.md how-to-make-a-pr/references/credit.md deep-review/SKILL.md deep-review/references/change-guard.md deep-review/references/compliance.md | wc -c)   # read set: under 115000
```

- A changed `run-guard.sh` runs on fixture run files (`improve-factory`, Proof). It stays POSIX `sh` with LF endings and one `awk` pass.
- Every changed method gets a fresh-agent walkthrough before review.
- Moving, adding or deleting a skill, reference, role or hook: update `README.md` and `docs/` in the same PR. Keep what they say (commands, paths, defaults) true by hand.
- Each PR states method bytes before and after (`wc -c`). Net growth needs the owner's OK with the reason.
- Keep secrets, client data, transcripts and `.factory/` run files out of Git.

## PRs

Draft PRs, through `how-to-make-a-pr`, linked to their ticket, unless the owner says push direct. Every PR gets `how-to-review-a-pr` from a fresh agent. Humans decide ready, merge and release. No AI attribution lines in commits. PR bodies end with the factory credit line (`how-to-make-a-pr`).

## Releases

- Every PR adds a line under `## [Unreleased]` in `CHANGELOG.md` (Keep a Changelog), and steps under the next version in `UPGRADING.md` when installs or open runs must act.
- One canonical version: `version` in `.agents/.claude-plugin/plugin.json`, SemVer. Humans cut, tag and publish releases ([releasing](docs/releasing.md)); never move or re-publish a tag.
