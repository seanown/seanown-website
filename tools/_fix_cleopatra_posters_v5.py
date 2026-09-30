# -*- coding: utf-8 -*-
"""女金剛鬥狂龍女 直版紅帶金字重修 v5
思路：招牌紅帶是弧形帶 → 逐「列」找最長連續紅段，整段用上下端點色垂直插值重鋪＋噪聲。
段外完全不动（保住柱子/手臂/背景），不會出現 v4 的整行橫線。
"""
from PIL import Image, ImageFilter
import numpy as np

GEN = 'generated-images'
SRC_V = GEN + '/Mondo_alternative_movie_poster_2026-09-29T17-39-37.png'


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


def resurface_band(img, rect, min_seg=8, seed=7, tag=''):
    x0, y0, x1, y1 = rect
    region = np.asarray(img.crop(rect), dtype=np.float32).copy()
    R, G, B = region[..., 0], region[..., 1], region[..., 2]
    red = (R > 105) & (R - G > 70) & (R - B > 80)
    h, w = red.shape
    rng = np.random.default_rng(seed)
    filled_cols = 0
    for x in range(w):
        col = red[:, x]
        # 最長連續 True 段
        best_s = best_e = -1
        s = None
        for y in range(h):
            if col[y] and s is None:
                s = y
            elif not col[y] and s is not None:
                if y - s > best_e - best_s:
                    best_s, best_e = s, y - 1
                s = None
        if s is not None and h - s > best_e - best_s:
            best_s, best_e = s, h - 1
        if best_s < 0 or (best_e - best_s + 1) < min_seg:
            continue
        top, bot = best_s, best_e
        # 段內金字/描邊等非紅像素才需要重鋪；純紅段跳過
        seg = region[top:bot + 1, x]
        segR = seg[:, 0]
        is_red = red[top:bot + 1, x]
        if is_red.all():
            continue
        # 垂直插值：端點取段頂/段底原色
        for c in range(3):
            t, b = seg[0, c], seg[-1, c]
            seg[:, c] = np.linspace(t, b, bot - top + 1)
        region[top:bot + 1, x] = seg
        filled_cols += 1
    region += rng.normal(0, 4, region.shape) * 0  # 先不加噪聲，看效果
    print(tag, 'filled cols:', filled_cols, '/', w)
    out = Image.fromarray(np.clip(region, 0, 255).astype(np.uint8))
    # 輕微模糊只在填充處（整體 0.4 不傷其他區域太多）
    orig = np.asarray(img, dtype=np.float32)
    # 用與 red 相反的 mask 做羽化融合：填充區=非紅且在段內 → 簡化：整區微混合
    om = np.asarray(out.filter(ImageFilter.GaussianBlur(0.6)), dtype=np.float32)
    # 僅混合非紅像素（字/描邊位置）
    blur_mask = Image.fromarray(((~red) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    a = (np.asarray(blur_mask, dtype=np.float32) / 255.0)[..., None]
    orig[y0:y1, x0:x1] = orig[y0:y1, x0:x1] * (1 - a) + om * a
    return Image.fromarray(np.clip(orig, 0, 255).astype(np.uint8))


v = Image.open(SRC_V).convert('RGB')
print('src:', v.size)

v = resurface_band(v, (315, 520, 480, 615), tag='Lcol')
v = resurface_band(v, (555, 520, 690, 615), tag='Rcol')
v = resurface_band(v, (385, 818, 615, 922), min_seg=12, tag='Arch')
v = remove_watermark(v, (870, 1448, 1024, 1536), (700, 1448))
v.save(GEN + '/_cleo_v_clean.png')
print('saved _cleo_v_clean.png')

for name, box in [('Lcol', (315, 525, 480, 610)), ('Rcol', (555, 525, 690, 610)), ('Arch', (390, 825, 610, 918))]:
    c = v.crop(box)
    c = c.resize((c.width * 3, c.height * 3), Image.LANCZOS)
    c.save(f'{GEN}/_fin5_v_{name}.png')
print('recheck crops saved')
