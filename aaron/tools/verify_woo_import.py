#!/usr/bin/env python3
"""
Verify the generated WooCommerce CSVs against the source catalog.json.

This is the gate. It proves the import is lossless before anything touches a real
store, and it fails loudly rather than warning quietly.

Run:  python3 tools/verify_woo_import.py
"""
import csv, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANDS = {
    'feathermoss': os.path.expanduser('~/ai_life/feathermoss'),
    'rexjewelz':   os.path.expanduser('~/ai_life/rexjewelz'),
}
CHECK_IMAGES = '--skip-images' not in sys.argv

def head(url):
    req = urllib.request.Request(url, method='HEAD',
                                 headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except Exception as e:
        return getattr(e, 'code', 0)

def verify(brand, src):
    cat  = json.load(open(os.path.join(src, 'catalog', 'catalog.json')))
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'out', f'{brand}-products.csv'))))
    errs, checked, pricing = [], 0, []

    by_sku    = {r['SKU']: r for r in rows}
    parents   = {r['SKU']: r for r in rows if r['Type'] == 'variable'}
    simples   = {r['SKU']: r for r in rows if r['Type'] == 'simple'}
    variations = [r for r in rows if r['Type'] == 'variation']

    # 1. every catalogue product became a variable parent, with matching variants
    for p in cat['products']:
        checked += 1
        if p['sku'] not in parents:
            errs.append(f"product {p['sku']} missing from CSV"); continue
        par = parents[p['sku']]
        if par['Name'] != p['name']:
            errs.append(f"{p['sku']} name mismatch {par['Name']!r} vs {p['name']!r}")
        if par['Categories'] != p['type']:
            errs.append(f"{p['sku']} category mismatch")
        mine = [v for v in variations if v['Parent'] == p['sku']]
        if len(mine) != len(p['variants']):
            errs.append(f"{p['sku']} has {len(mine)} variation rows, catalogue has {len(p['variants'])}")
        csv_prices = sorted(float(v['Regular price']) for v in mine)
        cat_prices = sorted(float(v['price']) for v in p['variants'])
        if csv_prices != cat_prices:
            errs.append(f"{p['sku']} price ladder mismatch {csv_prices} vs {cat_prices}")
        csv_labels = sorted(v['Attribute 1 value(s)'] for v in mine)
        cat_labels = sorted(v['label'] for v in p['variants'])
        if csv_labels != cat_labels:
            errs.append(f"{p['sku']} variant labels mismatch")
        # the parent must advertise exactly the labels its children carry
        if sorted(x.strip() for x in par['Attribute 1 value(s)'].split(',')) != cat_labels:
            errs.append(f"{p['sku']} parent attribute list does not match its variations")
        # one attribute name across the whole family, or Woo will not match them
        names = {v['Attribute 1 name'] for v in mine} | {par['Attribute 1 name']}
        if len(names) != 1:
            errs.append(f"{p['sku']} inconsistent attribute name {names}")

    # 2. every set became a simple product at its own catalogue price
    for s in cat['sets']:
        checked += 1
        if s['sku'] not in simples:
            errs.append(f"set {s['sku']} missing from CSV"); continue
        row = simples[s['sku']]
        if float(row['Regular price']) != float(s['price']):
            errs.append(f"{s['sku']} price {row['Regular price']} vs catalogue {s['price']}")
        # 'ALL' is a sentinel for the whole range, matching each brand's build.py
        raw = s.get('contains', [])
        children = [p['sku'] for p in cat['products']] if raw == ['ALL'] else raw
        csv_children = [x.strip() for x in row['Cross-sells'].split(',') if x.strip()]
        if sorted(csv_children) != sorted(children):
            errs.append(f"{s['sku']} cross sells do not match its contents")
        lo = hi = 0
        for child in children:
            cp = next((p for p in cat['products'] if p['sku'] == child), None)
            if cp is None:
                errs.append(f"{s['sku']} contains unknown SKU {child}"); continue
            if child not in by_sku:
                errs.append(f"{s['sku']} cross sells {child} which is not in the CSV")
            lo += min(v['price'] for v in cp['variants'])
            hi += max(v['price'] for v in cp['variants'])
        # Reported, never enforced. Whether a set is priced above or below its parts is
        # a business decision belonging to Aaron, not something this script may assume.
        if hi:
            price = float(s['price'])
            band = 'below parts floor' if price < lo else (
                   'inside the parts band' if price <= hi else 'ABOVE parts ceiling')
            pricing.append(f"{s['sku']:<22} ${price:>6.0f}  parts ${lo} to ${hi}   {band}")

    # 3. no orphan variations
    for v in variations:
        if v['Parent'] not in parents:
            errs.append(f"variation {v['SKU']} has no parent {v['Parent']}")

    # 4. SKUs unique, Woo rejects duplicates on import
    skus = [r['SKU'] for r in rows]
    dupes = {s for s in skus if skus.count(s) > 1}
    if dupes:
        errs.append(f"duplicate SKUs {sorted(dupes)}")

    # 5. every image URL actually resolves
    if CHECK_IMAGES:
        seen = set()
        for r in rows:
            for u in filter(None, (x.strip() for x in r['Images'].split(','))):
                if u in seen: continue
                seen.add(u); checked += 1
                st = head(u)
                if st != 200:
                    errs.append(f"image {st} {u}")
    return checked, errs, pricing

if __name__ == '__main__':
    total_err = 0
    for brand, src in BRANDS.items():
        checked, errs, pricing = verify(brand, src)
        print(f"{brand}: {checked} assertions"
              f"{'' if CHECK_IMAGES else ' (images skipped)'}")
        for e in errs:
            print('   FAIL', e)
        if not errs:
            print('   all passed')
        for line in pricing:
            print('   note', line)
        total_err += len(errs)
    print('\nRESULT:', 'PASS' if total_err == 0 else f'{total_err} FAILURES')
    sys.exit(1 if total_err else 0)
