# studio-booking: fast product run

<!-- Illustrative sample of a filled Fast work record (fast-run.md#work-record). It shows the gate markers for a
     product unrelated to any real run; never copy its content. A real run researches fresh. Ticket URLs and owner answers are examples, not real records. -->

Contents: request · research · kickoff · tickets · analysis · plan · design · schema · build log · done-run · handoff

## Request

> Build a proof of concept for a boutique yoga studio: members see the class schedule, book a spot, buy class packs and join a waitlist when a class is full; staff manage the schedule and check people in.

## Research

Summary shown to the owner: all three leaders cover booking, waitlists, packs, check-in and video; the gaps are price transparency and fees on direct bookings.

### Mindbody

- Members book in the Mindbody app, site widgets or a branded app; memberships, packs and intro offers share one checkout. https://www.mindbodyonline.com/business/client-experience
- Full classes offer a waitlist and a cancellation promotes the next client. https://www.mindbodyonline.com/business/scheduling
- Pricing page: plans from $79/month; branded app is an add-on; a fee applies to a new client's first app purchase. https://www.mindbodyonline.com/business/pricing

### Momence

- One calendar for classes, courses and workshops; automated waitlists; memberships, packs, drop-ins; optional branded app; livestream and on-demand. https://www.momence.com/yoga-studio-software/
- Waitlist modes: first-come, double opt-in, fast-fingers by SMS. https://help.momence.com/en/articles/12028307-waitlist-faq-s-classes
- Pricing not published (demo or quote). https://www.momence.com/pricing/

### Glofox

- One calendar, automated waitlists, credit packs, own branded app, self check-in kiosks. https://www.glofox.com/features/
- Waitlisted clients are notified or moved in automatically; staff check in from the roster. https://www.glofox.com/faq/

| Feature | Mindbody | Momence | Glofox |
|---|---|---|---|
| Class booking | ✅ | ✅ | ✅ |
| Waitlist | ✅ | ✅ | ✅ |
| Packs and memberships | ✅ | ✅ | ✅ |
| Branded app or site | ✅ add-on | ✅ | ✅ |
| Staff check-in | ✅ | ✅ | ✅ |
| Online or video classes | ✅ add-on | ✅ | ✅ |

**Opportunities:** (inference)
- Commission-free direct booking with the branded site included, against first-purchase fees and paid app add-ons.
- Flat published pricing for comparison shoppers; two of three leaders publish none.
- Video included in the base plan instead of an add-on.

### Stack options

| Stack | Fit | Speed | Look | Risk |
|---|---|---|---|---|
| Next.js + TypeScript + shadcn/ui + Drizzle + SQLite (recommended) | One full-stack app; booking rules in server actions | Fast local dev | shadcn defaults look finished | Payments added later |
| Vite + React + TypeScript + shadcn/ui + Hono API | Lean SPA plus small typed API | Very fast | Same kit | Two processes to run |
| SvelteKit + TypeScript + shadcn-svelte | Small bundles | Fast | Good | Smaller ecosystem |

## Kickoff

**Features:** schedule and booking, waitlist with auto-promotion, class packs (mock checkout, owner-approved; real payments follow-up #6), staff schedule and check-in
**Size:** POC (from the request): every requested item, minimal and working: one studio, seeded members and classes, a dev role switcher instead of sign-in
**Approach:** studio-branded booking site with packs (over a marketplace listing, or a staff-only scheduler)
**Stack:** Next.js + TypeScript + shadcn/ui + Drizzle + SQLite
**Answered by:** owner via the question tool (sample answers)

## Tickets

**Epic:** https://github.com/acme/studio-booking/issues/1
**Sub-issue:** https://github.com/acme/studio-booking/issues/2 (member books a class from the schedule)
**Sub-issue:** https://github.com/acme/studio-booking/issues/3 (full class: waitlist and auto-promotion)
**Sub-issue:** https://github.com/acme/studio-booking/issues/4 (member buys a class pack and spends credits)
**Sub-issue:** https://github.com/acme/studio-booking/issues/5 (staff publish classes and check members in)
**Requested:** R1 see the class schedule (#2), R2 book a spot (#2), R3 buy class packs (#4, mock checkout owner-approved), R4 join a waitlist when a class is full (#3), R5 staff manage the schedule (#5), R6 staff check people in (#5). Each delivering criterion names its item: `**A1 (R2):**`.
**Backlog:** searched "booking", "waitlist", "class pack": empty, new repository. Owned: #1 to #5, To do, P1, each with a Definition of done; checklists follow the plan. Follow-ups ticket #6 for the epic (real payments, owner-deferred; later deferrals append to it) in Backlog, P2. POC skips listed in #1. Affected and untouched: none.

## Analysis

**Success:** a member (dev role switcher) books a class with a pack credit, a full class puts the next person on the waitlist, a cancellation promotes them, and staff check the member in.
**Consumers:** members, front-desk staff, the studio owner.

```text
member ─ role ─► schedule ─► class ─┬─ spot free ─► book (−1 credit) ─► confirmation
                                       └─ full ─► waitlist ─► cancellation frees a spot ─► auto-promote
staff  ─ role ─► schedule editor ─► today's classes ─► check-in list
```

**Unknowns:** payment provider after the POC; cancellation window rules.

## Plan

### Files
`app/(app)/schedule/**`, `app/(app)/account/**`, `app/(staff)/**`, `lib/db/schema.ts`, `lib/booking.ts`, `lib/log.ts`, `components/**`, `public/logo.svg`, `scripts/seed.ts`.

### Critique
Capacity, credits and waitlist promotion live in `lib/booking.ts` behind one transaction, so pages never race each other. Mock checkout stays behind one function for a later payment provider.

### Phases
1. Foundation: schema, seed, logging, dev role switcher, environment badge. 2. Member booking. 3. Waitlist and packs. 4. Staff tools. 5. Header, footer, logo. 6. Done-run.

### Todos
Written into the sub-issues' checklists; the epic's checklist lists #2 to #5 and the combined done-run. Waves by files and dependencies; tier per todo.
- Wave 1: T1 schema and seed (#2, deep), T2 shared logger (#2, standard), T8 header, footer, logo (#2, standard)
- Wave 2: T3 dev role switcher and environment badge (#2, standard), T4 schedule and booking with capacity check (#2, standard)
- Wave 3: T5 waitlist and auto-promotion (#3, deep), T6 class packs with a labeled mock checkout (#4, standard), T7 staff schedule editor and check-in (#5, standard)

### Whole plan
Next.js app, SQLite through Drizzle, booking rules in one module. Light theme with the design brief below.

**Logging:** `lib/log.ts` JSON lines to `logs/app.log`; booking, waitlist, credit and check-in events with request IDs; secrets redacted.
**Efficiency:** one indexed query per schedule week, booking in a single transaction, no N+1 on rosters; first load under 200 KB JS on member pages.

## Design

**UI kit:** shadcn/ui (button, card, calendar, dialog, sheet, badge, toast, skeleton)
**Palette:** primary #2F6F5E, accent #E9A23B, ink #1F2933, surface #FBFAF7, success #2E7D32, danger #C62828
**Font:** Inter, 16px base
**Logo:** `public/logo.svg`: lotus mark plus the "Stillpoint" wordmark; favicon from the mark
**Icons:** lucide-react
**Layout:** header with logo, Schedule, My bookings and the dev role switcher; content area; footer with studio address, Help, Privacy and ©; one column on phones
**Theme:** light mode default; dark mode later
**Journeys:** book a class: 2 actions, 1 load, min 2 actions; cancel a booking: 2 actions, 0 loads, min 1 action (the destructive confirm is the reason for the gap); staff check-in: 1 action per member, 0 loads, min 1 action

## Schema

| Design | Fit | Verdict |
|---|---|---|
| Relational bookings with a transactional capacity check | Correct under concurrent bookings, simple queries | Chosen |
| Seat counter stored on the class row | Fast reads, but drifts from the bookings it summarizes | Rejected |
| Event log of credits and bookings | Full history, but every read replays | Rejected |

**Chosen:** relational on SQLite through Drizzle (migrations arrive with the MVP); capacity checked inside the booking transaction.

```text
members 1─* bookings *─1 classes (capacity, starts_at)   members 1─* credit_packs (remaining)
classes 1─* waitlist (position)   staff 1─* classes (instructor)
indexes: classes(starts_at), bookings(class_id, status), waitlist(class_id, position)
```

## Build log

- T1 pre: schema plan read | do: Drizzle schema and seed with 2 members, 1 staff, a week of classes | post: FKs and indexes match the access map; ticked in #2
- T2 pre: product bar logging rules | do: `lib/log.ts` with redaction and rotation | post: wired before the first route
- T3 pre: requested roles (member, staff) | do: dev-only role switcher in the header, DEV badge from runtime config | post: production build drops the switcher; only the production environment hides the badge
- T4 pre: T1 queries | do: week schedule and booking in one transaction | post: double click books once
- T5 pre: T4 transaction | do: waitlist join and promotion on cancellation | post: promotion and credit spend share the transaction
- T6 pre: credit rules | do: class packs with a checkout labeled "Test mode: no real charge" | post: checkout isolated in one function
- T7 pre: staff routes | do: schedule editor and check-in list | post: staff actions checked on the server under the staff role
- T8 pre: design brief | do: header, footer, logo, metadata | post: light theme, AA contrast checked

## Done-run

- PASS member (dev role switcher) buys a 5-class pack in test mode, books Tuesday 7:00 Flow
- PASS full class puts the second member on the waitlist; a cancellation promotes them and spends their credit
- PASS staff publishes a class and checks the booked member in
- FAIL then fixed: booking button stayed active during the request; disabled while pending
- Screenshot: .factory/fast/shots/schedule.png (DEV badge and "Sample data" tags visible)
**Hidden checks:** #2 A1 PASS, A2 PASS; #3 A1 PASS, A2 PASS; #4 A1 PASS, A2 PASS; #5 A1 PASS, A2 PASS (checker's .factory/fast/checks/studio-booking/, written after the plan, run after build)
**Logs:** logs/app.log shows request IDs for booking, waitlist promotion and check-in; no errors

## Handoff

**Run:** `pnpm install && pnpm db:seed && pnpm dev`, then http://localhost:3000
**Statuses:** every requested item delivered, real payments owner-deferred to #6 (mock checkout in this POC); #2, #3, #4, #5 checklists ticked, done-run PASS: Ready for QA with PR #7, Done on merge; epic #1 Ready for QA; #6 Backlog
**Dev sign-in:** header role switcher (Member, Staff), development only; this POC has no sign-in
**Unverified:** automated tests, independent review, Safari, payment provider
**Follow-ups:** real payments (#6, owner-approved mock in this POC, revisit at MVP kickoff). POC skips (real sign-in, security hardening, deployment, landing page) are listed in epic #1 for the MVP
