<?php
/**
 * Plugin Name: Conversion, no edge HTML cache
 * Description: The EasWrk LiteSpeed ADC caches HTML by default. The header prints the bag
 *   count server side, so a cached page hands one visitor another visitor's count and
 *   never updates after an add to cart. Front end HTML therefore has to stay uncached.
 *   Static assets are untouched and still cache at the edge.
 *   Kill switch: set option conv_no_edge_html_cache to 0.
 */
add_action('send_headers', function () {
    if (is_admin() || wp_doing_ajax()) { return; }
    if (get_option('conv_no_edge_html_cache', '1') !== '1') { return; }
    header('Cache-Control: no-cache, no-store, must-revalidate, max-age=0');
    header('Pragma: no-cache');
    header('X-LiteSpeed-Cache-Control: no-cache');
}, 1);
