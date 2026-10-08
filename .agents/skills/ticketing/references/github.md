# GitHub Issues commands

Load when the project's tracker is GitHub. `{owner}` and `{repo}` fill in from the current repository. Pass long bodies from a file.

## Check the target

```text
gh auth status
gh repo view --json nameWithOwner,isPrivate
```

No repository yet and the owner chose a private GitHub repository: `gh repo create <name> --private --source . --remote origin` from the local repository.

## Search before creating

```text
gh issue list --state all --search "<symptom or feature>" --json number,title,state,url
gh issue list --state all --search "<PR title or branch slug>" --json number,title,state,url
```

Reuse a match. Create only when both searches miss.

## Create

```text
gh issue create --title "<title>" --body-file <file>
```

If `gh issue create` errors, check for a duplicate first (search by the exact title, `--state all`). Only when none exists, create through REST:

```text
gh api repos/{owner}/{repo}/issues -X POST -f title="<title>" -F body=@<file>
```

## Link a sub-issue to the epic

The API takes the child's numeric `id`, not its issue number.

```text
gh api repos/{owner}/{repo}/issues/<child> --jq .id
gh api -X POST repos/{owner}/{repo}/issues/<epic>/sub_issues -F sub_issue_id=<id>
gh api repos/{owner}/{repo}/issues/<epic>/sub_issues --jq '.[].number'
```

Use `-F` (typed), not `-f`, so the id is sent as a number. The last command lists linked children to verify.

## Read, refresh and update

```text
gh issue view <n> --json title,state,body,updatedAt,comments,labels,assignees,projectItems
gh issue edit <n> --body-file <file>
gh issue comment <n> --body-file <file>
```

`updatedAt` changes on body, comment and state edits, so it works for the cheap refresh: re-read fully only when it differs from the last read.

Read before every edit; an edit replaces the whole body.

## Checklist

Task items in the body: `- [ ] T1 <todo> (A1)`. Issue lists show the progress (x of y). Tick: read the body, change `[ ]` to `[x]` and add the proof, then `gh issue edit <n> --body-file <file>`. One writer per body.

## Backlog

Check `gh auth status` for the `project` scope first: without it `projectItems` reads empty and a board looks absent. Missing: ask the owner to run `gh auth refresh -s project`, or use labels and say so. The issue sits on a project board with a Status field (`projectItems` above): set status there, and priority too when the board has that field. Otherwise labels: `status: backlog`, `status: to do`, `status: in progress`, `status: dev done`, `status: ready for qa`, `status: blocked`, and `priority: P0` to `priority: P3`. At most one of each per issue. Status labels count on open issues only: open without one is Backlog, closed as completed is Done, closed as not planned is Cancelled. A run's tickets always carry one.

```text
gh label list --limit 200 --json name
gh label create "status: dev done" --description "Backlog status"
gh issue list --state open --limit 200 --json number,title,labels,assignees,updatedAt
gh issue edit <n> --remove-label "status: to do" --add-label "status: in progress" --add-assignee @me
gh project list --owner <owner>
gh project item-add <project-number> --owner <owner> --url <issue-url>
gh project item-edit <project-number> --owner <owner> --url <issue-url> --field Status --value "In progress"
gh pr list --state merged --search "merged:>=<last intake date>" --limit 200 --json number,url,body,baseRefName
gh issue close <n> --reason completed --comment "<merged PR link>"
gh issue close <n> --reason "not planned" --comment "<owner decision>"
gh issue reopen <n>
```

- Create only the missing labels the run uses, spelled as listed. Never rename or delete existing ones.
- Sort the list by priority label.
- Done comes from the merge: closing keywords in the PR close the ticket when it merges into the default branch. They are ignored on any other base: at the next intake, close such tickets with the merged PR link. Drop the status label on close. Cancelled: drop it, close as not planned. Back from either: reopen and label.
- Boards: keep the built-in workflows that set Done when an item closes or its PR merges. A board without a Blocked status: add the `status: blocked` label too. New issues on a board: `item-add` first.
- Each move pairs with one activity comment (`gh issue comment`). A close with `--comment` is both.
