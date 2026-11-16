# GitHub PR commands

Load when project host is GitHub. Write bodies to a file.

## Open the draft

```text
git push -u origin <branch>
gh pr create --draft --base <base> --head <branch> --title "<type>(<scope>): <subject>" --body-file <file>
```

- `--body-file` replaces the repository template: copy the structure of `.github/pull_request_template.md` (or `PULL_REQUEST_TEMPLATE/`) into it.
- Always `--draft`. Never run `gh pr ready` or `gh pr merge`.
- Link every ticket in body: `Closes #<n>` where this skill's step 6 allows one, else `Refs #<n>`.
- Closing keywords act only on PRs into default branch; elsewhere ignored, link nothing. Next intake closes those tickets after merge; after a base change, check the linked issues.

## Attach proof media

Screenshots or recordings: `github-media.md`.

## Fix the base or body

```text
gh pr edit <n> --base <base>
gh pr edit <n> --body-file <file>
```

Read current body first (`gh pr view <n> --json body`). Edit replaces whole body; keep adjustment history.

## Inspect

```text
gh pr view <n> --json url,isDraft,baseRefName,headRefName,headRefOid,reviewDecision
gh pr checks <n>
```

`headRefOid` = exact candidate for proof and remote review.

## Request review and comment

```text
gh pr edit <n> --add-reviewer <login>
gh pr comment <n> --body-file <file>
```

Never guess logins. Comment only where authorized: own draft, or an approved reviewer checkpoint.

## Update the ticket

```text
gh issue comment <ticket> --body-file <activity entry with the PR url>
```
