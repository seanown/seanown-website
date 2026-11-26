# -*- coding: utf-8 -*-
"""《追兇記》Trace of Murderer (1965) 入庫 data/posts.json。

⚠️ 併行 session 分鐘級佔號：num 當場 max+1 現算（不寫死期望值）。
⚠️ OG_VER 自動讀現值尾字母進位（不寫死）。
"""
import json, io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
BUILD = os.path.join(ROOT, 'tools', 'build_articles.py')
DRAFT = os.path.join(ROOT, '_draft_zhuixiongji-1965.md')
SLUG = 'zhuixiongji-1965'

# --- OG_VER 自動讀現值並尾字母進位 ---
bsrc = io.open(BUILD, encoding='utf-8').read()
m = re.search(r"^OG_VER\s*=\s*'([^']+)'", bsrc, re.M)
assert m, 'build_articles.py 找不到 OG_VER'
prev = m.group(1)
mm = re.match(r'^(.*?)([a-z]+)$', prev)
tail = mm.group(2)
nx = chr(ord(tail[-1]) + 1) if tail[-1] != 'z' else 'aa'
OG_VER = mm.group(1) + (tail[:-1] + nx if len(tail) > 1 else nx)
print('OG_VER: %s -> %s' % (prev, OG_VER))

data = json.load(io.open(POSTS, encoding='utf-8'))
posts = data['posts']

# --- num 當場現算 ---
maxnum = max(int(p['num']) for p in posts)
NUM = maxnum + 1
assert not [p for p in posts if p.get('slug') == SLUG], 'slug 撞名'
assert not [p for p in posts if int(p['num']) == NUM], 'num 撞號'
print('現算 max num=%d -> NUM=%d' % (maxnum, NUM))

raw = io.open(DRAFT, encoding='utf-8').read().split('\n')
TITLE = raw[0].lstrip('# ').strip()
SUB = raw[2].replace('## 副標：', '').strip()
assert TITLE.startswith('《'), repr(TITLE)
assert '｜1965' in SUB, repr(SUB)

body = '\n'.join(raw[4:]).strip('\n')
POSTER = ('<img src="../../assets/og/%s-poster.jpg?v=%s" '
          'alt="Trace of Murderer 1965 追兇記 電影海報" '
          'style="column-span:all;width:min(100%%,520px);display:block;'
          'margin:8px auto 28px;border-radius:10px">' % (SLUG, OG_VER))
assert body.count('![') == 0, '草稿含 markdown 圖片語法'
body = POSTER + '\n\n' + body

entry = {
    'num': NUM,
    'title': TITLE,
    'subtitle': SUB,
    'slug': SLUG,
    'series': 'macau-film',
    'category': '影評',
    'date': '2026-09-30',
    'location': '澳門',
    'status': '已上線',
    'images': ['assets/og/%s.jpg' % SLUG],
    'body': body,
}

before = len(posts)
posts.append(entry)
json.dump(data, io.open(POSTS, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# --- SLUGS 字典：追加到末尾字典最後一條之後 ---
anchor = "'94': 'vengeance-2009',"
assert anchor in bsrc, 'build_articles.py 找不到 SLUGS anchor'
add = "%s\n    '%d': '%s',\n" % (anchor, NUM, SLUG)
bsrc = bsrc.replace(anchor, add, 1)
# 撞號檢查：解析一次語法並查重複 key
import ast
tree = ast.parse(bsrc)
keys = []
for node in ast.walk(tree):
    if isinstance(node, ast.Dict):
        for k in node.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str) and re.fullmatch(r'\d+', k.value):
                keys.append(k.value)
assert keys.count(str(NUM)) == 1, 'SLUGS 撞號: %s' % keys.count(str(NUM))
io.open(BUILD, 'w', encoding='utf-8').write(bsrc)
print('SLUGS 已追加 %r（AST 驗過、無重複 key）' % ("'%d': '%s'" % (NUM, SLUG)))

# --- 複核：輯內序號 ---
d2 = json.load(io.open(POSTS, encoding='utf-8'))
pub = sorted([p for p in d2['posts'] if p.get('series') == 'macau-film' and p.get('status') != '整理中'],
             key=lambda p: (p['date'], int(p['num'])))
idx = [int(p['num']) for p in pub].index(NUM) + 1
print('入庫：num=%d | %s | %s' % (NUM, SLUG, SUB))
print('body 長度:', len(body), 'chars')
print('posts 篇數: %d -> %d' % (before, len(d2['posts'])))
print('輯內序號：第 %d / %d 篇' % (idx, len(pub)))
print('TITLE:', TITLE)
