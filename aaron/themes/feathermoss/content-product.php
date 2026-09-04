<?php
/** WooCommerce loop item. Delegates to the same card the archives use. */
global $product;
if ( ! $product ) { $product = wc_get_product( get_the_ID() ); }
get_template_part( 'template-parts/card' );
