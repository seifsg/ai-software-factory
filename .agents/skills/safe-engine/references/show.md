# Look, Show, Prove, Ship

New UI runs follow this checkpoint; old runs keep their order. Resolve the current bundle before starting.

1. Plan the complete changed surfaces and these four phases. Freeze `show --plan <json>` before `done plan`; include light/dark and desktop/phone for each surface. Obtain matching design references before build. Missing references or unsupported variants stay explicit blockers; never invent images or silently drop a variant.
2. **Look:** finish the visual change. Use it before affected tests, type checks and a quick render. No full suite, accessibility audit or deep review yet. Record build start, then `done build`.
3. **Show:** batch known repairs, then freeze source for capture/review/proof. Validate one planned frame and playback/publication route before bulk recording; reuse that valid capture. Inspect every planned pair at matched dimensions/theme/state through real controls and ready conditions. Record `show --candidate`, then `show --prepare <json>`; Markdown pairs each screen/design with a plain description.
4. Share actual pictures; verify each is accessible/readable before `show --shared <json>` records the message, tool result or URL. Generating a report or claiming a send is not delivery. Share complete pictures within one hour of Look; record actual time and any missed target's cause.
5. Record the owner's actual answer with `show --reply <json>`. A stop remains binding; a change needs correction and fresh Show. For “leave that”, record the exact item/answer in the existing follow-ups ticket's Finishing touches section and include its URL. Required scope cuts need the owner's authority; never defer safety or required quality as polish. Design coverage retains its original denominator and owner decision records.
6. No reply: the configured wait, default 30 minutes from recorded delivery, releases only already-authorized Prove. Say that no reply arrived. Do not poll or block the agent with a long sleep; use the host's authorized wake-up facility or resume at the deadline. A timeout is neither approval nor merge permission. Record `done show` once the checkpoint permits proof.
7. **Prove:** final manual use and fresh UX/likeness review, then `prove --suite`. Reuse intact same-candidate/state/input observations/uploads for Show/PR; inspect provenance/access. Image hashes alone prove no freshness. Candidate drift, including tests/docs, needs fresh Show, never relabeled captures. Changed pictures/report need inspection/sharing, not an unchanged suite rerun. Failures, unknown impact and owner stops forbid reuse.
8. **Ship:** deliver the independently complete UI ticket as its own draft PR, with required dependencies integrated and checked. Humans alone decide ready, merge and release. Viewing, replying or timing out grants no merge authority. Do not hold a finished screen for unrelated wave tickets.

## Inputs

All JSON is inside the project, normally ignored `.factory/`. `show --plan` freezes this shape:

```json
{"version":1,"surfaces":[{"id":"home","name":"Home"}],"full_suite":["npm","test"],"suite_inputs":{"files":[],"environment":[]},"wait_minutes":30,"timeout_seconds":1800}
```

`viewports` optionally sets `desktop:[1280,800]` and `phone:[390,844]` (defaults); phone must be narrower. Each pair uses its planned size.

`show --prepare` takes `version:1`, `candidate` and `screens`. One row per surface/theme/device combination, each with a unique `id`, `surface`, `theme` (`light`/`dark`), `device` (`desktop`/`phone`), `viewport:[width,height]`, `state`, matching `reference_state`, PNG `reference` and `capture` paths, one-line `description`, and `inspected:true` only after inspecting both. A design-port run also includes every frozen design screen under its original ID/reference. Pixel checks refuse blank images, not misleading content.

`show --shared` takes `channel` (`chat`/`tool`/`url`), actual `source`, `sent:true` and `images_accessible:true`. Verify these facts first. URL sources use HTTPS; local files may be shown through the host's actual owner-visible image tool, with that tool result as source. The gate cannot prove delivery.

`show --reply` takes actual `source`, `quote`, `action` (`proceed`/`change`/`stop`) and optional `leave:[{"surface":"home","description":"exact item","followup":"https://tracker.example/ticket"}]`. Verify owner identity and cited authority. A follow-up URL is a record, not proof the tracker was updated.

Safe retains its controller: include shared Show, reply/deadline and the current source/captures as UI manual-criterion evidence before its proof batch. Fast commands do not change Safe enforcement.
