<?php get_header(); ?>
<main>
<main>
  <section class="hero wrap">
    <div class="hero__grid">
      <div>
        <h1 class="hero__h">Silly little things,<br><em>seriously made.</em></h1>
        <p class="hero__p">Glass fruit, enamel flowers and freshwater pearls, strung by hand in San Diego. Kitsch that survives being worn every day rather than photographed once.</p>
        <div class="hero__actions">
          <a class="btn btn--ember" href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">Shop the pieces</a>
          <a class="btn btn--ghost" href="<?php echo esc_url( home_url( "/product-category/charms-extras/" ) ); ?>">Charms from $12</a>
        </div>
      </div>
      <div class="hero__art"><img src="images/l-hero-fruitsalad.jpg" alt="Model wearing the Fruit Salad necklace in forest light"></div>
    </div>
  </section>

  <div class="ticker" aria-hidden="true">
    <div class="ticker__row">
      <span>Fruit Stand</span><span>Flower Bed</span><span>Pearl</span><span>Candy Counter</span><span>Everyday</span>
      <span>Fruit Stand</span><span>Flower Bed</span><span>Pearl</span><span>Candy Counter</span><span>Everyday</span>
    </div>
  </div>

  <section class="sec wrap">
    <div class="sec__head">
      <h2 class="sec__h">Start <em>somewhere</em></h2>
      <a class="sec__link" href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">All 20 pieces</a>
    </div>
    <div class="types">
      <a class="type" href="<?php echo esc_url( home_url( "/product-category/necklaces/" ) ); ?>"><span class="type__n">Necklaces</span><span class="type__c">5 pieces</span></a>
      <a class="type" href="shop.html#earrings"><span class="type__n">Earrings</span><span class="type__c">4 pieces</span></a>
      <a class="type" href="shop.html#bracelets"><span class="type__n">Bracelets</span><span class="type__c">3 pieces</span></a>
      <a class="type" href="shop.html#rings"><span class="type__n">Rings</span><span class="type__c">2 pieces</span></a>
      <a class="type" href="<?php echo esc_url( home_url( "/product-category/charms-extras/" ) ); ?>"><span class="type__n">Charms</span><span class="type__c">From $12</span></a>
      <a class="type" href="<?php echo esc_url( home_url( "/product-category/sets/" ) ); ?>"><span class="type__n">Sets</span><span class="type__c">4 edits</span></a>
    </div>
  </section>

  <section class="sec wrap">
    <div class="sec__head">
      <h2 class="sec__h">The <em>pieces</em></h2>
      <a class="sec__link" href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">See all</a>
    </div>
    <div class="grid">
<?php $skus = array('FM-FRUIT-SALAD', 'FM-SUNDAY-BEST', 'FM-OVERGROWN', 'FM-WET-PEARL', 'FM-TWO-CHERRIES', 'FM-BIG-SWIM', 'FM-CHARM-SCHOOL', 'FM-BIG-FEELINGS');
  $ids = array_values( array_filter( array_map( "wc_get_product_id_by_sku", $skus ) ) );
  if ( $ids ) {
    $q = new WP_Query( array( "post_type" => "product", "post__in" => $ids,
        "orderby" => "post__in", "posts_per_page" => count( $ids ) ) );
    while ( $q->have_posts() ) { $q->the_post(); global $product;
      $product = wc_get_product( get_the_ID() );
      get_template_part( "template-parts/card" ); }
    wp_reset_postdata();
  } ?>
</div></section>

  <section class="sec band">
    <div class="wrap band__grid">
      <div>
        <h2 class="sec__h">Made by hand,<br>badly behaved <em>on purpose</em></h2>
        <p class="band__p">Five women, one studio in San Diego, and a great deal of arguing about colour. Every piece is strung, knotted or set by hand, which is why no two are identical and why we are fine with that.</p>
        <a class="btn btn--ember" href="<?php echo esc_url( home_url( "/about/" ) ); ?>">Meet the studio</a>
      </div>
      <div class="band__art"><img src="images/l-workbench.jpg" alt="Hands stringing glass beads at the workbench"></div>
    </div>
  </section>

  <section class="sec wrap">
    <div class="sec__head">
      <h2 class="sec__h">Buy the whole <em>idea</em></h2>
      <a class="sec__link" href="<?php echo esc_url( home_url( "/product-category/sets/" ) ); ?>">All sets</a>
    </div>
    <div class="grid">
<?php $skus = array('FM-SET-STARTER', 'FM-SET-FRUIT-STAND', 'FM-SET-FULL-ARM', 'FM-SET-WHOLE-GARDEN');
  $ids = array_values( array_filter( array_map( "wc_get_product_id_by_sku", $skus ) ) );
  if ( $ids ) {
    $q = new WP_Query( array( "post_type" => "product", "post__in" => $ids,
        "orderby" => "post__in", "posts_per_page" => count( $ids ) ) );
    while ( $q->have_posts() ) { $q->the_post(); global $product;
      $product = wc_get_product( get_the_ID() );
      get_template_part( "template-parts/card" ); }
    wp_reset_postdata();
  } ?>
</div></section>

  <section class="sec wrap">
    <div class="charm">
      <div>
        <h2 class="charm__h">Charms that clip onto things you already own</h2>
        <p class="charm__p">A bee, a bow, a tiny mushroom, half a lemon. Attach them to a bracelet, a bag, a belt loop or a zip. They do not have to mean anything.</p>
      </div>
      <div>
        <p class="charm__from">Starting at</p>
        <p class="charm__price">$12</p>
        <a class="btn btn--ghost charm__btn" href="<?php echo esc_url( home_url( "/product-category/charms-extras/" ) ); ?>">Pick your charms</a>
      </div>
    </div>
  </section>
</main>
</main>
<?php get_footer(); ?>
