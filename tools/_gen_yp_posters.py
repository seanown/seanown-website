# -*- coding: utf-8 -*-
"""《黃禍》Yellow Peril (1984) 海報八件套生成：浮水印移除 + 直版/橫版/OG 全套輸出"""
import os
from PIL import Image, ImageFilter

BASE = r"C:/Users/user/WorkBuddy/Seanown.org/assets/og"
V_SRC = os.path.join(BASE, "Mondo_alternative_movie_poster_2026-09-29T20-35-20.png")
H_SRC = os.path.join(BASE, "LANDSCAPE_widescreen_compositi_2026-09-29T20-36-05.png")
SLUG = "yellow-peril-1984"


def remove_watermark(img, rect, band_w):
    """從同一行左側乾淨帶鏡像克隆＋左/上邊 12px 羽化貼回（右/下不羽化防露殘）"""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    band = img.crop((x0 - band_w, y0, x0, y1)).transpose(Image.FLIP_LEFT_RIGHT)
    if band.size != (w, h):
        band = band.resize((w, h), Image.LANCZOS)
    mask = Image.new("L", (w, h), 255)
    px = mask.load()
    for i in range(w):
        for j in range(h):
            a = 255
            if i < 12:
                a = min(a, int(255 * i / 12))
            if j < 12:
                a = min(a, int(255 * j / 12))
            px[i, j] = a
    img.paste(band, (x0, y0), mask)
    return img


def save(img, path, quality=92, fmt="JPEG"):
    if fmt == "JPEG":
        img = img.convert("RGB")
    kw = {"quality": quality} if fmt == "JPEG" else {"quality": quality, "method": 6}
    if fmt == "WEBP":
        kw = {"quality": quality, "method": 6}
    img.save(path, fmt, **kw)
    print("  ->", os.path.basename(path), os.path.getsize(path) // 1024, "KB", img.size)


# ---------- 直版 ----------
v = Image.open(V_SRC).convert("RGB")
print("直版源圖", v.size)
v = remove_watermark(v, (870, 1448, 1024, 1536), 700)
save(v, os.path.join(BASE, SLUG + "-poster.png"), fmt="PNG")
save(v, os.path.join(BASE, SLUG + "-poster.jpg"), quality=92)
save(v, os.path.join(BASE, SLUG + "-poster.webp"), quality=88, fmt="WEBP")

# ---------- 橫版 ----------
h = Image.open(H_SRC).convert("RGB")
print("橫版源圖", h.size)
# 1:1 等寬鏡像（帶寬=矩形寬，不做壓縮；壓縮會把波浪泡沫擠成鬼影字母）
h = remove_watermark(h, (1382, 936, 1536, 1024), 154)
save(h, os.path.join(BASE, SLUG + "-poster-land.png"), fmt="PNG")
save(h, os.path.join(BASE, SLUG + "-cover.jpg"), quality=92)
save(h, os.path.join(BASE, SLUG + "-cover.webp"), quality=88, fmt="WEBP")

# ---------- OG 1200x630：片名貼頂 -> 頂部對齊裁切（勿中心裁，會切標題下緣） ----------
og = h.resize((1200, 800), Image.LANCZOS).crop((0, 0, 1200, 630))
save(og, os.path.join(BASE, SLUG + ".jpg"), quality=90)
save(og, os.path.join(BASE, SLUG + ".webp"), quality=88, fmt="WEBP")

print("DONE")
