# -*- coding: utf-8 -*-
"""《馬達・蓮娜》Madalena (2021) 海報八件套。

直版/橫版獨立生成，浮水印右下角鏡像克隆移除（1:1 等寬、零 resize、只羽化左/上邊）。
OG 1200x630 由橫版「頂部對齊」裁切（片名貼頂）。
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_V = os.path.join(ROOT, 'generated-images', 'Mondo_alternative_movie_poster_2026-09-30T03-16-00.png')
SRC_H = os.path.join(ROOT, 'generated-images', 'LANDSCAPE_widescreen_compositi_2026-09-30T03-18-30.png')
OUT = os.path.join(ROOT, 'assets', 'og')
SLUG = 'madalena-2021'
ALIGN = 'top'  # 片名貼頂


def remove_watermark(img, rect, src_xy, feather=12):
    """右下角浮水印：從同圖左側乾淨帶鏡像克隆貼回（1:1 等寬、零 resize）。"""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    sx, sy = src_xy
    band = img.crop((sx, sy, sx + w, sy + h)).transpose(Image.FLIP_LEFT_RIGHT)
    mask = Image.new('L', (w, h), 255)
    px = mask.load()
    for y in range(h):
        for x in range(w):
            f = 255
            if x < feather:
                f = min(f, int(255 * x / feather))
            if y < feather:
                f = min(f, int(255 * y / feather))
            if f < 255:
                px[x, y] = f
    img.paste(band, (x0, y0), mask)
    return img


V = Image.open(SRC_V).convert('RGB')
H = Image.open(SRC_H).convert('RGB')
assert V.size == (1024, 1536) and H.size == (1536, 1024), (V.size, H.size)

# 浮水印矩形（右下角深色帶）
V = remove_watermark(V, (870, 1448, 1024, 1536), (716, 1448))
H = remove_watermark(H, (1382, 936, 1536, 1024), (1228, 936))

V.save(os.path.join(OUT, SLUG + '-poster.png'))
V.save(os.path.join(OUT, SLUG + '-poster.jpg'), quality=92)
V.save(os.path.join(OUT, SLUG + '-poster.webp'), quality=88)
H.save(os.path.join(OUT, SLUG + '-poster-land.png'))
H.save(os.path.join(OUT, SLUG + '-cover.jpg'), quality=92)
H.save(os.path.join(OUT, SLUG + '-cover.webp'), quality=88)

# OG 1200x630（片名偏左，中心裁會切掉 M → 從 x=0 起裁）
box = (0, 0, 1200, 630)
og = H.crop(box)
og.save(os.path.join(OUT, SLUG + '.jpg'), quality=90)
og.save(os.path.join(OUT, SLUG + '.webp'), quality=86)

print('八件套完成：', SLUG)
for f in ['-poster.png', '-poster.jpg', '-poster.webp', '-poster-land.png',
          '-cover.jpg', '-cover.webp', '.jpg', '.webp']:
    p = os.path.join(OUT, SLUG + f)
    print('  %-28s %7d bytes' % (f, os.path.getsize(p)))
