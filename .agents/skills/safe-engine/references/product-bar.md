# Product bar

Contents: Stack, Visual system, States and forms, Public pages, Data, Logging, Speed, Security, Dev sign-in, Environment and sample labels, Games and browser lifecycle, External effects, Release.

Quality floor for every product and mode; [size](sizes.md) sets scope. POC/MVPs are never disposable: record stack, design brief and budgets in the plan.

- Minimal code means no waste, never a weaker stack, missing states or a bare UI.
- New products meet all of it except what their size skips. Changes cover affected paths and their consumers; record wider gaps, no unrelated restructuring.
- Analysis and review requests stay read-only: record gaps against this bar.

## Stack

Defaults for new products; existing projects keep their stack.

- Best current stack for the job: modern, popular, well maintained, fast locally, good looking by default. At kickoff compare three (run `research-market`), recommend one; the owner picks.
- Strict TypeScript for all JavaScript-ecosystem code, no plain JavaScript source.
- React web UIs: shadcn/ui, Tailwind CSS, lucide icons. Other platforms: best-in-class equivalents named in the stack options. One consistent icon set.
- One command starts it locally with seeded data.
- No AGENTS.md in built products unless non-standard commands or tools would trip an agent: then 10 lines or fewer, hand-written, never generated from code.
- Clean structure from day one (typed models, shared logging, clear modules); every size grows the same code.
- Dependencies: check license, maintenance, current version, security and cost; versioned packages over copied code.

## Visual system

Fill the design brief before UI code; run `ux-quality` on every UI change. Defaults:

- Palette: brand primary, accent, neutrals, success/warning/danger as tokens; at least 4 hex values; WCAG AA contrast.
- Font: one modern readable sans (Geist or Inter class), 16px base, clear type scale.
- Logo: own small SVG mark and wordmark; favicon from the mark.
- Layout: header (logo, navigation, account), content, footer (product, links, ©). Signed-in screens omit marketing/sign-in links.
- POC/MVP: light desktop; mobile apps: light mobile. Extra theme/device/responsiveness work needs a cited request/requirement. Preserve production support and frozen designs.
- Light theme; polished motion. Honor reduced-motion preferences.

## States and forms

- Every screen has loading, empty (with next action), error (with retry) and success states.
- Design every collection for one, few and many items; one item shows in place, never behind a list of one.
- Errors say what happened and the next useful action; no blame, no false success.
- Forms validate inline and keep input; the server validates again.
- Button and link labels match what they do. One source each: a glossary module holds every object, state and action name; a typed route map per audience feeds nav, breadcrumbs, titles and H1s; lifecycle screens take their primary action and panels from a state map.

## Public pages

- Web products ship a landing page at `/`: who it is for, the outcome, one primary call to action, real proof only, features, FAQ, footer. Private-only product (decided at kickoff): a branded noindex sign-in page at `/` instead.
- Run `ux-quality` with its web SEO reference (search metadata) and copy reference (conversion copy).
- Private screens, staging and previews stay unindexed.

## Data

- New or materially changed persistence: run `database-schema`; design from real access patterns, index actual queries.
- Seed realistic data (sample media where the product shows media) so every screen looks used on first run.
- Collect only needed data; protect sensitive storage and backups.
- Analytics collect events, not people: no personal data, raw IP or fingerprinting; consent before non-essential tracking where the law requires it.

## Logging

Every app, game, service and tool keeps one working shared logging module; libraries emit through caller-configured hooks. Record lifecycle, journey and failure outcomes with real locations, correlation and sanitized inputs. Bound retention and logging failure behavior. Exercise success, rejection and recovery, then inspect emitted records before final tests. For new or changed logging, instrumentation, background work or integration effects, read [logging details](quality-cases.md#logging) before implementation and review.

## Speed

Budget in the first plan: fast first load, instant common actions, no N+1, paginated lists. Small copy or input fixes need no profiling.

- Trace `trigger → work → result → release`: size, frequency, concurrency, hardware, owner; startup, active use and idle work included.
- Record `workload → target → cost → decision → bound/lifetime → evidence`; mark targets measured or provisional.
- Workload-specific complexity and latency; no blanket O(1) claim. Remove work before caching. Batching, indexes, pools and coalescing solve different problems.
- No distributed services, deployment changes or spending without authority. Justify N/A; invent no infrastructure.
Profiling or reviewing CPU, memory, database, network, storage or interaction cost: [speed checklist](cases.md#speed-checklist).

Adding, changing or reviewing a cache, what cached work depends on (inputs, access scope), duplicate-work coalescing or generated-media reuse: [caching](cases.md#caching).

Evidence: source proves repetition; speed and memory claims need runtime measurement stating workload, environment and cold/warm conditions. Faster wrong or stale results fail. Fakes prove mechanics, not speed. Percentages need a comparable baseline. Log safe counts and timings. Report unmet targets.

## Security

Assess affected trust boundaries and reachable surfaces on every change. Protect secrets and private data, validate untrusted input, enforce authorization at the trusted boundary, keep dependencies current and exercise relevant denial paths before exposure. A failed required check stays blocking. For any change to untrusted input, accounts, sessions, access, files, URLs, network effects, dependencies, deployment or exposed data, read [security details](quality-cases.md#security) before implementation and review. MVP and production-slice verify still records Secrets, Dependencies and Static in the run file with the tool, command and result; confirmed secrets and high or critical findings block handoff until fixed or handled under the detailed rule.

## Dev sign-in

Apps with accounts seed one user per role. Development builds show one-click buttons beside the normal sign-in form ("Sign in as Admin", "Sign in as Client" and so on); only development servers accept them; production builds drop the route and buttons. The handoff names the URL and buttons; the owner never hunts for credentials.

## Environment and sample labels

- A small fixed environment badge (DEV, STAGING, PREVIEW; games: a corner tag) follows the runtime environment from config, not the build mode: staging and preview show it even on a production build. Only production hides it: render nothing, not CSS-hidden.
- Sample data and mocked or sandbox integrations carry a visible label wherever they appear outside production: "Sample data", "Test mode: no real charge". Production never seeds sample data.
- No screen (CLI, API, library, service): print the environment in the startup log and version or health output.
- After screenshots show the badge; the handoff names the environment.

## Games and browser lifecycle

A game or GPU-heavy rendering, built, changed or reviewed: [games](cases.md#games).

Final manual QA of web apps and games: relevant cases, not every permutation.

- Navigation: reload, deep link, back/forward, tab close/reopen, hide/resume, stale tabs, cancellation. Keep promised state; clear stuck input on focus loss or pointer cancel; release owned work.
- Game timing: elapsed-time or fixed-step simulation, refresh-rate independent, bounded resume delta. No catch-up jump after a hidden tab or suspended device.
- Connectivity: offline/reconnect, slow or interrupted requests, duplicate submit, expired session, uncertain completion. Truthful progress and recovery.
- Capabilities: touch, keyboard, controller, focus/pointer/fullscreen locks, audio unlock and mute, denied permissions, storage quota, device or context loss.
- Compatibility: supported browsers and devices, viewport, orientation, reduced motion, low-end performance, stale cached assets and client/server versions.

Record unsupported cases. One desktop browser proves nothing about mobile, audio or assistive behavior.

## External effects

Payments, messages, webhooks, remote jobs and any other state-changing call to another system: [external effects](cases.md#external-effects).

## Release

Proof before any ready claim:

- Before dependent work, record actual capabilities: build tools, browser or native control, audio inspection, devices, safe accounts and data, integration access. Verify each route exists; surface blockers early and keep independent work moving. No purchases, installs or new credentials implied.
- Map each criterion to manual, automated or mixed evidence: candidate, environment/device, action, result, limits. Feel, art and interaction need honest observation, not an unrelated passing script. Missing evidence stays UNKNOWN. Never fabricate a tester or infer completion from a screenshot.
- A demo names the exact build, environment, device, data or save identity, actions and result. Same URL is not same context. Passing checks alone prove no outcome.
- Local ready, PR approval, merge and live release are separate; never infer deployment authority.
- The release record, operations, or deploying and operating a live release: [live release](cases.md#live-release).
