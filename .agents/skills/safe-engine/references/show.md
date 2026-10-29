# Show before proof

Look, Show, Prove, Ship. Existing pins keep their order.

1. Before edits, capture affected existing views. Before `done plan`, freeze surfaces, variants, suite and wait with `show --plan <json>`; bind actual `before` rows. Design ports retain their frozen design references; PRs still need actual Before/After.
2. **Look:** implement, use it, then affected tests/type checks and a quick render. Record build start and `done build`. No full suite, accessibility audit or deep review yet.
3. **Show:** batch known repairs and freeze source. Preflight capture/playback/publication with one planned frame; reuse it. Inspect matched viewport/theme/state/data/framing pairs through real controls. Record `show --candidate`, then `show --prepare <json>`; share Before/After or Design/Current with plain descriptions.
4. Verify owner access and record `show --shared <json>`. Share within one hour of Look; record misses/causes. A local report is not delivery.
5. Record the actual answer with `show --reply <json>`. Stop/change binds. “Leave that” needs exact item/answer and the existing Finishing touches URL; scope cuts need owner authority. Safety/required quality are not polish.
6. No reply: after the wait (default30minutes from delivery), continue authorized Prove. Use an authorized wake-up/resume, never blocking sleep. Timeout grants no merge approval.
7. **Prove:** manual use and UX/likeness review, then `prove --suite`. Reuse intact observations/uploads only with verified inputs, provenance and access. Default source drift, including docs/tests, needs fresh Show; optional scoped reuse below retains original observations. Changed images/report need sharing, not an unchanged suite rerun. Unknown impact, failure or stop never grants reuse.
8. **Ship:** live `ticketing` refresh, criteria/proof, `how-to-make-a-pr`, draft, `done handoff`. Human ready/merge/release.

## Inputs

JSON stays project-local, normally ignored `.factory/`. Plan example:
```json
{"version":1,"surfaces":[{"id":"home","name":"Home"}],"variants":[{"theme":"light","device":"desktop"}],"comparison":"before","before":[{"id":"home-before","surface":"home","theme":"light","device":"desktop","state":"ready","reference":".factory/fast/shots/home-before.png"}],"full_suite":["npm","test"],"wait_minutes":30}
```

- New defaults: light/desktop; mobile selects light/phone. Extra themes/devices need a request or existing requirement. Unique theme/device pairs only; legacy plans without variants retain all four. Design ports use `comparison:design`; old plans without comparison retain Design/Current.
- `before`: one actual image row per planned pair, including manual/native captures. Final Show retains its bytes/state. New UI uses the prior entry/empty state, labeled “did not exist”. Disclose missing early captures in legacy runs.
- `viewports`: desktop `[1280,800]`, phone `[390,844]`; custom maps cover selected devices, phone narrower when both exist. Images match sizes, including crops.
- `full_suite`: argv; optional `suite_inputs` names files/environment/clock; `timeout_seconds` defaults1800.
- Prepare: `version:1`, current `candidate`, `screens` per planned pair: unique `id`, `surface`, `theme`, `device`, `viewport`, `state`, matching `reference_state`, PNG `reference`/`capture`, one-line `description`, `inspected:true`. Design ports include every original screen/reference. Pixel checks detect blank/corrupt content, not wrong screens.
- Shared: `channel:chat|tool|url`, actual `source`, `sent:true`, `images_accessible:true`; URLs HTTPS. Reply: `action:proceed|change|stop`, `source`, exact `quote`; optional `leave:[{surface,description,followup}]`.

## Scoped reuse

Only when useful, plan `visual_inputs`: `nonvisual` maps exact source paths to reasons; `evidence` names local JSON with `complete:true,sources:[...]`; `files` and `environment` list runtime inputs, optional `clock` fixes time. Rendering sources cannot be excluded. Establish the dependency evidence through actual inspection; a declaration cannot prove its own completeness. No glob or file-extension exemptions.

All other source, exception presence, dependency evidence and runtime inputs remain bound. Unknown/changed inputs or tampered media require fresh affected After. Carrying preserves the original candidate/record time and compatible owner delivery/deadline/response; never relabel it as a new capture or overwrite Before. Explicit stop/change remains binding. Show, viewer and likeness use the same visual identity; final suite/acceptance still use the full candidate.

Safe keeps its controller and shared Show/reply evidence. Fast commands never change Safe enforcement.
