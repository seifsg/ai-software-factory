# Look, Show, Prove, Ship

New UI runs follow this checkpoint; old runs keep their order. Resolve the current bundle before starting.

1. Freeze changed surfaces with `show --plan <json>` before `done plan`. POC/MVP: light desktop; mobile apps: light phone. Extra themes/devices need a cited request/requirement. Use actual Before captures; design ports select design comparison and keep every frozen reference. Missing required evidence blocks.
2. **Look:** finish the visual change. Use it before affected tests, type checks and a quick render. No full suite, accessibility audit or deep review yet. Record build start, then `done build`.
3. **Show:** inspect pairs at matching dimensions, theme, state, data and framing. Focus on changes with context; extra full-page/width shots need a coverage reason. Use real controls/ready conditions. Record `show --candidate`, then `show --prepare <json>`. Share Before/After with a plain description. Design ports show Design/Current too; the PR keeps actual Before/After.
4. Share actual pictures; verify access and readability, then `show --shared <json>` with the message, tool result or URL. Generating a report is not delivery. Share the first complete pictures within one hour of Look; record actual time and any miss/cause.
5. Record the actual owner answer with `show --reply <json>`. Stops bind; changes need correction and fresh Show. “Leave that”: put the exact item/answer in the existing follow-ups ticket's Finishing touches, with its URL. Scope cuts need owner authority; safety/required quality are never polish. Keep design denominators and owner records.
6. No reply: after the configured wait (default 30 minutes from delivery), continue only authorized Prove; state no reply arrived. Never poll or sleep through the wait; use an authorized wake-up or resume at the deadline. Timeout grants no approval or merge authority. Record `done show` when permitted.
7. **Prove:** manual use and fresh UX/likeness review, then `prove --suite`. Changed source, pictures or report need inspected/shared fresh Show. Picture-only refresh never repeats an unchanged full suite. Preserve evidence. The gate checks bytes and declared command timing, not hidden shell execution.
8. **Ship:** independently complete UI tickets get draft PRs after dependencies are integrated and checked. Never hold them for unrelated tickets. Humans decide ready, merge and release; Show grants none of these.

## Inputs

All JSON is inside the project, normally ignored `.factory/`. `show --plan` freezes this shape:

```json
{"version":1,"surfaces":[{"id":"home","name":"Home"}],"variants":[{"theme":"light","device":"desktop"}],"comparison":"before","full_suite":["npm","test"],"wait_minutes":30}
```

New input defaults to light/desktop and `comparison:before`; mobile selects light/phone. List unique theme (`light`/`dark`) and device (`desktop`/`phone`) pairs. Design ports use `comparison:design`. Stored plans lacking these fields keep four historical variants and Design/Current labels.

`viewports` defaults to desktop `[1280,800]`, phone `[390,844]`; custom maps cover selected devices. With both present, phone is narrower. Images match planned sizes, including crops. Optional `suite_inputs` declares files/environment; `timeout_seconds` defaults to 1800.

`show --prepare` takes `version:1`, `candidate` and `screens`: one row per planned surface/variant, unique `id`, `surface`, `theme`, `device`, `viewport:[width,height]`, `state`, matching `reference_state`, PNG `reference` and `capture`, one-line `description`, and `inspected:true` after inspection. `reference` is the prior UI for before comparison, the design for design comparison. New UI uses the prior entry/empty state, labeled "did not exist". Design ports include every original screen ID/reference. Pixel checks reject blank images, not misleading content.

`show --shared` takes `channel` (`chat`/`tool`/`url`), actual `source`, `sent:true` and `images_accessible:true`. Verify these facts first. URL sources use HTTPS; local files may be shown through the host's actual owner-visible image tool, with that tool result as source. The gate cannot prove delivery.

`show --reply` takes actual `source`, `quote`, `action` (`proceed`/`change`/`stop`) and optional `leave:[{"surface":"home","description":"exact item","followup":"https://tracker.example/ticket"}]`. Verify owner identity and cited authority. A follow-up URL is a record, not proof the tracker was updated.

Safe retains its controller: include shared Show, reply/deadline and the current source/captures as UI manual-criterion evidence before its proof batch. Fast commands do not change Safe enforcement.
