# -*- coding: utf-8 -*-
"""《追兇記》(1965) 已上線後的「內文更新」——不改 num、不改 OG_VER、不改 SLUGS。

用途：補寫大三巴牌坊線索後，用 _draft_zhuixiongji-1965.md 重寫 data/posts.json 裡
該篇的 title/subtitle/body。海報 <img> 沿用 build_articles.py 目前的 OG_VER 現值。
"""
import json, io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
BUILD = os.path.join(ROOT, 'tools', 'build_articles.py')
DRAFT = os.path.join(ROOT, '_draft_zhuixiongji-1965.md')
SLUG = 'zhuixiongji-1965'

# --- OG_VER 讀現值（本次不進位，海報沒重出） ---
bsrc = io.open(BUILD, encoding='utf-8').read()
m = re.search(r"^OG_VER\s*=\s*'([^']+)'", bsrc, re.M)
assert m, 'build_articles.py 找不到 OG_VER'
OG_VER = m.group(1)
print('OG_VER（沿用不進位）:', OG_VER)

raw = io.open(DRAFT, encoding='utf-8').read().split('\n')
TITLE = raw[0].lstrip('# ').strip()
SUB = raw[2].replace('## 副標：', '').strip()
assert TITLE.startswith('《'), repr(TITLE)
assert '｜1965' in SUB, repr(SUB)

body = '\n'.join(raw[4:]).strip('\n')
assert body.count('![') == 0, '草稿含 markdown 圖片語法'
POSTER = ('<img src="../../assets/og/%s-poster.jpg?v=%s" '
          'alt="Trace of Murderer 1965 追兇記 電影海報" '
          'style="column-span:all;width:min(100%%,520px);display:block;'
          'margin:8px auto 28px;border-radius:10px">' % (SLUG, OG_VER))
body = POSTER + '\n\n' + body

data = json.load(io.open(POSTS, encoding='utf-8'))
posts = data['posts']
hit = [p for p in posts if p.get('slug') == SLUG]
assert len(hit) == 1, 'slug 命中 %d 筆（應為 1）' % len(hit)
p = hit[0]
old_len = len(p['body'])
p['title'] = TITLE
p['subtitle'] = SUB
p['body'] = body

json.dump(data, io.open(POSTS, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# --- 複核 ---
d2 = json.load(io.open(POSTS, encoding='utf-8'))
q = [x for x in d2['posts'] if x.get('slug') == SLUG][0]
print('更新：num=%s | %s' % (q['num'], SLUG))
print('body: %d -> %d chars（+%d）' % (old_len, len(q['body']), len(q['body']) - old_len))
print('TITLE:', q['title'], '| SUB:', q['subtitle'])
pub = sorted([x for x in d2['posts'] if x.get('series') == 'macau-film' and x.get('status') != '整理中'],
             key=lambda x: (x['date'], int(x['num'])))
idx = [int(x['num']) for x in pub].index(int(q['num'])) + 1
print('輯內序號：第 %d / %d 篇' % (idx, len(pub)))
