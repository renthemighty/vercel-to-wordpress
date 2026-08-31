# Functional summary, FeatherMoss and Rex Jewelz

BUILD_SPEC.md section 2.7 asks for a written summary of what each app does, its user flows,
its page inventory, and which features are portable, produced from the crawl rather than
assumed. Cross-checked against Aaron's own description, which matched.

Both are hand-built static sites, not Next.js. See DISCOVERY notes on the webshare for the
measurements behind that.

---

## FeatherMoss

**What it is.** A 20 piece kitschy jewelry shop. Beaded, charmed and enamelled necklaces,
earrings, bracelets, rings and charm sets in a moss-girl aesthetic, strung by hand in San
Diego, priced in USD, shipped worldwide. Prices run $12 to $368.

**Who it is for.** Someone buying a small, characterful piece for themselves, at a price
that does not need thinking about. The copy leans on the pieces surviving daily wear rather
than being photographed once.

**Main user flows.**
1. Land, read the hero, go to Shop.
2. Browse all 20 pieces grouped by type, or filter to one category.
3. Open a product, pick a variant, add to bag.
4. Read shipping, returns, care or stockists.
5. Read the journal, three posts.

**Page inventory.** 38 routes. 1 front page, 1 shop, 4 category listings, 20 product pages,
6 standing pages, 1 journal index plus 3 posts, cart, checkout, 404.

**Catalogue.** 16 products with 40 variants across 5 attribute types, plus 4 sets. 6
categories, 5 collection tags.

**Shipping.** Free over $75, otherwise $6 flat.

---

## Rex Jewelz

**What it is.** A 20 piece body chain and body jewelry shop. A Miami brand, built for heat,
sweat and a full night out, priced in USD, shipped worldwide. Prices run $12 to $368.

**What makes it different.** The catalogue is organised by where a piece sits on the body,
read top to bottom, rather than by product type. That ordering is deliberate and the source
calls it the spine of the whole shop. Every product also carries a one word English gloss of
its Spanish name, shown under the name on every card.

**Who it is for.** Someone buying a piece that has to fit rather than just hang, which the
site treats as the harder problem and talks about directly. There is a dedicated fit and
sizing page and a made-to-measure option.

**Main user flows.**
1. Land, go to Shop or Body chains.
2. Browse by body zone, by set, or by everything under $50.
3. Read the fit guide before choosing a size.
4. Open a product, view the on-body shot, pick a size or finish, add to bag.
5. Read the journal, three posts.

**Page inventory.** 38 routes. 1 front page, 1 shop, 1 body chains editorial page, 1 sets
listing, 1 under $50 listing, 1 fit guide, 20 product pages, 5 standing pages, 1 journal
index plus 3 posts, cart, checkout, 404.

**Catalogue.** 16 products with 47 variants across 4 attribute types, plus 4 sets. 6 body
zone categories, 5 collection tags. 8 products carry a second on-body photograph.

**Shipping.** Free over $95, otherwise $7 flat. Note this differs from FeatherMoss.

---

## Portability, both brands

Everything is portable. Neither site has a server-backed feature, an external API
dependency, an auth flow, or a form. The only feature that could not be carried across
as-is is the checkout, because on the original it does not work: it is a holding page that
asks the visitor to send an email. That is replaced with real WooCommerce checkout by
decision, not by necessity. Full classification in FEATURE_DISPOSITION.md.

## Confidence

High. The live HTML is byte-identical to the local build output on both sites, so there is
no hidden runtime state, no middleware variance and no ISR drift to account for. Three
deterministic gates pass on both brands: catalogue-to-import equivalence, full route
coverage, and a structural diff of original against converted.
