# Public web SEO

For public pages meant for search: landing, marketing, content pages, a web app's public routes. Private screens stay out.
Plan early. Verify before launch and again after deployment. Small fixes stay scoped. Analysis stays read-only.

## Set the boundary

- Record production domain, audience and search intent, languages, public routes, private routes, staging, existing SEO setup.
- Reuse the CMS or framework SEO features. No duplicate sitemap or metadata generators.
- New site: every public template and key page. Existing fix: affected pages, shared templates, consumers.
- Research material unknowns in current primary guidance. Extend the checklist for real gaps only.
- Keep login, access controls and deliberate exclusions. Never index accounts, admin, personal data or previews.
- DNS, ownership verification, submissions and deployment need real project access and authority.

## Build the essentials

| Check | Require |
|---|---|
| Indexing | Remove accidental `noindex` from intended production pages: HTML meta and `X-Robots-Tag`. Keep intentional exclusions. A crawler must reach a page to read `noindex`. `robots.txt` is neither deindexing nor access control. |
| `robots.txt` | At the host root, with environment-correct rules and the sitemap location. Allow intended pages and the CSS, JS and images they need. Never ship staging's blanket block to production. |
| `sitemap.xml` | Generated from published routes. Absolute preferred-HTTPS URLs, indexable 200 pages only, truthful `lastmod` when known. Exclude private, duplicate, redirected, missing and noindex URLs. Update with routes and content. Split large sitemaps with an index at the current limits. |
| URLs and canonicals | Stable descriptive slugs. One host, protocol and trailing-slash convention. Absolute canonical per page, consistent with sitemap and internal links. Consolidate true duplicates. Never canonicalize distinct pages to home. URL changes get mapped permanent redirects and updated links. No chains, no loops. |
| Crawl and render | Main content, metadata and crawlable `<a href>` links available without login or clicks. Render assets not blocked. Prefer server or static rendering for public content; verify the actual output. Missing routes return a real 404 or 410, not a 200 shell. Bound faceted and search-parameter crawl paths. |
| Titles and descriptions | Unique, accurate title and meta description per indexable page, search intent first. No stuffing, boilerplate duplication or fabricated claims. Promise no exact length or snippet. |
| Headings and content | One H1. Logical heading hierarchy. Useful original content, descriptive internal links, key pages reachable, no broken links, no orphans. No keyword quota. |
| Images | Informative alt text. Decorative images `alt=""`. Compressed without visible damage, suitable formats, responsive sizes, explicit dimensions. Lazy-load below the fold. Load the LCP image promptly. |
| Structured data | Relevant JSON-LD whose properties match visible facts. Check current eligibility and syntax. No fake reviews, ratings or offers. No FAQ markup everywhere. Valid schema guarantees no rich result. |
| Mobile and performance | Responsive, readable, usable controls, same content and metadata as desktop. Control scripts, fonts, assets. No layout shifts or blocking overlays. Targets at p75, mobile and desktop separately: LCP ≤2.5 s, INP ≤200 ms, CLS ≤0.1. Recheck current thresholds. Lab results do not prove field performance. Missing field data stays unknown. |
| HTTPS | Valid certificate. HTTP redirects to the preferred HTTPS URL. No mixed content, broken assets, redirect loops. Keep a working host and security policy. |
| Sharing | Accurate Open Graph title, type, URL, description. Public absolute `og:image` with alt and dimensions. Inspect the real crop and legibility. Add platform card tags where needed. Previews are not ranking evidence. |
| Search console | Reuse the right property and owner. Verify by a supported method with authorized access. Keep verification records. Submit the sitemap. Inspect representative live URLs and the indexing and canonical reports. Missing access blocks this row only. Submission proves neither indexing nor ranking. |
| `llms.txt` | Only when requested. Root Markdown file: site H1, brief summary, grouped useful public links. Prefer real Markdown sources where they exist. Verify links. No private content, invented `.md` routes or giant dumps. Replaces neither sitemap nor access controls. Google Search ignores it. |

Multiple languages or regions: distinct locale URLs, page language, reciprocal `hreflang`, compatible canonicals.
Add domain-specific markup only where real: products, articles, local business, video, pagination, migrations.

## Verify and hand off

1. Finish implementation.
2. Open representative pages on mobile and desktop. Follow navigation. Inspect served HTML, headers, assets, redirects, sitemap, robots, `llms.txt`, private exclusions. Compare source with rendered output.
3. Fix observed defects. Recheck affected paths.
4. Then run automated checks: metadata, links, sitemap and schema validation, rich-result eligibility, performance audits. None earlier.
5. Record `check → URL/environment → evidence → PASS / FAIL / UNKNOWN / N/A with reason`.
6. After authorized deployment, recheck the real host and CDN output. Local green is not live verification.

Handoff: changes, limits, search console ownership and status, pending production checks.
Technical readiness is not indexed or ranked. No ranking promises. No perpetual polling.
