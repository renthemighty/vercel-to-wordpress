#!/usr/bin/env python3
"""
Prove every route on the original site is accounted for in the conversion.

Simon's scope bar is "every page/route the original app has, not a partial mirror".
This walks the built site, buckets every .html route against the conversion outputs,
and fails if a single one is unclassified.

Run:  python3 tools/verify_coverage.py
"""
import csv, json, os, sys, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from build_wxr import BRANDS as WB, SKIPPED  # noqa: E402

def routes(site):
    out = []
    for dirpath, _, files in os.walk(site):
        if '.vercel' in dirpath:
            continue
        for f in files:
            if f.endswith('.html'):
                rel = os.path.relpath(os.path.join(dirpath, f), site)
                out.append(rel[:-5])
    return sorted(out)

def check(brand, cfg):
    site = cfg['src']
    all_routes = routes(site)

    wxr = ET.parse(os.path.join(ROOT, 'out', f'{brand}-content.wxr')).getroot()
    ns = {'wp': 'http://wordpress.org/export/1.2/'}
    exported = {i.findtext('wp:post_name', namespaces=ns) for i in wxr.iter('item')}

    csv_path = os.path.join(ROOT, 'out', f'{brand}-products.csv')
    rows = list(csv.DictReader(open(csv_path)))
    # product page routes are product/<slug>; match them to CSV rows by name
    prod_names = {r['Name'].lower().replace(' ', '-'): r['SKU']
                  for r in rows if r['Type'] in ('variable', 'simple')}

    buckets = {'page/post': [], 'product': [], 'skipped': [], 'UNCLASSIFIED': []}
    for r in all_routes:
        base = os.path.basename(r)
        if r.startswith('product/'):
            buckets['product'].append(r)
        elif base in exported:
            buckets['page/post'].append(r)
        elif base in SKIPPED:
            buckets['skipped'].append(r)
        else:
            buckets['UNCLASSIFIED'].append(r)

    # every product route must map to a real SKU in the CSV
    orphans = []
    for r in buckets['product']:
        slug = os.path.basename(r)
        if slug not in prod_names:
            orphans.append(slug)

    return all_routes, buckets, orphans, len(rows)

if __name__ == '__main__':
    bad = 0
    for brand, cfg in WB.items():
        all_routes, b, orphans, nrows = check(brand, cfg)
        print(f"\n{brand}: {len(all_routes)} routes on the original site")
        for k in ('page/post', 'product', 'skipped'):
            print(f"   {k:<13} {len(b[k]):>2}")
        if b['UNCLASSIFIED']:
            bad += len(b['UNCLASSIFIED'])
            print('   UNCLASSIFIED:', b['UNCLASSIFIED'])
        if orphans:
            bad += len(orphans)
            print('   PRODUCT ROUTES WITH NO SKU:', orphans)
        covered = len(b['page/post']) + len(b['product']) + len(b['skipped'])
        print(f"   covered {covered}/{len(all_routes)}"
              + ('' if covered == len(all_routes) else '   <-- GAP'))
        if covered != len(all_routes):
            bad += 1
    print('\nRESULT:', 'FULL COVERAGE' if bad == 0 else f'{bad} GAPS')
    sys.exit(1 if bad else 0)
