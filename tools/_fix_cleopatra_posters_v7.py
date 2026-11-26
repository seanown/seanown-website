# -*- coding: utf-8 -*-
"""女金剛鬥狂龍女 直版招牌金字重修 v7
v6 教訓：字高 20-35px 把紅帶切成上下小段，取「最長段」永遠躲開字。
v7：每列合併間隙≤45px 的紅段 → 整條招牌帶為一段 → 段內字像素用上下最近紅色局部插值。
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


def fix_sign(img, rect, tag='', seed=7):
    x0, y0, x1, y1 = rect
    region = np.asarray(img.crop(rect), dtype=np.float32).copy()
    R, G, B = region[..., 0], region[..., 1], region[..., 2]
    red = (R > 140) & (G < R * 0.52) & (R - B > 85)
    txt = ~red
    h, w = red.shape
    rng = np.random.default_rng(seed)
    nfilled = 0
    print(tag, 'red ratio %.3f' % red.mean())
    for x in range(w):
        col_red = red[:, x]
        # 合併間隙 ≤45px 的紅段
        segs = []
        s = None
        gap = 0
        for y in range(h):
            if col_red[y]:
                if s is None:
                    s = y
                gap = 0
            elif s is not None:
                gap += 1
                if gap > 45:
                    segs.append((s, y - gap))
                    s = None
                    gap = 0
        if s is not None:
            segs.append((s, h - 1 - (gap if col_red[h - 1] == False else 0)))
        if not segs:
            continue
        top, bot = max(segs, key=lambda t: t[1] - t[0])
        L = bot - top + 1
        if L < 15 or L > 110:
            continue
        if col_red[top:bot + 1].mean() < 0.12:
            continue
        # 段內 txt run
        y = top
        while y <= bot:
            if txt[y, x]:
                a = y
                while y <= bot and txt[y, x]:
                    y += 1
                b = y - 1
                up = None
                for yy in range(a - 1, top - 1, -1):
                    if col_red[yy]:
                        up = yy
                        break
                dn = None
                for yy in range(b + 1, bot + 1):
                    if col_red[yy]:
                        dn = yy
                        break
                if up is not None and dn is not None and dn - up <= 75:
                    for c in range(3):
                        t, btm = region[up, x, c], region[dn, x, c]
                        region[a:b + 1, x, c] = np.linspace(t, btm, b - a + 1)
                    region[a:b + 1, x] += rng.normal(0, 3, (b - a + 1, 3))
                    nfilled += 1
            else:
                y += 1
    print(tag, 'runs filled:', nfilled)
    out = Image.fromarray(np.clip(region, 0, 255).astype(np.uint8))
    orig = np.asarray(img, dtype=np.float32)
    om = np.asarray(out, dtype=np.float32)
    tm = Image.fromarray((txt * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(
        ImageFilter.GaussianBlur(1.5))
    a = (np.asarray(tm, dtype=np.float32) / 255.0)[..., None]
    orig[y0:y1, x0:x1] = orig[y0:y1, x0:x1] * (1 - a) + om * a
    return Image.fromarray(np.clip(orig, 0, 255).astype(np.uint8))


v = Image.open(SRC_V).convert('RGB')
print('src:', v.size)

v = fix_sign(v, (300, 528, 428, 608), tag='LeftSign')    # DRIGONI
v = fix_sign(v, (582, 528, 662, 608), tag='RightSign')   # IONIC
v = fix_sign(v, (370, 833, 675, 914), tag='Arch')        # LOIVE
v = remove_watermark(v, (870, 1448, 1024, 1536), (700, 1448))
v.save(GEN + '/_cleo_v_clean.png')
print('saved _cleo_v_clean.png')

for name, box in [('L', (300, 525, 430, 610)), ('R', (580, 525, 665, 610)), ('Arch', (365, 828, 680, 918))]:
    c = v.crop(box)
    c = c.resize((c.width * 3, c.height * 3), Image.LANCZOS)
    c.save(f'{GEN}/_fin7_v_{name}.png')
print('recheck crops saved')
