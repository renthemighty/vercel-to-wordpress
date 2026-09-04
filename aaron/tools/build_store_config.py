#!/usr/bin/env python3
"""
Extract per brand store settings from the built site rather than transcribing them.

The shipping thresholds are hardcoded inside each brand's cart JS and they are NOT
the same between brands, so reading them from source is the only safe way to carry
them into WooCommerce.

Run:  python3 tools/build_store_config.py
"""
import json, os, re
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = {
    'feathermoss': (os.path.expanduser('~/ai_life/feathermoss'), 'feathermoss.com'),
    'rexjewelz':   (os.path.expanduser('~/ai_life/rexjewelz'),   'rexjewelz.com'),
}

def category_display_order(src, cat):
    """The catalogue's taxonomy array is NOT the display order.

    Rex Jewelz orders its zones top to bottom down the body, and build.py calls that
    ordering "the spine of the whole shop", while catalog.json lists them bottom to top.
    The rendered shop page is the only honest source for display order, so read it from
    there. FeatherMoss uses .shopgroup__h and Rex uses .zone__h.
    """
    shop = os.path.join(src, 'site', 'shop.html')
    html = open(shop, encoding='utf-8').read()
    found = re.findall(r'<h2 class="(?:shopgroup__h|zone__h)[^"]*">\s*([^<]+?)\s*</h2>', html)
    order = [unescape(x) for x in found]
    known = set(cat['taxonomy']['type'])
    order = [x for x in order if x in known]
    missing = [x for x in cat['taxonomy']['type'] if x not in order]
    if not order:
        raise SystemExit(f'{src}: could not read category display order from shop.html')
    return order + missing


def pdp_note(src):
    """The line under the add-to-bag button, lifted from the brand's own generator."""
    build = open(os.path.join(src, 'build.py'), encoding='utf-8').read()
    m = re.search(r'<p class="pdp__note">(.*?)</p>', build)
    if not m:
        raise SystemExit(f'{src}: could not find the pdp__note text')
    return unescape(m.group(1)).strip()


def care_bullets(src):
    """The "Looking after it" list, lifted rather than retyped."""
    build = open(os.path.join(src, 'build.py'), encoding='utf-8').read()
    m = re.search(r'Looking after it</p>\s*<ul>(.*?)</ul>', build, re.S)
    if not m:
        raise SystemExit(f'{src}: could not find the care bullets')
    return [unescape(x).strip() for x in re.findall(r'<li>(.*?)</li>', m.group(1), re.S)]


def size_note(src):
    """Rex prints a sizing block on every product that takes a size. Lifted, not retyped.

    Returns {heading, body} or None for brands that have no such block.
    """
    build = open(os.path.join(src, 'build.py'), encoding='utf-8').read()
    # build.py contains more than one fit__h block. The sets one comes first, so take the
    # one that is actually about sizing rather than the first match.
    for m in re.finditer(r'<p class="fit__h">(.*?)</p>\s*<p>(.*?)</p>', build, re.S):
        head = unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
        if 'size' not in head.lower():
            continue
        body = re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', '', m.group(2)))).strip()
        return {'heading': head, 'body': body}
    return None


def category_leads(src):
    """Lead lines from the original listing pages, keyed by category name.

    These sit on shop.html, sets.html, charms.html and so on. Dropping the listing pages
    in favour of WooCommerce archives would silently bin this copy, so it is carried
    across as the category description instead, which the theme renders.
    """
    site = os.path.join(src, 'site')
    # listing page file -> the product category it describes
    maps = {'charms.html': 'Charms & Extras', 'necklaces.html': 'Necklaces',
            'sets.html': 'Sets'}
    out = {}
    # Rex prints a short tagline beside each zone heading on the shop page. Same idea as
    # a category lead, different markup, and just as easy to lose.
    shop = os.path.join(site, 'shop.html')
    if os.path.exists(shop):
        shop_src = open(shop, encoding='utf-8').read()
        for m in re.finditer(
                r'<h2 class="zone__h">(.*?)</h2>(.*?)(?=<div class="(?:grid|rail)")',
                shop_src, re.S):
            zone = unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
            tail = re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', m.group(2)))).strip()
            if zone and tail and len(tail) < 120:
                out[zone] = tail
    for fname, cat in maps.items():
        path = os.path.join(site, fname)
        if not os.path.exists(path):
            continue
        html_src = open(path, encoding='utf-8').read()
        m = re.search(r'<p class="(?:cat__lead|zone__lead)"[^>]*>(.*?)</p>', html_src, re.S)
        if m:
            out[cat] = unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
    return out


def const(js, name):
    m = re.search(rf'var\s+{name}\s*=\s*([0-9]+)', js)
    if not m:
        raise SystemExit(f'{name} not found, refusing to guess')
    return int(m.group(1))

out = {}
for brand, (src, domain) in SRC.items():
    cart = next(os.path.join(src, 'site', f) for f in os.listdir(os.path.join(src, 'site'))
                if f.endswith('cart.js'))
    js = open(cart).read()
    cat = json.load(open(os.path.join(src, 'catalog', 'catalog.json')))
    out[brand] = {
        'target_domain':          domain,
        'source_of_truth':        os.path.relpath(cart, os.path.expanduser('~')),
        'currency':               cat['currency'],
        'free_shipping_over':     const(js, 'FREE_SHIPPING'),
        'flat_shipping_rate':     const(js, 'SHIP_FLAT'),
        'legacy_cart_storage_key': re.search(r"var KEY = '([^']+)'", js).group(1),
        'product_count':          len(cat['products']),
        'set_count':              len(cat['sets']),
        'categories':             category_display_order(src, cat),
        'tags':                   cat['taxonomy']['collection'],
        'support_email':          f'hello@{domain}',
        'pdp_note':               pdp_note(src),
        'care_bullets':           care_bullets(src),
        'size_note':              size_note(src),
        'category_descriptions':  category_leads(src),
    }

path = os.path.join(ROOT, 'out', 'store-config.json')
os.makedirs(os.path.dirname(path), exist_ok=True)
json.dump(out, open(path, 'w'), indent=2)
for b, c in out.items():
    print(f"{b}: {c['currency']}, free shipping over {c['free_shipping_over']}, "
          f"flat {c['flat_shipping_rate']}, {c['product_count']}+{c['set_count']} items")
print('->', os.path.relpath(path, ROOT))
