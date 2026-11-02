# GitHub Issues commands

Load when tracker is GitHub. `{owner}` and `{repo}` come from current repository. Pass long bodies from a file.

## Check the target

```text
gh auth status
gh repo view --json nameWithOwner,isPrivate
```

No repository yet (new project, or owner chose private GitHub): from local repository with its first commit, `gh repo create <name> --private --source . --remote origin --push`. First check name is free (`gh repo view <owner>/<name>` fails); taken: add short suffix, never reuse someone's repository.

## Search, then create

```text
gh issue list --state all --search "<term>" --json number,title,state,url
gh issue create --title "<title>" --body-file <file>
```

Search symptom or feature, then PR title or branch slug. Reuse a match; create only when every search misses.

`gh issue create` errors: first search exact title (`--state all`). Create through REST only when no duplicate exists:

```text
gh api repos/{owner}/{repo}/issues -X POST -f title="<title>" -F body=@<file>
```

## Link a sub-issue to the epic

API takes child's numeric `id`, not issue number; `-F` (typed, not `-f`) sends it as number.

```text
gh api repos/{owner}/{repo}/issues/<child> --jq .id
gh api -X POST repos/{owner}/{repo}/issues/<epic>/sub_issues -F sub_issue_id=<id>
gh api --paginate repos/{owner}/{repo}/issues/<epic>/sub_issues --jq '.[] | [.number, .state, .title] | @tsv'
```

Last one lists children: verify links; at intake, check the epic.

## Read, refresh and update

```text
gh issue view <n> --json title,state,body,updatedAt,comments,labels,assignees,projectItems
gh issue edit <n> --body-file <file>
gh issue comment <n> --body-file <file>
```

`updatedAt` changes on body, comment, state edits: cheap refresh compares it. An edit replaces whole body: read first. Tick: change `[ ]` to `[x]`, add proof, then edit. Issue lists show progress (x of y).

## Backlog

- First check `gh auth status` for `project` scope: without it `projectItems` reads empty, board looks absent. Missing: ask owner to run `gh auth refresh -s project`, or use labels and say so.
- Project board with Status field (`projectItems`): set status there, priority too if board has that field.
- Otherwise labels, at most one of each per issue: `status: backlog`, `status: to do`, `status: in progress`, `status: dev done`, `status: ready for qa`, `status: blocked`; `priority: P0` to `priority: P3`. Status labels count on open issues only: open without one = Backlog, closed as completed = Done, closed as not planned = Cancelled. Run's tickets always carry one.

```text
gh label list --limit 200 --json name
gh label create "status: dev done" --description "Backlog status"
gh issue list --state open --limit 200 --json number,title,labels,assignees,updatedAt
gh issue edit <n> --remove-label "status: to do" --add-label "status: in progress" --add-assignee @me
gh project list --owner <owner>
gh project item-add <project-number> --owner <owner> --url <issue-url>
gh project item-edit <project-number> --owner <owner> --url <issue-url> --field Status --value "In progress"
gh pr list --state <closed|open> --limit 1000 --json number,url,state,body,baseRefName,mergedAt,closedAt
gh pr view <n> --json comments --jq '.comments[-3:][] | [.author.login, .body] | @tsv'
gh api --paginate repos/{owner}/{repo}/issues/<n>/events --jq '.[] | select(.event == "reopened" or ((.event == "labeled" or .event == "unlabeled") and (.label.name | ascii_downcase | startswith("status:")))) | [.event, (.label.name // "-"), .created_at] | @tsv'
gh issue close <n> --reason <completed|"not planned"> --comment "<activity entry: merged PR link, or owner decision>"
gh issue reopen <n>
```

- Create only missing labels the run uses, spelled as listed. Never rename or delete existing ones.
- Sort list by priority label.
- Done comes from merge: closing keywords close ticket when its PR merges into default branch. Intake closed-PR list catches the rest; `state` reads `MERGED` or `CLOSED`. Full list (1000 rows): read on with `--search "closed:<<closedAt of the oldest listed>"`, stop once older than oldest open ticket.
- Merged into any base: per open ticket its `body` names with a closing keyword, read board status if it has one (board moves don't show in issue events) and events (`issues/<n>/events`); close per intake rule when nothing follows `mergedAt`. Closed unmerged: intake rule, same events check after `closedAt`.
- Close first, then drop status label: completed for Done, not planned for Cancelled. Back from either: reopen and label.
- Boards: keep built-in workflows that set Done when item closes or its PR merges. Board without Blocked status: add `status: blocked` label too. New issues on a board: `item-add` first.
- Each move pairs with one activity comment (`gh issue comment`); close with `--comment` is both.
