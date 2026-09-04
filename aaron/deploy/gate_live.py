#!/usr/bin/env python3
"""Run the structural gate against the live hosting before public DNS exists.

Both domains are delegated to nameservers that have no zone yet, so nothing resolves.
The origin answers correctly on the EasWrk edge, so resolve the two hostnames here
rather than editing /etc/hosts, and skip cert checks because the edge still presents
its own *.easwrk.net certificate until Let's Encrypt can run.
"""
import os, socket, ssl, sys

EDGE = '144.217.60.100'
MAP = {'feathermoss.com': EDGE, 'www.feathermoss.com': EDGE,
       'rexjewelz.com': EDGE, 'www.rexjewelz.com': EDGE}

_real = socket.getaddrinfo
def _patched(host, port, *a, **kw):
    return _real(MAP.get(host, host), port, *a, **kw)
socket.getaddrinfo = _patched
ssl._create_default_https_context = ssl._create_unverified_context

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
sys.argv = ['verify_structural_diff.py'] + sys.argv[1:]
exec(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'tools', 'verify_structural_diff.py')).read(),
     {'__name__': '__main__', '__file__': os.path.join(
         os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', 'verify_structural_diff.py')})
