# -*- coding: utf-8 -*-
"""《b420》(2005) 上線後的「內文更新」——不改 num、不改 SLUGS、不改 sitemap。

用途：軒哥指出版式問題（散場之後應在附錄之後）後，用 _draft_b420-2005.md
重寫 data/posts.json 裡該篇的 title/subtitle/body。
海報沒重出 → OG_VER 沿用 build_articles.py 現值（不進位）；
草稿 img 的 ?v= 由腳本自動改成現值，避免被並行線升版後對不上。

冪等：重複執行只會把同一份草稿再寫一次。
"""
import json, io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
BUILD = os.path.join(ROOT, 'tools', 'build_articles.py')
DRAFT = os.path.join(ROOT, '_draft_b420-2005.md')
SLUG = 'b420-2005'

# --- OG_VER 讀現值（本次不進位，海報沒重出） ---
bsrc = io.open(BUILD, encoding='utf-8').read()
m = re.search(r"^OG_VER\s*=\s*'([^']+)'", bsrc, re.M)
assert m, 'build_articles.py 找不到 OG_VER'
OG_VER = m.group(1)
print('OG_VER（沿用不進位）:', OG_VER)

raw = io.open(DRAFT, encoding='utf-8').read().split('\n')
TITLE = raw[2].lstrip('# ').strip()
SUB = raw[4].replace('## ', '').strip()
assert TITLE == '《b420》觀後感', repr(TITLE)
assert '｜2005' in SUB, repr(SUB)

body = '\n'.join(raw).strip('\n')
assert body.count('![') == 0, '草稿含 markdown 圖片語法（必須寫 HTML <img>）'
# 引句框兩行必須緊鄰
body = re.sub(r'(>\s*[^\n]*)\n\n(>\s*——)', r'\1\n\2', body)
# img 的 ?v= 一律對齊現行 OG_VER
body, n = re.subn(r'(' + SLUG + r'-poster\.jpg\?v=)[0-9a-zA-Z]+', r'\g<1>' + OG_VER, body)
assert n == 1, '海報 img 的 ?v= 替換次數異常：%d（應為 1）' % n

# 版式鐵律：散場之後必須在附錄之後
i_s, i_a = body.find('散場之後'), body.find('跟著電影遊澳門')
assert i_s > i_a > 0, '版式錯位：散場之後(%d) 應在附錄(%d) 之後' % (i_s, i_a)

data = json.load(io.open(POSTS, encoding='utf-8'))
hit = [p for p in data['posts'] if p.get('slug') == SLUG]
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
print('body: %d -> %d chars' % (old_len, len(q['body'])))
print('引句框:', q['body'].count('\n> '), '| 座標:', len(re.findall(r'22\.1\d{6}, ?113\.5\d{6}', q['body'])))
pub = sorted([x for x in d2['posts'] if x.get('series') == 'macau-film' and x.get('status') != '整理中'],
             key=lambda x: (x['date'], int(x['num'])))
idx = [int(x['num']) for x in pub].index(int(q['num'])) + 1
print('輯內序號：第 %d / %d 篇' % (idx, len(pub)))
