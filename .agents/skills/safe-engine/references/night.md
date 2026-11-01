# Night mode

An unattended run: the owner starts it with the host's night command and reads the result in the morning. The run file's header shows `Night: until <time>`; the guard holds the deadline and halts the run there.

The night command refuses to start unless the run is open, the guard is wired, the deny rules are in force, the branch is the run's own, the pre-push hook is installed and a push dry run and tracker sign-in work. The session it starts denies instead of prompting: a command the rules do not allow fails, it never waits.

## While it runs

1. **Owner questions:** never wait. Take the recommended answer and record `Default: <question> → <choice> (<why>)` in the step's block and the ticket's activity. The owner can reverse it before merging.
2. **Owner-reserved items** (spend, release, merge, scope beyond the ticket, deleting data, anything the request did not cover): never decide them. Record `Parked: <item>, needs <what>` in the step's block and the ticket's activity, and continue with independent work. Only parked work left, or a parked item blocks a required fix: `Waiting: owner: <the parked list>`.
3. **Outward actions:** push the run's own branch, open or update its draft PR and its tickets. Nothing else leaves the machine. A denied command is never retried another way: park it.
4. **Gates:** no waivers. A gate passes by its checker or its loop runs into the cap.
5. **Relay:** the guard asks for one before steps 4, 6 and 8 and after two compactions. Make sure the run file and the ticket hold everything the next step needs, then end the session as the prompt says. The fresh session reads only those two.
6. **Halt:** write the packet, set `Waiting: owner:`, end the turn. Never work around a halt.
7. **Delegates:** run them in the foreground and wait for their result in the same turn: a print-mode session may end with its turn, before a background result arrives.

## Morning

The watchdog sends one notification: done (the draft PR), halted (the reason and the packet) or parked (the list). The owner answers in the run's session or runs the guard's `clear` after a halt; `clear` also ends night mode and removes the `Night:` line.
