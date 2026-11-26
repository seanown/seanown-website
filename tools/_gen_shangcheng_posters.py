# -*- coding: utf-8 -*-
"""《傷城》海報後處理：移浮水印 + 八件套 + OG 裁切（先量片名再裁）"""
from PIL import Image, ImageFilter
import os, glob

SRC_V = "generated-images/Mondo_alternative_movie_poster_2026-09-30T08-16-15.png"
SRC_H = "generated-images/LANDSCAPE_widescreen_compositi_2026-09-30T08-19-23.png"
OUT = "assets/og"
SLUG = "shangcheng-2006"

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

def measure_title_x(img, y_top, y_bot, dark_thresh=90):
    """量片名實際 x 範圍（在 y_top..y_bot 帶內找深色像素邊界）。"""
    g = img.convert("L")
    w, h = g.size
    px = g.load()
    xs = []
    step = 2
    for y in range(y_top, min(y_bot, h), step):
        for x in range(0, w, step):
            if px[x, y] < dark_thresh:
                xs.append(x)
    return (min(xs), max(xs)) if xs else (0, w)

# ---------- 直版 ----------
v = Image.open(SRC_V).convert("RGB")
print("直版原始:", v.size)
v = remove_watermark(v, (870, 1448, 1024, 1536), (716, 1448))
vw = v.crop((850, 1400, 1024, 1536)).resize((348, 272))
vw.save("_ck_v_wm.png")
v.save(f"{OUT}/{SLUG}-poster.png")
v.save(f"{OUT}/{SLUG}-poster.jpg", quality=92)
v.save(f"{OUT}/{SLUG}-poster.webp", quality=88)

# ---------- 橫版 ----------
h_img = Image.open(SRC_H).convert("RGB")
print("橫版原始:", h_img.size)
h_img = remove_watermark(h_img, (1382, 936, 1536, 1024), (1228, 936))
hw = h_img.crop((1360, 900, 1536, 1024)).resize((352, 248))
hw.save("_ck_h_wm.png")
h_img.save(f"{OUT}/{SLUG}-poster-land.png")
h_img.save(f"{OUT}/{SLUG}-cover.jpg", quality=92)
h_img.save(f"{OUT}/{SLUG}-cover.webp", quality=88)

# ---------- OG 1200x630：先量片名再裁 ----------
# 橫版片名在頂部，先量帶 y=20..470 內深色像素的 x 範圍
x0, x1 = measure_title_x(h_img, 20, 470)
print(f"片名深色像素 x 範圍: {x0}..{x1} (畫寬 {h_img.size[0]})")
# 等比縮放到 1200 寬
sc = 1200 / h_img.size[0]
resized = h_img.resize((1200, round(h_img.size[1] * sc)), Image.LANCZOS)
# 630 高窗口：頂部對齊（片名貼頂）
box_y0 = 0
og = resized.crop((0, box_y0, 1200, box_y0 + 630))
og.save(f"{OUT}/{SLUG}.jpg", quality=90)
og.save(f"{OUT}/{SLUG}.webp", quality=86)
print("OG:", og.size, "頂部對齊裁切")
# 片名完整性複檢圖
og.crop((0, 0, 900, 300)).save("_ck_og_title.png")

print("\n八件套：")
for f in sorted(glob.glob(f"{OUT}/{SLUG}*")):
    print(" ", f, os.path.getsize(f) // 1024, "KB")
