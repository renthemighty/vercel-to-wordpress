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
      <?php $es = get_post_meta( $product->get_id(), '_es', true );
            if ( $es ) { echo '<p class="pdp__es">' . esc_html( $es ) . '</p>'; } ?>
      <?php if ( $product->get_short_description() ) : ?>
        <p class="pdp__blurb"><?php echo wp_kses_post( $product->get_short_description() ); ?></p>
      <?php endif; ?>
      <p class="pdp__price"><?php echo $product->get_price_html(); ?></p>
      <?php
        /* WooCommerce owns the add to cart form, including variation switching and
           stock. The old pill buttons and localStorage add are gone on purpose. */
        woocommerce_template_single_add_to_cart();
      ?>
      <?php $note = get_option( 'conv_pdp_note' );
            if ( $note ) { echo '<p class="pdp__note">' . esc_html( $note ) . '</p>'; } ?>
      <?php if ( $product->get_description() ) : ?>
        <div class="spec"><?php echo wp_kses_post( wpautop( $product->get_description() ) ); ?></div>
      <?php endif; ?>
      <?php /* Materials get their own spec block, as on the original. */
        $mats = get_post_meta( $product->get_id(), '_materials', true );
        $mats = $mats ? array_filter( explode( '|', $mats ) ) : array();
        if ( $mats ) : ?>
        <div class="spec">
          <p class="spec__h">What it is made of</p>
          <ul><?php foreach ( $mats as $m ) {
                echo '<li><strong>' . esc_html( $m ) . '</strong></li>'; } ?></ul>
        </div>
      <?php endif; ?>
      <?php /* Shown only where the product takes a size, which is the original's own
               condition, not on every product. */
        $sn = get_option( 'conv_size_note' );
        $has_size = false;
        foreach ( $product->get_attributes() as $a ) {
            $n = is_object( $a ) ? $a->get_name() : '';
            if ( $n && stripos( $n, 'size' ) !== false ) { $has_size = true; }
        }
        if ( $has_size && is_array( $sn ) && ! empty( $sn['heading'] ) ) : ?>
        <div class="fit">
          <p class="fit__h"><?php echo esc_html( $sn['heading'] ); ?></p>
          <p><?php echo esc_html( $sn['body'] ); ?></p>
        </div>
      <?php endif; ?>
      <?php $care = get_option( 'conv_care_bullets' );
            if ( is_array( $care ) && $care ) : ?>
        <div class="spec">
          <p class="spec__h">Looking after it</p>
          <ul><?php foreach ( $care as $c ) { echo '<li>' . esc_html( $c ) . '</li>'; } ?></ul>
        </div>
      <?php endif; ?>
    </div>
  </div>
<?php
/* The original prints a "Goes with" rail of four other pieces on every product page.
   Cross sells where they exist, otherwise the next four in catalogue order, which is
   what the original did. */
/* The original takes the first four catalogue items other than this one, the same on
   every page including sets. Cross sells are deliberately NOT used here: on a set they
   are its own contents, which already appear above under "What is in it". */
$q = new WP_Query( array(
    'post_type'      => 'product',
    'posts_per_page' => 4,
    'post__not_in'   => array( $product->get_id() ),
    'orderby'        => 'menu_order',
    'order'          => 'ASC',
) );
if ( $q->have_posts() ) : ?>
  <section class="sec wrap">
    <div class="sec__head">
      <h2 class="sec__h">Goes <em>with</em></h2>
      <a class="sec__link" href="<?php echo esc_url( home_url( '/shop/' ) ); ?>">All pieces</a>
    </div>
    <div class="grid">
      <?php while ( $q->have_posts() ) : $q->the_post(); global $product;
            $product = wc_get_product( get_the_ID() );
            get_template_part( 'template-parts/card' );
            endwhile; wp_reset_postdata(); ?>
    </div>
  </section>
<?php endif; ?>
</main>
<?php endwhile; ?>
<?php get_footer(); ?>
