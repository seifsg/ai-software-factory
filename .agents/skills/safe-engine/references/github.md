# GitHub app release commands

Use only when the app's established process calls for direct GitHub operations. Prefer an available integration with the needed capabilities; otherwise use authenticated `gh`. Existing app scripts/automation own their steps.

## Inspect before writing

Bind `<repo>` as `[HOST/]OWNER/REPO`, `<remote>` as the verified Git remote and every tag/commit explicitly. Discover permissions and installed CLI flags; never print tokens.

```text
gh repo view <repo> --json nameWithOwner,url,isPrivate
gh release list --repo <repo>
gh release view <tag> --repo <repo> --json id,url,tagName,targetCommitish,isDraft,isPrerelease,body,assets
git ls-remote --tags <remote> refs/tags/<tag> refs/tags/<tag>^{}
```

Inspect relevant tagged source, release preparation diff and repository scripts/config. Listings can be paginated; a missing listing entry or failed read is not absence. Peel annotated tags through Git and compare the full commit; `targetCommitish` is ignored when the tag already exists.

## Create only under the recorded authority

Preserve existing signing/tag creation and command order. Pushing a tag may trigger publication or deployment. If the authorized process already created the remote tag, verify its commit, then:

```text
gh release create <tag> --repo <repo> --verify-tag --draft --title <title> --notes-file <notes-file>
gh release upload <tag> <required-file> --repo <repo>
```

When the app instead delegates tag creation to GitHub, supply `--target <accepted-full-sha>` in place of `--verify-tag`. Omitted targets can create a tag at default-branch HEAD. An existing tag must still match the accepted commit; `--target` cannot repair it. Preserve prerelease/latest settings explicitly per app policy, including when publishing an existing draft.

Write curated notes to a file. Use generated notes only if the app owns them that way, with the correct previous-tag range; inspect the result before publication. Check every uploaded asset against prepared digests; never use `--clobber` to conceal mismatches.

After draft/content verification, only with publication authority:

```text
gh release edit <tag> --repo <repo> --draft=false
gh release view <tag> --repo <repo> --json id,url,tagName,isDraft,isPrerelease,body,assets
git ls-remote --tags <remote> refs/tags/<tag> refs/tags/<tag>^{}
```

Verify final tag commit, notes, required asset digests and requested channel/latest state using the API when CLI fields are insufficient. Repository rules and immutable releases may restrict later changes; never alter those settings to make a release succeed.

## Partial effects

Creation, asset uploads and publication are separate API operations. After failure/timeout, read the existing release and assets before retry; recover its ID and resume matching missing steps only. A 403/404 or unreadable draft may be access failure, not absence. Preserve conflicts and published content; `--clobber` deletes an old asset before replacement and can lose it on failure.
