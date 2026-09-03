<?php
/* Conversion runner. Token gated, runs the repo's own wp/ scripts over HTTP because
   this hosting tier has no SSH and therefore no WP-CLI. Delete after use. */
@set_time_limit(0);
@ini_set('memory_limit', '512M');
header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate');
$TOKEN = '__TOKEN__';
if (!isset($_GET['k']) || !hash_equals($TOKEN, (string)$_GET['k'])) { http_response_code(404); echo "nope\n"; exit; }
$ROOT = __DIR__;
$CONV = $ROOT . '/_conv';
$step = isset($_GET['step']) ? $_GET['step'] : 'verify';
$BRAND = isset($_GET['brand']) ? preg_replace('/[^a-z]/', '', $_GET['brand']) : '';

function say($k, $v = '') { echo str_pad($k, 26) . ' ' . $v . "\n"; }

/* WP-CLI shim so the repo scripts run unmodified. */
if (!class_exists('WP_CLI')) {
    class WP_CLI {
        public static function line($m = '')  { echo $m . "\n"; }
        public static function log($m = '')   { echo $m . "\n"; }
        public static function warning($m)    { echo 'WARN  ' . $m . "\n"; }
        public static function success($m)    { echo 'OK    ' . $m . "\n"; }
        public static function error($m)      { echo 'ERROR ' . $m . "\n"; exit; }
    }
}

require_once $ROOT . '/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';
require_once ABSPATH . 'wp-admin/includes/file.php';
require_once ABSPATH . 'wp-admin/includes/misc.php';
wp_set_current_user(1);

if ($step === 'woo') {
    /* The DirectAdmin placeholder index.html outranks index.php in the DirectoryIndex, so
       WordPress never gets a chance to answer. DA's delete API is a silent no-op on this
       host, so unlink it here. */
    if (file_exists("$ROOT/index.html")) { @unlink("$ROOT/index.html"); }
    say('index.html', file_exists("$ROOT/index.html") ? 'STILL THERE' : 'removed');

    $r = activate_plugin('woocommerce/woocommerce.php');
    say('activate woocommerce', is_wp_error($r) ? $r->get_error_message() : (is_plugin_active('woocommerce/woocommerce.php') ? 'active' : 'not active'));
    if (class_exists('WC_Install')) { WC_Install::install(); say('wc install', 'ran'); }

    update_option('permalink_structure', '/%postname%/');
    update_option('rewrite_rules', '');
    flush_rewrite_rules(true);
    /* The rewrite flush does not write .htaccess on this host, so write it directly. */
    $ht = "$ROOT/.htaccess";
    $rules = "# BEGIN WordPress\n<IfModule mod_rewrite.c>\nRewriteEngine On\nRewriteBase /\nRewriteRule ^index\\.php$ - [L]\nRewriteCond %{REQUEST_FILENAME} !-f\nRewriteCond %{REQUEST_FILENAME} !-d\nRewriteRule . /index.php [L]\n</IfModule>\n# END WordPress\n";
    $existing = file_exists($ht) ? file_get_contents($ht) : '';
    if (strpos($existing, 'BEGIN WordPress') === false) { file_put_contents($ht, $rules . $existing); }
    say('.htaccess', file_exists($ht) ? strlen(file_get_contents($ht)) . ' bytes' : 'MISSING');

    /* Front page and blog index. The theme's front-page.php answers the front page, and
       the journal needs a real posts page because every template links /journal/. */
    $home = get_page_by_path('home');
    if (!$home) { $hid = wp_insert_post(array('post_title' => 'Home', 'post_name' => 'home', 'post_type' => 'page', 'post_status' => 'publish')); }
    else { $hid = $home->ID; }
    $journal = get_page_by_path('journal');
    if (!$journal) { $jid = wp_insert_post(array('post_title' => 'Journal', 'post_name' => 'journal', 'post_type' => 'page', 'post_status' => 'publish')); }
    else { $jid = $journal->ID; }
    update_option('show_on_front', 'page');
    update_option('page_on_front', $hid);
    update_option('page_for_posts', $jid);
    say('front page', 'home #' . $hid . ', journal #' . $jid);

    update_option('blogdescription', '');
    update_option('default_comment_status', 'closed');
    update_option('default_ping_status', 'closed');
    /* Hello Dolly and the sample content are not part of either brand. */
    foreach (array('hello-world', 'sample-page', 'privacy-policy') as $slug) {
        $p = get_page_by_path($slug, OBJECT, array('post', 'page'));
        if ($p) { wp_trash_post($p->ID); say('trashed', $slug); }
    }
    say('permalinks', get_option('permalink_structure'));
    exit;
}

if ($step === 'theme') {
    $slug = $_GET['theme'];
    $theme = wp_get_theme($slug);
    if (!$theme->exists()) { say('theme', "$slug NOT FOUND in " . get_theme_root()); exit; }
    switch_theme($slug);
    say('theme', wp_get_theme()->get('Name') . ' (' . get_stylesheet() . ')');
    /* WooCommerce overrides theme button styles unless the theme claims them. */
    say('supports woocommerce', current_theme_supports('woocommerce') ? 'yes' : 'no');
    exit;
}

if ($step === 'products') {
    $csv = "$CONV/$BRAND-products.csv";
    if (!file_exists($csv)) { say('csv', "missing $csv"); exit; }
    say('csv', filesize($csv) . ' bytes');
    $GLOBALS['args'] = array($csv);
    $args = $GLOBALS['args'];
    include $CONV . '/import-products.php';
    exit;
}

if ($step === 'storecfg') {
    $json = "$CONV/store-config.json";
    if (!file_exists($json)) { say('json', "missing $json"); exit; }
    $GLOBALS['args'] = array($json, $BRAND);
    $args = $GLOBALS['args'];
    include $CONV . '/apply-store-config.php';
    exit;
}

if ($step === 'pages') {
    $file = "$CONV/$BRAND-content.wxr";
    if (!file_exists($file)) { say('wxr', "missing $file"); exit; }
    $xml = simplexml_load_file($file);
    if (!$xml) { say('wxr', 'could not parse'); exit; }
    $ns = $xml->getNamespaces(true);
    $made = 0; $skipped = 0;
    foreach ($xml->channel->item as $item) {
        $wp = $item->children($ns['wp']);
        $content = $item->children($ns['content']);
        $slug = (string)$wp->post_name;
        $type = (string)$wp->post_type;
        $existing = get_page_by_path($slug, OBJECT, array($type));
        if ($existing) { say('exists', "$type $slug #" . $existing->ID); $skipped++; continue; }
        $id = wp_insert_post(array(
            'post_title'   => (string)$item->title,
            'post_name'    => $slug,
            'post_type'    => $type,
            'post_status'  => (string)$wp->status ?: 'publish',
            'post_date'    => (string)$wp->post_date ?: current_time('mysql'),
            'post_content' => (string)$content->encoded,
            'menu_order'   => (int)$wp->menu_order,
            'comment_status' => 'closed',
        ), true);
        if (is_wp_error($id)) { say('FAIL', "$slug " . $id->get_error_message()); }
        else { say('created', "$type $slug #$id"); $made++; }
    }
    say('summary', "created $made, already there $skipped");
    exit;
}

if ($step === 'classic') {
    /* WooCommerce 11 fills the cart and checkout pages with BLOCKS, which render an empty
       shell server side and hydrate over the Store API in the browser. On a ported static
       theme that means the cart page says "your cart is currently empty" while the header
       correctly shows Bag (1), and none of the brand CSS applies. The classic shortcodes
       render server side and inherit the theme, which is what these two sites need. */
    foreach (array('cart' => '[woocommerce_cart]', 'checkout' => '[woocommerce_checkout]',
                   'myaccount' => '[woocommerce_my_account]') as $key => $shortcode) {
        $id = wc_get_page_id($key);
        if ($id <= 0) { say("page $key", 'MISSING'); continue; }
        $before = get_post_field('post_content', $id);
        if (strpos($before, $shortcode) !== false) { say("page $key", 'already classic'); continue; }
        wp_update_post(array('ID' => $id, 'post_content' => $shortcode));
        say("page $key", 'set to ' . $shortcode);
    }
    exit;
}

if ($step === 'verify') {
    say('site', get_option('siteurl'));
    say('theme', wp_get_theme()->get('Name'));
    say('woocommerce', is_plugin_active('woocommerce/woocommerce.php') ? WC()->version : 'INACTIVE');
    say('coming soon', get_option('woocommerce_coming_soon'));
    say('currency', get_option('woocommerce_currency'));
    say('hide rates when free', get_option('woocommerce_shipping_hide_rates_when_free'));
    say('permalinks', get_option('permalink_structure'));
    $counts = array();
    foreach (array('product', 'page', 'post') as $t) { $counts[] = $t . '=' . wp_count_posts($t)->publish; }
    say('published', implode(' ', $counts));
    $vars = get_posts(array('post_type' => 'product_variation', 'numberposts' => -1, 'fields' => 'ids', 'post_status' => 'any'));
    say('variations', count($vars));
    $cats = get_terms(array('taxonomy' => 'product_cat', 'hide_empty' => false));
    $cn = array();
    foreach ($cats as $c) { if ($c->slug === 'uncategorized' && $c->count == 0) continue; $cn[] = $c->name . '(' . $c->count . ')'; }
    say('categories', implode(', ', $cn));
    $noimg = 0;
    foreach (get_posts(array('post_type' => 'product', 'numberposts' => -1, 'fields' => 'ids')) as $pid) {
        if (!get_post_thumbnail_id($pid)) { $noimg++; }
    }
    say('products missing image', $noimg);
    say('attachments', wp_count_posts('attachment')->inherit);
    foreach (array('shop', 'cart', 'checkout') as $p) {
        $id = wc_get_page_id($p);
        say("wc page $p", $id > 0 ? get_permalink($id) : 'MISSING');
    }
    exit;
}

if ($step === 'cleanup') {
    $files = glob("$CONV/*");
    foreach ((array)$files as $f) { @unlink($f); }
    @rmdir($CONV);
    say('conv dir', is_dir($CONV) ? 'STILL THERE' : 'removed');
    /* The uploaded theme zip sits in wp-content/themes, which is publicly fetchable. */
    foreach (glob("$ROOT/wp-content/themes/*-theme.zip") as $z) { @unlink($z); say('theme zip', basename($z) . (file_exists($z) ? ' STILL THERE' : ' removed')); }
    @unlink("$ROOT/_boot.php");
    say('_boot.php', file_exists("$ROOT/_boot.php") ? 'STILL THERE' : 'removed');
    say('self', 'deleting');
    @unlink(__FILE__);
    exit;
}

say('step', "unknown: $step");
