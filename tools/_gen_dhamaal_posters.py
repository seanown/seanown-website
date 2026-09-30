# -*- coding: utf-8 -*-
"""《噴火女郎》(1959) double-dhamaal-2011：八件套生成（2026-09-30）。"""
from PIL import Image
import numpy as np
import os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
GEN = os.path.join(ROOT, "_poster_raw")
OG = os.path.join(ROOT, "assets", "og")
SRC_V = os.path.join(GEN, "Mondo_style_screen_printed_mov_2026-09-30T04-04-14.png")
SRC_H = os.path.join(GEN, "Mondo_style_screen_printed_mov_2026-09-30T04-04-39.png")
SLUG = "double-dhamaal-2011"


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
print("src:", v.size, h.size)
assert v.size == (1024, 1536), "直版尺寸錯"
assert h.size == (1536, 1024), "橫版尺寸錯"

# 直版浮水印 x870-1024, y1448-1536
v = remove_watermark(v, (870, 1448, 1024, 1536), (700, 1448))
# 橫版浮水印 x1382-1536, y936-1024
h = remove_watermark(h, (1382, 936, 1536, 1024), (1216, 936))

# ===== 八件套 =====
v.save(os.path.join(OG, SLUG + "-poster.png"))
v.save(os.path.join(OG, SLUG + "-poster.jpg"), quality=90)
v.save(os.path.join(OG, SLUG + "-poster.webp"), quality=88)

h.save(os.path.join(OG, SLUG + "-poster-land.png"))
h.save(os.path.join(OG, SLUG + "-cover.jpg"), quality=90)
h.save(os.path.join(OG, SLUG + "-cover.webp"), quality=88)

# OG 1200x630：由橫版放大後裁 630 高，裁切位置自動偵測（白／金字亮度帶）
TW, TH = 1200, 630
scale = max(TW / h.width, TH / h.height)
sw, sh = int(h.width * scale), int(h.height * scale)
r = h.resize((sw, sh), Image.LANCZOS)
arr = np.asarray(r, dtype=np.float32).mean(axis=2)
bright = (arr > 200).sum(axis=1)
half = sh // 2
top_amt, bot_amt = int(bright[:half].sum()), int(bright[half:].sum())
print("bright top/bottom:", top_amt, bot_amt)
top = 0 if top_amt >= bot_amt else sh - TH   # 亮字在哪半就往那半靠
top = max(0, min(top, sh - TH))
print("OG crop top:", top, "of", sh - TH)
og = r.crop(((sw - TW) // 2, top, (sw - TW) // 2 + TW, top + TH))
og.save(os.path.join(OG, SLUG + ".jpg"), quality=90)
og.save(os.path.join(OG, SLUG + ".webp"), quality=88)

for f in sorted(os.listdir(OG)):
    if f.startswith(SLUG):
        p = os.path.join(OG, f)
        print(f, Image.open(p).size, os.path.getsize(p) // 1024, "KB")
print("DONE")
