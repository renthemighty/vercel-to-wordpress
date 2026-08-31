#!/usr/bin/env python3
"""
Build a WordPress WXR import file from a brand's built static site.

Covers the content layer that the WooCommerce product CSV does not: the standing
pages and the journal. Listing pages (shop, sets, body, under-50) are deliberately
skipped because WooCommerce archives replace them, and cart/checkout are skipped
because WooCommerce owns those routes.

Content is lifted from <main> on each built page, so what lands in WordPress is
exactly what the generator produced and what the live site serves.

Run:  python3 tools/build_wxr.py
"""
import html, json, os, re, sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'out')

BRANDS = {
    'feathermoss': {
        'src':   os.path.expanduser('~/ai_life/feathermoss/site'),
        'cdn':   'https://feathermoss.vercel.app',
        'title': 'FeatherMoss',
        'pages': ['about', 'care', 'contact', 'returns', 'shipping', 'stockists'],
    },
    'rexjewelz': {
        'src':   os.path.expanduser('~/ai_life/rexjewelz/site'),
        'cdn':   'https://rexjewelz.vercel.app',
        'title': 'Rex Jewelz',
        # body and under-50 are NOT just listings. Both carry substantial editorial
        # copy that would be lost if they were treated as archives, so they come across
        # as real pages with the product grids stripped out.
        'pages': ['about', 'care', 'contact', 'returns', 'shipping', 'fit',
                  'body', 'under-50'],
    },
}

# Routes intentionally NOT exported, with the reason, so nothing looks forgotten.
SKIPPED = {
    'index':     'front page, rebuilt in the theme',
    'shop':      'replaced by the WooCommerce shop archive',
    'sets':      'replaced by a WooCommerce category archive',
    'charms':    'replaced by a WooCommerce category archive',
    'necklaces': 'replaced by a WooCommerce category archive',
    'cart':      'owned by WooCommerce',
    'checkout':  'owned by WooCommerce, and is a holding page on the original',
    'journal':   'replaced by the WordPress post archive',
    '404':       'owned by the theme',
}

def main_of(path):
    src = open(path, encoding='utf-8').read()
    m = re.search(r'<main[^>]*>(.*?)</main>', src, re.S)
    if not m:
        return None, None
    body = m.group(1)
    # Prefer the page's own <h1>. The <title> tag is "Care / FeatherMoss" while the h1 is
    # the real editorial heading, and using the title tag silently loses that copy.
    h = re.search(r'<h1[^>]*>(.*?)</h1>', body, re.S)
    if h:
        # replace tags with a space, not nothing, or a <br> welds two words together
        title = re.sub(r'\s+', ' ',
                       html.unescape(re.sub(r'<[^>]+>', ' ', h.group(1)))).strip()
        title = re.sub(r'\s+([,.;:])', r'\1', title)
    else:
        t = re.search(r'<title>(.*?)</title>', src, re.S)
        title = html.unescape(t.group(1)).split('/')[0].strip() if t else None
    return body, title

def clean(body, cdn, slug_to_sku=None):
    slug_to_sku = slug_to_sku or {}
    # The template prints the_title(), so the lifted <h1> would render the name twice.
    body = re.sub(r'<h1[^>]*>.*?</h1>', '', body, count=1, flags=re.S)
    # breadcrumb and back links are site chrome, WordPress renders its own
    body = re.sub(r'<p class="crumb">.*?</p>', '', body, flags=re.S)
    body = re.sub(r'<p class="prose__back">.*?</p>', '', body, flags=re.S)
    # Product grids come out, because a frozen copy of the catalogue inside page content
    # goes stale the first time a price changes. But the page still has to LIST those
    # products, so the SKUs it showed are captured first and re-emitted as a WooCommerce
    # shortcode. Same products, rendered live.
    listed = []
    for slug in re.findall(r'href="(?:\.\./)?product/([^"]+)\.html"', body):
        sku = slug_to_sku.get(slug)
        if sku and sku not in listed:
            listed.append(sku)
    # point relative assets at the live site so the importer can sideload them
    body = re.sub(r'(src|href)="(?!https?:|#|mailto:)/?(?:\.\./)*([^"]+)"',
                  lambda m: f'{m.group(1)}="{cdn}/{m.group(2)}"', body)
    body = re.sub(r'<div class="(?:grid|rail)"[^>]*>.*?</div>\s*(?=</section>|<section|<p|$)',
                  '', body, flags=re.S)
    body = re.sub(r'<a class="card".*?</a>', '', body, flags=re.S)
    if listed:
        body += ('\n<!-- products this page listed on the original, rendered live -->\n'
                 f'[products skus="{",".join(listed)}" limit="-1" columns="4" '
                 'orderby="menu_order" order="ASC"]')
    # drop build-only hooks that mean nothing in WordPress
    body = re.sub(r'\s+data-(add|cart-[a-z-]+|base|img|sku|name|price|type|src)="[^"]*"', '', body)
    return re.sub(r'\n{3,}', '\n\n', body).strip()

def item(title, slug, content, post_type, pid, order=0, date='2026-08-30 12:00:00'):
    return f"""	<item>
		<title>{escape(title)}</title>
		<link>/{slug}/</link>
		<pubDate>{date}</pubDate>
		<dc:creator><![CDATA[admin]]></dc:creator>
		<guid isPermaLink="false">/?p={pid}</guid>
		<description></description>
		<content:encoded><![CDATA[{content}]]></content:encoded>
		<excerpt:encoded><![CDATA[]]></excerpt:encoded>
		<wp:post_id>{pid}</wp:post_id>
		<wp:post_date><![CDATA[{date}]]></wp:post_date>
		<wp:post_date_gmt><![CDATA[{date}]]></wp:post_date_gmt>
		<wp:comment_status><![CDATA[closed]]></wp:comment_status>
		<wp:ping_status><![CDATA[closed]]></wp:ping_status>
		<wp:post_name><![CDATA[{slug}]]></wp:post_name>
		<wp:status><![CDATA[publish]]></wp:status>
		<wp:post_parent>0</wp:post_parent>
		<wp:menu_order>{order}</wp:menu_order>
		<wp:post_type><![CDATA[{post_type}]]></wp:post_type>
		<wp:post_password><![CDATA[]]></wp:post_password>
		<wp:is_sticky>0</wp:is_sticky>
	</item>
"""

def build(brand, cfg):
    items, pid, report = [], 100, []
    # product page slug -> SKU, so a listing page can be re-emitted as a live shortcode
    cat = json.load(open(os.path.join(os.path.dirname(cfg['src']), 'catalog', 'catalog.json')))
    slug_to_sku = {}
    for it in cat['products'] + cat['sets']:
        slug_to_sku[re.sub(r'[^a-z0-9]+', '-', it['name'].lower()).strip('-')] = it['sku']

    for order, slug in enumerate(cfg['pages'], start=1):
        path = os.path.join(cfg['src'], f'{slug}.html')
        if not os.path.exists(path):
            report.append(f'MISSING {slug}.html'); continue
        body, title = main_of(path)
        if body is None:
            report.append(f'NO <main> in {slug}.html'); continue
        pid += 1
        items.append(item(title or slug.title(), slug, clean(body, cfg['cdn'], slug_to_sku),
                          'page', pid, order))
        report.append(f'page  {slug:<12} {len(body):>6} bytes')

    jdir = os.path.join(cfg['src'], 'journal')
    for slug in sorted(os.listdir(jdir)) if os.path.isdir(jdir) else []:
        if not slug.endswith('.html'):
            continue
        name = slug[:-5]
        body, title = main_of(os.path.join(jdir, slug))
        if body is None:
            report.append(f'NO <main> in journal/{slug}'); continue
        pid += 1
        items.append(item(title or name, name, clean(body, cfg['cdn'], slug_to_sku), 'post', pid))
        report.append(f'post  {name:<12} {len(body):>6} bytes')

    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
	xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
	xmlns:content="http://purl.org/rss/1.0/modules/content/"
	xmlns:wfw="http://wellformedweb.org/CommentAPI/"
	xmlns:dc="http://purl.org/dc/elements/1.1/"
	xmlns:wp="http://wordpress.org/export/1.2/">
<channel>
	<title>{escape(cfg['title'])}</title>
	<link>{cfg['cdn']}</link>
	<description>Converted from the static build</description>
	<pubDate>Sat, 30 Aug 2026 12:00:00 +0000</pubDate>
	<language>en-US</language>
	<wp:wxr_version>1.2</wp:wxr_version>
	<wp:base_site_url>{cfg['cdn']}</wp:base_site_url>
	<wp:base_blog_url>{cfg['cdn']}</wp:base_blog_url>
	<wp:author><wp:author_id>1</wp:author_id>
		<wp:author_login><![CDATA[admin]]></wp:author_login>
		<wp:author_email><![CDATA[hello@{brand}.com]]></wp:author_email>
		<wp:author_display_name><![CDATA[{cfg['title']}]]></wp:author_display_name>
	</wp:author>
{''.join(items)}</channel>
</rss>
"""
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'{brand}-content.wxr')
    open(path, 'w', encoding='utf-8').write(xml)
    return path, len(items), report

if __name__ == '__main__':
    for brand, cfg in BRANDS.items():
        path, n, report = build(brand, cfg)
        print(f'{brand}: {n} items -> {os.path.relpath(path, ROOT)}')
        for line in report:
            print('   ', line)
        print(f'    skipped {len(SKIPPED)} routes by design, see SKIPPED in this file')
