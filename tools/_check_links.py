# -*- coding: utf-8 -*-
"""全站链接存在性检查：绝对 + 相对链接均按页面目录解析后验目标。"""
import os, re, posixpath, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES = ('article', 'series', 'collection', 'route')
SITE_HOST = 'https://seanown.org'  # 自家域名的绝对 URL 也按站内路径检查

pages = set()
for base in BASES:
    d = os.path.join(ROOT, base)
    if not os.path.isdir(d):
        continue
    for name in os.listdir(d):
        if os.path.isfile(os.path.join(d, name, 'index.html')):
            pages.add('/%s/%s/' % (base, name))
pages.add('/')


class A(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for k, v in attrs:
                if k == 'href' and v:
                    self.links.append(v)


def exists(t):
    """t 为剥掉 query/fragment 的站内路径；页目录 or 文件都要查。"""
    if t in pages:
        return True
    for cand in (ROOT + t, ROOT + t + 'index.html'):
        if os.path.isfile(cand):
            return True
    if os.path.isdir(ROOT + t):
        return True
    return False


bad = []
checked = 0
scanned = 0
for base in BASES:
    d = os.path.join(ROOT, base)
    if not os.path.isdir(d):
        continue
    for name in sorted(os.listdir(d)):
        fp = os.path.join(d, name, 'index.html')
        if not os.path.isfile(fp):
            continue
        scanned += 1
        html = open(fp, encoding='utf-8').read()
        html = re.sub(r'<script[\s\S]*?</script>', '', html)
        parser = A()
        parser.feed(html)
        page_dir = '/%s/%s/' % (base, name)
        for href in parser.links:
            if href.startswith((SITE_HOST + '/', SITE_HOST)):
                href = href[len(SITE_HOST):] or '/'
            if href.startswith(('http://', 'https://', 'mailto:', '#', 'tel:', 'data:')):
                continue
            if href.startswith('/'):
                t = href.split('?')[0].split('#')[0]
                if not t.endswith('/') and '.' not in t.rsplit('/', 1)[-1]:
                    t += '/'
            else:
                t = posixpath.normpath(posixpath.join(page_dir, href.split('?')[0].split('#')[0]))
                if not t.endswith('/') and '.' not in t.rsplit('/', 1)[-1]:
                    t += '/'
            checked += 1
            if not exists(t):
                bad.append((page_dir, href, t))

print('scanned pages:', scanned)
print('checked links:', checked)
print('bad:', len(bad))
for p, h, t in bad[:30]:
    print('  %s -> %s   (resolved %s)' % (p, h, t))
