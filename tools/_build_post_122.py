# -*- coding: utf-8 -*-
"""單篇生成 num 122 的靜態文章頁。

🔴 為何不能直接跑 tools/build_articles.py：
   它是全量的，會重建全部 109 篇文章頁，覆蓋其他 108 篇（已踩過坑）。
   且 main() 裡 `p['slug'] = SLUGS.get(num,'')` 會用映射表覆蓋 slug，
   直接呼叫 build() 必須先load_series() 並補齊 SLUGS，否則 slug 會被清空。
"""
import importlib.util as io_util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = io_util.spec_from_file_location('ba', os.path.join(ROOT, 'tools', 'build_articles.py'))
ba = io_util.module_from_spec(spec)
spec.loader.exec_module(ba)

# 1. 先載入 SLUGS 與 SERIES（build 依賴它們）
ba.load_series()

# 2. 讀資料
POSTS = os.path.join(ROOT, 'data', 'posts.json')
data = json.load(open(POSTS, encoding='utf-8'))
posts = data['posts']

# 3. 依 main() 的方式補 slug
for p in posts:
    p['slug'] = ba.SLUGS.get(str(p.get('num', '')).strip(), '')

# 4. 找出 122，只生成這一篇
target = None
for p in posts:
    if str(p.get('num', '')).strip() == '122':
        target = p
        break

if not target:
    print('!! 找不到 num 122')
    raise SystemExit(1)

print('目標文章: #%s %s' % (target['num'], target['title']))
print('slug 對應: %r' % target['slug'])

if not target['slug']:
    print('!! SLUGS 映射表沒有 122 → 需要在 build_articles.py 的 SLUGS 補一筆')
    raise SystemExit(1)

published = [p for p in posts if p.get('status') != '整理中']
ret = ba.build(target, published)
print('build() 回傳: %r' % (ret,))

# 5. 驗證產物
out = os.path.join(ROOT, 'article', target['slug'], 'index.html')
if os.path.exists(out):
    size = os.path.getsize(out)
    html = open(out, encoding='utf-8').read()
    print('產物: %s  (%.0f KB)' % (out, size / 1024))
    for k in ['禮儀不是形式', '右為尊', '121', '122', 'keypoints', 'deck']:
        print('  包含「%s」: %s' % (k, 'YES' if k in html else 'NO'))
else:
    print('產物不存在:', out)