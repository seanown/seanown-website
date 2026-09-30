import json, re, sys, io, os

NUM = int(sys.argv[1])
SLUG = 'dragon-1993'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
D = '零一二三四五六七八九'
def cn(n):
    if n < 10: return D[n]
    if n < 20: return '十' + (D[n%10] if n%10 else '')
    if n < 100: return D[n//10] + '十' + (D[n%10] if n%10 else '')
    if n < 1000:
        s = D[n//100] + '百'; r = n % 100
        if r == 0: return s
        if r < 10: return s + '零' + D[r]
        return s + cn(r)
    return str(n)

# 1. OG_VER 自動進位
bp = 'tools/build_articles.py'
src = open(bp, encoding='utf-8').read()
cur = re.search(r"OG_VER\s*=\s*'([^']+)'", src).group(1)
new_v = cur[:-1] + chr(ord(cur[-1]) + 1)
if f"OG_VER = '{new_v}'" not in src:
    src = src.replace(f"OG_VER = '{cur}'", f"OG_VER = '{new_v}'", 1)
    open(bp, 'w', encoding='utf-8').write(src)
    print(f'OG_VER: {cur} -> {new_v}')
else:
    print(f'OG_VER 已是 {new_v}，跳過')

# 2. SLUGS
src = open(bp, encoding='utf-8').read()
if f"'{NUM}': '{SLUG}'" not in src:
    keys = re.findall(r"^\s*'(\d+)':\s*'([^']+)',", src, re.M)
    assert SLUG not in [v for _, v in keys], 'slug 重複!'
    assert str(NUM) not in [k for k, _ in keys], f'num {NUM} 已被佔用!'
    last = keys[-1]
    anchor = f"'{last[0]}': '{last[1]}',"
    src = src.replace(anchor, anchor + f"\n    '{NUM}': '{SLUG}',", 1)
    open(bp, 'w', encoding='utf-8').write(src)
    print(f"SLUGS 已加 '{NUM}': '{SLUG}'")
else:
    print('SLUGS 已存在，跳過')

# 3. posts.json
d = json.load(open('data/posts.json', encoding='utf-8'))
posts = d['posts']
if any(str(p.get('num')) == str(NUM) or p.get('slug') == SLUG for p in posts):
    print('posts.json 已存在本篇，跳過')
else:
    t = open('_draft_李小龍傳.md', encoding='utf-8').read().splitlines()
    body = '\n'.join(l for i, l in enumerate(t) if i not in (0, 1, 2, 3)).strip()
    mf = [p for p in posts if p.get('series') == 'macau-film' and p.get('status') == '已上線']
    seq = len(mf) + 1
    c = cn(seq)
    n_before = body.count('{{PREV_COUNT}}')
    body = body.replace('{{PREV_COUNT}}', c)
    print(f'輯內篇號 = {seq}（第{c}篇），替換 {n_before} 處')

    IMG = ('<img src="../../assets/og/dragon-1993-poster.jpg?v=' + new_v + '" '
           'alt="Dragon The Bruce Lee Story 1993 電影海報" '
           'style="column-span:all;width:min(100%,520px);display:block;margin:8px auto 28px;border-radius:10px">')
    body = IMG + '\n\n' + body
    entry = {
        'num': NUM,
        'title': '《李小龍傳》觀後感',
        'subtitle': '香港最熱鬧的那一夜，是澳門借給它的｜1993',
        'slug': SLUG,
        'series': 'macau-film',
        'category': '影評',
        'date': '2026-09-30',
        'location': '澳門',
        'status': '已上線',
        'images': ['assets/og/dragon-1993.jpg'],
        'body': body,
    }
    posts.append(entry)
    with io.open('data/posts.json', 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'posts.json 已加入 num={NUM} slug={SLUG}')
    print('篇號檢查 — 第八十篇:', f'第八十篇' in body, '| 佔位殘留:', '{{PREV_COUNT}}' in body)
