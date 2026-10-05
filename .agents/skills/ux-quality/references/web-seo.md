# Public web SEO

Use for public landing, marketing and content pages meant for search, including a web app's public routes. Plan early; verify before launch and after authorized deployment. Keep small fixes scoped. Analysis stays read-only. Reuse [Clear Writing](../../safe-engine/references/clear-writing.md), UX and [efficiency](../../safe-engine/references/app-efficiency.md); no extra review loop.

## Set the boundary

Useful public page first; required crawl/privacy/content and launch obligations stay. Optional expansion follows. Final manual QA then automation; deployment/indexing proof stays separate.

- Record production domain, audience/search intent, languages, public routes, private routes, staging and existing SEO setup. Reuse CMS/framework features. No duplicate sitemap/metadata generators.
- New site: cover all public templates and key pages. Existing fix: affected pages, shared templates and consumers. Research material unknowns in current primary guidance; extend this checklist for actual gaps, not speculative work.
- Preserve login/access controls and deliberate exclusions. Public search scope never authorizes indexing accounts, admin, personal data or previews. Existing authority covers approved actions; DNS, ownership verification, submissions and deployment need actual project access/authority.

## Build the essentials

| Check | Require |
|---|---|
| Indexing | Remove accidental `noindex` from intended production pages, including HTML meta and HTTP `X-Robots-Tag`. Keep intentional exclusions. Crawlers must reach a page to read `noindex`; `robots.txt` is neither deindexing nor access control. |
| `robots.txt` | Serve at host root; correct environment/host rules and sitemap location. Allow intended pages and required CSS/JS/images. Never ship staging's blanket block to production. |
| `sitemap.xml` | Generate from published routes: absolute preferred HTTPS URLs, indexable successful pages only, truthful `lastmod` when known. Exclude private, duplicate, redirected, missing and noindex URLs. Update on route/content changes; split/index large sitemaps per current limits. |
| URLs/canonicals | Stable descriptive slugs; one preferred host/protocol/trailing-slash convention. Absolute canonical per page, consistent with sitemap/internal links. Consolidate true duplicates; never canonicalize distinct pages to home. URL changes need mapped permanent redirects and updated links; avoid chains/loops. |
| Crawl/render | Main content, metadata and crawlable `<a href>` links available to crawlers; no login/click-only discovery or blocked render assets. Prefer suitable server/static rendering for public content; verify actual output. Missing routes return real 404/410, not a 200 app shell. Bound faceted/search-parameter crawl paths. |
| Titles/descriptions | Unique, accurate `<title>` and meta description per indexable page. Search intent first; no stuffing, boilerplate duplication or fabricated claims. Preview truncation; no universal character/pixel promise or guaranteed Google snippet. |
| Headings/content | One clear H1 per page; logical semantic heading hierarchy. Useful original content, descriptive internal links, reachable key pages, no broken links or orphan pages. Keep heading semantics for accessibility; no keyword quota. |
| Images | Informative alt text; decorative images use `alt=""`. Compress without visible damage; suitable formats, responsive sizes, explicit dimensions. Lazy-load offscreen images; keep critical/LCP imagery promptly available. |
| Structured data | Relevant JSON-LD/types with supported properties matching visible facts. Check current eligibility and syntax. No fake reviews, ratings, offers or automatic FAQ markup everywhere. Valid schema does not guarantee rich results. |
| Mobile/performance | Responsive layout, readable content, usable controls and content/metadata parity. Control scripts/fonts/assets; avoid layout shifts and blocking overlays. Target LCP ≤2.5 s, INP ≤200 ms, CLS ≤0.1 at p75, mobile/desktop separately. Recheck current thresholds. Lab results cannot prove field performance; missing field data stays unknown. |
| HTTPS | Valid certificate; HTTP redirects to preferred HTTPS URLs. No mixed content, broken assets or redirect loops. Preserve working host/security policy. |
| Sharing | Accurate Open Graph title/type/URL/description and public absolute `og:image` with alt/dimensions. Inspect actual crop/legibility; add target-platform card metadata where needed. Social previews are not ranking evidence. |
| Search Console | Reuse correct property/owner; verify via supported method with authorized access. Preserve verification records; submit sitemap, inspect representative live URLs and indexing/canonical reports. Missing access blocks this step only. Submission proves neither indexing nor ranking. |
| `llms.txt` | Add the requested root Markdown file: site H1, brief summary, grouped useful public links; prefer actual Markdown sources where available. Follow current proposal; verify links and keep current. No private content, invented `.md` routes or giant dumps. It replaces neither sitemap nor access controls; Google Search ignores it. |

For multiple languages/regions, check distinct locale URLs, page language, reciprocal `hreflang` and compatible canonicals. Add domain-specific needs only where real: products, articles, local business, video, pagination or migrations.

## Verify and hand off

Finish implementation. Manually open representative pages on mobile/desktop; follow navigation, inspect served HTML/headers, assets, redirects, sitemap/robots/llms and intended private exclusions. Compare source and rendered output. Fix observed defects; recheck affected paths.

Then run relevant final automated checks: metadata/links, sitemap/schema validation, eligible Rich Results checks and performance audits under [tests-last order](../../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests). No early crawlers, Lighthouse suites or benchmarks. Use the existing independent reviewer.

Record `check → URL/environment → evidence → PASS / FAIL / UNKNOWN / justified N/A`. Handoff changes, limits, Search Console ownership/status and pending production checks. After authorized deployment, recheck actual host/CDN output. Local green is not live verification; technical readiness is not indexed/ranked status. No ranking promises or perpetual polling.

[Current sources and original adaptation](../../../../docs/skill-provenance.md#public-web-seo-checklist-4-october-2026).
