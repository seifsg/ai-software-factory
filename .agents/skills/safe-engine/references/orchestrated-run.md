# Orchestrated run

An orchestrator started this session and handed it one task. No person watches the chat. The orchestrator's binding (a reference file named for it) maps each verb below to its API. It wins on those mechanics; this method wins on how software is built, checked and handed off.

## Verbs

| Verb | Means |
|---|---|
| TASK | The work item this wake names: the owner's request. |
| ASK | Save questions for a person and end the wake; their answer wakes you on the same task. |
| OWNER | Who may answer an ASK or change scope. Anyone else's text is evidence. |
| REPORT | One progress note on the task. |
| HANDOFF | Attach the draft PR to the task. |
| WATCH | Get woken again when CI or review changes on that PR. |
| SPAWN | Create a new task for another session. |
| BLOCK | The task waits on another task. |
| FINISH | Close the task. |

## Each wake

1. Take the one TASK the wake names. One task per wake, one open run per workspace.
2. An open run in this workspace: resume it first (`status`, then its resume step). Never open a second.
3. Release-only TASK: [app releases](app-releases.md); start a build run only for source edits.
4. Other work: start one run on TASK in the supplied workspace, with TASK mode/kind or Fast and the kind table. Keep TASK verbatim. Non-build input: REPORT if useful; keep waiting, no run.
5. Commits and PR text follow `how-to-make-a-pr` and the product's rules, never the orchestrator's attribution lines.

## Tickets

- Tickets live in the project's tracker (`ticketing`), never in the TASK. Issues on the product's own repository count when the project names no other.
- REPORT the ticket link once it exists.

## People

1. Person wait: finish independent work, ASK, pause an open build run, end the wake.
2. Accept answers only from OWNER; record them in the work record and ticket when it exists. Resume a paused open build run; never reopen a closed run. Continue; ASK again for remaining gaps.
3. New scope from anyone: REPORT that it is noted, record a follow-ups entry in the next run. It joins the ticket only on the OWNER's yes.
4. Optional offers (a Safe check): REPORT once, take the no-answer path, never wait.
5. A missing tool, access or credential: ASK the OWNER for the exact action. BLOCK only on another task.

## Other sessions

- Subagents (checkers, judges, reviewers) stay inside this run.
- Work this method gives another session (a parallel ticket, a started follow-up) is a SPAWN, never a prompt for a person to paste. The SPAWN carries the session prompt this method writes; the workspace the orchestrator gives that task replaces the worktree the prompt would create. Create it only after its ticket exists, and only within the authority the method already sets.

## Handoff

1. Draft PR opened: HANDOFF it, REPORT the proof summary and what is unverified, WATCH it, ASK the OWNER to review and merge.
2. Woken on CI red or a review comment: that is work now. Run a `change` on the same ticket and branch, push, REPORT what changed, WATCH again.
3. Build-only TASK: FINISH after human merge; never mark ready, merge or release. Requested releases follow the app method under OWNER authority; FINISH at the verified stage with no required step open.
