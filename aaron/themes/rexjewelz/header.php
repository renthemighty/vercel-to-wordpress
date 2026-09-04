<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,500;1,600;1,700&family=Jost:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<header class="nav">
  <div class="wrap nav__in">
    <a href="<?php echo esc_url( home_url( "/" ) ); ?>" class="nav__mark metal">Rex <em>Jewelz</em></a>
    <nav class="nav__links" aria-label="Main">
      <a href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">Shop</a>
      <a href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">Body chains</a>
      <a href="<?php echo esc_url( home_url( "/product-category/sets/" ) ); ?>">Sets</a>
      <a href="<?php echo esc_url( home_url( "/fit/" ) ); ?>">Fit</a>
      <a href="<?php echo esc_url( home_url( "/about/" ) ); ?>">About</a>
    </nav>
    <details class="navmob"><summary class="navmob__btn">Menu</summary><div class="navmob__panel"><a href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">Shop</a>
      <a href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">Body chains</a>
      <a href="<?php echo esc_url( home_url( "/product-category/sets/" ) ); ?>">Sets</a>
      <a href="<?php echo esc_url( home_url( "/fit/" ) ); ?>">Fit</a>
      <a href="<?php echo esc_url( home_url( "/about/" ) ); ?>">About</a></div></details>
    <a class="nav__bag" href="<?php echo esc_url( wc_get_cart_url() ); ?>">Bag (<?php echo (int) rexjewelz_bag_count(); ?>)</a>
  </div>
</header>
