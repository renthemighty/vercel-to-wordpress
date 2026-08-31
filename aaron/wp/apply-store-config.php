<?php
$cfg = json_decode(file_get_contents($args[0]), true)[$args[1]];
update_option('woocommerce_currency', $cfg['currency']);
update_option('woocommerce_store_country', 'US:CA');
update_option('woocommerce_default_country', 'US:CA');
update_option('woocommerce_calc_taxes', 'no');
// free shipping over threshold, flat rate under, exactly as the cart JS did
$zone = new WC_Shipping_Zone(0);
foreach ($zone->get_shipping_methods() as $m) $zone->delete_shipping_method($m->instance_id);
$flat = $zone->add_shipping_method('flat_rate');
$free = $zone->add_shipping_method('free_shipping');
$zone->save();
$fi = WC_Shipping_Zones::get_shipping_method($flat);
$fi->instance_settings['cost'] = (string)$cfg['flat_shipping_rate'];
update_option($fi->get_instance_option_key(), $fi->instance_settings);
$fr = WC_Shipping_Zones::get_shipping_method($free);
$fr->instance_settings['requires']   = 'min_amount';
$fr->instance_settings['min_amount'] = (string)$cfg['free_shipping_over'];
update_option($fr->get_instance_option_key(), $fr->instance_settings);
// WooCommerce 11 ships with "Coming soon" mode ON by default on a fresh install, which
// replaces the ENTIRE storefront with a launch placeholder. Products import fine, the
// theme renders fine, and every visitor still sees "Great things are on the horizon".
update_option('woocommerce_coming_soon', 'no');
update_option('woocommerce_store_pages_only', 'no');

// On the original the cart JS simply declared shipping free above the threshold, it
// never offered a paid alternative. Without this WooCommerce lists flat rate AND free
// side by side above the threshold, which is not what the original did.
update_option('woocommerce_shipping_hide_rates_when_free', 'yes');
// Lead copy from the original listing pages becomes the category description, which the
// theme renders under the heading. Without this the copy is simply lost when the listing
// pages give way to WooCommerce archives.
foreach (($cfg['category_descriptions'] ?? []) as $catname => $desc) {
    $t = get_term_by('name', $catname, 'product_cat')
         ?: get_term_by('name', htmlspecialchars($catname, ENT_QUOTES), 'product_cat');
    if ($t) { wp_update_term($t->term_id, 'product_cat', array('description' => $desc)); }
    else { WP_CLI::warning("category not found, cannot describe: $catname"); }
}

// Category order is NOT alphabetical in either catalogue. FeatherMoss runs Necklaces
// first, and Rex Jewelz orders by where a piece sits on the body, top to bottom, which
// is deliberate and load bearing to that brand. Carry the catalogue order across as
// WooCommerce term order so the shop page does not resort it.
foreach ($cfg['categories'] as $i => $catname) {
    $t = get_term_by('name', $catname, 'product_cat');
    if (!$t) { $t = get_term_by('name', htmlspecialchars($catname, ENT_QUOTES), 'product_cat'); }
    if ($t) { update_term_meta($t->term_id, 'order', $i + 1); }
    else { WP_CLI::warning("category not found, cannot order: $catname"); }
}

WP_CLI::line("applied {$args[1]}: {$cfg['currency']}, free over {$cfg['free_shipping_over']}, flat {$cfg['flat_shipping_rate']}");
