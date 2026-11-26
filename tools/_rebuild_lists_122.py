# -*- coding: utf-8 -*-
"""重建列表頁與專輯頁（num 122 新增後必須重跑）。

🔴 為何必須重建：
靜態站的文章列表頁（/articles/）、專輯總覽（/series/）、
各專輯頁（/series/youth-crossover/）都是 build_articles.py 產生的靜態頁，
不會自動讀到 posts.json 的新文章。只重建文章頁會導致首頁有連結、
專輯頁卻沒有——這正是本次發現的遺漏。
"""
import importlib.util as io_util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = io_util.spec_from_file_location('ba', os.path.join(ROOT, 'tools', 'build_articles.py'))
ba = io_util.module_from_spec(spec)
spec.loader.exec_module(ba)

ba.load_series()

data = json.load(open(os.path.join(ROOT, 'data', 'posts.json'), encoding='utf-8'))
posts = data['posts']
for p in posts:
    p['slug'] = ba.SLUGS.get(str(p.get('num', '')).strip(), '')

published = [p for p in posts if p.get('status') != '整理中']
print('已上線文章:', len(published))

r = ba.build_list(published)
print('build_list →', r)

nser = 0
for s in ba.sorted_series():
    res = ba.build_series_page(s, published, ba.SERIES['series'])
    if res:
        nser += 1
        # 回傳格式為 (路徑, 名稱, 篇數字串)，直接印原值避免格式錯誤
        print('  %s' % (res,))
print('重建專輯頁:', nser, '個')

ba.build_series_index(published)
print('build_series_index 完成')

# 驗證
print()
print('=== 驗證 ===')
checks = [
    ('articles/index.html', '/articles/'),
    ('series/index.html', '/series/'),
]
for f, url in checks:
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        h = open(p, encoding='utf-8').read()
        print('  %-24s 122:%s  禮儀不是形式:%s'
              % (f, 'YES' if 'etiquette-is-not-form' in h else 'NO',
                 'YES' if '禮儀不是形式' in h else 'NO'))

# 找 youth-crossover 專輯頁實際路徑
for s in ba.sorted_series():
    if s.get('id') == 'youth-crossover':
        print('  youth-crossover 專輯頁路徑:', s.get('dir') or s.get('id'))
        break