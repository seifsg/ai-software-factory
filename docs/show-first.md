# Show the visual change before proof

New UI runs on the resolved current bundle plan Look, Show, Prove and Ship. Logic-only and older pinned runs retain their order. The viewer is unchanged; Show generates a Markdown report that the coordinator shares through the available owner-visible channel.

Before `done plan`, freeze changed surfaces, selected variants, exact full-suite argv and response wait with `show --plan <json>`. POC/MVP defaults are light desktop, or light phone for a mobile app. Build, inspect, screenshot and test extra themes/devices or responsiveness only when explicitly requested or already required; record the source. After the visual build and quick render, record `done build`. Missing required evidence remains a blocker. The full schema is in the [Show method](../.agents/skills/safe-engine/references/show.md).

Keep elegant visuals and polished motion; honor reduced-motion preferences.

New plan example: `{"version":1,"surfaces":[{"id":"summary","name":"Summary"}],"variants":[{"theme":"light","device":"desktop"}],"comparison":"before","full_suite":["npm","test"]}`. Omitting `variants` or `comparison` in new input selects these defaults. A mobile app sets `variants:[{"theme":"light","device":"phone"}]`; an explicit light/dark desktop request lists both theme/desktop pairs. Only listed pairs are required; missing, duplicate or unplanned captures fail preparation.

For ordinary changes, `reference` is an actual prior-state screenshot and `capture` the current candidate. Match viewport, theme, state, data and framing; focus on what changed with enough context. Use extra full-page shots only to prove required coverage. New UI uses the prior entry/empty state, labeled "did not exist". Design ports select `comparison:"design"` to show Design/Current and retain every frozen reference; their PR still includes actual Before/After.

```text
python skills/safe-engine/scripts/fast_gate.py show --project <project> --plan .factory/show-plan.json
python skills/safe-engine/scripts/fast_gate.py show --project <project> --candidate
python skills/safe-engine/scripts/fast_gate.py show --project <project> --prepare .factory/show-input.json
python skills/safe-engine/scripts/fast_gate.py show --project <project> --shared .factory/show-delivery.json
python skills/safe-engine/scripts/fast_gate.py show --project <project> --reply .factory/show-reply.json
python skills/safe-engine/scripts/fast_gate.py done show --project <project>
python skills/safe-engine/scripts/fast_gate.py prove --project <project> --suite
```

Preparation writes `.factory/fast/show.md` and prints its reference/current pairs. It does not send anything. Inspect the actual images, share them, verify access, then record the actual message/tool/HTTPS source. A local path alone is refused. The gate validates records and hashes; it cannot authenticate a sender, an owner answer or actual image inspection.

`viewports` defaults to desktop1280x800 and phone390x844. A custom map may contain just the selected device; each image must match its planned dimensions, including matched crops. When both devices have geometry, phone must be narrower. Old stored plans lacking `variants`/`comparison` retain all four light/dark desktop/phone cases and Design/Current labels. Active bundle pins never change automatically; no saved-plan migration is required.

`wait_minutes` defaults to30 and accepts0..1440; `timeout_seconds` defaults to1800 and accepts1..86400. The clock starts on recorded delivery. Zero is useful for explicitly configured isolated walkthroughs; it does not fake30 minutes passing. Before expiry, proof is refused without a recorded proceed reply. Explicit stop/change replies override the timer. A stop survives new pictures until the owner's subsequent proceed answer; a requested change is corrected and shown again. “Leave that” records the exact owner answer and its existing Finishing touches follow-up URL, without silently changing required scope.

`prove --suite` rechecks current source, report and picture hashes before executing the frozen argv without a shell through the existing bounded runner. The installed entry validates the run's selected bundle and uses its runner. It writes `.factory/fast/prove-suite.log`; failures/timeouts remain failures. Hook-capable hosts also refuse recognized direct invocations of the declared suite before the checkpoint. Hooks do not sandbox arbitrary programs that conceal tests; without hooks, use the explicit runner. Non-ignored test/docs edits also change the conservative source fingerprint, requiring fresh inspected/shared Show evidence. Completion rejects a passing receipt for older source, including after a fresh Show. Refreshing pictures alone preserves a pass for unchanged source. Replaced proof receipts remain in the bounded gate log.

An independently complete UI ticket gets its own draft after Prove. Its dependencies must already be included and checked. Humans retain merge/release authority; viewing, replying or a timeout never grants it. Safe retains its existing candidate-bound manual-evidence route; these commands govern Fast/Lucky only.

## Bounded capture and reuse

Freeze a required inventory in the plan. Finish known repairs in one batch before final capture; validate one planned frame, playback and the authorized publication route before bulk work. Reuse that valid artifact for Show and PR proof. Input variants with identical visible states need behavioral coverage, not repeated screenshots; clips may cover several outcomes with explicit chapters. Required journeys and frozen variants remain mandatory.

For unchanged candidate, state and effective inputs, retain intact observations and uploaded URLs with their original provenance and verify reviewer access. PNG validation caching does not prove a current observation. There is no per-surface dependency identity that permits cross-candidate Show reuse: source drift, including test/docs edits, still needs fresh inspected/shared Show. Never rewrite an old capture's candidate. Picture-only refresh does not rerun an intact unchanged suite; failed/tampered/unknown evidence and owner stops remain blocking.

Preflight uncertain wrapper guards/imports with their actual interpreter and non-interactive environment using a harmless bounded probe. For visual PR work, read the [media proof method](../.agents/skills/how-to-make-a-pr/references/media-proof.md). Keep the complete tool return, command, session and exit result. Pending or missing results never pass. This is capability discovery, not permission to run the full project suite before manual use/Show. Diagnose failures before retrying; neither a wrapper preflight nor a cached image is an acceptance result.
