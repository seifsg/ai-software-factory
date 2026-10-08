# Sizes

Size sets how far each requested item is built, never which requested items ship. It applies to new products and big features. Inside an existing product, every size keeps that product's protections and behavior, and new paths get the same protections. Ask it at kickoff when the request leaves it open. A Lucky product run without a size: POC.

## Requested scope

Every feature, journey, integration and behavior the owner asked for, plus what each needs to work end to end (if the item fails for a real user without it, it is part of the item). It ships in every size.

- A requested item leaves scope only by the owner's recorded decision: source, reason, follow-up ticket, revisit condition.
- Without that decision, nothing removes or replaces a requested item: no size label, research finding, generic follow-up, later iteration's focus or substitute (mock, sample data, a sandbox that cannot reach the real target, manual step). Seeded data fills content, never a requested integration. A provider's test mode on the real integration counts; live keys come with deployment.
- Capability unavailable: keep the item Blocked with its reason, build the rest, report the outcome unfinished.
- Additions need research evidence and the owner's approval. They never displace a requested item. A size label approves none.

## Compare

| | POC | MVP | Production slice |
|---|---|---|---|
| Promise | It works and does exactly what was asked | It works and can go live with real test users | It runs in production |
| Builds | Every requested item, minimal and working. No extras | Requested items, the launch baseline, and the extra gaps the owner approved | Requested scope at the full product bar |
| Skips unless requested | Sign-in, authorization, security hardening, a full backend, deployment, CI/CD, test suites, landing page and SEO (it opens on its main screen) | Only scale beyond launch (clusters, multiple regions), paid services without authority, and what the owner declined | Nothing |
| Keeps everything else, including | Stack, visual system and screen states, logging, secrets out of Git, environment and sample labels | Everything a launch needs | Everything |
| Research | How to build the requested items; the riskiest capability | Plus launch gaps users expect | Plus operations at scale |

## POC

The owner wants to see the requested features work. Build each one minimally: nothing extra, nothing cut.

- Minimal backend: the smallest real service and storage that run the requested behavior end to end (one local process, a file or an embedded database). It stays structured so the MVP can grow it.
- No sign-in layer. Requested roles switch through a development-only role switcher. A requested role rule is built as asked, checked on the server; it does not pull in the rest of the security bar.
- Local only. Any shared preview counts as exposure: the security bar applies in full before it.
- An owner-approved simplification of a requested item (a mock checkout) follows the requested-scope rule above, follow-up ticket included, and stays labeled in the interface.
- List the skipped parts once in the epic's guardrails as "POC skips". An MVP run turns that list into tickets. No follow-up ticket per skip.

## MVP

The owner wants to publish it and test it with real users. Fill every gap a launch needs.

- Launch baseline, built without asking:
  - real sign-in and enforced roles when anyone signs in or roles exist;
  - the security bar in full;
  - landing page and SEO for public products;
  - privacy and terms pages when it collects personal data;
  - the legal and platform duties of what it does (for example consent and one-click unsubscribe for marketing email);
  - onboarding;
  - transactional email when journeys send mail;
  - a logging destination (asked once when unknown) and error alerts;
  - migrations for persisted data, and backups;
  - automated tests, written after the journeys work, running in CI;
  - a release record ready to deploy.
- Deploying needs the owner's authority.
- Research launch gaps the owner may not think of: what competitors offer, what users expect before they trust a product, what breaks at first real use. Present each as a suggestion: gap, evidence, cost, recommendation.
- Suggestions go beyond the baseline. The owner approves or declines each; approved ones become criteria, declined or unanswered ones go to the Backlog as ideas.
- Suggest again whenever delivery uncovers a gap, at the latest when each sub-issue finishes. Keep it to one short message, not a gate.

## Production slice

The full product bar for the affected paths, release and operations included.
