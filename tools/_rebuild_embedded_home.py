#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重建首頁 embedded-posts 精選副本，並把 category 換成 seriesName（專輯名）。

🔴 為何需要這一步：
posts.json 是資料源，但 index.html 內還有一份 embedded 副本（fetch 失敗時的 fallback）。
2026-10-10 廢除分類體系時實測發現這份副本已嚴重過時——22 篇 series 為 null、
#123 的 series 缺 macau-reader、#125 根本不在其中。副本不同步＝首頁顯示舊資料。

🔴 JSON 安全：
embedded 區塊內不能有裸控制字元（含真換行），否則整個區塊 parse 失敗、
首頁文章列表全空（2026-09-03 曾因此空白一週）。所以用 json.dumps 輸出而非字串拼接。

精選規則（維持原本語意）：
  取最新 25 篇，但固定保留 #124（龍遊返鄉，軒哥指定的代表作）與 #125（大象投資第一堂）。
"""
import io, json, os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, 'index.html')
POSTS = os.path.join(ROOT, 'data', 'posts.json')
SERIES = os.path.join(ROOT, 'data', 'series.json')

LIMIT = 25
KEEP = {'124', '125'}          # 軒哥指定保留的代表作

html = io.open(IDX, encoding='utf-8').read()
m = re.search(
    r'(<script type="application/json" id="embedded-posts">)([\s\S]*?)(</script>)', html)
if not m:
    raise SystemExit('!! 找不到 embedded-posts 區塊')
head, blob, tail = m.groups()

# 先確認原檔能 parse（若這裡就壞，代表首頁現在是空的）
try:
    data = json.loads(blob)
except Exception as e:
    raise SystemExit('!! 原 embedded 區塊 parse 失敗：%s' % e)
old = data['posts'] if isinstance(data, dict) else data
print('原 embedded posts:', len(old))

S = json.load(io.open(SERIES, encoding='utf-8'))
name = {x['id']: (x.get('name') or x.get('title')) for x in S.get('series', [])}
P = json.load(io.open(POSTS, encoding='utf-8'))
posts_all = P['posts'] if isinstance(P, dict) else P

# 挑選：先取 KEEP，再依日期補到 LIMIT
def num(p):
    return str(p.get('num') or '')

pool = [p for p in posts_all if p.get('status') != '整理中']
pool.sort(key=lambda p: (str(p.get('date') or ''), num(p)), reverse=True)
picked, seen = [], set()
for p in pool:
    n = num(p)
    if n in KEEP and n not in seen:
        picked.append(p); seen.add(n)
rest = [p for p in pool if num(p) not in KEEP]
for p in rest:
    if len(picked) >= LIMIT:
        break
    picked.append(p)

# 依日期降序（與首頁呈現一致）
picked.sort(key=lambda p: (str(p.get('date') or ''), num(p)), reverse=True)

FIELDS = ('num', 'title', 'date', 'slug', 'series', 'images')
out = []
for p in picked:
    s = p.get('series')
    s = s if isinstance(s, list) else ([s] if s else [])
    it = {k: p.get(k) for k in FIELDS if k in p}
    it['num'] = p.get('num')
    it['series'] = s[0] if s else ''          # 首頁只需一個專輯名做標籤
    it['seriesName'] = name.get(s[0], '') if s else ''
    out.append(it)

new = {'posts': out}
# 🔴 只替換 JSON 區塊本體，head/tail 原封不動。
#    2026-10-10 踩過：用 head+blob+tail 整段 replace，若 blob 的 regex 抓取範圍
#    與實際寫入不一致，會把整份 index.html 的其他 script 一起吞掉（render 函式消失）。
new_blob = json.dumps(new, ensure_ascii=False, indent=2)
html = html[:m.start(2)] + new_blob + html[m.end(2):]
io.open(IDX, 'w', encoding='utf-8', newline='\n').write(html)

# ── 驗證 ──
chk = re.search(r'id="embedded-posts">([\s\S]*?)</script>', html).group(1)
v = json.loads(chk)['posts']
print('新 embedded posts:', len(v))
print('含 category 欄位:', sum(1 for x in v if 'category' in x))
print('有 seriesName:', sum(1 for x in v if x.get('seriesName')))
print('保留代表作:', [x['num'] for x in v if str(x['num']) in KEEP])
print('無 series 的篇數:', sum(1 for x in v if not x.get('seriesName')))
print('前 6 篇：')
for x in v[:6]:
    print('   #%s %s  %s' % (x['num'], x.get('date'), x.get('seriesName') or '(無)'))