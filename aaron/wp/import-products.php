<?php
/* Runs the REAL WooCommerce CSV importer with an explicit header -> internal key
   mapping, which is what the admin UI ends up passing after its mapping screen. */
$file = $args[0];
if (!file_exists($file)) { WP_CLI::error("no such file $file"); }
include_once WC_ABSPATH . 'includes/import/class-wc-product-csv-importer.php';

// WooCommerce's parse_categories_field() bails out unless the CURRENT USER holds
// manage_product_terms. Headless there is no current user, so every category is
// silently dropped while tags, which have no such check, import fine. Any
// programmatic import must assume an admin identity or it loses the whole
// category tree with no error at all.
wp_set_current_user(1);
if (!current_user_can('manage_product_terms')) {
    WP_CLI::error('current user cannot manage_product_terms, categories would be dropped');
}

$KEYS = [
    'ID'                      => 'id',
    'Type'                    => 'type',
    'SKU'                     => 'sku',
    'Name'                    => 'name',
    'Published'               => 'published',
    'Is featured?'            => 'featured',
    'Visibility in catalog'   => 'catalog_visibility',
    'Short description'       => 'short_description',
    'Description'             => 'description',
    'Tax status'              => 'tax_status',
    'Tax class'               => 'tax_class',
    'In stock?'               => 'stock_status',
    'Stock'                   => 'stock_quantity',
    'Backorders allowed?'     => 'backorders',
    'Sold individually?'      => 'sold_individually',
    'Allow customer reviews?' => 'reviews_allowed',
    'Sale price'              => 'sale_price',
    'Regular price'           => 'regular_price',
    'Categories'              => 'category_ids',
    'Tags'                    => 'tag_ids',
    'Images'                  => 'images',
    'Parent'                  => 'parent_id',
    'Upsells'                 => 'upsell_ids',
    'Cross-sells'             => 'cross_sell_ids',
    'Position'                => 'menu_order',
    'Attribute 1 name'        => 'attributes:name1',
    'Attribute 1 value(s)'    => 'attributes:value1',
    'Attribute 1 visible'     => 'attributes:visible1',
    'Attribute 1 global'      => 'attributes:taxonomy1',
];

// WooCommerce documents this as "csv_heading => schema_heading" and looks it up by
// header STRING, not by column index. Passing an index keyed array silently maps
// every column to nothing and imports blank products.
$headers = [];
if (($h = fopen($file, 'r')) !== false) { $headers = fgetcsv($h); fclose($h); }
$mapping = []; $unmapped = [];
foreach ($headers as $hh) {
    if (isset($KEYS[$hh])) { $mapping[$hh] = $KEYS[$hh]; }
    // "Meta: key" columns pass straight through as post meta. Without this they are
    // silently dropped, which is how the Rex product glosses went missing.
    // WooCommerce recognises the internal key "meta:<key>", lowercase and unspaced. Mapping
    // the header text to itself looks right and silently imports nothing.
    elseif (strpos($hh, 'Meta: ') === 0) { $mapping[$hh] = 'meta:' . substr($hh, 6); }
    else { $unmapped[] = $hh; }
}
if ($unmapped) { WP_CLI::warning('unmapped columns: ' . implode(', ', $unmapped)); }

$importer = new WC_Product_CSV_Importer($file, [
    'start_pos'        => 0,
    'lines'            => -1,
    'parse'            => true,
    'update_existing'  => false,
    'prevent_timeouts' => false,
    'mapping'          => $mapping,
]);
$res = $importer->import();
WP_CLI::line('imported : ' . count($res['imported']));
WP_CLI::line('updated  : ' . count($res['updated']));
WP_CLI::line('skipped  : ' . count($res['skipped']));
WP_CLI::line('failed   : ' . count($res['failed']));
foreach ($res['failed'] as $f)
    WP_CLI::line('  FAIL ' . (is_wp_error($f) ? $f->get_error_message() : print_r($f,true)));
foreach (array_slice($res['skipped'],0,5) as $s)
    WP_CLI::line('  SKIP ' . (is_wp_error($s) ? $s->get_error_message() : print_r($s,true)));
