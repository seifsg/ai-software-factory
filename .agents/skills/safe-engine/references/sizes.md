# Sizes

Size sets how far each requested item is built, never which requested items ship. It applies to new products and big features. Inside an existing product, every size keeps that product's protections and behavior, and new paths get the same protections. Ask it at kickoff when the request leaves it open. A Lucky product run without a size records `**Size:** POC`. A Lucky MVP request gets the launch baseline with product-bar defaults and no suggestion rounds; the suggestions it would have asked go to the epic's follow-ups ticket.

## Requested scope

Every feature, journey, integration and behavior the owner asked for, plus what each needs to work end to end (if the item fails for a real user without it, it is part of the item). It ships in every size.

- A requested item leaves scope only by the owner's recorded decision: source, reason, revisit condition, and its entry in the epic's follow-ups ticket.
- Without that decision, nothing removes or replaces a requested item: no size label, research finding, generic follow-up, later iteration's focus or substitute (mock, sample data, a sandbox that cannot reach the real target, manual step). Seeded data fills content, never a requested integration. A provider's test mode on the real integration counts; live keys come with deployment.
- Capability unavailable: keep the item Blocked with its reason, build the rest, report the outcome unfinished.
- Additions beyond the launch baseline need research evidence and the owner's approval. They never displace a requested item. A size label approves none of them.

## Compare

| | POC | MVP | Production slice |
|---|---|---|---|
| Promise | It works and does exactly what was asked | It works and can go live with real test users | It runs in production |
| Builds | Every requested item, minimal and working. No extras | Requested items, the launch baseline, and the extra gaps the owner approved | Requested scope at the full product bar |
| Skips unless requested | Sign-in, authorization, security hardening, a full backend, deployment, CI/CD, test suites, landing page and SEO (it opens on its main screen) | Only scale beyond launch (clusters, multiple regions), paid services without authority, and what the owner declined | Nothing |
| Keeps everything else, including | Stack, visual system and screen states, logging, secrets out of Git, environment and sample labels | Everything a launch needs | Everything |
| Research | How to build the requested items; the riskiest capability | Plus launch gaps users expect | Plus operations at scale |

## POC

Show each requested feature working, built minimally: nothing extra, nothing cut.

- Minimal backend: the smallest real service and storage running the requested behavior end to end (one local process, a file or an embedded database), structured so the MVP can grow it.
- No sign-in layer; requested roles switch through a development-only role switcher. A requested role rule is built as asked, checked on the server, without the rest of the security bar.
- No done-run scans (secrets, dependencies, static analysis).
- Local only. Any shared preview is exposure: the full security bar applies before it.
- An owner-approved simplification of a requested item (a mock checkout) follows the requested-scope rule, follow-ups ticket entry included, and stays labeled in the interface.
- List skipped parts once in the epic's guardrails as "POC skips"; an MVP run turns that list into tickets. No follow-up ticket per skip.

## MVP

The owner publishes it to test with real users: fill every gap a launch needs.

- Launch baseline (part of MVP), built without asking:
  - real sign-in and enforced roles when anyone signs in or roles exist;
  - the full security bar, with the three done-run scans (secrets, dependencies, static analysis);
  - landing page and SEO for public products;
  - privacy and terms pages when it collects personal data;
  - its legal and platform duties (for example consent and one-click unsubscribe for marketing email);
  - onboarding;
  - transactional email when journeys send mail;
  - a logging destination (asked once when unknown) and error alerts;
  - product analytics on key journey events, under the [product bar](product-bar.md)'s privacy rules, to a destination asked once when unknown (default: the app's own storage);
  - in-app feedback that reaches the owner, with the page and app version attached;
  - migrations for persisted data; backups stored apart from that data, with a tested restore;
  - automated tests, written after the journeys work, running in CI;
  - a release record ready to deploy.
- Deploying needs the owner's authority.
- Research launch gaps the owner may miss: what competitors offer, what users expect before trusting a product, what breaks at first real use. Present each as a suggestion beyond the baseline: gap, evidence, cost, recommendation.
- The owner approves or declines each; approved ones become criteria, declined or unanswered ones go to the epic's follow-ups ticket in Backlog.
- Suggest again whenever delivery uncovers a gap, at the latest when each sub-issue finishes: one short message, not a gate.

## Production slice

Full product bar for the affected paths, release and operations included.
