<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Prata&family=Style+Script&family=Hanken+Grotesk:ital,wght@0,300..800;1,300..800&display=swap" rel="stylesheet">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<header class="nav">
  <div class="wrap nav__in">
    <a href="<?php echo esc_url( home_url( "/" ) ); ?>" class="nav__mark">Feather<span>Moss</span></a>
    <nav class="nav__links" aria-label="Main">
      <a href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">Shop</a>
      <a href="<?php echo esc_url( home_url( "/product-category/sets/" ) ); ?>">Sets</a>
      <a href="<?php echo esc_url( home_url( "/product-category/charms-extras/" ) ); ?>">Charms</a>
      <a href="<?php echo esc_url( home_url( "/about/" ) ); ?>">About</a>
      <a href="<?php echo esc_url( home_url( "/journal/" ) ); ?>">Journal</a>
    </nav>
    <details class="navmob"><summary class="navmob__btn">Menu</summary><div class="navmob__panel"><a href="<?php echo esc_url( home_url( "/shop/" ) ); ?>">Shop</a>
      <a href="<?php echo esc_url( home_url( "/product-category/sets/" ) ); ?>">Sets</a>
      <a href="<?php echo esc_url( home_url( "/product-category/charms-extras/" ) ); ?>">Charms</a>
      <a href="<?php echo esc_url( home_url( "/about/" ) ); ?>">About</a>
      <a href="<?php echo esc_url( home_url( "/journal/" ) ); ?>">Journal</a></div></details>
    <a class="nav__bag" href="<?php echo esc_url( wc_get_cart_url() ); ?>">Bag (<?php echo (int) feathermoss_bag_count(); ?>)</a>
  </div>
</header>
