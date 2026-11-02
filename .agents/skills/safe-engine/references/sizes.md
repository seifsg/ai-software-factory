# Sizes

Build what asked + what it needs to work. Best quality, best UI/UX. No size default: never label a run POC or MVP unless owner names it. Inside an existing product, keep its protections and behavior; new paths get the same.

## Requested scope

Every feature, journey, integration and behavior the owner asked for, plus what each needs to work end to end (if the item fails for a real user without it, it is part of the item).

- A requested item leaves scope only by the owner's recorded decision: source, reason, revisit condition, and its entry in the epic's follow-ups ticket.
- Without that decision, nothing removes or replaces a requested item: no size label, research finding, generic follow-up, later iteration's focus or substitute (mock, sample data, a sandbox that cannot reach the real target, manual step). Seeded data fills content, never a requested integration. A provider's test mode on the real integration counts; live keys come with deployment.
- Capability unavailable: keep the item Blocked with its reason, build the rest, report the outcome unfinished.
- Extras, no ask: better UI/UX, small enhancements of asked items, critical or recommended additions an asked item needs. Nothing else: no unasked features or pages (sign-in, payments, analytics, onboarding), except an owner-named MVP's launch needs. Other ideas: suggestions in the follow-ups ticket (gap, evidence, cost), never built.
- Logic gets small tests, any run, except owner-named POC.

## Owner-named size

| | POC | MVP | Production slice |
|---|---|---|---|
| Promise | Asked idea works | Can go live with real test users | Runs in production |
| Builds | Asked items only | Asked items + this product's launch needs (research) | Asked scope, every `deep-review` lens in full |
| Skips unless asked | Sign-in, hardening, full backend, deploy, CI/CD, test suites | Scale beyond launch, paid services without authority, owner-declined | Nothing |

## POC

- Minimal backend: the smallest real service and storage running the requested behavior end to end (one local process, a file or an embedded database).
- No sign-in layer; requested roles switch through a development-only role switcher. A requested role rule is built as asked, checked on the server.
- Local only. Any shared preview is exposure: `deep-review`'s security lens applies in full before it.
- An owner-approved simplification of a requested item (a mock checkout) follows the requested-scope rule and stays labeled in the interface.
- List skips once in the epic's guardrails as "POC skips". No ticket per skip.

## MVP

Owner publishes it to real test users. Research what MVP means for this product: what competitors ship, what users expect before trusting it, what breaks at first real use. Build each launch need it shows, from this list and beyond:

- real sign-in and enforced roles when anyone signs in or roles exist;
- `deep-review`'s security lens in full, with the three verify scans (secrets, dependencies, static analysis);
- landing page and SEO for public products;
- privacy and terms pages when it collects personal data;
- its legal and platform duties (for example consent and one-click unsubscribe for marketing email);
- onboarding;
- transactional email when journeys send mail;
- a logging destination (asked once when unknown) and error alerts;
- product analytics on key journey events, with no personal data beyond what the journey needs, to a destination asked once when unknown (default: the app's own storage);
- in-app feedback that reaches the owner, with the page and app version attached;
- migrations for persisted data; backups stored apart from that data, with a tested restore;
- automated tests, written after the journeys work, run by one local command;
- a release record ready to deploy.

Each need: gap, evidence, cost in the block. Paid ones: owner approves; declined or unanswered go to the follow-ups ticket. Deploying needs the owner's authority.

## Production slice

Every `deep-review` lens in full for the affected paths, release and operations included.
