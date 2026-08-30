# Prompt for Aaron's Claude — Vercel App → WordPress Conversion

You're being asked to help convert one or more of Aaron's Vercel-hosted apps into
WordPress sites, as close to identical as possible. This is a new extension of an existing
EasWrk pipeline (base44towordpress / "b442") that already converts Base44/Lovable React
apps into WordPress themes with automated visual verification — we're adapting it for
Vercel/Next.js specifically because that platform behaves differently (server rendering,
edge middleware, on-demand image optimization) in ways that matter for a faithful
conversion.

**Read first:** `docs/BUILD_SPEC.md` in this repo — it has the full technical research and
pipeline design. Don't duplicate that thinking; work from it.

## Status update: the pipeline is proven, not just planned

Since this doc was first written, the underlying conversion pipeline (b442) went through a
real hardening pass: a customer-breaking packaging bug was found and fixed, a real
pre-deployment validator now runs on every build (structural checks + an actual disposable
WordPress install-and-activate smoke test before anything is called done), and a live
end-to-end proof was run: a real customer's app was rebuilt and installed live at
`werescrewed.ca` — fully working, zero fatals, images local, visual gate clean. This is a
live, working system now, not a research spec. Build with real confidence, but keep the
same discipline: stop and fix any defect you find, never ship or hand off a build with a
known issue "for now."

**Scope: full-site conversion, not a partial mirror.** Each app needs its ENTIRE site
converted — every page, every route, every piece of real content and interactive feature
Aaron's app has — not just a homepage or a representative sample. Treat "done" as "a visitor
to the new WordPress site can do everything they could do on the original app," not "the
main pages look right."

## Your job right now: discovery, not building yet

Before any conversion work starts, get precise answers to these questions for **each**
Vercel app Aaron wants converted. Don't guess or assume — ask him directly if you don't
know, and post the answers back (see "Where to post" below).

1. **Live URL(s)** — production domain, plus any staging/preview URLs that show different
   content or features.
2. **Source access** — is there a GitHub repo? If Aaron can grant read access (or export a
   zip), that unlocks build-time analysis (confirms whether pages are static/SSR/ISR,
   reveals Server Action logic, dynamic route lists) that scraping the live site alone
   cannot give us. If there's no repo access, say so explicitly — we'll work live-only.
3. **Framework confirmation** — check the page source and response headers
   (`x-powered-by`, `x-nextjs-cache`, `__NEXT_DATA__` in a `<script>` tag) to confirm it's
   actually Next.js (App Router vs Pages Router) and not another Vercel-hosted framework
   (Remix, Astro, SvelteKit — these behave differently and this spec is Next.js-specific).
4. **Any existing export/build artifact** — does Aaron already have a `.next` folder, an
   `out/` static export, or any downloadable zip of the built site? If so, that's a
   shortcut worth using directly rather than re-scraping.
5. **Sitemap check** — does `<domain>/sitemap.xml` exist and look complete? Note the
   result either way; a missing or thin sitemap means route discovery will need a full
   link-graph crawl instead, which takes longer and can miss unlinked pages.
6. **Interactive features inventory** — list every form, login/auth flow, cart/checkout,
   search, or dashboard-style feature you can find by using the app. Note whether each one
   visibly calls an external service (Stripe, Auth0, Shopify) vs. appears to be custom
   backend logic — you can often tell from the network tab. This matters because
   backend-custom features have no clean static equivalent and need a real decision
   (rebuild in PHP, or explicitly drop), while external-API-backed features usually port
   with minimal change.
7. **What does the app actually do?** — ask Aaron for a plain-language description of the
   app's purpose and its main user flows if he can give one. We'll also generate our own
   summary from crawling it, but a real description from the person who built/knows it is
   a much better cross-check than us guessing purely from screenshots.
8. **His GitHub username** — needed to add him as a collaborator on this private repo
   (`vercel-to-wordpress`) so we can push shared build artifacts and conversion notes both
   sides can see.
9. **Which target domain each app goes to.** Aaron has multiple domains/hosting accounts
   under his umbrella (see his AARON_ACCESS_PACK / AARON_STATUS sections on the webshare
   for the current roster). For EVERY Vercel app being converted, ask him explicitly and
   directly which one of his own domains it should end up living on — do not assume, do not
   guess from the app's name, and do not let this stay ambiguous. Build a simple table:
   source Vercel app URL → target domain. If Aaron has an app with no domain decided yet,
   flag that specific one as blocked-on-Aaron rather than picking one for him or leaving it
   unstated.

## Checks and balances — how this gets verified, not just built

This pipeline deliberately does NOT rely on an AI grading its own work. Research on
AI-driven code migration is clear that an LLM self-reviewing its own conversion output is
unreliable — the fix is an independent, deterministic check, not another "does this look
right?" prompt to the same or another model. Concretely, that means:

- A visual-diff comparison (screenshot pixel/structural comparison) between the live
  original and the rebuilt WordPress page gates every build — a page that fails the
  comparison does not ship silently.
- Any page where the crawl detects inconsistent content across repeat visits (a sign of
  edge middleware, A/B testing, or per-session variation) gets flagged for a human
  decision, not silently resolved one way.
- Any feature identified as backend-custom (no external API, likely a Next.js API
  route/Server Action) gets flagged with an explicit note — "rebuilt in PHP" or "dropped,
  needs manual follow-up" — never silently omitted without a record.

If you're building any part of the crawl/rebuild tooling yourself, keep this shape: a
step that produces output, and a **separate, non-generative** step that checks it, before
anything is called done.

## Where to post progress

Same as all other Microgenix/Aaron/EasWrk shared work: the webshare at
`https://microgenix.net/webshare/cs.php` (token/passphrase Aaron already has). Post
discovery answers as a section (`a=section&s=VEREL_DISCOVERY`, or whatever name makes
sense per-app if there are multiple apps) so Simon's side can pick it up without a live
sync call. Also push actual working files (crawl samples, notes, spec revisions) to this
GitHub repo directly, once you have collaborator access.

## Hosting

Do not attempt to self-provision a hosting account yet — that automation isn't built. Once
you know a target domain for a converted site, post the domain + any details in your
webshare update, and it'll get provisioned on the existing standard hosting product the
same way every prior conversion has been (see `BUILD_SPEC.md` Section 4 for why this
isn't yet self-service).
