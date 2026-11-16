# GitHub proof media

Load when a PR carries screenshots or recordings (Visual yes).

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

