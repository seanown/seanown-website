# -*- coding: utf-8 -*-
"""#155《誤判》Mondo 海報：去浮水印 + 抹除橫版中文字招牌 + 八件套。

來源：ImageGen 兩張（直 1024x1536／橫 1536x1024），2026-11-14 生成。
浮水印座標以數值方法實測（右下角 99.5 百分位亮像素），不靠推算：
  直版 x904-1012 / y1476-1524；橫版 x1416-1524 / y964-1012。
右下角為深色無紋理夜空 → 依 Skill #38 採「就地壓暗」，不用鏡像克隆。
橫版左側直式霓虹招牌出現中文字（「當」）→ 就地壓暗抹除，保留面板邊框。
OG 1200x630 採頂部對齊裁（標題貼頂，中心裁會切掉片名）。
"""
from PIL import Image
import numpy as np
import os

OG = r"C:\Users\user\WorkBuddy\01_網站\Seanown.org\assets\og"
SLUG = "the-prosecutor-2024"
SRC_V = os.path.join(OG, "Mondo_alternative_movie_poster_2026-11-13T17-45-09.png")
SRC_H = os.path.join(OG, "LANDSCAPE_widescreen_compositi_2026-11-13T17-45-21.png")


def _dilate(m, k=3):
    """手動 3x3 膨脹，抓抗鋸齒邊緣（不依賴 scipy）。"""
    out = m.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out = np.maximum(out, np.roll(np.roll(m, dy, axis=0), dx, axis=1))
    return out


def suppress_bright(img, rect, thresh=28, pct=30):
    """把區域內比暗部亮的像素壓到暗部色（去浮水印／去招牌字）。"""
    x0, y0, x1, y1 = rect
    base = np.asarray(img, dtype=np.float32).copy()
    reg = base[y0:y1, x0:x1]
    dark = np.percentile(reg.reshape(-1, 3), pct, axis=0)
    m = (reg.mean(axis=2) > max(dark.mean() + thresh, 60)).astype(np.float32)
    m = _dilate(m)[..., None]
    base[y0:y1, x0:x1] = reg * (1 - m) + dark * m
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


def fill_dark(img, rect, feather=14):
    """右下角是無紋理深色夜空 → 直接填同區暗色，只對左／上邊羽化（右／下貼邊不羽化）。

    複檢發現 suppress_bright 仍留極淡字影，故浮水印改用此法。
    """
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


v = Image.open(SRC_V).convert("RGB")
h = Image.open(SRC_H).convert("RGB")
assert v.size == (1024, 1536) and h.size == (1536, 1024), "來源尺寸不符"

# 1) 去右下角「AI生成 WORKBUDDY」浮水印（往外留邊；填補法，非壓暗法）
v = fill_dark(v, (888, 1458, 1024, 1536))
h = fill_dark(h, (1398, 946, 1536, 1024))

# 2) 抹除橫版左側直式霓虹招牌上的中文字（兩塊發光面板）
h = suppress_bright(h, (388, 108, 468, 322), thresh=32, pct=35)

# 3) 存清過的源圖（供複檢）
v.save(os.path.join(OG, "_" + SLUG + "_v_clean.png"))
h.save(os.path.join(OG, "_" + SLUG + "_h_clean.png"))

# ===== 八件套 =====
v.save(os.path.join(OG, SLUG + "-poster.png"))
v.save(os.path.join(OG, SLUG + "-poster.jpg"), quality=90)
v.save(os.path.join(OG, SLUG + "-poster.webp"), quality=88)

h.save(os.path.join(OG, SLUG + "-poster-land.png"))
h.save(os.path.join(OG, SLUG + "-poster-land.jpg"), quality=90)
h.save(os.path.join(OG, SLUG + "-poster-land.webp"), quality=88)

# OG 1200x630：頂部對齊裁（標題貼頂）
TW, TH = 1200, 630
scale = max(TW / h.width, TH / h.height)
sw, sh = int(h.width * scale), int(h.height * scale)
r = h.resize((sw, sh), Image.LANCZOS)
left, top = (sw - TW) // 2, 0
og = r.crop((left, top, left + TW, top + TH))
og.save(os.path.join(OG, SLUG + ".jpg"), quality=90)
og.save(os.path.join(OG, SLUG + ".webp"), quality=88)

# 右下角與招牌區放大複檢圖
v.crop((860, 1430, 1024, 1536)).resize((492, 318)).save(os.path.join(OG, "_inspect_v_corner.png"))
h.crop((1370, 920, 1536, 1024)).resize((498, 312)).save(os.path.join(OG, "_inspect_h_corner.png"))
h.crop((360, 80, 500, 350)).resize((420, 810)).save(os.path.join(OG, "_inspect_h_sign.png"))

for f in sorted(os.listdir(OG)):
    if f.startswith(SLUG):
        p = os.path.join(OG, f)
        print("%-46s %-12s %6d KB" % (f, str(Image.open(p).size), os.path.getsize(p) // 1024))
print("DONE")
