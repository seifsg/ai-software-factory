# Night mode

Unattended run: owner starts it with host's night command, reads result in the morning. Run file header shows `Night: until <time>`; guard holds the deadline and halts run there.

Night command refuses to start unless the run can finish unattended. Started session denies instead of prompting: a command the rules do not allow fails, never waits.

## While it runs

0. **Stop hook asks for the factory check:** never run it, never ask for approval. Say `check denied at night` once; the command guard drives.
1. **Owner questions:** never wait. Take the recommended answer and record `Default: <question> → <choice> (<why>)` in the step's block and the ticket's activity. Owner can reverse before merging.
2. **Owner-reserved items** (spend, release, merge, scope beyond the ticket, deleting data, anything the request did not cover): never decide them. Record `Parked: <item>, needs <what>` in the step's block and the ticket's activity, and continue with independent work. Only parked work left, or a parked item blocks a required fix: `Waiting: owner: <the parked list>`.
3. **Outward actions:** push the run's own branch, open or update its draft PR and its tickets. Nothing else leaves the machine. A denied command is never retried another way: park it.
4. **Gates:** no waivers. A gate passes by its checker or its loop runs into the cap.
5. **Relay:** guard asks for one before steps 4, 6 and 8 and after two compactions. Make sure run file and ticket hold everything next step needs, then end session as prompt says. Fresh session reads only those two.
6. **Halt:** write the packet, set `Waiting: owner:`, end the turn. Never work around a halt.
7. **Delegates:** run in foreground, wait for result in same turn: a print-mode session may end with its turn, before a background result arrives.

## Morning

Watchdog sends one notification: done (draft PR), halted (reason and packet) or parked (list). Owner answers in run's session or runs guard's `clear` after a halt; `clear` also ends night mode and removes `Night:` line.
