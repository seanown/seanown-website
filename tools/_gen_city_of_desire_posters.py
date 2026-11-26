# -*- coding: utf-8 -*-
"""《慾望之城》(2001) city-of-desire-2001：去浮水印 + 八件套生成（2026-09-30）。

沿用 _gen_macao_enfer_posters.py pattern：
1) 右下角「AI生成 WORKBUDDY」浮水印 → 同行乾淨帶鏡像克隆＋羽化貼回。
2) 生成 assets/og/city-of-desire-2001 八件套。
ALIGN='top'：橫版片名 CITY OF DESIRE 置頂，OG 1200x630 裁切保住片名。
"""
from PIL import Image
import numpy as np
import os
import sys

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
OG = os.path.join(ROOT, "assets", "og")
GEN = os.path.join(ROOT, "generated-images")
SRC_V = os.path.join(GEN, "Mondo_alternative_movie_poster_2026-09-29T20-14-02.png")
SRC_H = os.path.join(GEN, "LANDSCAPE_widescreen_compositi_2026-09-29T20-14-31.png")
SLUG = "city-of-desire-2001"
ALIGN = sys.argv[1] if len(sys.argv) > 1 else "top"


def remove_watermark(img, rect, src_xy, feather=12):
    x0, y0, x1, y1 = rect
    sx, sy = src_xy
    w, h = x1 - x0, y1 - y0
    patch = img.crop((sx, sy, sx + w, sy + h)).transpose(Image.FLIP_LEFT_RIGHT)
    base = np.asarray(img, dtype=np.float32)
    pat = np.asarray(patch, dtype=np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    ax = np.clip(xx / float(feather), 0, 1)
    ay = np.clip(yy / float(feather), 0, 1)
    alpha = np.minimum(ax, ay)[..., None].astype(np.float32)
    region = base[y0:y1, x0:x1]
    base[y0:y1, x0:x1] = region * (1 - alpha) + pat * alpha
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


v = Image.open(SRC_V).convert("RGB")
h = Image.open(SRC_H).convert("RGB")
print("src sizes:", v.size, h.size)
assert v.size == (1024, 1536), v.size
assert h.size == (1536, 1024), h.size

v = remove_watermark(v, (870, 1448, 1024, 1536), (700, 1448))
h = remove_watermark(h, (1382, 936, 1536, 1024), (1216, 936))

v.save(os.path.join(GEN, "_cod_v_clean.png"))
h.save(os.path.join(GEN, "_cod_h_clean.png"))

# 八件套
v.save(os.path.join(OG, SLUG + "-poster.png"))
v.save(os.path.join(OG, SLUG + "-poster.jpg"), quality=90)
v.save(os.path.join(OG, SLUG + "-poster.webp"), quality=88)

h.save(os.path.join(OG, SLUG + "-poster-land.png"))
h.save(os.path.join(OG, SLUG + "-cover.jpg"), quality=90)
h.save(os.path.join(OG, SLUG + "-cover.webp"), quality=88)

TW, TH = 1200, 630
scale = max(TW / h.width, TH / h.height)
sw, sh = int(h.width * scale), int(h.height * scale)
r = h.resize((sw, sh), Image.LANCZOS)
left = (sw - TW) // 2
if ALIGN == "top":
    top = 0
elif ALIGN == "bottom":
    top = sh - TH
else:
    top = (sh - TH) // 2
og = r.crop((left, top, left + TW, top + TH))
og.save(os.path.join(OG, SLUG + ".jpg"), quality=90)
og.save(os.path.join(OG, SLUG + ".webp"), quality=88)

print("ALIGN:", ALIGN)
for f in sorted(os.listdir(OG)):
    if f.startswith(SLUG):
        p = os.path.join(OG, f)
        print(" ", f, Image.open(p).size, os.path.getsize(p) // 1024, "KB")
print("DONE")
