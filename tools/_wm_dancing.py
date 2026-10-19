# -*- coding: utf-8 -*-
"""去浮水印：同源鄰域取樣（牆面/地面延伸）＋四邊羽化＋噪點。純 PIL，不依賴 numpy。
不可用 GaussianBlur（依 memory 鐵律）。
"""
import random
from PIL import Image

random.seed(20261019)

# (src, dst, dst_box, src_box)  — dst_box 為要覆蓋的矩形(x,y,w,h)
# src_box 為取樣來源，同尺寸，取自同一面牆的無字區域
JOBS = [
    # v4 寫實版：直版 1024x1536 水印 (876,1470,148,66)，取樣自上方同牆暗部
    ('generated-images/_dancing-poster-v3.png',
     'generated-images/_dancing-poster-v4.png',
     (901, 1473, 115, 55),
     (901, 1400, 115, 55), 0, 0),
    # 橫版 1536x1024 水印 (1413,960,123,64)，取樣自左側同色暗牆
    ('generated-images/_dancing-land-v4.png',
     'generated-images/_dancing-land-v5.png',
     (1408, 956, 122, 62),
     (1280, 956, 122, 62), 0, 0),
]


def make_mask(bw, bh, feather=None):
    """四邊羽化 alpha，中間完全不透明。羽化不得讓上下/左右漸變重疊，
    否則小尺寸矩形會整個被過渡區吃掉（實測踩過）。"""
    if feather is None:
        feather = max(4, min(bw, bh) // 6)
    if feather == 0:
        return Image.new('L', (bw, bh), 255)
    fy = max(2, feather)
    fx = max(2, feather)
    m = Image.new('L', (bw, bh), 255)
    if fy * 2 < bh:
        for x in range(bw):
            for i in range(fy):
                v = int(255 * (i + 1) / (fy + 1))
                m.putpixel((x, i), v)
                m.putpixel((x, bh - 1 - i), v)
    if fx * 2 < bw:
        for y in range(bh):
            for i in range(fx):
                v = int(255 * (i + 1) / (fx + 1))
                m.putpixel((i, y), v)
                m.putpixel((bw - 1 - i, y), v)
    return m


def process(src, dst, dst_box, src_box, noise=14, feather=None):
    im = Image.open(src).convert('RGB')
    W, H = im.size
    dx, dy, bw, bh = dst_box
    sx, sy, sw, sh = src_box
    patch = im.crop((sx, sy, sx + sw, sy + sh))
    if patch.size != (bw, bh):
        patch = patch.resize((bw, bh), Image.BICUBIC)
    mask = make_mask(bw, bh, feather=feather)
    im.paste(patch, (dx, dy), mask)
    # 噪點破壞均勻感，避免看出貼合
    px = im.load()
    for i in range(dy, min(dy + bh, H)):
        for j in range(dx, min(dx + bw, W)):
            r, g, b = px[j, i]
            n = random.randint(-noise, noise) if noise else 0
            px[j, i] = (max(0, min(255, r + n)),
                        max(0, min(255, g + n)),
                        max(0, min(255, b + n)))
    im.save(dst)
    print('done', dst, '| sample', src_box, '-> cover', dst_box)


for j in JOBS:
    process(*j)
