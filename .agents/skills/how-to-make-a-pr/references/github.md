# GitHub PR commands

Load when the project's host is GitHub. Write bodies to a file; skip shell escaping.

## Open the draft

```text
git push -u origin <branch>
gh pr create --draft --base <base> --head <branch> --title "<type>(<scope>): <subject>" --body-file <file>
```

- `--body-file` replaces the repository template. Check `.github/pull_request_template.md` and `.github/PULL_REQUEST_TEMPLATE/`, and copy that structure into the body file.
- Always `--draft`. Never run `gh pr ready` or `gh pr merge`; humans decide.
- Link every ticket in the body. `Closes #<n>` only on each sub-issue or change ticket this PR finishes; `Refs #<n>` for the rest. The epic always gets `Refs #<epic>`.
- Closing keywords act only when the PR targets the default branch; on other bases they are ignored and create no link. Keep them for the record: the next intake closes those tickets after the merge. After a base change, check the PR's linked issues.

## Attach proof media

`gh` cannot upload images. Put screenshots and recordings in a proof commit on their own branch instead. It never touches the working tree, the index or the PR's diff, and works in private repositories for everyone who can read them.

```text
printf '100644 blob %s\t%s\n' "$(git hash-object -w <before.png>)" <outcome>-before.png "$(git hash-object -w <after.png>)" <outcome>-after.png | git mktree
git commit-tree <tree id> -m "proof: <branch>"
git push origin <commit id>:refs/heads/proof/<branch>
```

- Later uploads to the same branch: `git fetch origin proof/<branch>`, then add `-p FETCH_HEAD` to `commit-tree`. Earlier links keep working. Required signing: add `-S`.
- Link pinned to the commit: `![<outcome> before](https://github.com/{owner}/{repo}/blob/<commit id>/<name>?raw=true)`. GIFs play inline. A video over 10 MB: link it, with a GIF or screenshot beside it.
- Check each file landed: `gh api "repos/{owner}/{repo}/contents/<name>?ref=<commit id>" --jq .size`. With a browser signed in, open the PR: each image must render and each linked video must open and play. A broken one is missing proof.
- Keep proof branches after the merge: links to them stay in the PR.

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
gh issue comment <ticket> --body-file <activity entry with the PR url>
```
