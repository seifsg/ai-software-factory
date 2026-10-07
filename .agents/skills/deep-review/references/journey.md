# User Journey

One question: in the target environment, do users get the promised outcome, and does everything they used to do still work?

Trust nothing until traced. Follow the user's or consumer's first action to the final result. Think like QA: for each claimed behavior, state **Actual** (what the code does now) vs **Expected**, and show where they diverge.

## The claim is delivered

- Trace input/event -> interface/API -> domain logic -> dependencies/storage -> state/output. Include game loops, jobs, notifications and navigation. Each hop must carry the change.
- Every promise is fully wired, partially wired or missing. An unreachable screen, unregistered handler or unused service is not delivered.
- Feedback: clear state, response or result. Long work shows progress and a final state. Input stays responsive.
- App and game changes: the shared logging module emits the changed journey's events, redacted. Module presence alone proves nothing.

## Existing journeys still work

- List pre-existing journeys through this code. Verify each, including alternate entry points, back/undo/navigation, reconnects and saved-state restore.
- Roles and variants: new vs returning, empty vs large data, first vs warm start, supported modes and privileges.

## Edge cases in the real flow

- Empty/null/first-run states, long text, rapid repeated input or submission, leaving mid-operation.
- Failure/offline: unavailable dependency, rejected request, lost connection, stale cache, expired session, uncertain completion. Truthful errors, retry/recovery and final state. No endless spinner or raw internal error.
- Exit/cancel/recovery: protect drafts, saves and active work. If saving keeps failing, explain unsaved work and offer a reachable explicit exit with truthful loss consequences. Retry alone is not an exit. Never silently discard private work. Owned processes/resources stop on quit.
- Permissions denied: graceful fallback; no crash or prompt loop.
- Platform/device/input: supported OS/hardware, window/screen sizes, orientation, safe areas, themes, keyboard/mouse/touch/controller and assistive input. Focus, contrast, labels, text scaling, reduced motion. Invent no unsupported platforms.
- Localization: actual supported locales, formatting, consistent copy. Flag placeholders, wrong-language text, truncation, missing translations.
- Time and dates: scheduling, past/edge dates, daylight saving, timezones.
- Web apps/games: reload/deep link, back/forward, tab close/reopen, hidden-tab resume, stale tabs, stuck input after focus loss, storage quota, stale cached assets vs server version.
- Games: elapsed-time or fixed-step simulation, refresh-rate independence, bounded resume delta. Preserve intended challenge; flag only accidental friction.
- Remote effects: operation identity, pending/success/failure/unknown outcomes, ambiguous timeouts, duplicate or out-of-order delivery, safe retry. A commit, sent request or webhook alone proves no completed effect.
- Headless systems: API/CLI contracts, errors, job status, recovery and observability. Missing UI is not a defect when none is required.

## UX and public pages

- UI/interaction changes: apply `ux-quality` to the affected journey: simple familiar flow, accessibility, rendered visuals, auditioned sounds. Missing interaction or listening evidence stays UNKNOWN.
- Public pages meant for search: apply the `ux-quality` SEO checks with actual crawl/render evidence. Keep private and staging pages excluded.

## Calibrate

- Prove the complete iteration's journey in its exact demo context. Keep remaining overall journeys visible; combined acceptance needs actual integration proof.
- Read the final manual QA observations for manual criteria. An unrelated green command certifies nothing.
- Judge against the claim, not what you would have built. Don't replace the author's goal.
- Distinguish "missing because broken" from "missing because out of scope".
- Separate code-traced behavior from behavior observed in the target environment. Source alone cannot certify unseen or unheard output. One desktop browser proves no mobile, audio or assistive behavior.

## Output

```markdown
| Claimed behavior | Actual | Expected | Where (File:Line) | Delivered? YES / PARTIAL / NO |
|------------------|--------|----------|-------------------|-------------------------------|
```

Then findings in the SKILL.md format. Severity: CRITICAL claim not delivered, existing journey broken, crash. HIGH happy path only, real scenario fails. MEDIUM rough edge, poor feedback. LOW polish. Impact: which user or consumer, doing what, gets what wrong outcome.

End with: `JOURNEY VERDICT: <delivers | partial | does-not-deliver | breaks-existing> - <one sentence>`
