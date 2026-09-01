#!/usr/bin/env python3
"""
Build WooCommerce product import CSVs from a brand's catalog.json.

Why this exists: FeatherMoss and Rex Jewelz are not React apps, they are Python
static site generators. Their upstream catalog.json carries the full variant and
price structure, which a crawl of the rendered HTML cannot recover reliably.
Importing from the catalog is lossless. Crawling is not.

Output is the standard WooCommerce CSV importer format, variable parents plus
variation rows, ready for WooCommerce > Products > Import.

Run:  python3 tools/build_woo_import.py
"""
import csv, json, os, re, sys

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT    = os.path.join(ROOT, 'out')

BRANDS = {
    'feathermoss': {
        'src':    os.path.expanduser('~/ai_life/feathermoss'),
        'cdn':    'https://feathermoss.vercel.app/images',
        'prefix': 'FM-',
        'onbody': {},
    },
    'rexjewelz': {
        'src':    os.path.expanduser('~/ai_life/rexjewelz'),
        'cdn':    'https://rexjewelz.vercel.app/images',
        'prefix': 'REX-',
        'onbody': {
            'REX-CINTURA':    'l-hero-cintura.jpg',
            'REX-LA-REINA':   'l-reina.jpg',
            'REX-ESPALDA':    'l-espalda.jpg',
            'REX-DIABLA':     'l-diabla.jpg',
            'REX-MEDIANOCHE': 'l-medianoche.jpg',
            'REX-HUMO':       'l-humo.jpg',
            'REX-MUSLO':      'l-muslo.jpg',
            'REX-JAULA':      'l-jaula.jpg',
        },
    },
}

COLUMNS = [
    'ID','Type','SKU','Name','Published','Is featured?','Visibility in catalog',
    'Short description','Description','Tax status','Tax class','In stock?','Stock',
    'Backorders allowed?','Sold individually?','Allow customer reviews?',
    'Sale price','Regular price','Categories','Tags','Images','Parent',
    'Upsells','Cross-sells','Position',
    'Attribute 1 name','Attribute 1 value(s)','Attribute 1 visible','Attribute 1 global',
    # Rex prints a one word English gloss under every product name on its cards. It is
    # real on-page copy, so it travels as product meta rather than being dropped.
    'Meta: _es',
    # Materials render as their own spec block on the PDP, same as the original, so they
    # travel as structured meta rather than being flattened into the description.
    'Meta: _materials',
]

# Variant labels are heterogeneous across the catalogue, so the attribute name is
# derived per product from the labels themselves rather than hardcoded globally.
def attribute_name(labels, product_type=None):
    """Derive the attribute name from the variant labels.

    Both brands' build.py fall back to a bare 'Option' for most products, which is
    less useful than the labels themselves allow, so this classifies properly. The
    one place the original was deliberate is FeatherMoss necklaces, labelled Length,
    and that is matched exactly so the rendered label does not drift.
    """
    if product_type == 'Necklaces':
        return 'Length'
    joined = ' '.join(labels).lower()
    if re.search(r'\binch\b', joined):                       return 'Length'
    if re.search(r'\b(gold|silver|bronze)\b', joined):       return 'Finish'
    if re.search(r'\brows?\b', joined):                      return 'Rows'
    if re.search(r'\bcharms?\b', joined):                    return 'Charms'
    if re.search(r'(size|to [sml0-9x]|made to measure)', joined): return 'Size'
    # bare garment sizes, caught before the Quantity rule so 'One'/'Pair' style
    # labels do not swallow them
    if all(l.lower() in ('small', 'medium', 'large') for l in labels): return 'Size'
    if re.search(r'\b(choker|classic)\b', joined):           return 'Style'
    if re.search(r'\b(one|two|three|four|six|single|pair|set of)\b', joined): return 'Quantity'
    return 'Option'

def img_for(sku, prefix):
    """Mirrors img_for() in each brand's build.py so filenames stay in sync."""
    if sku.startswith(prefix + 'SET-'):
        return 's-' + sku.replace(prefix + 'SET-', '').lower() + '.jpg'
    return 'p-' + sku.replace(prefix, '').lower() + '.jpg'

def description_for(item, catalog_products=None):
    """Long copy if the catalogue has it, otherwise the blurb. Materials appended
    as a plain list. Copy passes through untouched, it already follows the house
    rules and is not ours to rewrite."""
    parts = []
    # The blurb already ships as the short description, which the PDP prints under the
    # title. Repeating it here renders the same sentence twice on the page, so the long
    # description only carries the blurb when there is nothing longer to say and the
    # product has no other body copy at all.
    if item.get('long'):
        parts.append(f"<p>{item['long']}</p>")
    if item.get('es'):
        parts.append(f"<p><em>{item['name']}, {item['es']}</em></p>")
    if item.get('contains'):
        # The original lists each contained piece by NAME with its blurb, not by SKU.
        # A bare SKU list is both uglier and loses the copy that sells the set.
        lookup = {p['sku']: p for p in (catalog_products or [])}
        # The everything-set lists names only. A named set lists name plus blurb. That is
        # what each generator does, and the difference is deliberate: sixteen blurbs is a
        # wall of text, three is a sell.
        is_all = item['contains'] == ['ALL']
        members = list(lookup) if is_all else item['contains']
        li = ''
        for sku in members:
            p = lookup.get(sku)
            if not p:
                continue
            blurb = '' if is_all else (f", {p['blurb']}" if p.get('blurb') else '')
            li += f"<li><strong>{p['name']}</strong>{blurb}</li>"
        if li:
            parts.append(f"<p>What is in it</p><ul>{li}</ul>")
    return ''.join(parts)

def row(**kw):
    r = {c: '' for c in COLUMNS}
    r.update(kw)
    return r

def build(brand, cfg):
    cat = json.load(open(os.path.join(cfg['src'], 'catalog', 'catalog.json')))
    products, sets = cat['products'], cat['sets']
    rows, pos = [], 0
    img_dir = os.path.join(cfg['src'], 'site', 'images')
    missing = []

    def image_urls(sku):
        urls, names = [], [img_for(sku, cfg['prefix'])]
        if sku in cfg['onbody']:
            names.append(cfg['onbody'][sku])
        for n in names:
            if not os.path.exists(os.path.join(img_dir, n)):
                missing.append(f'{sku} -> {n}')
                continue
            urls.append(f"{cfg['cdn']}/{n}")
        return ', '.join(urls)

    # ---- variable products, one parent plus one row per variant
    for p in products:
        labels = [v['label'] for v in p['variants']]
        attr   = attribute_name(labels, p.get('type'))
        prices = [v['price'] for v in p['variants']]
        pos += 1
        rows.append(row(
            Type='variable', SKU=p['sku'], Name=p['name'], Published='1',
            **{'Is featured?': '0', 'Visibility in catalog': 'visible',
               'Short description': p.get('blurb', ''),
               'Description': description_for(p),
               'Tax status': 'taxable', 'In stock?': '1',
               'Backorders allowed?': '0', 'Sold individually?': '0',
               'Allow customer reviews?': '1',
               'Categories': p['type'],
               'Tags': p.get('collection', ''),
               'Images': image_urls(p['sku']),
               'Position': str(pos),
               'Attribute 1 name': attr,
               'Attribute 1 value(s)': ', '.join(labels),
               'Attribute 1 visible': '1',
               'Attribute 1 global': '1',
               'Meta: _es': p.get('es', ''),
               'Meta: _materials': '|'.join(p.get('materials', []))}))
        for v in p['variants']:
            rows.append(row(
                Type='variation', SKU=f"{p['sku']}-{re.sub(r'[^A-Z0-9]+','', v['label'].upper())}",
                Name=f"{p['name']} - {v['label']}", Published='1', Parent=p['sku'],
                **{'Visibility in catalog': 'visible', 'Tax status': 'taxable',
                   'In stock?': '1', 'Regular price': str(v['price']),
                   'Attribute 1 name': attr,
                   'Attribute 1 value(s)': v['label'],
                   'Attribute 1 visible': '1',
                   'Attribute 1 global': '1'}))
        assert min(prices) > 0, f"{p['sku']} has a non positive price"

    # ---- sets, simple products at their own price
    # Deliberately NOT WooCommerce grouped products. A grouped product derives its
    # price from its children, but every set here is priced BELOW the sum of its
    # parts, and that discount is the whole point of the set. Grouped would silently
    # destroy it. Children are carried as cross sells instead.
    all_skus = [p['sku'] for p in products]
    for s in sets:
        pos += 1
        # 'ALL' is a sentinel in the catalogue meaning the entire product range, not a
        # SKU. Each brand's build.py expands it the same way on the live site, so the
        # cross sells expand it too rather than writing a bogus 'ALL' product.
        raw = s.get('contains', [])
        children = all_skus if raw == ['ALL'] else raw
        contained = ', '.join(children)
        # The original prints the saving on every set, computed against the entry size of
        # each contained piece. It is real on-page copy and it is derivable, so it is
        # recomputed here rather than dropped.
        desc = description_for(s, products)
        floor = 0
        for ch in children:
            cp = next((x for x in products if x['sku'] == ch), None)
            if cp:
                floor += min(v['price'] for v in cp['variants'])
        if floor and s['price'] < floor:
            save = floor - s['price']
            pct = round(100 * save / floor)
            desc += (f"<p>Bought separately at entry size these come to ${floor}. "
                     f"The set is ${s['price']}, so you keep ${save}, which is {pct} "
                     f"percent off. Pick a larger size on any piece and the gap only "
                     f"widens.</p>")
        rows.append(row(
            Type='simple', SKU=s['sku'], Name=s['name'], Published='1',
            **{'Is featured?': '1', 'Visibility in catalog': 'visible',
               'Short description': s.get('blurb', ''),
               'Description': desc,
               'Tax status': 'taxable', 'In stock?': '1',
               'Backorders allowed?': '0', 'Sold individually?': '0',
               'Allow customer reviews?': '1',
               'Regular price': str(s['price']),
               'Categories': s['type'],
               'Tags': s.get('collection', ''),
               'Images': image_urls(s['sku']),
               'Cross-sells': contained,
               'Position': str(pos),
               'Meta: _es': s.get('es', ''),
               'Meta: _materials': '|'.join(s.get('materials', []))}))

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'{brand}-products.csv')
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    parents = sum(1 for r in rows if r['Type'] == 'variable')
    varis   = sum(1 for r in rows if r['Type'] == 'variation')
    simples = sum(1 for r in rows if r['Type'] == 'simple')
    return path, parents, varis, simples, missing

if __name__ == '__main__':
    fail = False
    for brand, cfg in BRANDS.items():
        path, parents, varis, simples, missing = build(brand, cfg)
        print(f'{brand}: {parents} variable + {varis} variations + {simples} sets '
              f'= {parents + varis + simples} rows -> {os.path.relpath(path, ROOT)}')
        if missing:
            fail = True
            print('  MISSING IMAGES:')
            for m in missing:
                print('   ', m)
    sys.exit(1 if fail else 0)
