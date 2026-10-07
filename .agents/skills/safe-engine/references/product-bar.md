# Product bar

Seif, 7 October 2026: a POC or MVP is the first slice of the real product, built right and never thrown away. Every mode meets this bar. Fast and Safe record it in the plan and design brief; Lucky applies it as its default.

Minimal code means no waste. It never justifies a weaker stack, missing states or a bare UI.

## Stack

- Choose the best current stack for the job: modern, popular, well maintained, fast to run locally, good looking by default. Compare three at kickoff ([research](../../research-market/SKILL.md#fast-kickoff-research)); recommend one; Seif picks.
- TypeScript for all JavaScript-ecosystem code, strict mode. No plain JavaScript source.
- React web UIs use shadcn/ui with Tailwind CSS and its icon set (lucide). Other platforms use their best-in-class equivalent; name it in the stack options.
- One command starts it locally with seeded data. No Docker, Kubernetes, CI/CD, deployment or unit-test suites for a POC unless Seif asks.
- Production-grade structure from day one: typed models, migrations, shared logging, clear modules. The MVP grows from this code.

## Visual system

Fill the design brief before UI code:

- **UI kit:** the stack's component kit (shadcn/ui for React).
- **Palette:** brand primary, accent, neutrals and success/warning/danger as tokens; ≥4 hex values; WCAG AA contrast.
- **Font:** one modern, readable sans (Geist or Inter class), 16px base, a clear type scale.
- **Logo:** our own small SVG mark and wordmark; favicon from the mark.
- **Icons:** one consistent set.
- **Layout:** header (logo, navigation, account), content area, footer (product, links, ©); responsive from phone to desktop.
- **Theme:** light mode by default. Dark mode is optional later; never default to dark.

Every screen has loading, empty (with the next action), error (with retry) and success states. Forms validate inline and keep input. Motion stays subtle and respects reduced motion. [UX Quality](../../ux-quality/SKILL.md) owns the audit and research.

## Public pages

Web products ship a landing page at `/` in the POC: who it is for, the outcome, one primary call to action, real proof only, features, FAQ, footer. Apply [Public Web SEO](../../ux-quality/references/web-seo.md) (titles, descriptions, social cards, sitemap, robots, structured data) and the conversion rules in [Clear Writing](clear-writing.md#make-action-clear). Only when the kickoff says the product is private-only: a branded sign-in page instead, marked noindex. Private screens stay unindexed.

## Data, logs and speed

- Persistence goes through the schema step: real access patterns, three designs, indexes for actual queries.
- Seed realistic data, including sample media where the product shows media, so every screen looks used on first run.
- [Shared logging](app-diagnostics.md) from startup.
- [Efficiency](app-efficiency.md) budget in the plan: fast first load, instant common actions, no N+1, paginated lists. Measure before claiming speed.

## Dev sign-in

Apps with accounts seed one user per role. Development builds show one-click buttons on the sign-in screen, beside the normal sign-in form: "Sign in as Admin", "Sign in as Client" and so on. The server only accepts them in development; production builds drop the route and buttons. The handoff names the URL and the buttons, so Seif never hunts for credentials.

## POC deferrals

A POC may defer security hardening (rate limits, CSRF, headers, audits), CI/CD and deployment. Each deferral becomes a follow-up ticket in the epic. Keep the role checks the journeys need, and never put secrets in code or Git. [Application Security](app-security.md) applies in full before any public exposure.
