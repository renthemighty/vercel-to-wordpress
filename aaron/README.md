# Aaron's side — FeatherMoss and Rex Jewelz conversion

Working files for the two conversions. Both are built, tested against a real WordPress, and
themed. Nothing is deployed and no hosting has been touched.

## Read this first: the pipeline assumption does not hold for these two

**Neither app is Next.js. Neither is React.** Both are hand-written Python static site
generators that read `catalog/catalog.json` and emit flat `.html` into `site/`, deployed to
Vercel as static hosting. Measured on the live sites, not assumed:

| Check from BUILD_SPEC section 3.3 | Result |
|---|---|
| `__NEXT_DATA__` in page source | absent |
| `x-powered-by` header | absent |
| `x-nextjs-cache` header | absent |
| `_next` references in HTML | 0 |
| `GET /_next/static` | 404 |
| URL shape | literal `.html`, `/shop` 404s and `/shop.html` is 200 |
| `/sitemap.xml` | 404 on both |

So none of BUILD_SPEC section 1's risks apply here: no `/_next/image` rewriting, no Server
Actions, no SSR or ISR, no edge middleware, no ISR cache drift to log. The live HTML is
byte-identical to the local build output on both sites, so there is no hidden runtime state
a crawl could miss and no middleware variance to flag.

The practical consequence: the upstream `catalog.json` carries the full variant and price
structure that a crawl of rendered HTML cannot recover reliably. These tools import from it
directly, which is lossless. Aaron's instruction was to run your pipeline as designed
anyway, so this does not replace it. It gives you a verified product, content and theme
layer to install rather than reconstruct, and a reference to diff a crawl against.

## What is here

```
tools/    build + verify, all deterministic, no model calls
wp/       apply to a live WordPress via WP-CLI
docs/     functional summary, feature disposition, recorded divergences
out/      generated artifacts, ready to import
themes/   a WordPress theme per brand
```

## The three gates

BUILD_SPEC section 2 asks for a deterministic non-LLM verifier in the loop. There are three,
all exit non-zero on failure, none of them call a model:

- `verify_woo_import.py` — every product, variant, price, image and cross-sell in the
  generated CSV checked against `catalog.json`, plus a live HEAD on every image URL.
- `verify_coverage.py` — proves all 38 routes per brand are accounted for as an exported
  page, a product, or an explicitly skipped route with a written reason.
- `verify_structural_diff.py` — fetches the original page and the converted page and
  compares content and structure: product cards, prices, headings, visible words.
  Structural rather than pixel, per BUILD_SPEC 2.6, which flags raw pixelmatch as the wrong
  tool across a React-DOM-vs-PHP comparison. Immune to font and reflow noise, still catches
  missing products, dropped prices and lost copy.

Current state, both brands: **all three pass.**

```
feathermoss   20 products, 40 variations, 6 categories, 5 attributes
              38/38 routes covered, 10/10 routes structurally equivalent
rexjewelz     20 products, 47 variations, 6 categories, 4 attributes
              38/38 routes covered, 10/10 routes structurally equivalent
```

Accepted differences are recorded in `docs/DIVERGENCES.md`, which the structural gate reads.
An entry there suppresses a failure and nothing else does, so anything the gate flags that
is not in that file is a real defect.

## Six silent WooCommerce failures, found by running it

Each reports success and leaves the store quietly wrong. Most will hit any programmatic
WooCommerce import, whoever wrote the CSV. Full write-up in `wp/README.md`.

1. `update_existing` must be false on a first import, or every row skips.
2. The importer mapping is keyed by CSV header string, not column index.
3. Categories are dropped entirely without a logged-in user holding `manage_product_terms`.
   Tags have no such check, which is why only categories vanish.
4. The option is `woocommerce_shipping_hide_rates_when_free`, not `..._when_free_available`.
5. WooCommerce 11 ships with Coming soon mode ON, replacing the whole storefront.
6. WooCommerce overrides theme buttons unless the theme claims them.

**Worth auditing werescrewed.ca for 3, 4 and 5.** Number 3 produces a store that looks
correct until someone browses a category. Number 5 means a correctly built store can sit
invisible behind a launch placeholder.

## Still blocked

`rexjewelz.com` ownership. Registered at eNom 2026-07-30, nameservers resolve to
`a84n2p8d.easwrk.net`, no A record, not in Aaron's GoDaddy account. Target domains are in
`VEREL_DOMAIN_MAP` on the webshare. Hosting has not been self-provisioned, per BUILD_SPEC
section 4.
