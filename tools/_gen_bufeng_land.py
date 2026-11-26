# -*- coding: utf-8 -*-
"""《捕風追影》(2025) 橫版海報生成 —— 83 篇唯一缺橫版的一篇。
2026-10-04 補齊，獨立生成 1536x1024 橫構圖（不可拿直版硬裁）。
"""
from PIL import Image
import numpy as np
import os

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
OG = os.path.join(ROOT, "assets", "og")
GEN = os.path.join(ROOT, "_poster_raw")
SRC = os.path.join(GEN, "LANDSCAPE_widescreen_compositi_2026-10-04T14-53-19.png")
SLUG = "bufeng-zhuiying"


def remove_watermark(img, rect, src_xy, feather=12):
    """浮水印固定右下角。從同行左側乾淨帶鏡像克隆貼回。
    帶寬必須＝矩形寬（1:1 零 resize），否則高對比橫紋會擠出鬼影。"""
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


h = Image.open(SRC).convert("RGB")
print("src:", h.size)
assert h.size == (1536, 1024), "橫版尺寸錯"

# 去浮水印：右下角 x1400-1536, y980-1024；乾淨帶取同行左側 x1250-1386
h = remove_watermark(h, (1400, 980, 1536, 1024), (1250, 980))

# 橫版源圖
h.save(os.path.join(OG, SLUG + "-poster-land.png"))
h.save(os.path.join(OG, SLUG + "-poster-land.jpg"), quality=90, optimize=True)
h.save(os.path.join(OG, SLUG + "-poster-land.webp"), quality=88, method=6)

# OG 1200x630：從橫版中心裁（片名在頂部，中心裁會保留）
ow, oh = 1200, 630
left = (h.width - ow) // 2
top = (h.height - oh) // 2
h.crop((left, top, left + ow, top + oh)).save(os.path.join(OG, SLUG + ".jpg"),
                                            quality=88, optimize=True)
h.crop((left, top, left + ow, top + oh)).save(os.path.join(OG, SLUG + ".webp"),
                                              quality=85, method=6)

# 複檢角落 3 倍
h.crop((1330, 930, 1536, 1024)).resize((618, 282), Image.NEAREST).save(
    os.path.join(GEN, "_bf_land_corner_check.png"))

print("完成：")
for f in ("-poster-land.png", "-poster-land.jpg", "-poster-land.webp", ".jpg", ".webp"):
    p = os.path.join(OG, SLUG + f)
    print("  ", SLUG + f, os.path.getsize(p) // 1024, "KB")
