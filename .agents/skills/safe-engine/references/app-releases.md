# App releases

Use during normal app work when prior releases or a release policy exist, and for release requests. Preserve the app's process; this method grants no publication authority.

## Discover and retain

1. Before planning edits, read existing release instructions, version/changelog files, scripts, generator config and automation. Cross-check the latest relevant release, its tag/commit and preparation diff. Missing remote access means unverified history, not no releases.
2. Identify the canonical process and each step's owner. Capture working directory, exact commands/order, inputs/config, version copies/build numbers, tag/signing/branch/channel rules, checks, artifacts and verification. Inspect merge/tag/publish triggers and side effects before running a tool.
3. Preserve changelog format, categories, ordering, links and timing. Distinguish per-change entries/fragments from release-time generation. Identify whether notes come from curated text, a changelog section or a configured generator/range. Do not substitute factory conventions or infer policy from one filename.
4. Reuse the existing project guide, scripts and config as the source of truth. During authorized source work, fill verified documentation gaps there; absent a guide, document the verified steps once in the project's established docs location. Keep credentials out; name requirements only. Do not create a competing policy or keep the only reusable steps in an ignored worktree record.
5. Carry canonical source paths/revisions, applicable steps and owners into the plan, delegate briefs, PR checks and handoff in every mode. Reuse verified pointers on resume; re-read changed sources or resolve contradictory instructions/history before dependent work. Preserve active runs, pins and owner stops.

No release history: still follow declared policy. If neither exists, propose conventions before dependent work; never invent a previous release or initial version. Explicit analysis/planning/review limits still apply to source and tracker writes.

## Ordinary changes

1. Perform the app's change-time obligations as part of the feature/fix. Use its entries, fragments or metadata; preserve generated outputs and historical entries. Bump versions only at the stage its policy requires, including companion values.
2. Use an explicit requested version, or derive a proposed increment from actual compatibility changes under the app's policy. Honor nonstandard versions, prereleases and component scope. Conflicting policy or an owner-reserved choice stays unresolved; no silent replacement.
3. Source edits use normal delivery checks and draft PRs. Record completed steps, generator-owned outputs and remaining release/owner actions. A merged implementation ticket does not prove a published release.

## Prepare and execute a release

1. Bind the repository/component, previous release, intended change range, accepted exact source commit and requested terminal stage. Verify ancestry/included changes. Follow existing tooling and stage order, including existing automation; never add direct publication beside a tool that owns it.
2. Prepare version/notes/upgrade information and required artifacts through that process. Bind artifact names, sizes and digests to the accepted build/config. Check freshness after merge/source/config changes; rerun affected checks when earlier proof no longer applies. Source-only releases need no dummy assets.
3. Keep one ignored per-attempt record, preferably the app's existing record, else `.factory/releases/<safe-local-key>/release.md`. Check ignore rules and safe path first. Record process pointers, request/authority, version/tag/channel/commit, notes/artifact digests, commands/results, remote identity and completed/remaining steps. Saved progress is neither authority nor current remote proof.
4. Finish the concrete prepared package before asking for missing authority. An existing explicit grant covers its disclosed steps without repeated confirmation. Draft, tag push, publication and deployment retain their own boundaries. If a script/trigger would exceed them, stop before that effect and name the remaining action.
5. Execute the app's documented commands. Missing provider capabilities: discover available tools first. Only when its process calls for direct provider operations, load the matching tool reference ([GitHub](github.md)); do not insert an alternative stage order.
6. Read back the result. Verify version/tag, actual peeled tag commit, notes, channel/draft/latest state and required artifact bytes/digests. Metadata naming a target is not proof of the tag's commit. Fetch exact assets for digest comparison when the provider lacks digests; names/sizes alone are insufficient. Report URL, prepared/draft/published status and gaps; deployment needs separate live proof.

## Reconcile and resume

- Uncertain create/upload/publish result: read actual tag/release/assets before retrying. A failed command does not prove no remote effect. Preserve diagnostics and unknown state.
- Matching complete release: verify and report already complete. Matching draft: resume only missing authorized steps. Active competing publisher or unclear ownership: stop dependent writes.
- Mismatched tag, notes or same-name artifact bytes: report conflict. Never move a published tag, overwrite, delete/recreate, or rewrite release history to force a match. Published incomplete releases need the app's recovery policy and appropriate authority.
- Missing permissions, unreadable drafts or private-repository errors: access remains unknown; never interpret them as absence or broaden credentials automatically.
- Changed source/config/notes/artifacts: reconcile with canonical policy and refresh affected preparation/proof before mutation. Keep prior failures; do not repeatedly retry an undiagnosed effect.
- Next session/worktree: recover canonical project process pointers and the attempt record, verify their sources and remote state, then continue the first unfinished step. Do not reopen a closed build run or replace its pinned methods.
