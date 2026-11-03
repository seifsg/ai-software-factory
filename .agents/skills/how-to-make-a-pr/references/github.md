# GitHub PR commands

Load when project host is GitHub. Write bodies to a file; skip shell escaping.

## Open the draft

```text
git push -u origin <branch>
gh pr create --draft --base <base> --head <branch> --title "<type>(<scope>): <subject>" --body-file <file>
```

- `--body-file` replaces repository template: copy structure of `.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE/` into body file.
- Always `--draft`. Never run `gh pr ready` or `gh pr merge`.
- Link every ticket in body: `Closes #<n>` where this skill's step 6 allows one, else `Refs #<n>`.
- Closing keywords act only on PRs into default branch; elsewhere ignored, link nothing. Keep them for the record: next intake closes those tickets after merge. After base change, check PR's linked issues.

## Attach proof media

`gh` cannot upload images: put screenshots and recordings in a proof commit under `refs/proof/<branch>` (clones never fetch it). It never touches working tree, index or PR diff.

```text
printf '100644 blob %s\t%s\n' "$(git hash-object -w <before.png>)" <outcome>-before.png "$(git hash-object -w <after.png>)" <outcome>-after.png | git mktree
git commit-tree <tree id> -m "proof: <branch>"
git push origin <commit id>:refs/proof/<branch>
```

- Later uploads: `git fetch origin refs/proof/<branch>`, then list the earlier files too in `git mktree` input and add `-p FETCH_HEAD` to `commit-tree`; earlier links keep working. Required signing: add `-S`.
- Link pinned to commit: `![<outcome> before](https://github.com/{owner}/{repo}/blob/<commit id>/<name>?raw=true)`. GIFs play inline. Video over 10 MB: link it, with GIF or screenshot beside it.
- Check each file landed: `gh api "repos/{owner}/{repo}/contents/<name>?ref=<commit id>" --jq .size`, then rendering and playback in PR from signed-in browser.
- Keep proof refs after merge: PR links to them.

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

Never guess logins. Comment only where authorized: own draft, or reviewer checkpoint someone approved.

## Update the ticket

```text
gh issue comment <ticket> --body-file <activity entry with the PR url>
```
