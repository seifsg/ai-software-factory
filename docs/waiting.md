# Quiet waits

`fast_gate.py wait --add registration.json --project <absolute-project>` records an acknowledged finite helper or background job. `wait --status` shows current names, terminal results and recovery problems. `wait --finish completion.json` appends a terminal receipt; it never rewrites the run ledger.

Registration fields (all required, no extra keys):

```json
{
  "version": 1,
  "coordinator": "actual-host-session-id",
  "job": "actual-returned-helper-id",
  "name": "Check the changed screen",
  "kind": "helper",
  "host": "codex",
  "wakeup": "native-subagent-result",
  "source": "Host spawn acknowledgement and native completion delivery",
  "observed_at": "2026-01-01T10:00:00Z",
  "expires_at": "2026-01-01T10:30:00Z"
}
```

Replace the sample timestamps and identifiers with actual observations. Observations must be no older than five minutes; deadlines must be future and at most 24 hours after observation. `kind` is `helper` or `job`; `wakeup` is `native-subagent-result` or `none`. Unsupported routes/jobs can be recorded, but do not exempt Stop. A bare process or lane supervisor is not evidence of a parent wakeup. Native subagent results are supported for Codex and Claude Code; other hosts use their event wait tool until their adapter has a verified completion route.

The command returns `run`, `coordinator`, `job` and a fresh `generation`. Copy exactly those fields into completion JSON, adding `version: 1`, `status` (`completed`, `failed` or `cancelled`) and a short `source` identifying the observed result. Give this identity to the helper after spawn. The helper writes completion before its final native response; callback failure must be visible in that response. A receipt does not send a host notification.

Receipts live under the gate home's `waits/` using project/run identity. Registration uses the existing project selection lock; OS exit releases it. Atomic create-only terminal writes preserve identical replay and refuse conflicting results. Each run permits at most 256 generations; all fields and reads are bounded. Pending duplicate job registrations are refused. Reuse after terminal completion gets a new generation. No daemon or model polling is added.

Every owned unfinished run needs eligible pending work for Stop to pass. Paused, closed, repeated and aborted stops retain their existing behavior. Matching terminal receipts override stale host background lists. Missing identity, corrupt data, clock rollback, expiry or an unsupported route removes the exemption. An expired receipt does not schedule a wakeup. New runs require explicit receipts; older runs retain their host-list rule unless they register a wait.

Matching host observations of an observer, persistent task or server remove the exemption. An absent or empty background list is not a complete inventory and does not cancel an otherwise valid receipt. Input text is trimmed at registration and completion; returned identity fields are the exact values required by the completion command. A registration is refused before writing if its serialized receipt would exceed the read limit.

The gate validates declared identities and state transitions, not the truth of a caller's host observation. Verify acknowledgement, finite work and actual result delivery. Normal permissions still govern the helper. `status` is an observation, not liveness telemetry; it does not prove a job succeeded or that its output meets the ticket.
