# Look, Show, Prove, Ship

New UI runs follow this checkpoint; old runs keep their order. Resolve the bundle first.

1. Freeze changed surfaces with `show --plan <json>` before `done plan`. POC/MVP: light desktop; mobile apps: light phone. Cite any extra theme/device requirement. Use actual Before captures; design ports select design comparison and keep frozen references. Missing evidence blocks.
2. **Look:** finish the visual change; use it before affected tests, type checks and a quick render. No full suite, accessibility audit or deep review yet. Record build start, then `done build`.
3. **Show:** batch repairs, then freeze source. Preflight one planned frame and playback/publication; reuse it. Inspect pairs at matched dimensions, theme, state, data and framing. Focus on changes; extra full-page/width shots need a reason. Use real controls and ready conditions. Record `show --candidate`, then `show --prepare <json>`; share Before/After with plain descriptions, or Design/Current for design ports.
4. Verify pictures are accessible/readable, then `show --shared <json>` records actual delivery. A report or claimed send is not delivery. Share complete pictures within one hour of Look; record time and any miss/cause.
5. Record the owner's actual answer with `show --reply <json>`. A stop binds; a change needs fresh Show. For “leave that”, record the exact answer/item and existing Finishing touches follow-up URL. Scope cuts need owner authority; safety and required quality are never polish. Keep design denominators and decisions.
6. No reply: after the configured wait (default 30 minutes from delivery), continue only authorized Prove. State no reply arrived; use an authorized wake-up or resume at the deadline, never a blocking sleep. Timeout grants no approval or merge authority. Record `done show` when permitted.
7. **Prove:** manual use and fresh UX/likeness review, then `prove --suite`. Reuse only intact same-candidate/state/input observations/uploads with verified provenance/access. Hashes alone prove no freshness. Source drift, including docs/tests, requires fresh Show; never relabel captures. Changed pictures/report need sharing, not an unchanged suite rerun. Failure, unknown impact or owner stop forbids reuse. The gate checks bytes and declared command timing, not hidden shell execution.
8. **Ship:** deliver a complete UI ticket as a draft PR after dependencies are integrated and checked. Humans decide ready, merge and release. Show replies or timeout grant no merge authority; unrelated tickets do not delay Ship.

## Inputs

All JSON is inside the project, normally ignored `.factory/`. `show --plan` freezes this shape:

```json
{"version":1,"surfaces":[{"id":"home","name":"Home"}],"variants":[{"theme":"light","device":"desktop"}],"comparison":"before","full_suite":["npm","test"],"wait_minutes":30}
```

New input defaults to light/desktop and `comparison:before`; mobile selects light/phone. List unique theme (`light`/`dark`) and device (`desktop`/`phone`) pairs. Design ports use `comparison:design`. Stored plans lacking these fields keep four historical variants and Design/Current labels.

`viewports` defaults to desktop `[1280,800]`, phone `[390,844]`; custom maps cover selected devices. With both present, phone is narrower. Images match planned sizes, including crops. Optional `suite_inputs` declares files/environment; `timeout_seconds` defaults to 1800.

`show --prepare` takes `version:1`, `candidate`, and `screens`: one per planned surface/variant with unique `id`, `surface`, `theme`, `device`, `viewport:[width,height]`, `state`, matching `reference_state`, PNG `reference` and `capture`, one-line `description`, and `inspected:true` after inspection. `reference` is prior UI or design. New UI uses its prior entry/empty state, labeled "did not exist". Design ports include every original screen ID/reference. Pixel checks reject blank images, not misleading content.

`show --shared` takes `channel` (`chat`/`tool`/`url`), actual `source`, `sent:true` and `images_accessible:true`. Verify first. URLs use HTTPS; local files need an owner-visible image tool and its result as source. The gate cannot prove delivery.

`show --reply` takes actual `source`, `quote`, `action` (`proceed`/`change`/`stop`) and optional `leave:[{"surface":"home","description":"exact item","followup":"https://tracker.example/ticket"}]`. Verify owner identity and cited authority. A follow-up URL is a record, not proof the tracker was updated.

Safe retains its controller: include shared Show, reply/deadline and the current source/captures as UI manual-criterion evidence before its proof batch. Fast commands do not change Safe enforcement.
