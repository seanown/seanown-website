# -*- coding: utf-8 -*-
"""把軒哥課堂《AI 的終局》收進 data/posts.json（num=143, slug=ai-zhongju）。

正文取 temp/ai-zhongju-body.md（由移交包獨立 HTML 逐段轉為站內 Markdown：
表格→GFM 表、拉引→blockquote、流程/時間軸/卡片→列表；文字全數保留）。
冪等：已存在 num=143 時先移除再重新寫入。
"""
import json
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PJ = os.path.join(ROOT, 'data', 'posts.json')
BODY_MD = os.path.join(ROOT, 'temp', 'ai-zhongju-body.md')

body = io.open(BODY_MD, encoding='utf-8').read().strip()

post = {
    'num': 143,
    'title': 'AI 的終局：平台只剩兩件事，泡沫在二〇三〇年見真章',
    'subtitle': '軒哥課堂 AI 系列：把 AI 當成一門生意來拆',
    'category': '軒哥課堂AI2026.10',
    'date': '2026-10-25',
    'location': '澳門',
    'status': '已上線',
    'images': ['assets/images/posts/143-cover.jpg'],
    'slug': 'ai-zhongju',
    'series': 'classroom-ai',
    'byline': '翁振軒 SEAN OWN ・ 龍遊集團創辦人 · 粵港澳大灣區電子商會會長',
    'keypoints': [
        'AI 的本質是撮合交易：目標明確的 APP 消費最先被 AI 助手取代，平台撮合層被拿走，外賣平台被剝到只剩即時配送網與 B 端 AI 運營兩件事。',
        '史上最大的技術革命與史上最大的泡沫並存：OpenAI 一年半估值翻五倍、達年化收入的七十一倍，資本轉向追求回報的節點約在二〇三〇年；懸空無實際業務的原生 AI 公司先死。',
        '巨頭最看好 Google（唯一全棧公司）；中國走 AI＋硬件路線；出海三要素＝曝光＋履約＋售後；創業勇氣第一、藍海多為偽需求，能在紅海活下來的人才配談藍海。',
    ],
    'lead': 'AI 的本質是撮合交易。當 AI 助手能直接比價、直連商家，目標明確的 APP 消費與平台撮合層將被取代；平台最後只剩即時配送網與 B 端 AI 運營兩件事。與此同時，人類正經歷史上最大的技術革命，也正經歷史上最大的泡沫——資本轉向回報的節點，大約在二〇三〇年。',
    'body': body,
}

d = json.load(io.open(PJ, encoding='utf-8'))
before = len(d['posts'])
d['posts'] = [p for p in d['posts'] if str(p.get('num')) != '143']
d['posts'].append(post)

with io.open(PJ, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write('\n')

print('posts.json 更新完成：%d -> %d 篇（num 143 已寫入，slug=ai-zhongju，body %d 字）'
      % (before, len(d['posts']), len(body)))
