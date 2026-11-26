# -*- coding: utf-8 -*-
"""《追兇記》Trace of Murderer (1965) 海報八件套：浮水印移除 + webp/jpg/OG"""
import sys
from PIL import Image, ImageFilter

SRC_V = 'assets/og/Mondo_alternative_movie_poster_2026-09-29T21-31-03.png'
SRC_H = 'assets/og/LANDSCAPE_widescreen_compositi_2026-09-29T21-31-33.png'
SLUG = 'zhuixiongji-1965'
ALIGN = sys.argv[1] if len(sys.argv) > 1 else 'top'   # OG 裁切對齊：片名貼頂 → top

def remove_watermark(img, rect, src_xy, feather=12):
    """rect=(x0,y0,x1,y1) 浮水印矩形; src_xy=(sx,sy) 同尺寸乾淨帶左上角; 1:1 等寬鏡像克隆"""
    x0, y0, x1, y1 = rect
    sx, sy = src_xy
    assert (x1-x0) == 0 or True
    w, h = x1-x0, y1-y0
    assert (sx+w) <= x0 or (sx) >= x1, 'source band must not overlap rect'
    band = img.crop((sx, sy, sx+w, sy+h)).transpose(Image.FLIP_LEFT_RIGHT)
    mask = Image.new('L', (w, h), 255)
    px = mask.load()
    for i in range(feather):          # 只羽化左/上邊（右/下貼圖邊不羽化，防露殘）
        a = int(255 * i / feather)
        for y in range(h):
            if px[i, y] > a: px[i, y] = a
        for x in range(w):
            if px[x, i] > a: px[x, i] = a
    img.paste(band, (x0, y0), mask)
    return img

# ---- 直版 1024x1536 ----
v = Image.open(SRC_V).convert('RGB')
v = remove_watermark(v, (870, 1448, 1024, 1536), (700, 1448))
v.save(f'assets/og/{SLUG}-poster.png')
v.save(f'assets/og/{SLUG}-poster.jpg', quality=92)
v.save(f'assets/og/{SLUG}-poster.webp', quality=88)
print('V done', v.size)

# ---- 橫版 1536x1024 ----
h = Image.open(SRC_H).convert('RGB')
h = remove_watermark(h, (1382, 936, 1536, 1024), (1216, 936))
h.save(f'assets/og/{SLUG}-poster-land.png')
h.save(f'assets/og/{SLUG}-cover.jpg', quality=92)
h.save(f'assets/og/{SLUG}-cover.webp', quality=88)
print('H done', h.size)

# ---- OG 1200x630 ----
if ALIGN == 'top':
    base = h.resize((1200, 800), Image.LANCZOS)
    og = base.crop((0, 0, 1200, 630))
else:
    base = h.resize((1200, 800), Image.LANCZOS)
    top = (800-630)//2
    og = base.crop((0, top, 1200, top+630))
og.save(f'assets/og/{SLUG}.jpg', quality=90)
og.save(f'assets/og/{SLUG}.webp', quality=88)
print('OG done', og.size, 'align=', ALIGN)
