# -*- coding: utf-8 -*-
"""把《科技無國界的迷夢：黃仁勳事件與中美 AI 生態分叉》收進 data/posts.json。

num=156 (int), slug=tech-no-borders-ai-split, series=classroom-ai（學 AI 子輯）。
正文取自 WORKBUDDY 任務整理/_body_156_觀察筆記.md（繁體原文，僅補章節標題與兩張插圖）。

冪等：已存在 num=156 時先移除再重新寫入。
防撞號：num 統一轉 int 取 max+1 並斷言 ==156；斷言 slug 未被佔用。
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PJ = os.path.join(ROOT, 'data', 'posts.json')
DRAFT = 'C:/Users/user/WorkBuddy/WORKBUDDY 任務整理/_body_156_觀察筆記.md'

body = io.open(DRAFT, encoding='utf-8').read().strip()

assert body.startswith('2026 年 11 月 12 日'), 'body 開頭不符'
assert '## 一、事件本身' in body, '缺少第一節'
assert '## 九、澳門坐標' in body, '缺少第九節'
assert '## 結語' in body and body.rstrip().endswith('修煉自己。'), '結語不符'
assert body.count('AI 示意圖') == 4, '示意圖圖註數量不符（應 2 圖 × alt+圖註）'
assert '![算力金融' in body and '![澳門河口' in body, '插圖語法不符'
assert '證据' not in body and '客户' not in body, '仍有簡體殘留'

d = json.load(io.open(PJ, encoding='utf-8'))
posts = d['posts']

nums = [int(p['num']) for p in posts if str(p.get('num', '')).isdigit()]
existing = [p for p in posts if str(p.get('num')) == '156']
if existing:
    # 更新模式：156 已存在（例如改正文後重跑），確認它沒有把編號往前推
    assert max(nums) == 156, '更新模式下最大編號不是 156，實得 %d' % max(nums)
    assert existing[0].get('slug') == 'tech-no-borders-ai-split', '既有 156 的 slug 不符'
else:
    # 首次新增模式
    assert max(nums) + 1 == 156, '編號不是 156，實得 %d' % (max(nums) + 1)
    assert 'tech-no-borders-ai-split' not in [p.get('slug') for p in posts], 'slug 已被佔用'

post = {
    'num': 156,
    'title': '科技無國界的迷夢：黃仁勳事件與中美 AI 生態分叉',
    'category': '',
    'date': '2026-11-20',
    'location': '澳門',
    'status': '已上線',
    'images': ['assets/images/posts/156-cover.jpg'],
    'body': body,
    'slug': 'tech-no-borders-ai-split',
    'series': 'classroom-ai',
    'subtitle': '一場創辦人閃辭，攤開了中美 AI 生態分叉的全局',
}

before = len(d['posts'])
d['posts'] = [p for p in d['posts'] if str(p.get('num')) != '156']
d['posts'].append(post)
if existing:
    assert len(d['posts']) == before, '更新模式篇數不應變化'
else:
    assert len(d['posts']) == before + 1, '篇數不對'

with io.open(PJ, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write('\n')

print('OK: %d -> %d 篇；num=156 (int)；slug=tech-no-borders-ai-split；'
      'series=classroom-ai；body %d 字' % (before, len(d['posts']), len(body)))
