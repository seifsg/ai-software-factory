# App releases

Use when the app has prior releases or a declared release policy, and for release requests. This method grants no publication authority.

## Every change

1. Before planning, find the app's process: release guide, scripts, version files and their copies, changelog, notes source or generator, automation and its triggers. Cross-check the latest release. Unreadable history is unverified, never absent.
2. Follow it exactly: changelog format, section, order and timing; per-change entries or fragments versus generated files; version bump stage; tag, branch and channel rules. Never impose factory conventions, hand-edit generated output or bump a version early.
3. Conflicting sources, or neither history nor policy: ask before dependent work. Never invent a previous release or version.
4. Plan, briefs, PR checks and handoff carry the process source paths and the remaining release steps. On resume, re-read sources that changed. Reusable steps live in the project's own release guide; fill verified gaps there during authorized work. No new gate or controller fields.

## Release work

Release-only work needs no build run; source edits use normal delivery.

1. Bind the exact source commit, the previous release and the requested stage: prepared, draft or published. Deployment needs its own authority.
2. Run the app's own tools in their order. Never publish beside automation that owns publication. Call the provider directly only where the process does.
3. A step without authority: finish everything before it, stop and name the exact remaining action.
4. Keep progress in the app's release record, else an ignored `.factory/releases/<version>/release.md`: authority, commit, version, digests, commands and results, next step. It is neither authority nor remote proof.
5. Read back version, peeled tag commit (target metadata is not proof), notes, draft or prerelease state and artifact digests. Report the URL and stage.

## Recovery

- Failed or uncertain create, upload or publish: read remote state before any retry. A failed command does not prove no effect; a 403 or 404 may be access, not absence.
- Matching release: report it done. Matching draft: finish only the missing steps.
- Mismatched tag, notes or artifact bytes: report the conflict. Never move a published tag, overwrite an asset or delete and recreate.
