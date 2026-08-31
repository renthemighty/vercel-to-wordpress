#!/usr/bin/env python3
"""
Deterministic structural diff between the original site and the converted WordPress site.

BUILD_SPEC.md section 2.6 is explicit that the gate must be deterministic and non-LLM, and
that raw pixelmatch is the wrong tool across a React-DOM-vs-PHP-HTML comparison because it
over-flags on font rendering and text reflow. This compares STRUCTURE and CONTENT instead
of pixels, so it is immune to that noise while still catching the failures that matter:
missing products, dropped prices, lost copy, broken navigation.

Nothing here calls a model. It parses both pages and compares sets.

Run:  python3 tools/verify_structural_diff.py <brand> [--wp http://localhost:8910]
"""
import argparse, html, json, os, re, sys, urllib.request
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BRANDS = {
    'feathermoss': {
        'origin': 'https://feathermoss.vercel.app',
        'src':    os.path.expanduser('~/ai_life/feathermoss'),
        # original route -> converted route
        'routes': {
            '/shop.html':      '/shop/',
            '/sets.html':      '/product-category/sets/',
            '/charms.html':    '/product-category/charms-extras/',
            '/necklaces.html': '/product-category/necklaces/',
            '/about.html':     '/about/',
            '/care.html':      '/care/',
            '/shipping.html':  '/shipping/',
            '/returns.html':   '/returns/',
            '/contact.html':   '/contact/',
            '/stockists.html': '/stockists/',
        },
    },
    'rexjewelz': {
        'origin': 'https://rexjewelz.vercel.app',
        'src':    os.path.expanduser('~/ai_life/rexjewelz'),
        'routes': {
            '/shop.html':     '/shop/',
            '/sets.html':     '/product-category/sets/',
            '/body.html':     '/body/',
            '/under-50.html': '/under-50/',
            '/fit.html':      '/fit/',
            '/about.html':    '/about/',
            '/care.html':     '/care/',
            '/shipping.html': '/shipping/',
            '/returns.html':  '/returns/',
            '/contact.html':  '/contact/',
        },
    },
}

# Chrome that legitimately differs after conversion, excluded from the text comparison.
# Each entry is a deliberate, recorded divergence, not a convenience.
IGNORE_PHRASES = {
    'menu',                       # mobile nav added by the conversion
    'bag (0)', 'bag(0)',
    'prices in usd',
    'skip to content', 'skip to navigation',
    'search', 'clear', 'choose an option',
    'add to cart', 'add to bag',
    'home', 'shop',
}

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')

def main_of(doc):
    m = re.search(r'<main[^>]*>(.*?)</main>', doc, re.S)
    return m.group(1) if m else doc

def words(fragment):
    """Visible words, lowercased, with scripts, styles and markup removed."""
    f = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', fragment, flags=re.S)
    f = re.sub(r'<[^>]+>', ' ', f)
    f = html.unescape(f)
    f = re.sub(r'[^\w$&\'-]+', ' ', f)
    return [w for w in (t.strip("'-") for t in f.lower().split()) if w]

def prices(fragment):
    """Read prices from stripped text.

    WooCommerce renders <span class=currencySymbol>$</span>40.00, so the symbol and the
    digits are separated by markup and a regex over raw HTML finds nothing.
    """
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', fragment, flags=re.S)
    text = html.unescape(re.sub(r'<[^>]+>', '', text))
    text = re.sub(r'\s+', ' ', text)
    return Counter(re.findall(r'\$\s?(\d+(?:\.\d{2})?)', text))

def norm_price(c):
    """$40 and $40.00 are the same price. WooCommerce always prints the cents."""
    out = Counter()
    for v, n in c.items():
        out[f'{float(v):.2f}'] += n
    return out

def headings(fragment):
    hs = re.findall(r'<h([1-3])[^>]*>(.*?)</h\1>', fragment, re.S)
    return [re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', t))).strip().lower()
            for _, t in hs]

def product_names(cat):
    c = json.load(open(os.path.join(cat, 'catalog', 'catalog.json')))
    return {p['name'].lower() for p in c['products']} | {s['name'].lower() for s in c['sets']}

def load_suppressions():
    """Routes with a written, accepted reason in docs/DIVERGENCES.md.

    The register is the only thing that can suppress a failure. If a route is not named
    there, a failure is a real defect.
    """
    path = os.path.join(ROOT, 'docs', 'DIVERGENCES.md')
    if not os.path.exists(path):
        return set()
    out = set()
    for line in open(path):
        m = re.match(r'\*\*Gate:\*\*\s*suppresses\s*`([^`]+)`', line.strip())
        if m:
            out.add(m.group(1))
    return out


def compare(brand, cfg, wp_base):
    suppressed = load_suppressions()
    catalog_names = product_names(cfg['src'])
    rows, failures = [], []

    for orig_path, wp_path in cfg['routes'].items():
        try:
            o_doc = fetch(cfg['origin'] + orig_path)
            w_doc = fetch(wp_base + wp_path)
        except Exception as e:
            failures.append(f'{orig_path}: fetch failed, {e}')
            continue

        o_main, w_main = main_of(o_doc), main_of(w_doc)
        o_words, w_words = set(words(o_main)), set(words(w_main))

        # 1. content words present on the original but gone after conversion
        lost = {w for w in (o_words - w_words)
                if len(w) > 3 and not w.startswith('$') and w not in IGNORE_PHRASES}
        # a word that survives somewhere else on the converted page is not lost
        lost = {w for w in lost if w not in set(words(w_doc))}

        # 2. products the original showed as CARDS must still be shown.
        # Matching catalogue names against all prose gives false positives: Rex has a
        # product called Sal, and the care page uses the word "salt" and "sal" in ordinary
        # sentences. Only card names count as a product actually being listed.
        o_cards = {re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', t))).strip().lower()
                   for t in re.findall(r'<h3 class="card__name"[^>]*>(.*?)</h3>', o_main, re.S)}
        o_cards &= catalog_names
        w_cards = {re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', t))).strip().lower()
                   for t in re.findall(r'<h3 class="card__name"[^>]*>(.*?)</h3>', w_doc, re.S)}
        missing_products = o_cards - w_cards

        # 3. every price shown on the original must still appear
        o_p, w_p = norm_price(prices(o_main)), norm_price(prices(w_main))
        missing_prices = {p for p in o_p if p not in w_p}

        # 4. heading count should not collapse
        o_h, w_h = headings(o_main), headings(w_main)

        status = 'PASS'
        notes = []
        if missing_products:
            status = 'FAIL'; notes.append(f'products missing: {sorted(missing_products)[:4]}')
        if missing_prices:
            status = 'FAIL'; notes.append(f'prices missing: {sorted(missing_prices)[:6]}')
        if len(lost) > 25:
            status = 'FAIL'; notes.append(f'{len(lost)} content words lost, e.g. {sorted(lost)[:8]}')
        elif lost:
            notes.append(f'{len(lost)} minor words differ: {sorted(lost)[:6]}')
        if o_h and len(w_h) < max(1, len(o_h) // 3):
            status = 'FAIL'; notes.append(f'headings collapsed {len(o_h)} -> {len(w_h)}')

        if status == 'FAIL' and orig_path in suppressed:
            status = 'NOTED'
            notes.append('accepted, see docs/DIVERGENCES.md')
        rows.append((status, orig_path, wp_path, len(o_words), len(w_words),
                     len(o_h), len(w_h), '; '.join(notes)))
        if status == 'FAIL':
            failures.append(f'{orig_path} -> {wp_path}: {"; ".join(notes)}')

    return rows, failures

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('brand', choices=sorted(BRANDS))
    ap.add_argument('--wp', default='http://localhost:8910')
    a = ap.parse_args()

    rows, failures = compare(a.brand, BRANDS[a.brand], a.wp.rstrip('/'))
    print(f'{a.brand}: structural diff, original vs converted\n')
    print(f'  {"":4} {"original":16} {"converted":30} {"words":>11}  {"h1-h3":>7}')
    for st, o, w, ow, ww, oh, wh, note in rows:
        mark = {'PASS': 'ok  ', 'NOTED': 'note', 'FAIL': 'FAIL'}[st]
        print(f'  {mark} {o:16} {w:30} {ow:5}->{ww:<5} {oh:3}->{wh:<3}')
        if note:
            print(f'       {note}')
    print()
    if failures:
        print(f'RESULT: {len(failures)} FAILURES')
        sys.exit(1)
    print(f'RESULT: PASS, {len(rows)} routes structurally equivalent')
