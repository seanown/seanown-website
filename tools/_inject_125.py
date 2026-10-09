# -*- coding: utf-8 -*-
"""把轉好的繁體正文 + 中繼資料寫入 data/posts.json（num=125）。
格式與 build_articles.py 一致：ensure_ascii=False, indent=2, 結尾換行。
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
BODY = os.path.join(ROOT, 'tools', '_body_125.md')

body = io.open(BODY, encoding='utf-8').read().strip()

entry = {
    "num": 125,
    "title": "跟 Paulo Andrez 學天使投資",
    "subtitle": "第一堂 · 大象投資學｜零風險，不是天賦，是一門可以學習的紀律",
    "category": "生活隨筆",
    "date": "2026-10-09",
    "location": "澳門",
    "status": "已上線",
    "images": ["assets/images/posts/125-cover.jpg"],
    "slug": "paulo-andrez-angel-investing",
    "series": "youth-crossover",
    "byline": "翁振軒 SEAN(大象) ・ 龍遊集團創辦人",
    "keypoints": [
        "「零風險」不是天賦，是一門可以學習的紀律——靠學習、紀律、測試，把風險一層層鎖進你能控制的範圍。",
        "四層防線：鎖在資產上、驗在市場上、寫在條款裡、借政策之力；每一層都讓錢有東西托著。",
        "六個條款（清算優先權、歸屬、隨售、拖售、反稀釋、認股權證）是投資人的六道防線，談不下來的，錢再多也不投。"
    ],
    "lead": "有人說天使投資是九死一生的賭博；我說，真正懂的人、有經驗的人，可以做到零風險。這一堂，把 Paulo Andrez 的天使投資工具，熔進我自己的投資哲學。",
    "body": body,
}

data = json.load(io.open(POSTS, encoding='utf-8'))

# slug 唯一性檢查
slugs = {p.get('slug') for p in data['posts']}
nums = {str(p.get('num')) for p in data['posts']}
assert entry['slug'] not in slugs, 'slug 撞名：' + entry['slug']
assert str(entry['num']) not in nums, 'num 撞號：' + str(entry['num'])

data['posts'].append(entry)

io.open(POSTS, 'w', encoding='utf-8').write(
    json.dumps(data, ensure_ascii=False, indent=2) + '\n')

print('已寫入 num=125，總篇數：', len(data['posts']))
print('slug:', entry['slug'])
