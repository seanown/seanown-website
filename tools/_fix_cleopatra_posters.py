# -*- coding: utf-8 -*-
"""#71 女金剛鬥狂龍女 海報修圖 v2：去 AI 加字＋去浮水印（從原圖重來）"""
from PIL import Image, ImageFilter
import numpy as np

GEN = 'generated-images'
SRC_V = GEN + '/Mondo_alternative_movie_poster_2026-09-29T17-39-37.png'
SRC_H = GEN + '/LANDSCAPE_widescreen_compositi_2026-09-29T17-39-35.png'


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


def fill_nonbase(img, rect, base_mask_fn, feather=2, seed=7):
    """rect 內：非底色像素（文字+描邊）→ 底色中值+噪聲；邊緣羽化融合。"""
    x0, y0, x1, y1 = rect
    region = np.asarray(img.crop(rect), dtype=np.float32)
    R, G, B = region[..., 0], region[..., 1], region[..., 2]
    base = base_mask_fn(R, G, B)
    txt = ~base
    # dilate 吃描邊
    m = Image.fromarray((txt * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
    txt = np.asarray(m) > 0
    bp = region[base]
    med = np.median(bp.reshape(-1, 3), axis=0) if bp.size else np.array([150, 60, 45.])
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 6, region.shape)
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


def clone_fill(img, rect, src_xy, feather=3):
    """從 src_xy 取同尺寸 patch 平移蓋到 rect。"""
    x0, y0, x1, y1 = rect
    sx, sy = src_xy
    w, h = x1 - x0, y1 - y0
    patch = img.crop((sx, sy, sx + w, sy + h))
    base = np.asarray(img, dtype=np.float32)
    pat = np.asarray(patch, dtype=np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    ax = np.clip(xx / float(feather), 0, 1)
    ay = np.clip(yy / float(feather), 0, 1)
    alpha = np.minimum(ax, ay)[..., None].astype(np.float32)
    region = base[y0:y1, x0:x1]
    base[y0:y1, x0:x1] = region * (1 - alpha) + pat * alpha
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


# 紅底（招牌帶）
red_base = lambda R, G, B: (R > 120) & (R - G > 45) & (R - B > 55)
# 灰匾底
grey_base = lambda R, G, B: (np.abs(R - G) < 45) & (R < 210) & (R > 60)

v = Image.open(SRC_V).convert('RGB')
h_ = Image.open(SRC_H).convert('RGB')
print('src:', v.size, h_.size)

# ── 直版：三處紅帶金字 ──
v = fill_nonbase(v, (342, 551, 420, 586), red_base)   # 左柱 DELGONI
v = fill_nonbase(v, (592, 551, 648, 583), red_base)   # 右柱 ONIK
v = fill_nonbase(v, (418, 844, 578, 892), red_base)   # 拱門 LOIVE
# 直版浮水印
v = remove_watermark(v, (870, 1448, 1024, 1536), (700, 1448))
v.save(GEN + '/_cleo_v_clean.png')

# ── 橫版：灰匾「澳門」→ 乾淨灰帶克隆（兩段平鋪）──
h_ = clone_fill(h_, (662, 447, 702, 489), (618, 447))   # 蓋「澳」
h_ = clone_fill(h_, (702, 447, 742, 489), (618, 447))   # 蓋「門」
# 橫版浮水印
h_ = remove_watermark(h_, (1382, 936, 1536, 1024), (1216, 936))
h_.save(GEN + '/_cleo_h_clean.png')

print('saved cleaned')

# ── 複檢裁圖 ──
v.crop((320, 520, 680, 620)).resize((1080, 300)).save(GEN + '/_recheck_v_cols.png')
v.crop((390, 815, 610, 925)).resize((880, 440)).save(GEN + '/_recheck_v_arch.png')
h_.crop((600, 420, 800, 520)).resize((1000, 500)).save(GEN + '/_recheck_h_macau.png')
print('recheck crops saved')
