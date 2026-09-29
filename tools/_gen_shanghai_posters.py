# -*- coding: utf-8 -*-
"""#67 上海驚情 (shanghai-surprise-1986)：AI 生成圖去浮水印 + 八件套生成（2026-09-29）。

流程：
1) ImageGen 直版/橫版右下角有「AI生成 WORKBUDDY」浮水印 → 以同行乾淨深色帶
   鏡像克隆＋左/上邊羽化貼回移除（右/下貼圖邊不羽化，避免露殘）。
2) 清好的圖直接生成 assets/og/shanghai-surprise-1986 八件套（沿用 _swap_sisterhood_posters.py pattern）。
"""
from PIL import Image
import numpy as np
import os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
GEN = os.path.join(ROOT, "generated-images")
OG = os.path.join(ROOT, "assets", "og")
SRC_V = os.path.join(GEN, "Vintage_retro_mood_Mondo_scree_2026-09-29T16-43-05.png")
SRC_H = os.path.join(GEN, "Vintage_retro_mood_Mondo_scree_2026-09-29T16-44-07.png")
SLUG = "shanghai-surprise-1986"


def remove_watermark(img, rect, src_xy, feather=12):
    """rect=(x0,y0,x1,y1) 覆蓋浮水印；src_xy=同行乾淨區左上角；鏡像克隆＋左/上羽化。"""
    x0, y0, x1, y1 = rect
    sx, sy = src_xy
    w, h = x1 - x0, y1 - y0
    patch = img.crop((sx, sy, sx + w, sy + h)).transpose(Image.FLIP_LEFT_RIGHT)
    base = np.asarray(img, dtype=np.float32)
    pat = np.asarray(patch, dtype=np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    ax = np.clip(xx / float(feather), 0, 1)   # 左邊羽化
    ay = np.clip(yy / float(feather), 0, 1)   # 上邊羽化
    alpha = np.minimum(ax, ay)[..., None].astype(np.float32)
    region = base[y0:y1, x0:x1]
    base[y0:y1, x0:x1] = region * (1 - alpha) + pat * alpha
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


v = Image.open(SRC_V).convert("RGB")
h = Image.open(SRC_H).convert("RGB")
print("src:", v.size, h.size)

# 直版浮水印實測約 x894-1024, y1466-1536 → rect 再往外留邊；克隆源取同帶左側 (700,1448)
v = remove_watermark(v, (870, 1448, 1024, 1536), (700, 1448))
# 橫版浮水印實測約 x1406-1536, y954-1024；克隆源取 (1216,936)
h = remove_watermark(h, (1382, 936, 1536, 1024), (1216, 936))

v_clean = os.path.join(GEN, "_shanghai_v_clean.png")
h_clean = os.path.join(GEN, "_shanghai_h_clean.png")
v.save(v_clean)
h.save(h_clean)
print("cleaned saved:", v_clean, h_clean)

# ===== 八件套 =====
# 1) 直版源 png + 正文 jpg + webp
v.save(os.path.join(OG, SLUG + "-poster.png"))
v.save(os.path.join(OG, SLUG + "-poster.jpg"), quality=90)
v.save(os.path.join(OG, SLUG + "-poster.webp"), quality=88)

# 2) 橫版源 png + hero cover jpg + webp
h.save(os.path.join(OG, SLUG + "-poster-land.png"))
h.save(os.path.join(OG, SLUG + "-cover.jpg"), quality=90)
h.save(os.path.join(OG, SLUG + "-cover.webp"), quality=88)

# 3) OG 1200x630：橫版改「底部對齊」裁（片名 SHANGHAI SURPRISE 在左下，
#    中心裁會切掉 SURPRISE 下緣；bottom-align 才保完整片名）
TW, TH = 1200, 630
scale = max(TW / h.width, TH / h.height)
sw, sh = int(h.width * scale), int(h.height * scale)
r = h.resize((sw, sh), Image.LANCZOS)
left, top = (sw - TW) // 2, (sh - TH)  # bottom-aligned
og = r.crop((left, top, left + TW, top + TH))
og.save(os.path.join(OG, SLUG + ".jpg"), quality=90)
og.save(os.path.join(OG, SLUG + ".webp"), quality=88)

for f in sorted(os.listdir(OG)):
    if f.startswith(SLUG):
        p = os.path.join(OG, f)
        print(f, Image.open(p).size, os.path.getsize(p) // 1024, "KB")
print("DONE")
