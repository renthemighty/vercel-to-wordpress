<?php get_header(); ?>
<section class="hero wrap">
    <div class="hero__grid">
      <div>
        <p class="hero__eyebrow">Body jewelry, made in Miami</p>
        <h1 class="hero__h metal metal--sweep">Worn under<em>everything.</em></h1>
        <p class="hero__p">Chain that sits on skin and stays where you put it. Built for heat, for sweat, and for a night that runs long. Starts at $12.</p>
        <div class="hero__actions">
          <a class="btn btn--ember" href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">Shop all 20 pieces</a>
          <a class="btn btn--ghost" href="<?php echo esc_url( home_url( "/fit/" ) ); ?>">Find your fit</a>
        </div>
      </div>
      <div class="hero__art"><img src="images/l-hero-cintura.jpg" alt="A fine gold waist chain worn low on the waist under a white tank" fetchpriority="high"></div>
    </div>
  </section>
<?php
/* The original front page hand listed products. These are real queries now, so the
   page follows the catalogue instead of going stale. */
$sections = array(
    array( 'title' => 'Featured', 'args' => array(
        'post_type' => 'product', 'posts_per_page' => 8,
        'meta_key' => '_featured', 'orderby' => 'menu_order', 'order' => 'ASC' ) ),
    array( 'title' => 'Everything', 'args' => array(
        'post_type' => 'product', 'posts_per_page' => 8,
        'orderby' => 'menu_order', 'order' => 'ASC' ) ),
);
foreach ( $sections as $s ) :
    $q = new WP_Query( $s['args'] );
    if ( ! $q->have_posts() ) { continue; } ?>
  <section class="sec wrap">
    <div class="sec__head">
      <h2 class="sec__h"><?php echo esc_html( $s['title'] ); ?></h2>
      <a class="sec__link" href="<?php echo esc_url( home_url( '/shop/' ) ); ?>">All pieces</a>
    </div>
    <div class="grid">
      <?php while ( $q->have_posts() ) : $q->the_post(); global $product;
            $product = wc_get_product( get_the_ID() );
            get_template_part( 'template-parts/card' );
            endwhile; wp_reset_postdata(); ?>
    </div>
  </section>
<?php endforeach; ?>
<?php get_footer(); ?>
