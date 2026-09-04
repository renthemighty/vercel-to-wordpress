# Applying the conversion to a WordPress install

Both scripts run through WP-CLI against a WordPress with WooCommerce active.

```
wp eval-file wp/import-products.php    out/<brand>-products.csv
wp eval-file wp/apply-store-config.php out/store-config.json <brand>
wp import out/<brand>-content.wxr --authors=create
```

Run the product import BEFORE apply-store-config, and the WXR at any point.

## Four traps, all found by actually running this

Every one of these fails **silently**. Nothing errors, the import reports success, and
the store is quietly wrong. They are the reason these scripts exist instead of a note
saying "import the CSV in wp-admin".

**1. `update_existing` must be false on a first import.**
With it true, WooCommerce skips every row that has no existing product to update and
reports `imported: 0, skipped: 60` while claiming success.

**2. The mapping array is keyed by CSV header STRING, not column index.**
WooCommerce documents it as `csv_heading => schema_heading`. Passing an index keyed
array maps every column to nothing, and the import "succeeds" with 60 blank simple
products, no prices, no images, no variations.

**3. Categories need a logged in user with `manage_product_terms`.**
`WC_Product_CSV_Importer::parse_categories_field()` hits
`if ( ! current_user_can( 'manage_product_terms' ) ) break;` and returns an empty array.
Headless there is no current user, so **every category is dropped with no error**, while
tags import fine because they have no such check. `wp_set_current_user(1)` fixes it, and
`import-products.php` hard fails if the capability is missing rather than importing a
miscategorised store.

**4. The free shipping option is `woocommerce_shipping_hide_rates_when_free`.**
Not `..._when_free_available`. With the wrong name the option is a no-op and WooCommerce
offers flat rate *alongside* free shipping above the threshold. The original sites never
did that, they simply declared shipping free.

## Verified behaviour after a clean run

```
Rex Jewelz    20 products (16 variable + 4 sets), 47 variations
              6 categories, 4 attribute taxonomies, every product has an image
              on-body shots land as gallery images (REX-CINTURA + l-hero-cintura.jpg)
              $12 cart  -> $7 flat rate, only option
              $111 cart -> free shipping, only option
              $72 cart  -> $7 flat rate, only option
FeatherMoss   20 products (16 variable + 4 sets), 40 variations
              6 categories, 7 attribute taxonomies, every product has an image
```

Tested against WordPress 7.1 and WooCommerce 11.0.1 on PHP 8.5, SQLite.

## Known and expected

- **No payment gateway is configured**, so `available gateways: NONE`. Cart reports
  `needs_payment: yes` and checkout is reachable. Connecting a real gateway is the
  remaining step for Aaron's real-checkout decision.
- **Category names containing `&` store as `&amp;`.** That is normal WordPress term
  encoding and renders correctly. Only "Charms & Extras" on FeatherMoss is affected.
- **Images sideload from the live Vercel URLs**, so those deployments must stay up until
  the import has run.

## Two more traps, found while building the theme

**5. WooCommerce 11 ships with "Coming soon" mode ON.**
A fresh install replaces the ENTIRE storefront with a launch placeholder. Products import
fine, the theme renders fine, and every visitor still sees "Great things are on the
horizon". `apply-store-config.php` turns it off.

**6. WooCommerce overrides theme button styles unless you claim them.**
Its button rules are guarded by
`:where(body:not(.woocommerce-block-theme-has-button-styles))`. Adding that body class is
the supported way for a theme to say it styles its own buttons, and it beats fighting an
eight selector chain with `!important`. The generated themes add it.

## Theme install

```
cp -R out/themes/<brand> wp-content/themes/<brand>
wp theme activate <brand>
```

Run `apply-store-config.php` AFTER the products import, because it sets the category
display order and needs the categories to exist.

## Content that would otherwise have been lost

Route coverage proved every URL was *accounted for*. It did not prove the content on those
URLs survived, and on the first pass some of it did not.

- **Rex `body.html` and `under-50.html` are not listings.** Both carry several hundred words
  of real editorial copy. They now export as WordPress pages with the product grids
  stripped, because a frozen copy of the catalogue inside page content goes stale the first
  time a price changes.
- **Category lead lines** from `charms.html`, `necklaces.html` and `sets.html`, plus the
  per zone taglines on Rex's shop page, now become `product_cat` descriptions, which the
  archive template renders.
- The lifted `<h1>` is stripped from exported pages, because the template already prints
  `the_title()` and the page rendered its name twice.
- Product long descriptions no longer repeat the blurb. FeatherMoss products have no `long`
  field, so the description fell back to the blurb that the short description already
  displays, printing the same sentence twice on every PDP.

## Mobile

Both originals hide `.nav__links` below 860px and put nothing in its place, so a phone
visitor could only navigate from the footer. The converted themes add a `<details>`
disclosure menu reusing the same links, styled from each brand's own button rule. This is a
deliberate divergence and a visual gate will flag the header on narrow widths. Remove the
`.navmob` block in `build_theme.py` to go back to exact parity.

Verified at 500px on both brands: no horizontal overflow, cards reflow, filter pills wrap,
PDP goes single column, and the add to cart controls go full width.
