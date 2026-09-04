<?php
/** One product card. Mirrors the original Rex .card block, gloss and footer included. */
global $product;
if ( ! $product ) { return; }
$cats = wp_get_post_terms( $product->get_id(), 'product_cat', array( 'fields' => 'names' ) );
$es   = get_post_meta( $product->get_id(), '_es', true );
?>
<a class="card" href="<?php the_permalink(); ?>">
  <div class="card__art"><?php echo $product->get_image( 'woocommerce_thumbnail' ); ?></div>
  <h3 class="card__name"><?php echo esc_html( $product->get_name() ); ?></h3>
  <?php if ( $es ) : ?><p class="card__es"><?php echo esc_html( $es ); ?></p><?php endif; ?>
  <div class="card__foot">
    <span class="card__meta"><?php
      echo $cats ? esc_html( html_entity_decode( $cats[0] ) ) : ''; ?></span>
    <span class="card__price"><?php
      echo $product->is_type( 'variable' )
          ? 'From ' . wc_price( $product->get_variation_price( 'min' ) )
          : wc_price( $product->get_price() );
    ?></span>
  </div>
</a>
