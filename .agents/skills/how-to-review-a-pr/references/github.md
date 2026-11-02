# GitHub Commands

Use when PR host is GitHub. Check access first: `gh auth status`.

| Step | Command |
|---|---|
| Repository | `gh repo view <owner/repo> --json nameWithOwner`; add `-R <owner/repo>` to every `gh pr` command when outside that repository |
| PR number | Last path segment of `/pull/<n>` |
| Metadata | `gh pr view <n> --json number,title,body,author,state,url,headRefName,headRefOid,baseRefName,baseRefOid,isCrossRepository,mergeable,mergeStateStatus,additions,deletions,changedFiles,labels,commits,files,comments,reviews` |
| Diff | `gh pr diff <n>` |
| CI status | `gh pr checks <n>` |
| Checkout | `git status` must be clean, then `gh pr checkout <n>` |
| Push | `git add <changed files>`, `git commit`, `git push`. Never `--force`. |
| Comment | Write the body to a temp file, then `gh pr comment <n> --body-file <file>` |

- Record `baseRefOid` and `headRefOid` as the exact reviewed candidate.
- Fork PRs: `gh pr checkout` tracks the fork. Pushing back needs "allow maintainer edits". Push rejected: put patch in comment.
- `--body-file` avoids shell-escaping problems with markdown.
