# -*- coding: utf-8 -*-
"""把 num 122 加入首頁 embedded-posts 副本，並擠掉最後一篇維持25 篇。

🔴 為何需要這一步：
posts.json 是資料源，但index.html 內還有一份 embedded 副本（fetch 失敗時的 fallback），
2026-10-08 曾因漏改這份導致「330%」文案殘留上線。靜態站同一內容有多份副本，必須同步。

🔴 JSON 安全：
embedded 區塊內不能有裸控制字元（含真換行），否則整個區塊 parse 失敗、
首頁文章列表全空（2026-09-03 曾因此空白一週）。所以用 json.dumps 輸出而非字串拼接。
"""
import json
import re

P = 'index.html'
NUM = '122'
LIMIT = 25

html = open(P, encoding='utf-8').read()
m = re.search(
    r'(<script type="application/json" id="embedded-posts">)([\s\S]*?)(</script>)', html)
if not m:
    raise SystemExit('!! 找不到 embedded-posts 區塊')

head, blob, tail = m.groups()
data = json.loads(blob)          # 先解析，若失敗代表原檔已壞
posts = data['posts'] if isinstance(data, dict) else data
print('原 embedded posts:', len(posts))

# 讀資料源拿 122
src = json.load(open('data/posts.json', encoding='utf-8'))['posts']
mine = [p for p in src if str(p.get('num')) == NUM][0]

# 精簡欄位，避免整篇 body 塞進首頁（首頁只需列表資訊）
slim = {
    'num': mine['num'],
    'title': mine['title'],
    'category': mine['category'],
    'date': mine['date'],
    'slug': mine['slug'],
    'series': mine.get('series', ''),
    'images': mine.get('images', []),
}

if any(str(p.get('num')) == NUM for p in posts):
    print('已存在，跳過')
else:
    posts.insert(0, slim)
    if len(posts) > LIMIT:
        dropped = posts.pop()
        print('擠掉:', dropped.get('num'), dropped.get('title', '')[:24])
    print('加入後:', len(posts))

out = json.dumps({'posts': posts}, ensure_ascii=False, indent=2)
# 🔴 保險：確認輸出不含裸控制字元
bad = [c for c in out if ord(c) < 32 and c not in '\n\t']
assert not bad, '輸出含控制字元 %r' % bad[:5]

new_html = html[:m.start()] + head + out + tail + html[m.end():]
open(P, 'w', encoding='utf-8', newline='\n').write(new_html)

# 重新驗證
h2 = open(P, encoding='utf-8').read()
m2 = re.search(r'<script type="application/json" id="embedded-posts">([\s\S]*?)</script>', h2)
d2 = json.loads(m2.group(1))
p2 = d2['posts']
print('驗證重新解析: OK')
print('  posts 數:', len(p2))
print('  含 122:', any(str(p.get('num')) == NUM for p in p2))
print('  第一篇:', p2[0].get('title', '')[:30])