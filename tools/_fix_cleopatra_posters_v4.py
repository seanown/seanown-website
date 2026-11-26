# -*- coding: utf-8 -*-
"""女金剛鬥狂龍女 直版紅帶金字重修 v4
v2 教訓：red_base (R-G>45) 把金字(R-G≈50)誤判成底色 → mask 空 → 沒填。
v4 策略：嚴格紅底(R-G>85)定位紅帶行 → 行內金字/白字/描邊全標記 → 逐行水平插值 inpaint + 噪聲。
"""
from PIL import Image, ImageFilter
import numpy as np

GEN = 'generated-images'
SRC_V = GEN + '/Mondo_alternative_movie_poster_2026-09-29T17-39-37.png'


def clean_band(img, rect, dilate=9, seed=7, tag=''):
    x0, y0, x1, y1 = rect
    region = np.asarray(img.crop(rect), dtype=np.float32).copy()
    R, G, B = region[..., 0], region[..., 1], region[..., 2]
    # 嚴格紅底：R-G 很大
    red_strict = (R > 110) & (R - G > 85) & (R - B > 95)
    # 金字：偏黃（G/R 高於紅底）
    gold = (R > 125) & (G > R * 0.52) & (B < R * 0.82) & ~red_strict
    # 白/淺字
    white = (R > 185) & (G > 160) & (B > 130)
    # 深色描邊（僅紅帶行內）
    dark = (R < 120) & (G < 95)
    txt = gold | white | dark
    row_red = red_strict.mean(axis=1) > 0.22
    txt &= row_red[:, None]
    if not txt.any():
        print(tag, 'no text pixels found');  return img
    ys, xs = np.nonzero(txt)
    print(tag, 'txt px:', txt.sum(), 'bbox x', xs.min()+x0, xs.max()+x0, 'y', ys.min()+y0, ys.max()+y0)
    m = Image.fromarray((txt * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(dilate))
    txt = np.asarray(m) > 0
    txt &= row_red[:, None]  # dilate 後仍限制在紅帶行
    h, w = txt.shape
    rng = np.random.default_rng(seed)
    for i in range(h):
        if not row_red[i]:
            continue
        clean = ~txt[i]
        if clean.sum() < 2:
            continue
        idx = np.flatnonzero(clean)
        for c in range(3):
            region[i, :, c] = np.interp(np.arange(w), idx, region[i, clean, c])
    region[txt] += rng.normal(0, 5, region[txt].shape)
    region = np.clip(region, 0, 255)
    out = Image.fromarray(region.astype(np.uint8))
    # 融合：僅在 txt 區域用新值（其餘保留原圖），邊緣羽化
    orig = np.asarray(img, dtype=np.float32)
    alpha = np.zeros((h, w), dtype=np.float32)
    am = Image.fromarray((txt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    alpha = np.asarray(am, dtype=np.float32) / 255.0
    blended = orig[y0:y1, x0:x1] * (1 - alpha[..., None]) + region * alpha[..., None]
    orig[y0:y1, x0:x1] = blended
    return Image.fromarray(np.clip(orig, 0, 255).astype(np.uint8))


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
    alpha = np.minimum(ax, ay)[..., None].astype(np.float32)
    region = base[y0:y1, x0:x1]
    base[y0:y1, x0:x1] = region * (1 - alpha) + pat * alpha
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


v = Image.open(SRC_V).convert('RGB')
print('src:', v.size)

# 三處紅帶（搜索區已放寬）
v = clean_band(v, (315, 520, 480, 615), tag='Lcol')
v = clean_band(v, (555, 520, 690, 615), tag='Rcol')
v = clean_band(v, (385, 818, 615, 922), dilate=11, tag='Arch')
# 浮水印（沿用 v2 參數）
v = remove_watermark(v, (870, 1448, 1024, 1536), (700, 1448))
v.save(GEN + '/_cleo_v_clean.png')
print('saved _cleo_v_clean.png')

# 複檢放大圖
for name, box in [('Lcol', (315, 525, 480, 610)), ('Rcol', (555, 525, 690, 610)), ('Arch', (390, 825, 610, 918))]:
    c = v.crop(box)
    c = c.resize((c.width * 3, c.height * 3), Image.LANCZOS)
    c.save(f'{GEN}/_fin4_v_{name}.png')
print('recheck crops saved')
