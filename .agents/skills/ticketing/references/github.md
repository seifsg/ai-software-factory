# GitHub Issues commands

Load when the project's tracker is GitHub. `{owner}` and `{repo}` fill in from the current repository. Pass long bodies from a file.

## Check the target

```text
gh auth status
gh repo view --json nameWithOwner,isPrivate
```

No repository yet and the owner chose private GitHub: `gh repo create <name> --private --source . --remote origin` from the local repository.

## Search, then create

```text
gh issue list --state all --search "<term>" --json number,title,state,url
gh issue create --title "<title>" --body-file <file>
```

Search the symptom or feature, then the PR title or branch slug. Reuse a match; create only when every search misses.

`gh issue create` errors: search the exact title (`--state all`) first. Only when no duplicate exists, create through REST:

```text
gh api repos/{owner}/{repo}/issues -X POST -f title="<title>" -F body=@<file>
```

## Link a sub-issue to the epic

The API takes the child's numeric `id`, not its issue number; `-F` (typed, not `-f`) sends it as a number.

```text
gh api repos/{owner}/{repo}/issues/<child> --jq .id
gh api -X POST repos/{owner}/{repo}/issues/<epic>/sub_issues -F sub_issue_id=<id>
gh api --paginate repos/{owner}/{repo}/issues/<epic>/sub_issues --jq '.[] | [.number, .state, .title] | @tsv'
```

The last lists the children: verify links; at intake, check the epic.

## Read, refresh and update

```text
gh issue view <n> --json title,state,body,updatedAt,comments,labels,assignees,projectItems
gh issue edit <n> --body-file <file>
gh issue comment <n> --body-file <file>
```

`updatedAt` changes on body, comment and state edits, so the cheap refresh compares it. An edit replaces the whole body: read first. Tick: change `[ ]` to `[x]`, add the proof, then edit. Issue lists show the progress (x of y).

## Backlog

- First check `gh auth status` for the `project` scope: without it `projectItems` reads empty and a board looks absent. Missing: ask the owner to run `gh auth refresh -s project`, or use labels and say so.
- On a project board with a Status field (`projectItems`): set status there, and priority too when the board has that field.
- Otherwise labels, at most one of each per issue: `status: backlog`, `status: to do`, `status: in progress`, `status: dev done`, `status: ready for qa`, `status: blocked`; `priority: P0` to `priority: P3`. Status labels count on open issues only: open without one is Backlog, closed as completed is Done, closed as not planned is Cancelled. A run's tickets always carry one.

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

- Create only the missing labels the run uses, spelled as listed. Never rename or delete existing ones.
- Sort the list by priority label.
- Done comes from the merge: closing keywords close the ticket when its PR merges into the default branch. The intake closed-PR list catches the rest; `state` reads `MERGED` or `CLOSED`. A full list (1000 rows): read on with `--search "closed:<<closedAt of the oldest listed>"`, and stop once older than the oldest open ticket.
- Merged into any base: for each open ticket its `body` names with a closing keyword, read its board status when it has one (board moves don't show in issue events) and its events (`issues/<n>/events`); close it per the intake rule when nothing follows `mergedAt`. Closed unmerged: the intake rule, with the same events check after `closedAt`.
- Close first, then drop the status label: completed for Done, not planned for Cancelled. Back from either: reopen and label.
- Boards: keep the built-in workflows that set Done when an item closes or its PR merges. A board without a Blocked status: add the `status: blocked` label too. New issues on a board: `item-add` first.
- Each move pairs with one activity comment (`gh issue comment`); a close with `--comment` is both.
