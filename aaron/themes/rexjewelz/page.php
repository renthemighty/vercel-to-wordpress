<?php get_header(); ?>
<main class="sec wrap">
  <?php while ( have_posts() ) : the_post(); ?>
    <div class="sec__head"><h1 class="sec__h"><?php the_title(); ?></h1></div>
    <div class="prose"><?php the_content(); ?></div>
  <?php endwhile; ?>
</main>
<?php get_footer(); ?>
