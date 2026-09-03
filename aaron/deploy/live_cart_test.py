#!/usr/bin/env python3
"""Exercise the real cart and checkout on the live hosting, as a customer would.

Nothing here reads the database. It adds a variation to the cart over plain HTTP, then
reads the rendered cart page, so it proves what a visitor actually gets: the right
variation, the right price, and the shipping rule each brand had in its cart JS.
"""
import http.cookiejar, json, re, socket, ssl, sys, urllib.parse, urllib.request

EDGE = '144.217.60.100'
MAP = {'feathermoss.com': EDGE, 'rexjewelz.com': EDGE}
_real = socket.getaddrinfo

def _resolves(host):
    try:
        _real(host, 443)
        return True
    except socket.gaierror:
        return False

# Public DNS was missing while these two were being built. Fall back to the edge address
# only while a hostname still does not resolve, so the test runs against the real thing
# the moment the zone is published.
if not all(_resolves(h) for h in MAP):
    socket.getaddrinfo = lambda h, p, *a, **k: _real(MAP.get(h, h), p, *a, **k)
    ssl._create_default_https_context = ssl._create_unverified_context
    print('note: resolving through the EasWrk edge, public DNS not answering yet')

BRANDS = {
    'feathermoss': dict(host='feathermoss.com', free_over=75, flat=6.0),
    'rexjewelz':   dict(host='rexjewelz.com',   free_over=95, flat=7.0),
}

def session():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [('User-Agent', 'Mozilla/5.0')]
    return op

def get(op, url):
    with op.open(url, timeout=60) as r:
        return r.read().decode('utf-8', 'replace')

def post(op, url, data):
    body = urllib.parse.urlencode(data).encode()
    with op.open(urllib.request.Request(url, data=body), timeout=60) as r:
        return r.read().decode('utf-8', 'replace')

def text(html_):
    """Visible text with prices normalised.

    WooCommerce splits the currency symbol from the digits with markup, so stripping tags
    leaves "$ 40.00" and a naive "$40.00" search finds nothing. Close the gap here rather
    than searching for both spellings at every call site.
    """
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', html_, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    import html as h
    t = re.sub(r'\s+', ' ', h.unescape(t).replace('\xa0', ' ')).strip()
    return re.sub(r'\$\s+(\d)', r'$\1', t)

def money(s):
    return [float(x) for x in re.findall(r'\$\s?(\d+(?:\.\d{2})?)', s)]

def first_variable_product(op, host):
    """Pick a product from the shop page and read its variation form."""
    shop = get(op, f'https://{host}/shop/')
    links = re.findall(r'href="(https://[^"]+/product/[^"]+/)"', shop)
    seen = []
    for url in links:
        if url in seen:
            continue
        seen.append(url)
        pdp = get(op, url)
        m = re.search(r'data-product_variations="([^"]+)"', pdp)
        if not m:
            continue
        import html as h
        variations = json.loads(h.unescape(m.group(1)))
        pid = re.search(r'name="add-to-cart" value="(\d+)"', pdp)
        if not pid:
            pid = re.search(r'data-product_id="(\d+)"', pdp)
        if not pid:
            continue
        return url, int(pid.group(1)), variations, pdp
    return None, None, None, None

def add(op, host, product_id, var):
    data = {'add-to-cart': product_id, 'product_id': product_id,
            'variation_id': var['variation_id'], 'quantity': 1}
    for k, v in var['attributes'].items():
        data[k] = v
    return post(op, f'https://{host}/?add-to-cart={product_id}', data)

def report(brand):
    cfg = BRANDS[brand]
    host = cfg['host']
    op = session()
    url, pid, variations, pdp = first_variable_product(op, host)
    if not url:
        print(f'{brand}: FAIL, no variable product with a variation form found')
        return False
    var = sorted(variations, key=lambda v: float(v['display_price']))[0]
    print(f'{brand}: {url}')
    print(f'  product #{pid}, variation #{var["variation_id"]} at ${var["display_price"]}, '
          f'{var["attributes"]}')
    add(op, host, pid, var)
    cart = get(op, f'https://{host}/cart/')
    ct = text(cart)
    ok = True
    if 'your cart is currently empty' in ct.lower():
        print('  FAIL cart is empty after add to cart')
        return False
    price = float(var['display_price'])
    if f'${price:.2f}' not in ct and f'${price:,.2f}' not in ct:
        print(f'  FAIL cart does not show ${price:.2f}')
        ok = False
    else:
        print(f'  ok   cart shows the variation price ${price:.2f}')
    under_free = 'free shipping' in ct.lower()
    under_flat = f'${cfg["flat"]:.2f}' in ct
    if price < cfg['free_over']:
        if under_flat and not under_free:
            print(f'  ok   under ${cfg["free_over"]}, flat ${cfg["flat"]:.2f} offered, no free option')
        else:
            print(f'  FAIL under threshold: flat_shown={under_flat} free_shown={under_free}')
            ok = False
    # now push the cart over the free shipping threshold
    need = cfg['free_over'] - price
    qty = int(need // price) + 2
    post(op, f'https://{host}/cart/', {'cart[qty]': qty})
    add_more = add(op, host, pid, var)
    for _ in range(qty):
        add(op, host, pid, var)
    cart2 = text(get(op, f'https://{host}/cart/'))
    totals = money(cart2)
    over = max(totals) if totals else 0
    free_now = 'free shipping' in cart2.lower()
    flat_still = f'${cfg["flat"]:.2f}' in cart2
    if over >= cfg['free_over'] and free_now and not flat_still:
        print(f'  ok   over ${cfg["free_over"]} (cart ${over:.2f}), free shipping only')
    else:
        print(f'  FAIL over threshold: cart ${over:.2f} free={free_now} flat_still={flat_still}')
        ok = False
    checkout = text(get(op, f'https://{host}/checkout/'))
    has_form = 'billing' in checkout.lower() or 'place order' in checkout.lower()
    print(f'  {"ok  " if has_form else "FAIL"} checkout renders a real form')
    ok = ok and has_form
    return ok

if __name__ == '__main__':
    brands = sys.argv[1:] or list(BRANDS)
    results = {b: report(b) for b in brands}
    print()
    for b, r in results.items():
        print(f'{b}: {"PASS" if r else "FAIL"}')
    sys.exit(0 if all(results.values()) else 1)
