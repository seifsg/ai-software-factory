# Show the visual change before proof

New UI runs on the resolved current bundle plan Look, Show, Prove and Ship. Logic-only and older pinned runs retain their order. The viewer is unchanged; Show generates a Markdown report that the coordinator shares through the available owner-visible channel.

Before `done plan`, freeze the changed surface inventory, exact full-suite argv and response wait with `show --plan <json>`. After the full visual build and quick render, record `done build`. Prepare four paired cases per surface: light/dark at desktop/phone dimensions, each with a matching reference and one-line change description. Missing references remain blockers. The full schema is in the [Show method](../.agents/skills/safe-engine/references/show.md).

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

`viewports` defaults to desktop1280x800 and phone390x844; override both before plan for the design references. Phone must be narrower.

`wait_minutes` defaults to30 and accepts0..1440; `timeout_seconds` defaults to1800 and accepts1..86400. The clock starts on recorded delivery. Zero is useful for explicitly configured isolated walkthroughs; it does not fake30 minutes passing. Before expiry, proof is refused without a recorded proceed reply. Explicit stop/change replies override the timer. A stop survives new pictures until the owner's subsequent proceed answer; a requested change is corrected and shown again. “Leave that” records the exact owner answer and its existing Finishing touches follow-up URL, without silently changing required scope.

`prove --suite` rechecks current source, report and picture hashes before executing the frozen argv without a shell through the existing bounded runner. The installed entry validates the run's selected bundle and uses its runner. It writes `.factory/fast/prove-suite.log`; failures/timeouts remain failures. Hook-capable hosts also refuse recognized direct invocations of the declared suite before the checkpoint. Hooks do not sandbox arbitrary programs that conceal tests; without hooks, use the explicit runner. Non-ignored test/docs edits also change the conservative source fingerprint, requiring fresh inspected/shared Show evidence. Completion rejects a passing receipt for older source, including after a fresh Show. Refreshing pictures alone preserves a pass for unchanged source. Replaced proof receipts remain in the bounded gate log.

An independently complete UI ticket gets its own draft after Prove. Its dependencies must already be included and checked. Humans retain merge/release authority; viewing, replying or a timeout never grants it. Safe retains its existing candidate-bound manual-evidence route; these commands govern Fast/Lucky only.
