# -*- coding: utf-8 -*-
# 在 tools/build_articles.py 的 CSS 變數區域逐行檢查花括號平衡。
#
# 只檢查普通 CSS 變數（module-level 的 NAME = 三引號字串），
# 不碰會被 .format() 處理的 page 模板（那些的雙花括號是合法的）。

import io, re, sys

P = 'tools/build_articles.py'
src = io.open(P, encoding='utf-8').read()

# 找出所有 module-level 的 XXX_CSS = """ ... """ 區塊
pat = re.compile(r'^([A-Z_][A-Z0-9_]*)\s*=\s*"""', re.M)
blocks = []
for m in pat.finditer(src):
    name = m.group(1)
    start = m.end()
    end = src.index('"""', start)
    blocks.append((name, start, end))

print('找到 CSS 變數區塊:', len(blocks))
print()

bad = []
for name, s0, e0 in blocks:
    body = src[s0:e0]
    o, c = body.count('{'), body.count('}')
    line_no = src[:s0].count('\n') + 1
    status = 'OK' if o == c else 'UNBALANCED'
    if o != c:
        # 找第一個未閉合
        depth = 0
        first = None
        for ln in body.split('\n'):
            if first is None and ln.count('{'):
                first = ln.strip()[:78]
            depth += ln.count('{') - ln.count('}')
            if depth == 0:
                first = None
        bad.append((name, line_no, o, c, first))
    print('  %-18s L%-5d {=%-4d }=%-4d %s' % (name, line_no, o, c, status))

print()
if bad:
    print('=== 需要修正 ===')
    for name, line_no, o, c, first in bad:
        print('  %s  (L%d)  {=%d }=%d  差 %d' % (name, line_no, o, c, c - o))
        print('      首個未閉合: %s' % (first or '(?)'))
else:
    print('全部 CSS 變數花括號平衡')
sys.exit(1 if bad else 0)
