# studio-booking: fast product run

<!-- Sample record (fast-run.md#work-record): every gate marker, for an unrelated product. Never copy its content; a real run researches fresh. URLs and answers are examples. -->

Contents: request, research, kickoff, tickets, analysis, plan, design, schema, build log, done-run, handoff, MVP done-run example

## Request
> Build a POC for a yoga studio: members see the schedule, book a spot, buy class packs, join a waitlist when full; staff manage the schedule and check people in.

## Research
Summary shown to the owner: all three match on features; gaps: price transparency, direct-booking fees.
### Mindbody
- Booking by app, widgets or branded app; packs in one checkout. https://www.mindbodyonline.com/business/client-experience
- Full class: waitlist; a cancellation promotes the next client. https://www.mindbodyonline.com/business/scheduling
- From $79/month; branded app add-on; fee on a new client's first app purchase. https://www.mindbodyonline.com/business/pricing
### Momence
- One booking calendar, auto waitlists, packs, optional branded app. https://www.momence.com/yoga-studio-software/
- Pricing unpublished (demo or quote). https://www.momence.com/pricing/
### Glofox
- Booking calendar, auto waitlists, credit packs, branded app. https://www.glofox.com/features/

| Feature | Mindbody | Momence | Glofox |
|---|---|---|---|
| Class booking | ✅ | ✅ | ✅ |
| Waitlist | ✅ | ✅ | ✅ |
| Packs | ✅ | ✅ | ✅ |
| Branded app | ✅ add-on | ✅ | ✅ |

**Opportunities:** (inference) commission-free direct booking, branded site included, against first-purchase fees and paid app add-ons; flat published pricing (two of three hide it).
### Stack options
| Stack | Fit | Speed | Look | Risk |
|---|---|---|---|---|
| Next.js + TypeScript + shadcn/ui + Drizzle + SQLite (recommended) | One full-stack app | Fast | Finished | Payments later |
| Vite + React + TypeScript + Hono | Lean SPA, typed API | Very fast | Same kit | Two processes |
| SvelteKit + TypeScript + shadcn-svelte | Small bundles | Fast | Good | Fewer libraries |

## Kickoff
**Features:** schedule and booking, waitlist with auto-promotion, packs (mock checkout, owner-approved; real payments #6), staff schedule and check-in
**Size:** POC (from the request): every requested item, minimal and working; one studio, seeded data, role switcher instead of sign-in
**Approach:** studio-branded booking site (over a marketplace listing or staff-only scheduler)
**Stack:** Next.js + TypeScript + shadcn/ui + Drizzle + SQLite
**Answered by:** owner via the question tool

## Tickets
**Epic:** https://github.com/acme/studio-booking/issues/1 Studio booking POC
**Sub-issue:** https://github.com/acme/studio-booking/issues/2 Book a class
**Sub-issue:** https://github.com/acme/studio-booking/issues/3 Waitlist
**Sub-issue:** https://github.com/acme/studio-booking/issues/4 Class packs
**Sub-issue:** https://github.com/acme/studio-booking/issues/5 Staff tools
**Requested:** R1 schedule (#2), R2 book (#2), R3 packs (#4, mock checkout owner-approved), R4 waitlist (#3), R5 staff schedule (#5), R6 check-in (#5). Each delivering criterion names its item: `**A1 (R2):**`.
**Backlog:** searched "booking", "waitlist", "pack": empty, new repo. Owned: #1 to #5 (To do, P1, Definition of done each). Follow-ups #6 (real payments, owner-deferred; later deferrals append to it): Backlog, P2. POC skips in #1. Affected, untouched: none.

## Analysis
**Success:** a member books with a pack credit; a full class waitlists the next; a cancellation promotes them; staff check them in.
**Consumers:** members, front desk, owner.
```text
member -> schedule -> class -+- free -> book (-1 credit)
                             +- full -> waitlist -> promoted on cancellation
staff  -> editor -> today -> check-in
```
**Unknowns:** payment provider; cancellation window.

## Plan

`checks --plan` first.
### Files
`app/(app)/schedule/**`, `app/(staff)/**`, `lib/db/schema.ts`, `lib/booking.ts`, `lib/log.ts`, `scripts/seed.ts`
### Critique
`lib/booking.ts` transaction holds capacity, credits and promotion: no races. One checkout mock.
### Phases
1. Schema, seed, logging. 2. Booking. 3. Waitlist, packs. 4. Staff tools. 5. Header, footer. 6. Done-run.
### Todos
In sub-issue checklists; the epic's lists #2 to #5 and the done-run. Tier per todo. Waves: 1 = T1, T2, T8; 2 = T3, T4; 3 = T5, T6, T7.
- T1 (deep) Schema, seed → app opens with seeded data (#2, A1)
- T2 (standard) Logger → one redacted log of requests and errors (#2, A1)
- T3 (standard) Role switcher, env badge → switch member or staff in one click (#2, A2)
- T4 (standard) Booking → book a spot; a full class refuses (#2, A1)
- T5 (deep) Waitlist → a cancellation moves the next member in (#3, A1)
- T6 (standard) Packs, mock checkout → buy a pack, spend its credits (#4, A1)
- T7 (standard) Staff tools → publish classes, check members in (#5, A1)
- T8 (standard) Header, footer, logo → every page shows the studio and nav (#2, A3)
### Whole plan
Next.js app, SQLite through Drizzle, booking rules in one module.
**Logging:** `lib/log.ts`: JSON lines with request IDs to `logs/app.log`; secrets redacted.
**Efficiency:** one indexed query per week, one booking transaction, no N+1; under 200 KB JS.
**Ports:** app 3000 (main checkout, the project default)
**UX rules:** U1 to U10 (ux-quality); no project rule file
### Interface
`lib/booking.ts` exports `book(memberId, classId)`, `cancel(bookingId)`, `promote(classId)`; `Booking { id, memberId, classId, status: booked | waitlisted | cancelled }` in `lib/types.ts`; routes `/schedule`, `/account`, `/staff/schedule`, `/staff/today`; buttons `Book`, `Join waitlist`, `Cancel booking`, `Check in`.

## Design
**UI kit:** shadcn/ui
**Palette:** primary #2F6F5E, accent #E9A23B, ink #1F2933, surface #FBFAF7, success #2E7D32, danger #C62828
**Font:** Inter, 16px
**Logo:** `public/logo.svg`, lotus mark and "Stillpoint" wordmark; favicon from the mark
**Icons:** lucide-react
**Layout:** header (logo, role nav, switcher), content, footer (address, Help, Privacy, ©); one column on phones
**Theme:** light mode default
**Journeys:** book: 2 actions, 1 load, min 2; cancel: 2 actions, 0 loads, min 1 (confirm); check-in: 1 action, 0 loads, min 1
**Map:** member: Schedule > class, My bookings, Packs; staff: Editor > roster, Today. Header nav per role, the same on every screen; phones get a bottom bar with the same items. Tree test 5/5.
**Hierarchy:** schedule: primary Book (Join waitlist when full), secondary day filter, deferred description; roster: primary Check in, secondary Add walk-in; packs: primary Buy pack, deferred past orders
**Labels:** class, spot, booking (booked, cancelled), waitlist (waiting, promoted), pack, credit, check in (checked in); buttons Book, Join waitlist, Cancel booking, Buy pack, Check in

## Schema
| Design | Fit | Verdict |
|---|---|---|
| Relational, transactional capacity check | Correct under concurrency | Chosen |
| Seat counter on the class row | Drifts from bookings | Rejected |
| Event log | Reads replay history | Rejected |

**Chosen:** relational via Drizzle; capacity checked in the booking transaction.
```text
members 1-* bookings *-1 classes (capacity, starts_at)
members 1-* credit_packs; classes 1-* waitlist (position)
indexes: classes(starts_at), bookings(class_id, status), waitlist(class_id, position)
```

## Build log
- T1 pre: schema plan do: Drizzle schema, seed post: FKs and indexes match the access map; ticked in #2
- T2 pre: logging rules do: `lib/log.ts`, redaction post: wired before the first route
- T3 pre: roles do: dev-only switcher, DEV badge from runtime config post: production build drops the switcher; only the production environment hides the badge
- T4 pre: T1 queries do: booking in one transaction post: a double click books once
- T5 pre: T4 do: waitlist, promotion on cancel post: one transaction with the credit spend
- T6 pre: credit rules do: packs, checkout labeled "Test mode: no real charge" post: one checkout function
- T7 pre: staff routes do: editor, check-in post: staff role checked on the server
- T8 pre: design brief do: header, footer, logo post: AA contrast checked

**Now:** none, every todo built

## Done-run
- PASS member buys a 5-class pack in test mode, books Tuesday 7:00 Flow
- PASS a full class waitlists member 2; a cancellation promotes them and spends a credit
- PASS staff publish a class and check the member in
- FAIL then fixed: Book stayed active while pending; now disabled. Checked fix pushed; reset fixtures and demo; replaced After, kept Before.
- Use log: book 2 actions, 1 load; cancel 2 with confirm; loading, empty, full, failed-retry seen; double click books once; keyboard booking; back keeps the week
- Shots: .factory/fast/shots/schedule.png, roster.png, packs.png at 375 and 1280 (DEV badge and "Sample data" tags visible)
- U1 PASS schedule, bookings, packs, editor, roster: reached from the role header, no dead ends
- U2 PASS schedule, roster, packs (375, 1280): nav marks the page; title and H1 match the nav label; back keeps the week
- U3 PASS schedule, roster, packs: one filled button per view
- U4 PASS schedule, packs: description collapsed, booking never in a menu
- U5 PASS schedule, roster, packs: labels match the glossary; every field has a visible label
- U6 PASS per use log: book 2 actions, 1 load, min 2
- U7 PASS per use log: loading, empty, full, failed with retry
- U8 PASS shots at 375 and 1280, keyboard booking, axe 0 violations
- U9 PASS schedule, roster, packs: one icon family, Cancel booking in one place
- U10 UNKNOWN no low-end phone; 180 KB JS measured on desktop
**UX judge:** fresh mid-size subagent, not the builder, from shots, outlines, axe scan, use log
**Hidden checks:**
- #1 A1: PASS, #1 A2: PASS (epic integration: credits booked, promoted member checked in)
- #2 A1: PASS, #2 A2: PASS
- #3 A1: PASS, #3 A2: PASS (A2 FAIL first; fixed, all rerun)
- #4 A1: PASS, #4 A2: PASS
- #5 A1: PASS, #5 A2: PASS
**Findings:** .factory/fast/final-findings.json
**Logs:** logs/app.log: request IDs on booking, promotion, check-in; no errors

## Handoff
**Run:** `pnpm install && pnpm db:seed && pnpm dev`, then http://localhost:3000
**Statuses:** all requested items delivered; #2 to #5 ticked, done-run PASS: Ready for QA with PR #7, Done on merge; epic #1 Ready for QA; #6 Backlog
**Dev sign-in:** header role switcher (Member, Staff), development only; this POC has no sign-in
**PR:** https://github.com/acme/studio-booking/pull/7 (body: .factory/fast/pr-body.md): Before & after per outcome with Visual and Journey; screenshot pairs for every changed view and state; videos per journey plus changed failure/retry paths; shared clips mark each journey's timestamps
**Deferred:** none
**Unverified:** automated tests, independent review, Safari, payments
**Follow-ups:** real payments (#6, revisit at MVP kickoff); POC skips (sign-in, hardening, deployment, landing page) in epic #1

## MVP done-run example
An MVP or production slice adds these to its Done-run; a POC has none:

**Secrets:** `gitleaks git .` and `gitleaks dir .`: 0 findings
**Dependencies:** `pnpm audit --prod`: 1 high in `qs`, bumped; rerun 0
**Static:** `pnpm exec eslint .` with security rules: 0 high or critical
