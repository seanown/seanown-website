# -*- coding: utf-8 -*-
"""《賭城大亨II之至尊無敵》已上線改稿：換切入角度（聶傲天／葉漢）。

⚠️ 已上線文章 ≠ 重跑 insert（會重複入庫）：按 slug 更新 title/subtitle/body，
   num／date／SLUGS 全不動；OG_VER 沿用現值（海報沒重出就不進位）。
🆕 {{PREV_COUNT}}：本篇已上線，故「本篇之前共有 N 篇」＝輯內序號 - 1。
"""
import json, io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
BUILD = os.path.join(ROOT, 'tools', 'build_articles.py')
DRAFT = os.path.join(ROOT, '_draft_casino-tycoon-2-1992.md')
SLUG = 'casino-tycoon-2-1992'

CN = '零一二三四五六七八九'


def cn(n):
    if n < 10:
        return CN[n]
    if n < 20:
        return '十' + (CN[n % 10] if n % 10 else '')
    if n < 100:
        return CN[n // 10] + '十' + (CN[n % 10] if n % 10 else '')
    if n < 1000:
        s = CN[n // 100] + '百'
        r = n % 100
        if r == 0:
            return s
        if r < 10:
            return s + '零' + CN[r]
        return s + cn(r)
    return str(n)


data = json.load(io.open(POSTS, encoding='utf-8'))
posts = data['posts']
hit = [p for p in posts if p.get('slug') == SLUG]
assert len(hit) == 1, '找不到 slug（或重複）：%d' % len(hit)
p = hit[0]
NUM = int(p['num'])

# --- 保留現有 body 的 OG_VER 與海報 img 行 ---
old_body = p.get('body', '')
m = re.search(r'\?v=([^&"\']+)', old_body)
assert m, '舊 body 找不到 ?v= 版本號'
OG_VER = m.group(1)
print('沿用 OG_VER =', OG_VER)

raw = io.open(DRAFT, encoding='utf-8').read().split('\n')
TITLE = raw[0].lstrip('# ').strip()
SUB = raw[2].replace('##', '').strip()
assert TITLE.startswith('《'), repr(TITLE)
assert '｜1992' in SUB, repr(SUB)

# --- 輯內序號現算：本篇已上線，故 PREV = 序號 - 1 ---
pub = sorted([x for x in posts if x.get('series') == 'macau-film' and x.get('status') != '整理中'],
             key=lambda x: (x['date'], int(x['num'])))
idx = [int(x['num']) for x in pub].index(NUM) + 1
PREV = idx - 1
PREV_CN = cn(PREV)
raw = [L.replace('{{PREV_COUNT}}', PREV_CN) for L in raw]
print('輯內第 %d / %d 篇 -> 佔位符填「%s」' % (idx, len(pub), PREV_CN))

body = '\n'.join(raw[4:]).strip('\n')
assert '{{PREV_COUNT}}' not in body, '仍有未替換的佔位符'
assert body.count('![') == 0, '草稿含 markdown 圖片語法'
assert body.find('散場之後') > body.find('跟著《賭城大亨II') > 0, '散場之後不在附錄之後'
assert '不在場' not in body, '又出現「不在場」框架'

POSTER = ('<img src="../../assets/og/%s-poster.jpg?v=%s" '
          'alt="Casino Tycoon II 1992 賭城大亨II之至尊無敵 電影海報" '
          'style="column-span:all;width:min(100%%,520px);display:block;'
          'margin:8px auto 28px;border-radius:10px">' % (SLUG, OG_VER))
body = POSTER + '\n\n' + body

p['title'] = TITLE
p['subtitle'] = SUB
p['body'] = body
json.dump(data, io.open(POSTS, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# 複核
d2 = json.load(io.open(POSTS, encoding='utf-8'))
q = [x for x in d2['posts'] if x.get('slug') == SLUG][0]
print('num 不變:', q['num'], '| date 不變:', q['date'])
print('body:', len(q['body']), 'chars')
print('TITLE:', q['title'])
print('SUB  :', q['subtitle'])
print('img ?v= 版本號（應只有一個）:', set(re.findall(r'\?v=([^&"\']+)', q['body'])))
