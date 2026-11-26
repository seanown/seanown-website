# -*- coding: utf-8 -*-
"""以軒哥提供的定稿海報替換 #58 濠江風雲 8 件套（2026-09-29）。"""
from PIL import Image
import os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
OG = os.path.join(ROOT, "assets", "og")
SRC_V = r"H:\桌面\05346de1b3cfc5142ff1731595914887.jpg"   # 直版（CASINO 黃字滿版）
SRC_H = r"H:\桌面\b247268e08023d50499c07f7fde10feb.jpg"   # 橫版（CASINO 紅字奶油底）
SLUG = "hao-jiang-feng-yun"

v = Image.open(SRC_V).convert("RGB")
h = Image.open(SRC_H).convert("RGB")
print("vertical:", v.size, "landscape:", h.size)

# 1) 直版源 png + 正文 jpg + webp
v.save(os.path.join(OG, SLUG + "-poster.png"))
v.save(os.path.join(OG, SLUG + "-poster.jpg"), quality=90)
v.save(os.path.join(OG, SLUG + "-poster.webp"), quality=88)

# 2) 橫版源 png + hero cover jpg + webp
h.save(os.path.join(OG, SLUG + "-poster-land.png"))
h.save(os.path.join(OG, SLUG + "-cover.jpg"), quality=90)
h.save(os.path.join(OG, SLUG + "-cover.webp"), quality=88)

# 3) OG 1200x630：橫版中心裁
TW, TH = 1200, 630
scale = max(TW / h.width, TH / h.height)
sw, sh = int(h.width * scale), int(h.height * scale)
r = h.resize((sw, sh), Image.LANCZOS)
left, top = (sw - TW) // 2, (sh - TH) // 2
og = r.crop((left, top, left + TW, top + TH))
og.save(os.path.join(OG, SLUG + ".jpg"), quality=90)
og.save(os.path.join(OG, SLUG + ".webp"), quality=88)

for f in sorted(os.listdir(OG)):
    if SLUG in f:
        print(f, os.path.getsize(os.path.join(OG, f)) // 1024, "KB")
print("DONE")
