# PR cases

Rare situations for SKILL.md steps 3 and 7. Commands: `github.md`.

## Branch

- **Dependent ticket:** branch from the dependency's delivered commit; PR against the dependency's branch, retargeted to the base once that branch merges. Several dependencies: against the base, naming each dependency PR that merges first.
- **Wrong base:** head already on the right ancestry: change the PR base. Diverged: new branch from the right base, cherry-pick the relevant commits, open a replacement PR, close the old one as replaced after approval. No force-push.
- **Hotfix**, only on explicit request. Separate production and integration branches mean a pair: the production PR plus a companion PR with the same change, branched from integration with `git cherry-pick -x` of only the fix commits. Never a PR from the production branch into integration: it drags in production-only commits. Link both; mirror every follow-up. One release branch: no pair.

## Remote review

Request a fresh one (separate agent, fresh context, the exact pushed head); record where it ran, run ID, base/head and verdict. Local review never substitutes; missing remote access leaves the review open.
