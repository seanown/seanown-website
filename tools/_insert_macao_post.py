# -*- coding: utf-8 -*-
"""《Macao》(1952) 入庫 data/posts.json（num 當場現算，2026-09-30）。"""
import json, io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
DRAFT = os.path.join(ROOT, '_draft_macao-1952.md')
SLUG = 'macao-1952'
OG_VER = '20260930b'

data = json.load(io.open(POSTS, encoding='utf-8'))
posts = data['posts']

# --- 現算：不可照草稿檔名或印象 ---
maxnum = max(int(p['num']) for p in posts)
NUM = maxnum + 1
assert NUM == 72, 'max num 變了，重新確認=%d' % maxnum
assert not [p for p in posts if p.get('slug') == SLUG], 'slug 撞名'
assert not [p for p in posts if int(p['num']) == NUM], 'num 撞號'

raw = io.open(DRAFT, encoding='utf-8').read().split('\n')
title_line = raw[0]                      # # 《Macao》觀後感
sub_line = raw[2]                        # ## 副標：地球上一粒了不起的微粒｜1952
TITLE = title_line.lstrip('# ').strip()
SUB = sub_line.replace('## 副標：', '').strip()
assert TITLE.startswith('# 《') or TITLE.startswith('《'), repr(TITLE)
assert '｜1952' in SUB, repr(SUB)

body = '\n'.join(raw[4:]).strip('\n')

POSTER = ('<img src="../../assets/og/%s-poster.jpg?v=%s" alt="Macao 1952 電影海報" '
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

# --- 複核：輯內序號（排除 整理中）---
d2 = json.load(io.open(POSTS, encoding='utf-8'))
pub = sorted([p for p in d2['posts'] if p.get('series') == 'macau-film' and p.get('status') != '整理中'],
             key=lambda p: (p['date'], int(p['num'])))
idx = [int(p['num']) for p in pub].index(NUM) + 1
print('入庫：num=%d | %s | %s' % (NUM, SLUG, SUB))
print('body 長度:', len(body), 'chars')
print('posts 篇數: %d -> %d' % (before, len(d2['posts'])))
print('輯內序號：第 %d / %d 篇' % (idx, len(pub)))
print('TITLE:', TITLE)
