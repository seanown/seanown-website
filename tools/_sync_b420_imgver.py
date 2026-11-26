# -*- coding: utf-8 -*-
"""同步《b420》正文海報 img 的 ?v= 到 build_articles.py 現行 OG_VER。

用途：入庫後被並行線把 OG_VER 從 20261001a 升到 b，正文 img 仍停在舊值；
build_articles.py 只會套用 OG_VER 在頁面層，不會改 posts.json body 裡的 ?v=。
冪等：已對齊則不做任何改動。
"""
import json, re, os, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PJ = os.path.join(ROOT, 'data', 'posts.json')
BA = os.path.join(ROOT, 'tools', 'build_articles.py')
SLUG = 'b420-2005'

bsrc = io.open(BA, encoding='utf-8').read()
VER = re.search(r"^OG_VER\s*=\s*'([^']+)'", bsrc, re.M).group(1)
print('現行 OG_VER:', VER)

data = json.load(io.open(PJ, encoding='utf-8'))
hit = [p for p in data['posts'] if p.get('slug') == SLUG]
assert len(hit) == 1, 'slug 命中 %d 筆' % len(hit)
p = hit[0]

new_body, n = re.subn(r'(' + SLUG + r'-poster\.jpg\?v=)[0-9a-zA-Z]+', r'\g<1>' + VER, p['body'])
assert n == 1, '替換次數異常：%d' % n
if new_body == p['body']:
    print('已對齊，無需改動（冪等）')
else:
    old = re.search(SLUG + r'-poster\.jpg\?v=([0-9a-zA-Z]+)', p['body']).group(1)
    p['body'] = new_body
    json.dump(data, io.open(PJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('img ?v= %s -> %s' % (old, VER))

d2 = json.load(io.open(PJ, encoding='utf-8'))
q = [x for x in d2['posts'] if x.get('slug') == SLUG][0]
cur = re.search(SLUG + r'-poster\.jpg\?v=([0-9a-zA-Z]+)', q['body']).group(1)
assert cur == VER, '仍未對齊：%s != %s' % (cur, VER)
print('複核 OK：num=%s | ?v=%s | body %d chars' % (q['num'], cur, len(q['body'])))
