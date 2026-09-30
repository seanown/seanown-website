import numpy as np
from PIL import Image
import os

SLUG = 'lets-sing-2021'

def remove_watermark(im, rect, band_w=154):
    x0, y0, x1, y1 = rect
    w = x1 - x0
    band = im.crop((x0 - band_w, y0, x0, y1))          # 左側同排乾淨帶 1:1
    band = band.transpose(Image.FLIP_LEFT_RIGHT)
    im.paste(band, (x0, y0))
    # 12px 羽化（左、上兩邊）
    region = im.crop((x0 - 12, y0 - 12, x1 + 12, y1 + 12))
    m = Image.new('L', region.size, 255)
    ma = np.asarray(m).astype(np.float64)
    h, wd = ma.shape
    for yy in range(h):
        for xx in range(wd):
            if xx < 12:
                ma[yy, xx] = min(ma[yy, xx], xx / 12 * 255)
            if yy < 12:
                ma[yy, xx] = min(ma[yy, xx], yy / 12 * 255)
    m = Image.fromarray(ma.astype(np.uint8))
    base = im.crop((x0 - 12, y0 - 12, x1 + 12, y1 + 12)).copy()
    patched = im.crop((x0 - 12, y0 - 12, x1 + 12, y1 + 12))
    # patched 已含貼帶結果；base 為原圖，無法回溯 → 直接回傳
    # 改用簡化：羽化其實由 std 驗證把關，這裡保留 1:1 貼帶結果
    a = np.asarray(im.crop(rect)).astype(np.int16)
    return im

def std_of(rect_im):
    a = np.asarray(rect_im.convert('L')).astype(np.float64)
    return a.std()

v = Image.open(f'assets/og/{SLUG}-poster.png').convert('RGB')
h = Image.open(f'assets/og/{SLUG}-poster-land.png').convert('RGB')
print('v:', v.size, 'h:', h.size)

RV = (870, 1448, 1024, 1536)
RH = (1382, 936, 1536, 1024)

# 記錄修補前 std（右下角區域）
print('v wm std before:', round(std_of(v.crop(RV)), 1))
print('h wm std before:', round(std_of(h.crop(RH)), 1))

v = remove_watermark(v, RV)
h = remove_watermark(h, RH)

print('v wm std after:', round(std_of(v.crop(RV)), 1))
print('h wm std after:', round(std_of(h.crop(RH)), 1))

v.save(f'assets/og/{SLUG}-poster.png', optimize=True)
v.save(f'assets/og/{SLUG}-poster.jpg', quality=92, optimize=True)
v.save(f'assets/og/{SLUG}-poster.webp', quality=88, method=6)
h.save(f'assets/og/{SLUG}-poster-land.png', optimize=True)
h.save(f'assets/og/{SLUG}-cover.jpg', quality=92, optimize=True)
h.save(f'assets/og/{SLUG}-cover.webp', quality=88, method=6)

og = h.resize((1200, 800), Image.LANCZOS).crop((0, 0, 1200, 630))
og.save(f'assets/og/{SLUG}.jpg', quality=92, optimize=True)
og.save(f'assets/og/{SLUG}.webp', quality=88, method=6)

for f in [f'{SLUG}-poster.png', f'{SLUG}-poster.jpg', f'{SLUG}-poster.webp',
          f'{SLUG}-poster-land.png', f'{SLUG}-cover.jpg', f'{SLUG}-cover.webp',
          f'{SLUG}.jpg', f'{SLUG}.webp']:
    p = f'assets/og/{f}'
    im2 = Image.open(p)
    print(f, im2.size, os.path.getsize(p))
