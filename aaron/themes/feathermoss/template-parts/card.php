<?php
/** One product card. Markup mirrors the original .card block so the CSS applies unchanged. */
global $product;
if ( ! $product ) { return; }
$cats = wp_get_post_terms( $product->get_id(), 'product_cat', array( 'fields' => 'names' ) );
$tags = wp_get_post_terms( $product->get_id(), 'product_tag', array( 'fields' => 'names' ) );
$meta = trim( implode( ' / ', array_filter( array(
    $cats ? html_entity_decode( $cats[0] ) : '',
    $tags ? html_entity_decode( $tags[0] ) : '',
) ) ), ' /' );
?>
<a class="card" href="<?php the_permalink(); ?>">
  <div class="card__art"><?php echo $product->get_image( 'woocommerce_thumbnail' ); ?></div>
  <h3 class="card__name"><?php echo esc_html( $product->get_name() ); ?></h3>
  <?php if ( $meta ) : ?><p class="card__meta"><?php echo esc_html( $meta ); ?></p><?php endif; ?>
  <p class="card__price"><?php
      echo $product->is_type( 'variable' )
          ? 'From ' . wc_price( $product->get_variation_price( 'min' ) )
          : wc_price( $product->get_price() );
  ?></p>
</a>
