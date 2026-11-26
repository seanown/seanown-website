# -*- coding: utf-8 -*-
"""把 PPT 用的 PNG 轉成 JPEG，體積降一個數量級（背景圖不需要透明通道）。"""
import os, io
from PIL import Image

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'slides', 'meeting-sop', 'assets')

def conv(name):
    src = os.path.join(SRC, name + '.png')
    if not os.path.exists(src):
        print('skip (missing): ' + name); return
    im = Image.open(src).convert('RGB')
    w, h = im.size
    # 單邊最長限制 1920，PPT 畫布 1280 寬足夠
    if max(w, h) > 1920:
        s = 1920.0 / max(w, h)
        im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
    dst = os.path.join(SRC, name + '.jpg')
    im.save(dst, 'JPEG', quality=82, optimize=True, progressive=True)
    a = os.path.getsize(src); b = os.path.getsize(dst)
    print('%-16s %6.2fMB -> %6.2fMB  (%dx%d)' % (name, a / 1048576, b / 1048576, im.size[0], im.size[1]))
    if b * 12 < a:      # 收益夠大才刪原檔
        os.remove(src)

if __name__ == '__main__':
    for n in ['cover_table', 'chapter_1', 'chapter_2', 'host_speaking', 'meeting_scene']:
        conv(n)