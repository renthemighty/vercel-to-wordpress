# Build Spec — Vercel/Next.js → WordPress Conversion

Status: DRAFT, unreviewed by Simon. Research-backed plan, not yet executed against a real
target. Feeds into base44towordpress (b442) once proven — see
`wiki/questions/Research: SPA-to-WordPress AI Conversion with Visual QA.md` in the Obsidian
vault for full sourced research this spec is built on.

## 1. Why this is a new track, not a copy of b442

b442 already converts live Base44/Lovable React SPAs into WordPress themes via: Playwright
crawl → Analyzer (theme tokens, nav, shared chrome) → StaticRebuilder + Claude SectionGen
(per-page PHP template rebuild) → MediaImporter → visual-diff gate (screenshot pixel
comparison) before a build is accepted.

Vercel/Next.js apps are **rendered the same way at the DOM level** (a headless browser
still gets real, hydrated HTML), so the crawl-and-capture method carries over unchanged.
What's different, confirmed by research:

- **No forced static mode.** `output: 'export'` requires the source repo and a `next
  build` — irrelevant against someone else's live deployment. Assume you are always
  scraping whatever hybrid SSR/ISR/SSG mix the live site actually serves.
- **`/_next/image?url=...&w=...&q=...` always 404s once off Vercel.** Every image
  reference must be rewritten: resolve `url=`, fetch the original, drop the wrapper.
- **Server Actions and API routes have no static equivalent.** A form wired to a Server
  Action is a dead POST target once there's no Next.js server behind the page — must be
  reimplemented in PHP (wp_mail, WooCommerce, a custom endpoint) or explicitly dropped.
- **Middleware/Proxy (edge-level redirects, auth gating, A/B bucketing) is invisible in
  rendered HTML.** A crawl only sees one branch. Detect by diffing a fresh-session crawl
  against a common-cookie-pattern crawl; flag mismatches for manual review, don't silently
  pick one.
- **Route discovery**: `/sitemap.xml` / `robots.txt` / full link-graph crawl only — no
  tool reconstructs a live Next.js app's route list from outside (next-sitemap and
  generateStaticParams are both build-time/source-only).
- **ISR cache drift**: log the `x-nextjs-cache` response header per page; STALE/MISS
  captures are lower-confidence and worth a re-crawl.
- **No public precedent exists for Next.js/Vercel → WordPress specifically** (confirmed
  searched, not just unsearched). Treat this as first-of-its-kind, budget extra spot-check
  QA accordingly, and document what we learn — this becomes the prior art.

## 2. Pipeline (checks-and-balances design)

Per the legacy-code-migration research (arXiv 2605.21537, 2607.28271): an LLM cannot
reliably self-review its own migration output. The fix is a **deterministic, non-LLM
verifier** in the loop, not a second "does this look right?" Claude call. b442's pixelmatch
visual gate already follows this pattern — keep it, but improve it (see 2.4).

1. **Discovery** (human/Claude-assisted, see Section 3 questions) — establish target
   URL(s), whether source/GitHub access exists, static vs hybrid rendering, sitemap
   presence, known interactive features.
2. **Crawl agent** — Playwright, wait for network-idle + a fixed hydration-settle delay,
   capture `document.documentElement.outerHTML` + full-page screenshot per route. Route
   list from sitemap.xml first, fall back to recursive link-graph traversal. Log
   `x-nextjs-cache` per response.
3. **Rewrite/normalize pass** — resolve every `/_next/image?url=...` back to its source
   image and rewrite references; harvest every `/_next/static/...` asset, font, and CSS
   file explicitly (Next's own standalone builds have this exact gap — assets never travel
   with HTML automatically).
4. **Analyzer agent** — theme tokens (colors, fonts, spacing), shared header/footer chrome,
   nav structure, page inventory. Also classifies each interactive element found:
   (a) external-API-backed (Clerk/Auth0 standalone SDK, Shopify Storefront API, Stripe
   Checkout links) → portable near-unchanged as an isolated JS "island"; or
   (b) Next.js-server-backed (API route/Server Action) → flagged, needs PHP
   reimplementation or an explicit feature-drop decision.
5. **StaticRebuilder + Claude SectionGen** — same as b442, rebuilds each page as a WP PHP
   template from the captured markup + theme tokens.
6. **Deterministic visual-diff gate** — do NOT use raw pixelmatch alone across a
   React-DOM-vs-PHP-HTML comparison; research flags this as likely to over-flag on
   font-rendering/text-reflow noise. Move toward perceptual/structural diffing: CW-SSIM or
   a masked-text + layout-bounding-box comparison, with a tolerance budget (reference
   figures found in research: ~0.1% pixel tolerance is standard same-stack CI; AI-generated
   UI comparisons commonly use `maxDiffPixels:100, maxDiffPixelRatio:0.01`, but those are
   same-stack too — needs its own calibration pass against a known-good b442 build before
   trusting a threshold for cross-stack comparison).
7. **Functional summary agent** — before or during conversion, generate a written summary
   of what the app does (purpose, key user flows, page inventory, which features are
   fully portable vs. flagged) purely from the crawl + screenshots. No public prior art for
   this exact "app archaeology from a live URL" pattern was found — b442's existing
   Analyzer crawl approach is already ahead of published practice here; formalize its
   output into a customer-facing summary document rather than just internal build config.
8. **MediaImporter** — same as b442, pulls resolved images into the WP media library.
9. **Human/Simon review gate** — any page with a flagged Middleware-variance, a
   Server-Action-backed feature with no clean PHP equivalent, or a failed visual-diff
   after retry gets surfaced for manual decision, not silently shipped or silently dropped.

## 3. Discovery questions (ask before starting any conversion)

For each Vercel app to convert:

1. **Live URL(s)** — production domain and any staging/preview URLs.
2. **Source/repo access** — is there a GitHub repo? If yes, can we get read access (or a
   zip export)? Source access unlocks `output: 'export'`/build-time tooling that live-only
   scraping cannot use, and tells us definitively whether pages are SSG/SSR/ISR.
3. **Framework confirmation** — Next.js (App Router or Pages Router?), or another
   Vercel-hosted framework (Remix, Astro, SvelteKit)? Check response headers
   (`x-powered-by`, `x-nextjs-cache`) and page source for `__NEXT_DATA__`/RSC markers.
4. **Any downloadable export/build artifact already produced** (a `.next` folder, an
   `out/` static export, a zip Aaron already has)?
5. **Sitemap/robots** — does `/sitemap.xml` exist and look complete? If not, expect route
   discovery to be harder and budget extra crawl time.
6. **Known interactive features** — forms, auth/login, checkout/cart, search, dashboards,
   real-time data. Get a plain-language list up front rather than discovering them mid-crawl.
7. **What does the app do?** — if Aaron/the client can supply a short functional
   description, use it to cross-check the auto-generated functional summary (Section 2.7)
   rather than generating one from zero context.

## 4. Hosting/WHMCS

The standard deployment product already exists: WHMCS product id 121 ("Tier !") — free,
hidden from the public order form, spans the load-balanced DA server group (uilpwnms /
ab9iejct / po3jwnmi). This is what every recent b442-style conversion deployment has been
provisioned on (sacredmeds.net, myceliahealth.org, mymicrowellness.com, chat.bizar.cc,
pacificglasses.ca, etc.) — no new product needs to be created, the "recreate it every time"
problem is a **provisioning workflow** gap, not a missing product.

**Current state**: provisioning a new hosting account on product 121 is admin/API-console
only (localAPI AddOrder + AcceptOrder + ModuleCreate). There is no coupon system in this
WHMCS install (`tblcoupons` doesn't exist) — "free trial via coupon" isn't a real mechanism
here, and doesn't need to be; the product is already free and hidden, which achieves the
same effect.

**Not yet built**: a scoped self-service path for Aaron's Claude to trigger account
creation directly. WHMCS 8.13+ has an API Roles table (`tblapi_roles`) already present,
which is the correct mechanism — a role restricted to order-creation only against product
121, issued as a credential scoped to Aaron's own client account, not a full admin key.
**This has not been built yet and should not be treated as available** — until it exists,
Aaron's Claude should request a new hosting account by name/domain via the webshare
activity log, and Simon (or this Claude session) provisions it manually the same way every
prior deployment has been. Building the scoped API role automation is a separate, explicit
task Simon has not yet greenlit.

## 5. Repo / collaboration

This repo (`vercel-to-wordpress`) is private, created for this workstream specifically.
Aaron (or his Claude, on his behalf) should get collaborator access once we have his GitHub
username — ask for it as part of Section 3 discovery, do not guess it. Push working
artifacts (crawl output samples, per-app conversion notes, build spec revisions) here so
both sides see the same state, same spirit as the MGX webshare but for code/artifacts
rather than free-text status.

## 6. Open items / not yet done

- Visual-diff gate calibration for cross-stack (React DOM vs PHP HTML) comparison — needs
  a real test run against a known b442 build before trusting any specific threshold.
- Scoped WHMCS API role for self-service hosting provisioning (see Section 4) — designed,
  not built.
- No live Vercel/Next.js target has been run through any part of this pipeline yet. Every
  item above is research-backed planning, not verified-in-production fact, until a real
  conversion attempt happens.
