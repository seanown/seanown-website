# -*- coding: utf-8 -*-
"""翁振軒風格量化檢查（只驗正文，不驗附錄表格）。

鐵律：平均句長 ≥40、短句 <20 字佔比 <15%、零 emoji、零 Markdown 條列、零簡體字。
"""
import io, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'drafts', '108-高效會議主持SOP.md')

s = io.open(P, encoding='utf-8').read()
body = s.split('## 附錄')[0]          # 附錄是表格化 SOP，不納入句型統計

t = re.sub(r'[#*>\-|' + chr(96) + r'\n]', '', body)
cn = re.findall(r'[\u4e00-\u9fff]', t)
sents = [x for x in re.split(r'[。！？]', t) if len(re.findall(r'[\u4e00-\u9fff]', x)) > 3]
L = [len(re.findall(r'[\u4e00-\u9fff]', x)) for x in sents]
avg = sum(L) / len(L)
short = sum(1 for x in L if x < 20) / len(L) * 100
emo = len(re.findall(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]', s))
bul = len(re.findall(r'^\s*[-*]\s', body, re.M)) + len(re.findall(r'^\s*\d+\.\s', body, re.M))
SIMP = set('会议这个们时后里说过还没无为产业发经济万与东车马门问间闻风飞长张图书华')
simp = [c for c in cn if c in SIMP]

rows = [
    ('中文字數', '%d' % len(cn), True, ''),
    ('句數', '%d' % len(L), True, ''),
    ('平均句長', '%.1f 字' % avg, avg >= 40, '門檻 ≥40'),
    ('短句 <20字', '%.1f%%' % short, short < 15, '門檻 <15%'),
    ('emoji', '%d' % emo, emo == 0, ''),
    ('Markdown 條列', '%d' % bul, bul == 0, ''),
    ('簡體字殘留', '%d' % len(simp), len(simp) == 0, ''),
]
print('正文（不含附錄）風格檢查')
print('-' * 46)
allok = True
for name, val, ok, note in rows:
    allok = allok and ok
    print('%-16s %-12s %s  %s' % (name, val, 'PASS' if ok else 'FAIL', note))
print('-' * 46)
print('總計：' + ('全部通過' if allok else '有項目未通過'))
sys.exit(0 if allok else 1)