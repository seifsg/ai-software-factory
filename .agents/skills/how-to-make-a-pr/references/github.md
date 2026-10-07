# GitHub PR commands

Load when the project's host is GitHub. Write bodies to a file; skip shell escaping.

## Open the draft

```text
git push -u origin <branch>
gh pr create --draft --base <base> --head <branch> --title "<type>(<scope>): <subject>" --body-file <file>
```

- `--body-file` replaces the repository template. Check `.github/pull_request_template.md` and `.github/PULL_REQUEST_TEMPLATE/`, and copy that structure into the body file.
- Always `--draft`. Never run `gh pr ready` or `gh pr merge`; humans decide.
- Link the ticket in the body: `Refs #<ticket>`. `Closes #<n>` only for a sub-issue. Never for the epic.
- `gh` cannot upload images. Link media the reviewer can already open. Without an authorized upload route, name the gap in the PR.

## Fix the base or body

```text
gh pr edit <n> --base <base>
gh pr edit <n> --body-file <file>
```

Read the current body first (`gh pr view <n> --json body`), then edit. An edit replaces the whole body; keep the adjustment history.

## Inspect

```text
gh pr view <n> --json url,isDraft,baseRefName,headRefName,headRefOid,reviewDecision
gh pr checks <n>
```

Use `headRefOid` as the exact candidate for proof and remote review.

## Request review and comment

```text
gh pr edit <n> --add-reviewer <login>
gh pr comment <n> --body-file <file>
```

Use the actual review owner from the project's rules. Do not guess logins. Comment only where authorized: your own draft, or a reviewer checkpoint someone approved.

## Update the ticket

```text
gh issue comment <ticket> --body "PR: <url>"
gh issue edit <ticket> --add-label "<existing awaiting-review label>"
```

List labels first (`gh label list --json name`). Use exact spelling.
