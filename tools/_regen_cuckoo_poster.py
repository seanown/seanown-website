# -*- coding: utf-8 -*-
"""《十月初五的月光》直版海報重生：舊圖左上有誤植數字「18」。
2026-10-04 重生成直版，換掉舊的 return-of-the-cuckoo-poster.*。
只換直版與其衍生（poster.jpg / webp / cover / og / webp），
橫版 -poster-land.png 本身乾淨，保留不動。
"""
from PIL import Image
import numpy as np
import os, shutil

ROOT = r"C:\Users\user\WorkBuddy\Seanown.org"
OG = os.path.join(ROOT, "assets", "og")
GEN = os.path.join(ROOT, "_poster_raw")
SLUG = "return-of-the-cuckoo"
SRC = os.path.join(GEN, "Mondo_alternative_movie_poster_2026-10-04T14-27-21.png")

# 舊版備份
OLD = os.path.join(GEN, "_old_cuckoo_2026-10-04")
if not os.path.isdir(OLD):
    os.makedirs(OLD)
    for suf in ("poster.png", "poster.jpg", "poster.webp",
                "cover.jpg", "cover.webp", ".jpg", ".webp"):
        src = os.path.join(OG, SLUG + suf)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(OLD, SLUG + suf))
    print("舊版已備份 ->", OLD)


def remove_watermark(img, rect, src_xy, feather=12):
    """浮水印固定在右下角深色帶。從同行左側乾淨帶鏡像克隆貼回。
    帶寬必須＝矩形寬（1:1 零 resize），否則高對比橫紋會擠出鬼影字母。"""
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


v = Image.open(SRC).convert("RGB")
print("src:", v.size)
assert v.size == (1024, 1536), "直版尺寸錯"

# 去浮水印：右下角 x870-1024, y1448-1536；乾淨帶取同行左側 x700-854
v = remove_watermark(v, (870, 1448, 1024, 1536), (700, 1448))

# 直版源圖
v.save(os.path.join(OG, SLUG + "-poster.png"))
v.save(os.path.join(OG, SLUG + "-poster.jpg"), quality=90, optimize=True)
v.save(os.path.join(OG, SLUG + "-poster.webp"), quality=88, method=6)

# cover：直接用直版（此片 cover 原本尺寸就是直版，維持不變）
v.save(os.path.join(OG, SLUG + "-cover.jpg"), quality=90, optimize=True)
v.save(os.path.join(OG, SLUG + "-cover.webp"), quality=88, method=6)

# OG 1200x630：從直版中心裁
ow, oh = 1200, 630
left = (v.width - ow) // 2
top = int((v.height - oh) * 0.06)  # 略偏上，保留片名
v.crop((left, top, left + ow, top + oh)).save(
    os.path.join(OG, SLUG + ".jpg"), quality=88, optimize=True)
v.crop((left, top, left + ow, top + oh)).save(
    os.path.join(OG, SLUG + ".webp"), quality=85, method=6)

# 複檢角落 3 倍放大
v.crop((820, 1400, 1024, 1536)).resize((612, 408), Image.NEAREST).save(
    os.path.join(GEN, "_cuckoo_corner_check.png"))

print("完成八件套（直版系）：")
for f in ("-poster.png", "-poster.jpg", "-poster.webp",
          "-cover.jpg", "-cover.webp", ".jpg", ".webp"):
    p = os.path.join(OG, SLUG + f)
    print("  ", SLUG + f, os.path.getsize(p) // 1024, "KB")
