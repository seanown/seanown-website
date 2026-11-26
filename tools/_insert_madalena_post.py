# -*- coding: utf-8 -*-
"""《馬達・蓮娜》Madalena (2021) 入庫 data/posts.json。

⚠️ 併行 session 分鐘級佔號：num 當場 max+1 現算（不寫死期望值）。
⚠️ OG_VER 自動讀現值尾字母進位（不寫死）。
⚠️ SLUGS anchor 取字典末條（不寫死號碼）。
🆕 {{PREV_COUNT}} 佔位符：入庫那刻現算輯內已上線篇數，轉中文數字（67→六十七）。
"""
import json, io, os, re, ast

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
BUILD = os.path.join(ROOT, 'tools', 'build_articles.py')
DRAFT = os.path.join(ROOT, '_draft_madalena-2021.md')
SLUG = 'madalena-2021'

CN = '零一二三四五六七八九'


def cn(n):
    """1-999 轉中文數字（67 -> 六十七）。"""
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
assert '｜2021' in SUB, repr(SUB)

# --- 輯內已上線篇數現算，填佔位符 ---
PUB = [p for p in posts if p.get('series') == 'macau-film' and p.get('status') != '整理中']
PREV = len(PUB)
PREV_CN = cn(PREV)
raw = [L.replace('{{PREV_COUNT}}', PREV_CN) for L in raw]
print('輯內已上線 %d 篇 -> 佔位符填「%s」' % (PREV, PREV_CN))

body = '\n'.join(raw[4:]).strip('\n')
assert '{{PREV_COUNT}}' not in body, '仍有未替換的佔位符'
assert body.count('![') == 0, '草稿含 markdown 圖片語法'
POSTER = ('<img src="../../assets/og/%s-poster.jpg?v=%s" '
          'alt="Madalena 2021 馬達・蓮娜 電影海報" '
          'style="column-span:all;width:min(100%%,520px);display:block;'
          'margin:8px auto 28px;border-radius:10px">' % (SLUG, OG_VER))
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

# --- SLUGS 字典：追加到末條之後（anchor 不寫死號碼） ---
cand = re.findall(r"^(\s*)'(\d+)':\s*'([^']+)',\s*$", bsrc, re.M)
cand = [c for c in cand if c[0] == '    ']
assert cand, '找不到 SLUGS 條目'
last = cand[-1]
anchor = "%s'%s': '%s'," % (last[0], last[1], last[2])
assert bsrc.count(anchor) == 1, 'SLUGS anchor 不唯一'
bsrc = bsrc.replace(anchor, anchor + "\n    '%d': '%s'," % (NUM, SLUG), 1)
tree = ast.parse(bsrc)
keys = []
for node in ast.walk(tree):
    if isinstance(node, ast.Dict):
        for k in node.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str) and re.fullmatch(r'\d+', k.value):
                keys.append(k.value)
assert keys.count(str(NUM)) == 1, 'SLUGS 撞號: %s' % keys.count(str(NUM))
io.open(BUILD, 'w', encoding='utf-8').write(bsrc)
print('SLUGS 已追加 %r（anchor=%r，AST 驗過無重複）' % ("'%d': '%s'" % (NUM, SLUG), anchor))

# --- 複核 ---
d2 = json.load(io.open(POSTS, encoding='utf-8'))
q = [x for x in d2['posts'] if x.get('slug') == SLUG][0]
pub2 = sorted([x for x in d2['posts'] if x.get('series') == 'macau-film' and x.get('status') != '整理中'],
              key=lambda x: (x['date'], int(x['num'])))
idx = [int(x['num']) for x in pub2].index(NUM) + 1
print('入庫：num=%d | %s' % (NUM, SLUG))
print('body 長度:', len(q['body']), 'chars')
print('posts 篇數: %d -> %d' % (before, len(d2['posts'])))
print('輯內序號：第 %d / %d 篇' % (idx, len(pub2)))
print('TITLE:', q['title'], '| SUB:', q['subtitle'])
