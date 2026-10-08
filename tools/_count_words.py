# -*- coding: utf-8 -*-
"""小課堂文章字數統計：只算散文，不算標題、表格、引用"""
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else 'drafts/122-商務禮儀與典禮SOP.md'
t = open(path, encoding='utf-8').read()

keep = []
for line in t.split('\n'):
    s = line.strip()
    # 去掉標題行、表格行、引用行、程式碼區塊
    if s.startswith('|') or s.startswith('#') or s.startswith('>'):
        continue
    keep.append(line)

body = '\n'.join(keep)
body = re.sub(r'\*\*|`', '', body)
body = re.sub(r'[#*>\[\]()]', '', body)
n = len(body)

print('散文淨字數:', n)
print('門檻 ≥2500:', 'OK' if n >= 2500 else 'FAIL (差 %d)' % (2500 - n))

# 表格統計
tbl_rows = t.count('\n|')
print('表格行數:', tbl_rows)

# 條列檢查（skill 要求正文不得有條列）
bullet = re.findall(r'^\s*[-*+]\s+', t, re.M)
numbered = re.findall(r'^\s*\d+\.\s+', t, re.M)
print('無序條列:', len(bullet), '| 有序條列:', len(numbered))
if bullet or numbered:
    print('  ⚠ 有條列，會被風檢判違禁')

# emoji
emo = re.findall(r'[\U0001F300-\U0001FAFF\u2600-\u27BF]', t)
print('emoji:', len(emo))

# 簡體字
simp = re.findall(r'[们这来对时会说学经济么间无动务农产发风汉艺龙亿]',
                   t)
print('簡體字殘留:', len(simp), set(simp) if simp else '')