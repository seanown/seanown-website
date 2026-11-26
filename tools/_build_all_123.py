# -*- coding: utf-8 -*-
"""num 123 完整靜態產物生成（上次的教訓：一次做完清單，不要分兩次 commit）。

產出清單：
  1. 文章頁 article/{slug}/
  2. 文章列表 /articles/
  3. 各專輯頁 × 5（含 youth-crossover）
  4. 專輯總覽 /series/
  5. OG 圖
  6. 首頁 embedded-posts 副本
"""
import importlib.util as io_util
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = '123'
SLUG = 'leadership-and-crisis'
DECK_SRC = '商會幹部領導力'

spec = io_util.spec_from_file_location('ba', os.path.join(ROOT, 'tools', 'build_articles.py'))
ba = io_util.module_from_spec(spec)
spec.loader.exec_module(ba)
ba.load_series()

data = json.load(open(os.path.join(ROOT, 'data', 'posts.json'), encoding='utf-8'))
posts = data['posts']
for p in posts:
    p['slug'] = ba.SLUGS.get(str(p.get('num', '')).strip(), '')

target = [p for p in posts if str(p.get('num', '')).strip() == NUM][0]
print('目標: #%s %s' % (target['num'], target['title']))
print('slug: %r' % target['slug'])
assert target['slug'] == SLUG, 'SLUGS 映射不符'

published = [p for p in posts if p.get('status') != '整理中']
print('已上線: %d 篇' % len(published))

# ── 1. 文章頁 ──
print('\n[1/6] 文章頁')
ba.build(target, published)

# ── 2. 文章列表 ──
print('\n[2/6] 文章列表')
ba.build_list(published)

# ── 3. 各專輯頁 ──
print('\n[3/6] 專輯頁')
n = 0
for s in ba.sorted_series():          # sorted_series() 本身已排序，不可再套sorted()
    if ba.build_series_page(s, published, ba.SERIES['series']):
        n += 1
print('  重建 %d 個' % n)

# ── 4. 專輯總覽 ──
print('\n[4/6] 專輯總覽')
ba.build_series_index(published)

# ── 5. OG 圖 ──
print('\n[5/6] OG 圖')
spec2 = io_util.spec_from_file_location('og', os.path.join(ROOT, 'tools', 'build_og.py'))
og = io_util.module_from_spec(spec2)
spec2.loader.exec_module(og)
og.build(SLUG, target['title'], target['category'], target['date'])

# ── 6. 首頁 embedded 副本 ──
print('\n[6/6] 首頁 embedded 副本')
idx = os.path.join(ROOT, 'index.html')
html = open(idx, encoding='utf-8').read()
m = re.search(r'(<script type="application/json" id="embedded-posts">)([\s\S]*?)(</script>)', html)
blob = json.loads(m.group(2))
eps = blob['posts'] if isinstance(blob, dict) else blob
if any(str(x.get('num')) == NUM for x in eps):
    print('  已存在，跳過')
else:
    slim = {k: target[k] for k in ('num', 'title', 'category', 'date', 'slug', 'series', 'images')}
    eps.insert(0, slim)
    if len(eps) > 25:
        dropped = eps.pop()
        print('  擠掉: #%s %s' % (dropped.get('num'), dropped.get('title', '')[:22]))
    out = json.dumps({'posts': eps}, ensure_ascii=False, indent=2)
    bad = [c for c in out if ord(c) < 32 and c not in '\n\t']
    assert not bad, '含控制字元'
    open(idx, 'w', encoding='utf-8', newline='\n').write(
        html[:m.start()] + m.group(1) + out + m.group(3) + html[m.end():])
    print('  已加入，維持 25 篇')

# ── 放映版 ──
print('\n[附] 放映版')
dst = os.path.join(ROOT, 'slides', 'leadership-sop')
os.makedirs(os.path.join(dst, 'assets'), exist_ok=True)
import shutil
for f in os.listdir(os.path.join(ROOT, DECK_SRC)):
    if f == 'shots':
        continue
    s = os.path.join(ROOT, DECK_SRC, f)
    if os.path.isfile(s):
        shutil.copy2(s, os.path.join(dst, f))
    elif f == 'assets':
        for a in os.listdir(s):
            shutil.copy2(os.path.join(s, a), os.path.join(dst, 'assets', a))
print('  slides/leadership-sop/')

# ── 驗證 ──
print('\n=== 驗證 ===')
data2 = json.load(open(os.path.join(ROOT, 'data', 'posts.json'), encoding='utf-8'))
print('  posts.json: %d 篇' % len(data2['posts']))
checks = [
    ('article/%s/index.html' % SLUG, SLUG),
    ('articles/index.html', SLUG),
    ('series/youth-crossover/index.html', SLUG),
]
for f, k in checks:
    p = os.path.join(ROOT, f)
    ok = os.path.exists(p) and k in open(p, encoding='utf-8').read()
    print('  %-40s %s' % (f, 'OK' if ok else 'MISSING'))
for f in ['index.html', 'article/%s/index.html' % SLUG]:
    h = open(os.path.join(ROOT, f), encoding='utf-8', errors='ignore').read()
    b = re.findall(r'<script[^>]*application/json[^>]*>(.*?)</script>', h, re.S)
    for i, x in enumerate(b):
        json.loads(x.strip())
    h2 = re.sub(r'<script[\s\S]*?</script>', '', h)
    h2 = re.sub(r'<style[\s\S]*?</style>', '', h2)
    h2 = re.sub(r'<!--[\s\S]*?-->', '', h2)
    bad = []
    for t in ['div', 'section', 'a', 'p', 'h1', 'h2', 'ol', 'li', 'table', 'tr']:
        o = len(re.findall(r'<%s[\s>]' % t, h2)); c = len(re.findall(r'</%s>' % t, h2))
        if o != c: bad.append('%s %d/%d' % (t, o, c))
    print('  %-40s %s' % (f, 'JSON OK，標籤全平衡' if not bad else ' '.join(bad)))