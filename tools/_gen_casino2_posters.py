# -*- coding: utf-8 -*-
"""《賭城大亨II之至尊無敵》海報後處理：移浮水印 + 八件套 + OG 頂部對齊裁切"""
from PIL import Image
import os, glob

SRC_V = "assets/og/Mondo_alternative_movie_poster_2026-09-30T09-12-20.png"
SRC_H = "assets/og/LANDSCAPE_widescreen_compositi_2026-09-30T09-13-00.png"
OUT = "assets/og"
SLUG = "casino-tycoon-2-1992"

def remove_watermark(img, rect, src_xy, feather=12):
    """右下角浮水印：從同一張圖左側乾淨帶 1:1 等寬鏡像貼回，左/上邊羽化。"""
    x0, y0, x1, y1 = rect
    sx, sy = src_xy
    w, h = x1 - x0, y1 - y0
    band = img.crop((sx, sy, sx + w, sy + h)).transpose(Image.FLIP_LEFT_RIGHT)
    mask = Image.new("L", (w, h), 255)
    px = mask.load()
    for i in range(w):
        for j in range(h):
            a = 255
            if i < feather:
                a = min(a, int(255 * i / feather))
            if j < feather:
                a = min(a, int(255 * j / feather))
            px[i, j] = a
    img.paste(band, (x0, y0), mask)
    return img

# ---------- 直版 ----------
v = Image.open(SRC_V).convert("RGB")
print("直版原始:", v.size)
v = remove_watermark(v, (870, 1448, 1024, 1536), (716, 1448))
v.crop((850, 1400, 1024, 1536)).resize((348, 272)).save("_ck_v2_wm.png")
v.save(f"{OUT}/{SLUG}-poster.png")
v.save(f"{OUT}/{SLUG}-poster.jpg", quality=92)
v.save(f"{OUT}/{SLUG}-poster.webp", quality=88)

# ---------- 橫版 ----------
h_img = Image.open(SRC_H).convert("RGB")
print("橫版原始:", h_img.size)
h_img = remove_watermark(h_img, (1382, 936, 1536, 1024), (1228, 936))
h_img.crop((1360, 900, 1536, 1024)).resize((352, 248)).save("_ck_h2_wm.png")
h_img.save(f"{OUT}/{SLUG}-poster-land.png")
h_img.save(f"{OUT}/{SLUG}-poster-land.jpg", quality=92)
h_img.save(f"{OUT}/{SLUG}-cover.jpg", quality=92)
h_img.save(f"{OUT}/{SLUG}-cover.webp", quality=88)

# ---------- OG 1200x630：片名貼頂 → 頂部對齊裁切 ----------
sc = 1200 / h_img.size[0]
resized = h_img.resize((1200, round(h_img.size[1] * sc)), Image.LANCZOS)
og = resized.crop((0, 0, 1200, 630))
og.save(f"{OUT}/{SLUG}.jpg", quality=90)
og.save(f"{OUT}/{SLUG}.webp", quality=86)
print("OG:", og.size, "頂部對齊裁切")
og.crop((0, 0, 900, 300)).save("_ck_fb_v2_title.png")

print("\n八件套：")
for f in sorted(glob.glob(f"{OUT}/{SLUG}*")):
    print(" ", f, os.path.getsize(f) // 1024, "KB")
