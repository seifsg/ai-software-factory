# Show and scoped reuse

New UI runs use Look, Show, Prove, Ship; stored plans/pins retain their contracts. [Complete schema and sequence](../.agents/skills/safe-engine/references/show.md).

Capture actual Before before source edits and bind it in show --plan. Use final QA for After/video; keep early Before. Default variants are light/desktop, or light/phone for mobile; additional variants require a source. Design references supplement actual Before/After.

Optional visual_inputs enables scoped reuse. Example:
```json
{"nonvisual":{"unit.py":"Not imported by the static renderer"},"evidence":".factory/render-inputs.json","files":[".factory/fixture.json"],"environment":["TZ"]}
```
The evidence JSON declares complete:true and sources:["index.html"]. Establish completeness from actual dependencies, not filename extensions; rendering sources cannot be exceptions. Exact existing source paths only. All other source, dependency evidence and declared runtime inputs remain identity-bound. Unknown impact means fresh affected proof. Optional clock uses instant/timezoneId, as suite_inputs does.

Reuse preserves original candidate/record time and compatible delivery/deadline/proceed response. Stop/change remains binding. Changed visual meaning needs the normal sharing process. Show, viewer and likeness share this identity; the final suite and hidden acceptance still bind the whole candidate. The gate validates declared bytes/identities, not dependency completeness or owner authenticity.

Commands: `python skills/safe-engine/scripts/fast_gate.py show --plan .factory/show-plan.json` (also --candidate, --prepare, --shared, --reply). `python skills/safe-engine/scripts/fast_gate.py prove --suite` follows manual use and owner reply/deadline; timeout is not merge authority. Legacy plans without optional reuse remain conservative. No new stage, extra default form or mandatory helper.

The legacy full_suite field holds the planned validation command, which may be affected tests. Record scope once; preserve exact proof identity. Full suites are justified by shared risk, unknown impact or release, not every edit/push.
