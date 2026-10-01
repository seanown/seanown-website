#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""將 tools/inferred_scenes_draft.json 寫入 data/posts.json：
- 設定 movieInfo.scenesLabel + macauScenes（推論補充）
- 對 9 部有結構化「跟著電影遊澳門」附錄者，從影評 body 移除該附錄（避免與電影資訊頁重複）
- dan-shen-nan-nv / jin-zhi-yu-ye-1959 / cleopatra-jones 三段影評正文為散文中場景，保留 body 不刪
不改 git、不 build，僅更新 posts.json。"""
import json, re, shutil
from pathlib import Path

POSTS_PATH = Path('data/posts.json')
full = json.loads(POSTS_PATH.read_text(encoding='utf-8'))
posts = full['posts']
draft = json.load(open('tools/inferred_scenes_draft.json', encoding='utf-8'))

KEEP_BODY = {'dan-shen-nan-nv', 'jin-zhi-yu-ye-1959', 'cleopatra-jones-casino-of-gold-1975'}
COORD = r'(\d{2}\.\d+,\s*\d{3}\.\d*)'

def find_bounds(body):
    starts = []
    for kw in ['跟著電影遊澳門', '### 一、主場景', '一、主場景', '主場景（核心打卡）']:
        i = body.find(kw)
        if i >= 0:
            starts.append(i)
    s = min(starts) if starts else -1
    if s < 0:
        m = re.search(COORD, body)
        if m:
            pre = body[:m.start()]
            hi = pre.rfind('\n## ')
            s = hi + 1 if hi >= 0 else max(0, m.start() - 250)
    if s < 0:
        s = 0
    # 結尾：附錄之後的第一個「散場之後」所在行行首（搜尋從 s 之後開始）
    idx = body.find('散場之後', s + 1)
    if idx >= 0:
        nl = body.rfind('\n', 0, idx)
        e = nl + 1 if nl >= 0 else idx
    else:
        e = len(body)
    return s, e

shutil.copy(POSTS_PATH, POSTS_PATH.with_suffix('.json.bak_inferred'))

for slug in draft:
    p = next(x for x in posts if x['slug'] == slug)
    mi = p.setdefault('movieInfo', {})
    mi['scenesLabel'] = draft[slug]['scenesLabel']
    mi['macauScenes'] = draft[slug]['macauScenes']
    if slug not in KEEP_BODY:
        body = p['body']
        s, e = find_bounds(body)
        if s > 0 and e > 0:
            head = body[:s].rstrip()
            while head.endswith('---'):
                head = head[:-3].rstrip()
            p['body'] = head + '\n\n' + body[e:]
            print('移除附錄: %s  (%d -> %d 字)' % (slug, len(body), len(p['body'])))
        else:
            print('跳過移除(未偵測到附錄):', slug)
    else:
        print('保留 body(散文場景):', slug)

full['posts'] = posts
POSTS_PATH.write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding='utf-8')
print('posts.json 已更新')
