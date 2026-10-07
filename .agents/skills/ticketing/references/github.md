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
gh issue view <n> --json title,state,body,updatedAt,comments
gh issue edit <n> --body-file <file>
gh issue comment <n> --body-file <file>
gh issue close <n> --comment "<outcome passed>"
```

`updatedAt` changes on body, comment and state edits, so it works for the cheap refresh: re-read fully only when it differs from the last read.

Close a sub-issue when its outcome passed. Never close the epic until the owner accepts. Read before every edit; an edit replaces the whole body.

## Status labels

```text
gh label list --json name
gh issue edit <n> --add-label "<existing label>"
```

Use a label that exists. Do not guess its spelling.
