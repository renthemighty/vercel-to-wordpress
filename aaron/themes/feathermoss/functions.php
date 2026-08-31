<?php
/**
 * FeatherMoss theme setup.
 *
 * The cart is WooCommerce now, not the old localStorage drawer, so the original
 * cart JS is deliberately NOT enqueued. Everything else about the design is the
 * original CSS untouched.
 */
add_action( 'after_setup_theme', function () {
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'woocommerce' );
    add_theme_support( 'wc-product-gallery-zoom' );
    add_theme_support( 'wc-product-gallery-lightbox' );
    add_theme_support( 'wc-product-gallery-slider' );
    add_theme_support( 'html5', array( 'search-form', 'gallery', 'caption', 'style', 'script' ) );
    register_nav_menus( array( 'primary' => 'Primary', 'footer' => 'Footer' ) );
} );

add_action( 'wp_enqueue_scripts', function () {
    wp_enqueue_style( 'feathermoss', get_stylesheet_uri(), array(), '1.0' );
} );

/** Bag count in the header, replacing the old data-bag-count JS hook. */
function feathermoss_bag_count() {
    if ( ! function_exists( 'WC' ) || ! WC()->cart ) { return 0; }
    return WC()->cart->get_cart_contents_count();
}

/**
 * Stand down WooCommerce's own button styling.
 *
 * Woo guards its button rules with :where(body:not(.woocommerce-block-theme-has-button-styles)).
 * Declaring that class is the supported way for a theme to say "I style my own buttons",
 * and it is far cleaner than fighting an eight selector chain with !important.
 */
add_filter( 'body_class', function ( $c ) {
    $c[] = 'woocommerce-block-theme-has-button-styles';
    return $c;
} );

/** The original grid used 4 across, WooCommerce defaults to 3. */
add_filter( 'loop_shop_columns', function () { return 4; } );
add_filter( 'loop_shop_per_page', function () { return 24; } );
