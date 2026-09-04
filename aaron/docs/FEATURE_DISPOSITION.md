# Feature disposition register

BUILD_SPEC.md section 2.4 requires every interactive element to be classified as either
(a) external-API-backed and portable, or (b) server-backed and needing a PHP rebuild or an
explicit drop decision. The checks-and-balances rule is that nothing is silently omitted
without a record. This is that record.

Applies to both FeatherMoss and Rex Jewelz, which are structurally identical builds.

## Classification result

**Neither app has any server-backed feature.** There are no Next.js API routes, no Server
Actions, no backend of any kind. There is also no external API. Both sites are static HTML
with one hand-written vanilla JS file, and every piece of state lives in the visitor's own
browser. That makes the usual hard case, a Server Action with no static equivalent, simply
absent here.

| Feature | Original mechanism | Class | Disposition |
|---|---|---|---|
| Cart | `localStorage`, key `fm_cart_v1` / `rex_cart_v1` | neither, client only | **Rebuilt in PHP** as the WooCommerce cart |
| Cart drawer | vanilla JS, focus trap, scroll lock | client only | **Dropped**, superseded by the WooCommerce cart page |
| Add to bag | JS writing to `localStorage` | client only | **Rebuilt in PHP**, WooCommerce add to cart form |
| Variant selection | `.pill` buttons with `data-price` | client only | **Rebuilt in PHP**, WooCommerce product attributes and variations |
| Shipping calculation | two constants in the cart JS | client only | **Rebuilt in PHP**, WooCommerce shipping zone, per brand thresholds |
| Checkout | holding page, no payment, `mailto:` fallback | none | **Replaced** by real WooCommerce checkout, see DIVERGENCES.md item 1 |
| Category filter pills | JS show/hide on `data-filter` | client only | **Rebuilt** as real links to category archives, works without JS |
| On-body image swap (Rex) | `data-src` swapping the still | client only | **Rebuilt in PHP** as WooCommerce gallery images |
| Contact | `mailto:` link | none | **Kept as is**, still a `mailto:` link |
| Forms | none exist, zero `<form>` elements sitewide | n/a | nothing to port |
| Auth / login / accounts | none | n/a | nothing to port |
| Search | none | n/a | nothing to port |

## Nothing dropped without a replacement

The only outright drop is the cart drawer, and only because the WooCommerce cart page
replaces the job it was doing. No feature is dropped and left unavailable.

## Outstanding

**Payment gateway is not connected.** The cart correctly reports `needs_payment: yes` and
checkout renders a real form, so this is configuration on a live store, not a build task.
It is the one thing standing between the converted sites and being able to take money,
which is the entire point of the conversion.
