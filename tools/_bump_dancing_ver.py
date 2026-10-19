# -*- coding: utf-8 -*-
"""《與你相遇的日子》海報換版：只把本篇 HTML 內該 slug 圖片的 ?v= 升版。
全站 OG_VER 不動（否則 84 張 macau-film 海報會全部重新下載）。
"""
import re
import io

SLUG = 'dancing-in-the-sea-breeze-2024'
OLD = '20261001n'
NEW = '20261019a'

for path in [f'article/{SLUG}/index.html', f'movie/{SLUG}/index.html']:
    with io.open(path, encoding='utf-8') as f:
        s = f.read()
    pat = re.compile(r'(/assets/og/' + re.escape(SLUG) + r'[^\'"]*?\?v=)' + OLD)
    s2, n = pat.subn(r'\g<1>' + NEW, s)
    if n:
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(s2)
    print(path, '替換', n, '處')