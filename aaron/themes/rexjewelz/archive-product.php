<?php get_header();
$is_shop = is_shop();
$total   = wp_count_posts( 'product' )->publish;
// Ordered by the term order applied from the catalogue, not alphabetically.
$cats    = get_terms( array(
    'taxonomy'   => 'product_cat',
    'hide_empty' => true,
    'meta_key'   => 'order',
    'orderby'    => 'meta_value_num',
    'order'      => 'ASC',
) );
?>
<main class="sec wrap">
  <div class="sec__head">
    <?php if ( $is_shop ) : ?>
      <h1 class="sec__h">All <em><?php echo (int) $total; ?> pieces</em></h1>
    <?php else : ?>
      <h1 class="sec__h"><?php echo esc_html( html_entity_decode( single_term_title( '', false ) ) ); ?></h1>
    <?php endif; ?>
    <span class="sec__note">Prices in <?php echo esc_html( get_woocommerce_currency() ); ?></span>
  </div>

  <?php /* The original filtered client side. These are real links instead, so they
           work without JS and each category is its own crawlable URL. */ ?>
  <div class="filters" role="group" aria-label="Filter by type">
    <a class="pill<?php echo $is_shop ? ' is-on' : ''; ?>"
       href="<?php echo esc_url( get_permalink( wc_get_page_id( 'shop' ) ) ); ?>">Everything</a>
    <?php foreach ( $cats as $c ) :
        if ( 'uncategorized' === $c->slug ) { continue; }
        $on = is_tax( 'product_cat', $c->term_id ); ?>
      <a class="pill<?php echo $on ? ' is-on' : ''; ?>"
         href="<?php echo esc_url( get_term_link( $c ) ); ?>"><?php
         echo esc_html( html_entity_decode( $c->name ) ); ?></a>
    <?php endforeach; ?>
  </div>

  <?php /* term_description() arrives wpautop'd, so this is a div. Wrapping it in a
           <p> would nest paragraphs and produce invalid markup. */
        $d = term_description();
        if ( $d ) { echo '<div class="cat__lead">' . wp_kses_post( $d ) . '</div>'; } ?>

  <?php if ( $is_shop ) :
    /* Shop groups by category with a subheading, exactly like the original. */
    foreach ( $cats as $c ) :
      if ( 'uncategorized' === $c->slug ) { continue; }
      $q = new WP_Query( array(
          'post_type'      => 'product',
          'posts_per_page' => -1,
          'orderby'        => 'menu_order',
          'order'          => 'ASC',
          'tax_query'      => array( array(
              'taxonomy' => 'product_cat', 'field' => 'term_id', 'terms' => $c->term_id ) ),
      ) );
      if ( ! $q->have_posts() ) { continue; } ?>
      <section class="shopgroup" id="<?php echo esc_attr( $c->slug ); ?>">
        <h2 class="zone__h"><?php echo esc_html( html_entity_decode( $c->name ) ); ?></h2>
        <?php /* The original prints a short tagline beside each group heading. */
              if ( $c->description ) {
                  echo '<p class="zone__lead">' . esc_html( wp_strip_all_tags( $c->description ) ) . '</p>';
              } ?>
        <div class="grid">
          <?php while ( $q->have_posts() ) : $q->the_post(); global $product;
                $product = wc_get_product( get_the_ID() );
                get_template_part( 'template-parts/card' );
                endwhile; wp_reset_postdata(); ?>
        </div>
      </section>
    <?php endforeach;
  elseif ( have_posts() ) : ?>
    <div class="grid">
      <?php while ( have_posts() ) : the_post(); global $product;
            $product = wc_get_product( get_the_ID() );
            get_template_part( 'template-parts/card' );
            endwhile; ?>
    </div>
    <?php the_posts_pagination();
  else : ?>
    <p>Nothing here yet.</p>
  <?php endif; ?>
</main>
<?php get_footer(); ?>
