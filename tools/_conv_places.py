# -*- coding: utf-8 -*-
"""把「澳門電影取景地banner」24 張 PNG 轉成 collection 取景地頁的頂圖。

來源：軒哥 2026-10-16 02:00 給的 H:\桌面\澳門電影取景地banner.zip
（24 張 3128×1340 動漫風黃昏插畫，檔名 01_議事亭前地 … 24_澳門旅遊塔，
編號與 collection/place-01…place-24 一一對應；place-25 白鴿巢公園無圖）。
輸出：assets/images/places/place-NN.jpg（長邊 1600／q87／progressive）。
"""
import io
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, 'temp', 'banner', '澳門電影取景地banner')
OUT_DIR = os.path.join(ROOT, 'assets', 'images', 'places')
LONG_SIDE = 1600
QUALITY = 87


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    names = sorted(os.listdir(SRC_DIR))
    names = [n for n in names if n.lower().endswith('.png')]
    assert len(names) == 24, '應為 24 張 PNG，實得 %d' % len(names)
    total_in = total_out = 0
    for n in names:
        # '01_議事亭前地.png' -> 'place-01'
        idx = int(n.split('_', 1)[0])
        assert 1 <= idx <= 24, n
        src = os.path.join(SRC_DIR, n)
        im = Image.open(src).convert('RGB')
        w, h = im.size
        if max(w, h) > LONG_SIDE:
            if w >= h:
                im = im.resize((LONG_SIDE, round(h * LONG_SIDE / w)), Image.LANCZOS)
            else:
                im = im.resize((round(w * LONG_SIDE / h), LONG_SIDE), Image.LANCZOS)
        out = os.path.join(OUT_DIR, 'place-%02d.jpg' % idx)
        im.save(out, 'JPEG', quality=QUALITY, optimize=True, progressive=True)
        si, so = os.path.getsize(src), os.path.getsize(out)
        total_in += si
        total_out += so
        print('place-%02d  %-14s %dx%d  %.0fKB -> %.0fKB' % (idx, n.split('_', 1)[1].replace('.png', ''), im.size[0], im.size[1], si / 1024, so / 1024))
    print('done: 24 files, %.1fMB -> %.1fMB' % (total_in / 1e6, total_out / 1e6))


if __name__ == '__main__':
    main()
