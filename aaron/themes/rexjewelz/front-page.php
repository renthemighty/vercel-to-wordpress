<?php get_header(); ?>
<main>
<div class="subnav">
  <div class="subnav__in">
    <a href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">Shop</a>
    <a href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">Body chains</a>
    <a href="<?php echo esc_url( home_url( "/product-category/sets/" ) ); ?>">Sets</a>
    <a href="<?php echo esc_url( home_url( "/fit/" ) ); ?>">Fit</a>
    <a href="<?php echo esc_url( home_url( "/about/" ) ); ?>">About</a>
  </div>
</div>
<main>
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

  <div class="ticker" aria-hidden="true">
    <div class="ticker__row">
      <span>Sal</span><span>Fuego</span><span>Medianoche</span><span>Brasa</span><span>Veneno</span><span>La Reina</span><span>Diabla</span><span>Cintura</span>
      <span>Sal</span><span>Fuego</span><span>Medianoche</span><span>Brasa</span><span>Veneno</span><span>La Reina</span><span>Diabla</span><span>Cintura</span>
    </div>
  </div>

  <section class="sec wrap">
    <div class="sec__head">
      <h2 class="sec__h metal">Start where it <em>sits</em></h2>
      <a class="sec__link" href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">All 20 pieces</a>
    </div>
    <div class="zones">
      <a class="zonecard" href="shop.html#neck-hand"><span class="zonecard__n">Neck &amp; Hand</span><span class="zonecard__c">4 pieces</span></a>
      <a class="zonecard" href="shop.html#chest-bra"><span class="zonecard__n">Chest &amp; Bra</span><span class="zonecard__c">3 pieces</span></a>
      <a class="zonecard" href="shop.html#harness-back"><span class="zonecard__n">Harness &amp; Back</span><span class="zonecard__c">3 pieces</span></a>
      <a class="zonecard" href="shop.html#waist-belly"><span class="zonecard__n">Waist &amp; Belly</span><span class="zonecard__c">4 pieces</span></a>
      <a class="zonecard" href="shop.html#anklets-thigh"><span class="zonecard__n">Anklets &amp; Thigh</span><span class="zonecard__c">2 pieces</span></a>
      <a class="zonecard" href="shop.html#sets"><span class="zonecard__n">Sets</span><span class="zonecard__c">4 pieces</span></a>
    </div>
  </section>

  <section class="sec wrap">
    <div class="sec__head">
      <h2 class="sec__h metal">The <em>loud ones</em></h2>
      <a class="sec__link" href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">See all</a>
    </div>
      <div class="grid">
<?php $skus = array('REX-LA-REINA', 'REX-BRASA', 'REX-JAULA', 'REX-CINTURA', 'REX-DIABLA', 'REX-ESPALDA', 'REX-HUMO', 'REX-MONEDAS');
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
        <h2 class="sec__h metal">If it cannot survive<br>a full night, <em>we do not sell it</em></h2>
        <p class="band__p">Two sisters, one studio off Calle Ocho, and a rule that started as a joke and turned into the whole business. Every piece gets worn out dancing before it gets a price. Whatever slid, snapped, tangled or went green got sent back to the bench.</p>
        <a class="btn btn--ember" href="<?php echo esc_url( home_url( "/about/" ) ); ?>">Read the rule</a>
      </div>
      <div class="band__art"><img src="images/a-studio.jpg" alt="The Rex Jewelz bench in Miami" loading="lazy"></div>
    </div>
  </section>

  <section class="sec wrap">
    <div class="sec__head">
      <h2 class="sec__h metal">Buy the whole <em>look</em></h2>
      <a class="sec__link" href="<?php echo esc_url( home_url( "/product-category/sets/" ) ); ?>">All sets</a>
    </div>
      <div class="grid">
<?php $skus = array('REX-SET-PRIMERA', 'REX-SET-NOCHE', 'REX-SET-CALIENTE', 'REX-SET-TODO');
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
    <div class="pitch">
      <div>
        <h2 class="pitch__h metal">Body chain is a fit problem<br>before it is a taste problem</h2>
        <p class="pitch__p">A waist chain that rides up all night is a waist chain you stop wearing. Every piece here comes in real sizes with real adjustment, and the big ones can be built to your measurements. Take two minutes with a tape measure and get it right the first time.</p>
      </div>
      <div>
        <p class="pitch__from">Entry piece</p>
        <p class="pitch__price metal">$12</p>
        <a class="btn btn--ghost pitch__btn" href="<?php echo esc_url( home_url( "/fit/" ) ); ?>">Measure up</a>
      </div>
    </div>
  </section>
</main>
</main>
<?php get_footer(); ?>
