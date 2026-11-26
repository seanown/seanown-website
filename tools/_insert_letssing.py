import json, re, sys, io, os

NUM = int(sys.argv[1])
SLUG = 'lets-sing-2021'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# ---------- 1. OG_VER 自動讀現值並尾字母進位 ----------
bp = 'tools/build_articles.py'
src = open(bp, encoding='utf-8').read()
cur = re.search(r"OG_VER\s*=\s*'([^']+)'", src).group(1)
if cur.endswith('z'):
    new_v = cur[:-1] + 'a' + 'a'
else:
    new_v = cur[:-1] + chr(ord(cur[-1]) + 1)
if new_v == cur:
    raise SystemExit('OG_VER 進位失敗: ' + cur)
if f"OG_VER = '{new_v}'" not in src:
    src = src.replace(f"OG_VER = '{cur}'", f"OG_VER = '{new_v}'", 1)
    open(bp, 'w', encoding='utf-8').write(src)
    print(f'OG_VER: {cur} -> {new_v}')
else:
    print(f'OG_VER 已是 {new_v}，跳過')

# ---------- 2. SLUGS ----------
src = open(bp, encoding='utf-8').read()
if f"'{NUM}': '{SLUG}'" not in src:
    keys = re.findall(r"^\s*'(\d+)':\s*'([^']+)',", src, re.M)
    assert SLUG not in [v for _, v in keys], 'slug 重複!'
    assert str(NUM) not in [k for k, _ in keys], f'num {NUM} 已被佔用!'
    last = keys[-1]
    anchor = f"'{last[0]}': '{last[1]}',"
    src = src.replace(anchor, anchor + f"\n    '{NUM}': '{SLUG}',", 1)
    open(bp, 'w', encoding='utf-8').write(src)
    print(f"SLUGS 已加 '{NUM}': '{SLUG}'（插在 {anchor} 後）")
else:
    print('SLUGS 已存在，跳過')

# ---------- 3. posts.json ----------
raw = open('data/posts.json', encoding='utf-8').read()
d = json.loads(raw)
posts = d['posts']
if any(str(p.get('num')) == str(NUM) or p.get('slug') == SLUG for p in posts):
    print('posts.json 已存在本篇，跳過')
else:
    t = open('_draft_熱唱吧.md', encoding='utf-8').read().splitlines()
    # 去標題行與副標行
    body_lines = [l for i, l in enumerate(t) if i not in (0, 1, 2, 3)]
    body = '\n'.join(body_lines).strip()
    # 篇號：本篇 = 輯內已上線篇數 + 1
    mf = [p for p in posts if p.get('series') == 'macau-film' and p.get('status') == '已上線']
    seq = len(mf) + 1
    CN = {66: '六十六', 67: '六十七', 70: '七十', 71: '七十一', 72: '七十二'}
    cn = CN.get(seq)
    assert cn, f'篇號 {seq} 未在對應表，請補 CN'
    n_before = body.count('第六十七篇')
    body = body.replace('第六十七篇', f'第{cn}篇')
    print(f'輯內篇號 = {seq}（第{cn}篇），替換 {n_before} 處')

    IMG = ('<img src="../../assets/og/lets-sing-2021-poster.jpg?v=' + new_v + '" '
           'alt="Let\'s Sing 2021 電影海報" '
           'style="column-span:all;width:min(100%,520px);display:block;margin:8px auto 28px;border-radius:10px">')
    body = IMG + '\n\n' + body

    sub = '寫到第' + cn + '篇，終於輪到澳門人自己拍澳門｜2021'
    entry = {
        'num': NUM,
        'title': '《熱唱吧》觀後感',
        'subtitle': sub,
        'slug': SLUG,
        'series': 'macau-film',
        'category': '影評',
        'date': '2026-09-30',
        'location': '澳門',
        'status': '已上線',
        'images': ['assets/og/lets-sing-2021.jpg'],
        'body': body,
    }
    posts.append(entry)
    with io.open('data/posts.json', 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'posts.json 已加入 num={NUM} slug={SLUG}；副標={sub}')
