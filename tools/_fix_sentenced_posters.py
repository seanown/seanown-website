# -*- coding: utf-8 -*-
"""#76《三狼奇案》海報修圖：去右下角浮水印 + 橫版右側招牌 AI 自加字
流程：remove_watermark 鏡像克隆 → 招牌區 fill_nonbase 填掉白色字 → 產八件套
"""
from PIL import Image, ImageFilter
import numpy as np

GEN = 'generated-images'
SRC_V = GEN + '/Mondo_alternative_movie_poster_2026-09-29T18-43-19.png'
SRC_H = GEN + '/LANDSCAPE_widescreen_compositi_2026-09-29T18-43-17.png'


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
    alpha = np.minimum(ax, ay)[..., None]
    region = base[y0:y1, x0:x1]
    base[y0:y1, x0:x1] = region * (1 - alpha) + pat * alpha
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


def fill_nonbase(img, rect, base_mask_fn, feather=2, seed=7):
    x0, y0, x1, y1 = rect
    region = np.asarray(img.crop(rect), dtype=np.float32)
    R, G, B = region[..., 0], region[..., 1], region[..., 2]
    base = base_mask_fn(R, G, B)
    txt = ~base
    m = Image.fromarray((txt * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
    txt = np.asarray(m) > 0
    bp = region[base]
    med = np.median(bp.reshape(-1, 3), axis=0) if bp.size else np.array([150., 140., 110.])
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 5, region.shape)
    fill = np.clip(med[None, None, :] + noise, 0, 255)
    region[txt] = fill[txt]
    out = Image.fromarray(np.clip(region, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5))
    base_img = np.asarray(img, dtype=np.float32)
    om = np.asarray(out, dtype=np.float32)
    h, w = y1 - y0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w]
    ax = np.minimum(np.minimum(xx, w - 1 - xx) / float(feather * 2), 1)
    ay = np.minimum(np.minimum(yy, h - 1 - yy) / float(feather * 2), 1)
    alpha = np.minimum(ax, ay)[..., None]
    base_img[y0:y1, x0:x1] = base_img[y0:y1, x0:x1] * (1 - alpha) + om * alpha
    return Image.fromarray(np.clip(base_img, 0, 255).astype(np.uint8))


v = Image.open(SRC_V).convert('RGB')
h = Image.open(SRC_H).convert('RGB')

# 兩圖浮水印
v = remove_watermark(v, (870, 1448, 1024, 1536), (700, 1448))
h = remove_watermark(h, (1382, 936, 1536, 1024), (1216, 936))

# 橫版右側 "DRIVING" 招牌 AI 自加字：棕色招牌上白色字 → 填成周圍棕色
base_fn = lambda R, G, B: (R > 140) & (G > 90) & (B < 130) & (R - B > 30) & (G - B > 10) & (R < 230)
h = fill_nonbase(h, (1260, 465, 1460, 520), base_fn)

v.save(GEN + '/_stl_v_clean.png')
h.save(GEN + '/_stl_h_clean.png')
print('saved cleaned')
