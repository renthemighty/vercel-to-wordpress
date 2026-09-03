#!/usr/bin/env python3
"""
Build a WordPress theme per brand from the brand's own built site.

The chrome is LIFTED from the original index.html rather than retyped, so the header,
footer and every class name are identical to what the CSS already expects. Only the
links are rewritten to WordPress routes, and the product grids become real loops.

Run:  python3 tools/build_theme.py
"""
import json, os, re, shutil, sys, time

# The EasWrk LiteSpeed edge caches CSS and JS by URL and a purge does NOT clear them,
# so a stylesheet change is invisible until the query string moves. Stamp every build so
# the enqueued URL changes whenever the theme is rebuilt.
BUILD_VERSION = time.strftime('%Y%m%d.%H%M%S')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'out', 'themes')

BRANDS = {
    'feathermoss': {
        'src':   os.path.expanduser('~/ai_life/feathermoss/site'),
        'name':  'FeatherMoss',
        'css':   'fm.css',
        'slug':  'feathermoss',
        'grouph': 'shopgroup__h',
        # original nav file -> WordPress route
        'links': {'index.html': '/', 'shop.html': '/shop/', 'sets.html': '/product-category/sets/',
                  'charms.html': '/product-category/charms-extras/',
                  'necklaces.html': '/product-category/necklaces/',
                  'about.html': '/about/', 'journal.html': '/journal/', 'care.html': '/care/',
                  'contact.html': '/contact/', 'returns.html': '/returns/',
                  'shipping.html': '/shipping/', 'stockists.html': '/stockists/',
                  'cart.html': '/cart/', 'checkout.html': '/checkout/'},
    },
    'rexjewelz': {
        'src':   os.path.expanduser('~/ai_life/rexjewelz/site'),
        'name':  'Rex Jewelz',
        'css':   'rex.css',
        'slug':  'rexjewelz',
        'grouph': 'zone__h',
        'links': {'index.html': '/', 'shop.html': '/shop/', 'sets.html': '/product-category/sets/',
                  'body.html': '/shop/', 'fit.html': '/fit/', 'under-50.html': '/shop/?max_price=50',
                  'about.html': '/about/', 'journal.html': '/journal/', 'care.html': '/care/',
                  'contact.html': '/contact/', 'returns.html': '/returns/',
                  'shipping.html': '/shipping/', 'cart.html': '/cart/', 'checkout.html': '/checkout/'},
    },
}


def rule_body(css, selector):
    """Pull one rule's declarations out of the brand stylesheet.

    Used so the WooCommerce bridge below reuses each brand's real values instead of
    inventing colours that only approximate them.
    """
    m = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', css)
    if not m:
        raise SystemExit(f'could not find rule {selector} to mirror')
    return m.group(1).strip().rstrip(';')

def grab(src, pattern):
    m = re.search(pattern, src, re.S)
    return m.group(0) if m else None

def rewrite_links(html, links):
    """Point original .html hrefs at WordPress routes. Anything unmapped is reported."""
    unmapped = set()
    def sub(m):
        pre, target = m.group(1), m.group(2)
        clean = target.lstrip('./')
        if clean.startswith('product/'):
            slug = clean[len('product/'):-len('.html')]
            return f'{pre}"<?php echo esc_url( home_url( "/product/{slug}/" ) ); ?>"'
        if clean in links:
            return f'{pre}"<?php echo esc_url( home_url( "{links[clean]}" ) ); ?>"'
        if clean.endswith('.html'):
            unmapped.add(clean)
        return m.group(0)
    out = re.sub(r'(href=)"([^"]+\.html)"', sub, html)
    return out, unmapped

def build(brand, cfg):
    src_dir = cfg['src']
    index = open(os.path.join(src_dir, 'index.html'), encoding='utf-8').read()
    theme = os.path.join(OUT, cfg['slug'])
    os.makedirs(theme, exist_ok=True)
    unmapped = set()

    fonts = grab(index, r'<link href="https://fonts\.googleapis\.com[^>]*>') or ''
    header_html = grab(index, r'<header class="nav">.*?</header>')
    footer_html = grab(index, r'<footer class="foot">.*?</footer>')
    if not header_html or not footer_html:
        raise SystemExit(f'{brand}: could not lift header/footer from index.html')

    header_html, u = rewrite_links(header_html, cfg['links']); unmapped |= u
    # The lifted bag button drove the old localStorage drawer and rendered a static
    # "Bag (0)". Point it at the WooCommerce cart with a live count instead.
    slug = cfg['slug']
    bag = ('<a class="nav__bag" href="<?php echo esc_url( wc_get_cart_url() ); ?>">'
           f'Bag (<?php echo (int) {slug}_bag_count(); ?>)</a>')
    header_html, n = re.subn(r'<button class="nav__bag".*?</button>', bag, header_html, flags=re.S)
    if n != 1:
        raise SystemExit(f'{brand}: expected exactly one nav__bag button, found {n}')

    # ---- mobile navigation.
    # BOTH originals hide .nav__links below 860px and put nothing in its place, so a phone
    # visitor can only navigate from the footer. That is a real defect on the surface that
    # matters most, so the converted themes add a disclosure menu reusing the same links.
    # Deliberate divergence: a visual gate will flag the header on narrow widths. Remove
    # this block and the .navmob CSS to go back to exact parity.
    links_m = re.search(r'<nav class="nav__links"[^>]*>(.*?)</nav>', header_html, re.S)
    if not links_m:
        raise SystemExit(f'{brand}: could not find nav__links to build a mobile menu from')
    header_html = header_html.replace(
        links_m.group(0),
        links_m.group(0) +
        '\n    <details class="navmob">'
        '<summary class="navmob__btn">Menu</summary>'
        f'<div class="navmob__panel">{links_m.group(1).strip()}</div>'
        '</details>')
    footer_html, u = rewrite_links(footer_html, cfg['links']); unmapped |= u

    # ---- style.css, theme header then the brand's own stylesheet verbatim
    css = open(os.path.join(src_dir, cfg['css']), encoding='utf-8').read()
    # The original toggled the filter pills with aria-pressed via JS. The converted
    # archive uses real links, so the active state needs a class. Mirror the brand's
    # OWN aria-pressed rule rather than inventing colours for it.
    m = re.search(r'\.pill\[aria-pressed="true"\]\{([^}]*)\}', css)
    if not m:
        raise SystemExit(f'{brand}: could not find the active pill rule to mirror')
    css += ('\n\n/* Converted archive: active filter pill, mirroring the rule above\n'
            '   because the pills are links now rather than JS toggled buttons. */\n'
            f'.pill.is-on{{{m.group(1)}}}\n')

    # Rex Jewelz never had a pill row on its shop page, it used the sticky body rail, so
    # its stylesheet carries no .filters rule at all. The converted archive's pills then
    # lay out inline and a long label wraps INSIDE its own border, which is what "Chest &
    # Bra" did at 390. Add the row only when the brand does not already style it, so
    # FeatherMoss keeps its own spacing untouched.
    if not re.search(r'\.filters\s*\{', css):
        css += ('\n\n/* Converted archive: the filter row. This brand had no pill row of its\n'
                '   own, so without this the pills lay out inline and long labels wrap\n'
                '   inside their border. The pill itself is the brand\'s existing rule. */\n'
                '.filters{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:clamp(2rem,4vw,3rem)}\n'
                '.filters .pill{white-space:nowrap}\n')

    # ---- WooCommerce bridge.
    # WooCommerce renders its own add to cart form, quantity box and notices, none of
    # which know about the brand. Rather than approximate the look, lift the brand's
    # own .btn and .btn--ember declarations and re-point them at the Woo selectors.
    nav_rule = rule_body(css, '.nav')
    _bg   = re.search(r'background:\s*([^;]+)', nav_rule)
    _line = re.search(r'border-bottom:\s*([^;]+)', nav_rule)
    shell = _bg.group(1).strip() if _bg else 'inherit'
    hair  = _line.group(1).strip().split()[-1] if _line else 'currentColor'
    btn  = rule_body(css, '.btn')
    ember = rule_body(css, '.btn--ember')
    css += f"""

/* ---------------------------------------------------------------- WooCommerce bridge
   The add to cart form is WooCommerce's markup, so these rules re-use the brand's own
   button declarations rather than restating them in different values. */
form.cart .button,
.woocommerce a.button, .woocommerce button.button, .woocommerce input.button,
.woocommerce button.button.alt, .woocommerce a.button.alt,
.woocommerce button.single_add_to_cart_button {{
  {btn};
  {ember};
}}
form.cart .button,
.woocommerce button.single_add_to_cart_button {{ width:100%; text-align:center; }}
form.cart .variations {{ width:100%; margin:0 0 1.2rem; }}
form.cart .variations th,
form.cart .variations td {{
  display:block; width:100%; text-align:left; padding:0 0 .5rem;
}}
form.cart .variations label {{
  font-size:.68rem; letter-spacing:.15em; text-transform:uppercase; font-weight:400;
}}
form.cart .variations select {{
  width:100%; padding:.8rem .9rem; border-radius:999px; font:inherit;
  background:transparent; color:inherit; border:1px solid currentColor;
}}
form.cart .quantity {{ margin:0 0 .8rem; }}
form.cart .quantity input {{
  width:100%; padding:.8rem .9rem; border-radius:999px; font:inherit;
  background:transparent; color:inherit; border:1px solid currentColor; text-align:center;
}}
form.cart .woocommerce-variation-price {{ margin:0 0 1rem; }}
.woocommerce .quantity, form.cart div.quantity {{ float:none; }}

/* ---------------------------------------------------------------- mobile navigation
   Added by the conversion. The originals hid the nav below 860px with no replacement. */
.navmob {{ display:none; }}
.navmob__btn {{
  list-style:none; cursor:pointer; user-select:none;
  font-size:.68rem; letter-spacing:.16em; text-transform:uppercase;
  padding:.55rem 1.1rem; border-radius:999px; border:1px solid currentColor;
}}
.navmob__btn::-webkit-details-marker {{ display:none; }}
.navmob__panel {{
  position:absolute; left:0; right:0; top:100%; z-index:60;
  display:flex; flex-direction:column;
  padding:.8rem var(--gut, 1.2rem) 1.3rem;
  background:{shell};
  border-bottom:1px solid {hair};
}}
.navmob__panel a {{ padding:.8rem 0; display:block; }}
@media(max-width:860px) {{
  .navmob {{ display:block; }}
  .nav__in {{ position:relative; }}
}}
"""
    open(os.path.join(theme, 'style.css'), 'w').write(
        f"""/*
Theme Name: {cfg['name']}
Description: Converted from the static {cfg['name']} build. Class names and CSS are the
  originals, so the design is a port rather than a reinterpretation.
Version: {BUILD_VERSION}
Requires PHP: 7.4
*/

{css}
""")

    # ---- functions.php
    open(os.path.join(theme, 'functions.php'), 'w').write(f"""<?php
/**
 * {cfg['name']} theme setup.
 *
 * The cart is WooCommerce now, not the old localStorage drawer, so the original
 * cart JS is deliberately NOT enqueued. Everything else about the design is the
 * original CSS untouched.
 */
add_action( 'after_setup_theme', function () {{
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'woocommerce' );
    add_theme_support( 'wc-product-gallery-zoom' );
    add_theme_support( 'wc-product-gallery-lightbox' );
    add_theme_support( 'wc-product-gallery-slider' );
    add_theme_support( 'html5', array( 'search-form', 'gallery', 'caption', 'style', 'script' ) );
    register_nav_menus( array( 'primary' => 'Primary', 'footer' => 'Footer' ) );
}} );

add_action( 'wp_enqueue_scripts', function () {{
    wp_enqueue_style( '{cfg['slug']}', get_stylesheet_uri(), array(), '{BUILD_VERSION}' );
}} );

/** Bag count in the header, replacing the old data-bag-count JS hook. */
function {cfg['slug']}_bag_count() {{
    if ( ! function_exists( 'WC' ) || ! WC()->cart ) {{ return 0; }}
    return WC()->cart->get_cart_contents_count();
}}

/**
 * Stand down WooCommerce's own button styling.
 *
 * Woo guards its button rules with :where(body:not(.woocommerce-block-theme-has-button-styles)).
 * Declaring that class is the supported way for a theme to say "I style my own buttons",
 * and it is far cleaner than fighting an eight selector chain with !important.
 */
add_filter( 'body_class', function ( $c ) {{
    $c[] = 'woocommerce-block-theme-has-button-styles';
    return $c;
}} );

/** The original grid used 4 across, WooCommerce defaults to 3. */
add_filter( 'loop_shop_columns', function () {{ return 4; }} );
add_filter( 'loop_shop_per_page', function () {{ return 24; }} );
""")

    # ---- header.php
    open(os.path.join(theme, 'header.php'), 'w').write(f"""<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{fonts}
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
{header_html}
""")

    # ---- footer.php
    open(os.path.join(theme, 'footer.php'), 'w').write(
        footer_html + "\n<?php wp_footer(); ?>\n</body>\n</html>\n")

    # ---- the product card, matching the original .card markup exactly
    card_fm = """<?php
/** One product card. Markup mirrors the original .card block so the CSS applies unchanged. */
global $product;
if ( ! $product ) { return; }
$cats = wp_get_post_terms( $product->get_id(), 'product_cat', array( 'fields' => 'names' ) );
$tags = wp_get_post_terms( $product->get_id(), 'product_tag', array( 'fields' => 'names' ) );
$meta = trim( implode( ' / ', array_filter( array(
    $cats ? html_entity_decode( $cats[0] ) : '',
    $tags ? html_entity_decode( $tags[0] ) : '',
) ) ), ' /' );
?>
<a class="card" href="<?php the_permalink(); ?>">
  <div class="card__art"><?php echo $product->get_image( 'woocommerce_thumbnail' ); ?></div>
  <h3 class="card__name"><?php echo esc_html( $product->get_name() ); ?></h3>
  <?php if ( $meta ) : ?><p class="card__meta"><?php echo esc_html( $meta ); ?></p><?php endif; ?>
  <p class="card__price"><?php
      echo $product->is_type( 'variable' )
          ? 'From ' . wc_price( $product->get_variation_price( 'min' ) )
          : wc_price( $product->get_price() );
  ?></p>
</a>
"""
    # Rex cards carry a Spanish gloss and wrap meta and price in a .card__foot. FeatherMoss
    # does neither. Same data, different markup, so each brand gets its own card.
    card_rex = """<?php
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
"""
    os.makedirs(os.path.join(theme, 'template-parts'), exist_ok=True)
    chosen = card_rex if cfg['slug'] == 'rexjewelz' else card_fm
    open(os.path.join(theme, 'template-parts', 'card.php'), 'w').write(chosen)
    # WooCommerce loops, including the [products] shortcode used on the converted listing
    # pages, call wc_get_template_part('content','product'). Without this override they
    # render WooCommerce's default card and the page stops matching the rest of the site.
    open(os.path.join(theme, 'content-product.php'), 'w').write(
        "<?php\n/** WooCommerce loop item. Delegates to the same card the archives use. */\n"
        "global $product;\n"
        "if ( ! $product ) { $product = wc_get_product( get_the_ID() ); }\n"
        "get_template_part( 'template-parts/card' );\n")

    # ---- front-page.php.
    # The whole body between header and footer is lifted, so the ticker, the type row,
    # the editorial band and the closing block all survive. Only the product grids are
    # swapped for live queries, carrying the exact SKUs the original listed so the page
    # keeps its curation instead of becoming a generic "latest products" rail.
    body_m = re.search(r'</header>(.*?)<footer', index, re.S)
    if not body_m:
        raise SystemExit(f'{brand}: could not lift the front page body')
    fp = body_m.group(1)

    cat = json.load(open(os.path.join(os.path.dirname(src_dir), 'catalog', 'catalog.json')))
    slug_to_sku = {}
    for it in cat['products'] + cat['sets']:
        slug_to_sku[re.sub(r'[^a-z0-9]+', '-', it['name'].lower()).strip('-')] = it['sku']

    def grid_to_loop(m):
        block = m.group(0)
        skus = []
        for slug in re.findall(r'href="(?:\.\./)?product/([^"]+)\.html"', block):
            sku = slug_to_sku.get(slug)
            if sku and sku not in skus:
                skus.append(sku)
        if not skus:
            return block
        php_list = ", ".join(f"'{k}'" for k in skus)
        return (
            '<div class="grid">\n'
            '<?php $skus = array(' + php_list + ');\n'
            '  $ids = array_values( array_filter( array_map( "wc_get_product_id_by_sku", $skus ) ) );\n'
            '  if ( $ids ) {\n'
            '    $q = new WP_Query( array( "post_type" => "product", "post__in" => $ids,\n'
            '        "orderby" => "post__in", "posts_per_page" => count( $ids ) ) );\n'
            '    while ( $q->have_posts() ) { $q->the_post(); global $product;\n'
            '      $product = wc_get_product( get_the_ID() );\n'
            '      get_template_part( "template-parts/card" ); }\n'
            '    wp_reset_postdata();\n'
            '  } ?>\n'
            '</div>')

    fp = re.sub(r'<div class="(?:grid|rail)"[^>]*>.*?</div>\s*(?=</section>|<section|<div class="sec)',
                grid_to_loop, fp, flags=re.S)
    fp, u = rewrite_links(fp, cfg['links']); unmapped |= u
    # build-only hooks mean nothing in WordPress
    fp = re.sub(r'\s+data-(add|cart-[a-z-]+|base|img|sku|name|price|type|src)="[^"]*"', '', fp)
    open(os.path.join(theme, 'front-page.php'), 'w').write(
        "<?php get_header(); ?>\n<main>\n" + fp.strip() + "\n</main>\n<?php get_footer(); ?>\n")

    # ---- product archive, reproducing the original shop page
    archive_tpl = """<?php get_header();
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
        <h2 class="GROUPH"><?php echo esc_html( html_entity_decode( $c->name ) ); ?></h2>
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
"""
    open(os.path.join(theme, 'archive-product.php'), 'w').write(
        archive_tpl.replace('GROUPH', cfg['grouph']))

    # ---- single product, WooCommerce form inside the original pdp shell
    open(os.path.join(theme, 'single-product.php'), 'w').write("""<?php get_header(); ?>
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
""")

    # ---- generic page / post / fallback
    page_tpl = """<?php get_header(); ?>
<main class="sec wrap">
  <?php while ( have_posts() ) : the_post(); ?>
    <div class="sec__head"><h1 class="sec__h"><?php the_title(); ?></h1></div>
    <div class="prose"><?php the_content(); ?></div>
  <?php endwhile; ?>
</main>
<?php get_footer(); ?>
"""
    for f in ('page.php', 'single.php', 'index.php'):
        open(os.path.join(theme, f), 'w').write(page_tpl)

    # ---- images referenced by the lifted markup.
    # The hero and the editorial band carry <img src="images/x.jpg"> straight from the
    # original build. Those paths are RELATIVE, so they resolve against whatever URL the
    # visitor is on and 404 everywhere except the site root. Copy the files into the theme
    # and point at them absolutely, so the port keeps the pictures the design was built
    # around instead of quietly losing them.
    assets = os.path.join(theme, 'assets')
    for dp, _, fs in os.walk(theme):
        for f in fs:
            if not f.endswith('.php'):
                continue
            path = os.path.join(dp, f)
            body = open(path).read()
            refs = set(re.findall(r'(?:\.\./)?images/([A-Za-z0-9_.-]+)', body))
            if not refs:
                continue
            os.makedirs(assets, exist_ok=True)
            for name in refs:
                srcp = os.path.join(src_dir, 'images', name)
                if os.path.exists(srcp):
                    shutil.copy(srcp, os.path.join(assets, name))
                else:
                    print(f'    MISSING IMAGE {brand}: {name}')
            body = re.sub(
                r'(?:\.\./)?images/([A-Za-z0-9_.-]+)',
                lambda m: "<?php echo esc_url( get_template_directory_uri() ); ?>/assets/" + m.group(1),
                body)
            open(path, 'w').write(body)

    # screenshot for the theme picker
    for cand in ('l-hero-fruitsalad.jpg', 'l-hero-cintura.jpg'):
        p = os.path.join(src_dir, 'images', cand)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(theme, 'screenshot.jpg'))
            break

    files = sorted(os.path.relpath(os.path.join(dp, f), theme)
                   for dp, _, fs in os.walk(theme) for f in fs)
    return theme, files, unmapped

if __name__ == '__main__':
    bad = 0
    for brand, cfg in BRANDS.items():
        theme, files, unmapped = build(brand, cfg)
        print(f'{brand}: {len(files)} files -> {os.path.relpath(theme, ROOT)}')
        for f in files:
            print('   ', f)
        if unmapped:
            bad += 1
            print('    UNMAPPED LINKS (would 404):', sorted(unmapped))
    sys.exit(1 if bad else 0)
