#!/usr/bin/env python3
"""Minimal DirectAdmin file API client for the two conversion accounts."""
import os, sys, subprocess, shlex, json

ENV = os.path.expanduser('~/.config/fmrex/da.env')

def env():
    out = {}
    for line in open(ENV):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out

E = env()
BRANDS = {
    'feathermoss': dict(user=E['FM_USER'], pw=E['FM_PASS'], domain='feathermoss.com', token=E['FM_TOKEN']),
    'rexjewelz':   dict(user=E['RX_USER'], pw=E['RX_PASS'], domain='rexjewelz.com',   token=E['RX_TOKEN']),
}
BASE = E['DA_BASE']
EDGE = '144.217.60.100'

def curl(args, timeout=300):
    p = subprocess.run(['curl', '-s', '-k', '--max-time', str(timeout)] + args,
                       capture_output=True, text=True)
    return p.stdout

def upload(brand, local, remote_name, subdir=''):
    b = BRANDS[brand]
    d = f"domains/{b['domain']}/public_html" + (('/' + subdir) if subdir else '')
    out = curl(['-u', f"{b['user']}:{b['pw']}", '-X', 'POST',
                f"{BASE}/api/filemanager-actions/upload?dir={d}&name={remote_name}&overwrite=true",
                '-F', f'file=@{local};type=application/octet-stream',
                '-w', '%{http_code}'])
    return out.strip()

def mkdir(brand, path):
    b = BRANDS[brand]
    d = f"domains/{b['domain']}/public_html"
    return curl(['-u', f"{b['user']}:{b['pw']}", '-X', 'POST', f"{BASE}/CMD_API_FILE_MANAGER",
                 '--data-urlencode', 'action=folder',
                 '--data-urlencode', f'path={d}/{path}']).strip()

def extract(brand, zip_rel, into_rel):
    b = BRANDS[brand]
    d = f"domains/{b['domain']}/public_html"
    return curl(['-u', f"{b['user']}:{b['pw']}", '-X', 'POST', f"{BASE}/CMD_API_FILE_MANAGER",
                 '--data-urlencode', 'action=extract',
                 '--data-urlencode', f'path={d}/{zip_rel}',
                 '--data-urlencode', f'directory={d}/{into_rel}',
                 '--data-urlencode', 'page=1']).strip()

def listdir(brand, rel=''):
    b = BRANDS[brand]
    d = f"domains/{b['domain']}/public_html" + (('/' + rel) if rel else '')
    raw = curl(['-u', f"{b['user']}:{b['pw']}", f"{BASE}/api/filemanager/list?path={d}&limit=500&offset=0"])
    try:
        j = json.loads(raw)
        return [(f['name'], f['type'], f['sizeBytes']) for f in j.get('files', [])]
    except Exception:
        return raw

def call(brand, script='_run.php', timeout=600, **params):
    b = BRANDS[brand]
    args = ['-A', 'Mozilla/5.0', '-H', 'Cache-Control: no-cache',
            '--resolve', f"{b['domain']}:443:{EDGE}", '-G', f"https://{b['domain']}/{script}",
            '--data-urlencode', f"k={b['token']}"]
    for k, v in params.items():
        args += ['--data-urlencode', f'{k}={v}']
    args += ['-w', '\n[http %{http_code}]']
    return curl(args, timeout=timeout)

def dns(brand):
    b = BRANDS[brand]
    return curl(['-u', f"{b['user']}:{b['pw']}", f"{BASE}/CMD_API_DNS_CONTROL?domain={b['domain']}"])

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'list':
        print(listdir(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ''))
    elif cmd == 'call':
        brand = sys.argv[2]
        kw = dict(a.split('=', 1) for a in sys.argv[3:])
        print(call(brand, **kw))
    elif cmd == 'dns':
        print(dns(sys.argv[2]))
