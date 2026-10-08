# -*- coding: utf-8 -*-
"""把 num 122／123 的修正重新寫入 posts.json 並重建產物。

修正內容：移除讀者看不懂的內部術語
  - 「素材裡給了一個很好用的方法」→「這幾年我自己處理過幾次這種情況，累積出一個很好用的方法」
  - 「本堂金句」→「幾句值得記下來的話」
  - 「附錄：第三堂 · ...」→「附錄：...」（讀者不知道「第三堂」從哪來）
"""
import importlib.util as io_util
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')

TARGETS = [
    {'num': '121', 'slug': 'meeting-ends-things-begin',
     'src': 'drafts/108-高效會議主持SOP.md'},
    {'num': '122', 'slug': 'etiquette-is-not-form',
     'src': 'drafts/122-商務禮儀與典禮SOP.md'},
    {'num': '123', 'slug': 'leadership-and-crisis',
     'src': 'drafts/123-領導力傳承與危機管理.md'},
]

# 重用_add_post_*.py 裡已驗證的轉換器
import importlib.util as u1
spec = u1.spec_from_file_location('a122', os.path.join(ROOT, 'tools', '_add_post_122.py'))
a122 = u1.module_from_spec(spec); spec.loader.exec_module(a122)
md_to_html = a122.md_to_html

data = json.load(open(POSTS, encoding='utf-8'))
posts = data['posts']

for t in TARGETS:
    raw = open(os.path.join(ROOT, t['src']), encoding='utf-8').read()
    body_md = re.sub(r'^# .*\n+', '', raw)
    body_md = re.sub(r'^> (來源|適用)：.*\n?', '', body_md, flags=re.M)
    html = md_to_html(body_md)
    for p in posts:
        if str(p.get('num')) == t['num']:
            p['body'] = html
            print('%s → body 更新，淨字數 %d，<ol> %d'
                  % (t['num'], len(re.sub(r'<[^>]+>', '', re.sub(r'<table>[\s\S]*?</table>', '', html))),
                     html.count('<ol')))

with open(POSTS, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# ── 重建全部靜態產物 ──
spec2 = u1.spec_from_file_location('ba', os.path.join(ROOT, 'tools', 'build_articles.py'))
ba = u1.module_from_spec(spec2); spec2.loader.exec_module(ba)
ba.load_series()

data2 = json.load(open(POSTS, encoding='utf-8'))
posts2 = data2['posts']
for p in posts2:
    p['slug'] = ba.SLUGS.get(str(p.get('num', '')).strip(), '')
pub = [p for p in posts2 if p.get('status') != '整理中']

for t in TARGETS:
    tgt = [p for p in posts2 if str(p.get('num')) == t['num']][0]
    ba.build(tgt, pub)
    print('重建文章頁:', t['slug'])

ba.build_list(pub)
n = sum(1 for s in ba.sorted_series() if ba.build_series_page(s, pub, ba.SERIES['series']))
ba.build_series_index(pub)
print('列表頁＋%d 個專輯頁＋總覽 已重建' % n)

# ── 驗證 ──
print('\n=== 驗證術語已清除 ===')
bad_words = ['素材裡', '本堂金句', '附錄：第三堂', '附錄：第二堂']
for f in ['index.html', 'article/meeting-ends-things-begin/index.html',
          'article/etiquette-is-not-form/index.html',
          'article/leadership-and-crisis/index.html']:
    h = open(os.path.join(ROOT, f), encoding='utf-8', errors='ignore').read()
    hits = [w for w in bad_words if w in h]
    print('  %-44s %s' % (f, '乾淨' if not hits else '殘留 ' + str(hits)))

h = open(os.path.join(ROOT, 'index.html'), encoding='utf-8', errors='ignore').read()
for i, x in enumerate(re.findall(r'<script[^>]*application/json[^>]*>(.*?)</script>', h, re.S), 1):
    json.loads(x.strip())
print('  首頁 embedded JSON 解析 OK')

h2 = re.sub(r'<script[\s\S]*?</script>', '', h)
h2 = re.sub(r'<style[\s\S]*?</style>', '', h2)
h2 = re.sub(r'<!--[\s\S]*?-->', '', h2)
bad = []
for tag in ['div', 'section', 'a', 'p', 'ol', 'li', 'table', 'tr']:
    o = len(re.findall(r'<%s[\s>]' % tag, h2)); c = len(re.findall(r'</%s>' % tag, h2))
    if o != c: bad.append('%s %d/%d' % (tag, o, c))
print('  首頁標籤:', '全平衡' if not bad else ' '.join(bad))