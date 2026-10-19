# -*- coding: utf-8 -*-
"""為指定 slug 補齊首頁需要的 webp 檔（首頁 wsrc() 會把 jpg/png 轉 .webp）。
首頁 wsrc() 的命名慣例：<slug>.webp / <slug>-poster.webp / <slug>-cover.webp
"""
import os
import sys
from PIL import Image

OUT = 'assets/og'

# 來源 → 目標 webp 清單
def build(slug):
    jobs = []
    for base in (slug, f'{slug}-poster', f'{slug}-cover', f'{slug}-poster-land'):
        src_png = f'{OUT}/{base}.png'
        src_jpg = f'{OUT}/{base}.jpg'
        # webp 目標名：cover 對應 poster-land（首頁/輯頁 hero 用 -cover）
        stem = f'{slug}-cover' if base == f'{slug}-poster-land' else base
        src = src_png if os.path.exists(src_png) else (src_jpg if os.path.exists(src_jpg) else None)
        dst = f'{OUT}/{stem}.webp'
        if src and not os.path.exists(dst):
            jobs.append((src, dst))
    return jobs


if __name__ == '__main__':
    for slug in sys.argv[1:]:
        for src, dst in build(slug):
            Image.open(src).convert('RGB').save(dst, 'WEBP', quality=86, method=6)
            print('建立', dst, os.path.getsize(dst), 'bytes  ←', src)