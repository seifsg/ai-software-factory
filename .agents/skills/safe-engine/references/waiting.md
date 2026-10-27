# Quiet helper waits

Use when a finite delegated job can report completion to its coordinator without polling.

1. Check the host's completion route. A result delivered to the coordinator qualifies; a file write, running process or observer does not. Unsupported: use the host's event wait tool, never a polling agent.
2. Spawn and read its acknowledgement. Run `wait --add <json>` with that actual job identity, coordinator session, finite deadline, current observation and completion-route source. Never register intended work as running.
3. Pass the returned run/job/coordinator/generation identity to the helper. Before its final host response, it runs `wait --finish <json>` with that identity, completed/failed/cancelled result and source. A failed callback is reported in its response, never hidden.
4. Use `wait --status` to see pending names and invalid records. Stop passes only when every owned unfinished run has a supported pending wait. No model turns solely to poll. A new user instruction still takes precedence.
5. On native completion, reconcile the result and continue. Completion is not a passed check or accepted delivery. Failed/cancelled work also ends its wait. Receipt errors, expiry and unknown state require recovery; they never imply success.

Only the gate writes wait receipts. Registration and terminal records are immutable; callbacks do not rewrite run progress. Matching terminal results outrank stale host observations. Repeated identical completion is safe; conflicting results are refused. To reuse a helper for a new job, finish its earlier generation and register the new observation explicitly.

Expiry is checked at the next command or hook. It is not an alarm and cannot wake an idle coordinator. Do not grant a quiet wait without an actual completion route. Preserve pause, owner stop and lost-state recovery. A new run or rehomed coordinator cannot reuse a foreign callback identity.
