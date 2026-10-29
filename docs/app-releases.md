# App releases

Normal factory work discovers how an existing app ships. It retains that process through planning, implementation, PR checks, handoff and later sessions. A separate release request is not needed to remember changelog or version obligations.

## Existing process first

The agent reads the app's existing guide, scripts, version files, changelog, generators and automation, then checks relevant release/tag/preparation evidence. It records:

- Exact working directory, commands and order, inputs/config and step owners.
- Version source and companion values, bump timing, component/branch/tag/signing/channel rules.
- Changelog structure and update timing; curated notes versus generator-owned outputs.
- Required artifacts, build/checks, side effects, publication and verification steps.

Existing project instructions and tools remain authoritative. Contradictory sources or inaccessible release history remain explicit. The agent never treats a failed private-repository lookup as proof that no release exists.

If the guide omits verified steps, authorized source work fills the gap in that guide. If no guide exists, add one small guide in the app's established docs location. Do not create a parallel policy or keep the sole reusable instructions in one ignored worktree folder.

Plans, delegate briefs, PR checks and handoff carry canonical source paths/revisions, applicable obligations and remaining steps. On resume, reuse those pointers and re-read sources that changed or conflict. This applies to Fast, Lucky and Safe without new gate/controller fields.

## Ordinary features and fixes

Follow each app's timing and format:

| App process | Factory behavior |
|---|---|
| Each PR adds a curated changelog entry | Add the entry in its existing section, category and order |
| Each PR adds a change fragment | Add the expected fragment; preserve generated changelog and notes |
| Version bumps occur only at release | Keep versions unchanged during ordinary fixes |
| A release tool updates several version values | Use that tool at the prescribed stage; do not hand-edit one copy |
| Automation publishes after an approved trigger | Follow the trigger and verify its result; do not publish a second release |

No imposed changelog format, new generator or universal version parser. An app with no history still follows its declared policy. Only when both are absent does the factory propose conventions before dependent work.

## Creating a release

The existing app process determines command order. The factory binds the intended previous-release range and accepted source commit, prepares its version/notes/artifacts, then performs only authorized remote effects. Source edits still use normal review and draft PRs. Release-only work needs no artificial build run.

A concrete prepared package includes the process source, exact commit, version/tag/channel, notes, required artifact names/digests, completed checks and remaining commands. Verify final artifacts against the accepted build/config, including changes introduced at merge.

Publication authority does not imply deployment authority. Inspect configured tag/merge/publish triggers before a step that could deploy or publish elsewhere. Existing explicit grants cover their disclosed sequence without repeated confirmation; otherwise finish preparation and present the remaining action.

For a single attempt, reuse the app's existing ignored release record, else an ignored `.factory/releases/<safe-local-key>/release.md`. Keep reusable process instructions in project docs. The record holds authority/limits, source pointers, completed steps, notes/artifact digests, command results, remote identity and next action. It cannot grant authority or replace a current remote read.

When direct provider operations are part of the app's process, use available integrations or authenticated local tooling. GitHub's fallback commands live in the method's `references/github.md`; they do not override an app's release script. No hosted CI requirement is introduced, and existing required app checks remain.

## Verification and recovery

Read back the release URL/identity, actual peeled tag commit, notes, requested draft/prerelease/latest state and required artifact integrity. Provider target metadata or matching filenames/sizes alone do not prove the source or bytes. Compare provider digests or download exact assets for digest verification when necessary.

Prepared, draft, published and deployed remain separate states. A merged implementation ticket does not certify publication. Orchestrated build-only tasks finish after human merge; requested releases finish at their verified stage, including when source preparation first needs a human merge.

- Matching complete release: verify and report it instead of creating another.
- Matching partial draft: resume only missing authorized steps.
- Uncertain create/upload/publish: reconcile actual remote state before retrying.
- Conflicting tag, content or asset bytes: preserve it and report the conflict; no tag move, clobber or automatic delete/recreate.
- Missing access, competing writer or changed source/config: stop dependent mutations and resolve the cause.

## Use

Normal work: `safe-engine Fix <behavior> in <absolute app path>.` Release-process discovery is part of that delivery.

Explicit release work: `safe-engine Prepare the next release in <absolute app path>.` or `safe-engine Publish version <version> in <absolute app path>.` Only the requested and authorized effects are performed.

The workflow is agent instructions backed by existing tools, not a new publication runtime or tamper-resistant approval system. Method walkthroughs and local fixtures do not prove a real hosted release; actual hosted verification requires an authorized disposable target or an explicitly authorized app release.
