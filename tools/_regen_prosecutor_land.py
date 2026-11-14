# -*- coding: utf-8 -*-
"""#155《誤判》重生成「真橫向滿版」橫海報（2026-11-14 12:26）。

原因：第一版橫圖雖為 1536x1024，但內容是中央直式構圖＋左右各約 25% 黑邊，
違反 macau-movie-poster §直版+橫版雙生成「橫版必須獨立生成橫構圖」，
CTA 卡因此看起來像直的。本腳本只換橫版系與 OG 系共 5 檔，
直版 3 檔（poster.png/jpg/webp）與正文一個字都不動。

浮水印座標以數值方法實測（右下角 99% 亮像素）：x1416-1524 / y964-1012。
新圖右下角為暗色水面帶反光 → 用 fill_dark 就地填暗，只對左／上邊羽化。
"""
from PIL import Image
import numpy as np
import os

OG = r"C:\Users\user\WorkBuddy\01_網站\Seanown.org\assets\og"
SLUG = "the-prosecutor-2024"
SRC = os.path.join(OG, "LANDSCAPE_widescreen_compositi_2026-11-14T12-05-31.png")


def _dilate(m, k=3):
    out = m.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out = np.maximum(out, np.roll(np.roll(m, dy, axis=0), dx, axis=1))
    return out


def suppress_bright(img, rect, thresh=28, pct=30):
    x0, y0, x1, y1 = rect
    base = np.asarray(img, dtype=np.float32).copy()
    reg = base[y0:y1, x0:x1]
    dark = np.percentile(reg.reshape(-1, 3), pct, axis=0)
    m = (reg.mean(axis=2) > max(dark.mean() + thresh, 60)).astype(np.float32)
    m = _dilate(m)[..., None]
    base[y0:y1, x0:x1] = reg * (1 - m) + dark * m
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


def fill_dark(img, rect, feather=16):
    x0, y0, x1, y1 = rect
    base = np.asarray(img, dtype=np.float32).copy()
    ref = base[max(0, y0 - 44):y0, x0:x1]
    color = np.percentile(ref.reshape(-1, 3), 40, axis=0)
    reg = base[y0:y1, x0:x1]
    hh, ww = reg.shape[:2]
    yy, xx = np.mgrid[0:hh, 0:ww]
    ax = np.clip(xx / float(feather), 0, 1)
    ay = np.clip(yy / float(feather), 0, 1)
    alpha = np.minimum(ax, ay)[..., None].astype(np.float32)
    fill = np.ones_like(reg) * color
    base[y0:y1, x0:x1] = reg * (1 - alpha) + fill * alpha
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


h = Image.open(SRC).convert("RGB")
assert h.size == (1536, 1024), "來源尺寸不符：%s" % (h.size,)

# 1) 清右下角「AI生成 WORKBUDDY」浮水印（往外留邊）
h = fill_dark(h, (1400, 948, 1536, 1024))
h = suppress_bright(h, (1408, 956, 1532, 1018), thresh=18, pct=35)

h.save(os.path.join(OG, "_" + SLUG + "_h_clean_v2.png"))

# 2) 橫版系 3 檔
h.save(os.path.join(OG, SLUG + "-poster-land.png"))
h.save(os.path.join(OG, SLUG + "-poster-land.jpg"), quality=90)
h.save(os.path.join(OG, SLUG + "-poster-land.webp"), quality=88)

# 3) OG 1200x630：由新橫版頂部對齊裁（標題貼頂，中心裁會切片名）
TW, TH = 1200, 630
scale = max(TW / h.width, TH / h.height)
sw, sh = int(h.width * scale), int(h.height * scale)
r = h.resize((sw, sh), Image.LANCZOS)
left, top = (sw - TW) // 2, 0
og = r.crop((left, top, left + TW, top + TH))
og.save(os.path.join(OG, SLUG + ".jpg"), quality=90)
og.save(os.path.join(OG, SLUG + ".webp"), quality=88)

# 4) 放大複檢圖
h.crop((1370, 920, 1536, 1024)).resize((664, 416)).save(os.path.join(OG, "_inspect_h_corner_v2.png"))
h.crop((0, 0, 1536, 1024)).resize((768, 512)).save(os.path.join(OG, "_inspect_h_full_v2.png"))

for f in sorted(os.listdir(OG)):
    if f.startswith(SLUG) and not f.startswith("_"):
        p = os.path.join(OG, f)
        print("%-46s %-12s %6d KB" % (f, str(Image.open(p).size), os.path.getsize(p) // 1024))
print("DONE")
