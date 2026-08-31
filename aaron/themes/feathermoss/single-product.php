<?php get_header(); ?>
<?php while ( have_posts() ) : the_post(); global $product; $product = wc_get_product( get_the_ID() ); ?>
<main class="pdp wrap">
  <p class="crumb">
    <a href="<?php echo esc_url( home_url( '/' ) ); ?>">Home</a> /
    <a href="<?php echo esc_url( home_url( '/shop/' ) ); ?>">Shop</a> /
    <?php echo esc_html( $product->get_name() ); ?>
  </p>
  <div class="pdp__grid">
    <div>
      <div class="gal__main"><?php echo $product->get_image( 'woocommerce_single' ); ?></div>
      <?php foreach ( $product->get_gallery_image_ids() as $gid ) : ?>
        <div class="gal__main"><?php echo wp_get_attachment_image( $gid, 'woocommerce_single' ); ?></div>
      <?php endforeach; ?>
    </div>
    <div>
      <h1 class="pdp__name"><?php echo esc_html( $product->get_name() ); ?></h1>
      <?php if ( $product->get_short_description() ) : ?>
        <p class="pdp__blurb"><?php echo wp_kses_post( $product->get_short_description() ); ?></p>
      <?php endif; ?>
      <p class="pdp__price"><?php echo $product->get_price_html(); ?></p>
      <?php
        /* WooCommerce owns the add to cart form, including variation switching and
           stock. The old pill buttons and localStorage add are gone on purpose. */
        woocommerce_template_single_add_to_cart();
      ?>
      <?php if ( $product->get_description() ) : ?>
        <div class="spec"><?php echo wp_kses_post( wpautop( $product->get_description() ) ); ?></div>
      <?php endif; ?>
    </div>
  </div>
</main>
<?php endwhile; ?>
<?php
$ids = $product->get_cross_sell_ids();
if ( $ids ) :
  $q = new WP_Query( array( 'post_type' => 'product', 'post__in' => $ids, 'posts_per_page' => 4 ) ); ?>
  <section class="sec wrap">
    <div class="sec__head"><h2 class="sec__h">Goes with</h2></div>
    <div class="grid">
      <?php while ( $q->have_posts() ) : $q->the_post(); global $product;
            $product = wc_get_product( get_the_ID() );
            get_template_part( 'template-parts/card' );
            endwhile; wp_reset_postdata(); ?>
    </div>
  </section>
<?php endif; ?>
<?php get_footer(); ?>
