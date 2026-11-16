# PR cases

Rare situations for SKILL.md steps 3, 7 and 8. Commands: `github.md`.

## Epic waves

- Share one integration branch and draft PR. Finished lanes incorporate it, resolve/recheck, then integrate and push without force. Exception: independently complete UI ticket ships own draft after its verify; dependencies must be included and checked. Never wait on unrelated wave tickets.
- Wave's draft PR open: push to that branch and update that PR: append run's outcomes, criteria verification, remaining steps; refresh summary.

## Branch

- **Dependent ticket:** branch from dependency's delivered commit; PR against dependency's branch, retarget to base once it merges. Several dependencies: against base, naming each dependency PR that merges first.
- **Wrong base:** head already on right ancestry: change PR base. Diverged: new branch from right base, cherry-pick relevant commits, open replacement PR, close old one as replaced after approval. No force-push.
- **Hotfix**, only on explicit request. Separate production and integration branches = a pair: production PR plus companion PR with same change, branched from integration with `git cherry-pick -x` of only fix commits. Never a PR from production branch into integration: drags in production-only commits. Link both; mirror every follow-up. One release branch: no pair.

## Remote review

Request a fresh one (separate agent, fresh context, exact pushed head); record where it ran, run ID, base/head, verdict. Local review never substitutes; missing remote access leaves review open.
