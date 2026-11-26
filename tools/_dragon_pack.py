import numpy as np
from PIL import Image, ImageFilter
import os

SLUG = 'dragon-1993'

def remove_watermark(im, rect, band_w=154):
    x0, y0, x1, y1 = rect
    w = x1 - x0
    band = im.crop((x0 - band_w, y0, x0, y1)).transpose(Image.FLIP_LEFT_RIGHT)
    b = np.asarray(band).astype(np.float64)
    ns = np.asarray(Image.effect_noise((w, y1-y0), 11).convert('L')).astype(np.float64) - 128
    b = b + ns[:,:,None]*1.1
    region = np.asarray(im.crop(rect)).astype(np.float64)
    alpha = np.ones((y1-y0, w), dtype=np.float64)
    FX, FY = 18, 26
    for yy in range(y1-y0):
        for xx in range(w):
            a = 1.0
            if yy < FY: a = min(a, yy/FY)
            if xx < FX: a = min(a, xx/FX)
            alpha[yy, xx] = a
    patched = b*alpha[:,:,None] + region*(1-alpha[:,:,None])
    im.paste(Image.fromarray(patched.clip(0,255).astype(np.uint8)), (x0,y0))
    return im

def std_of(im, rect):
    return round(np.asarray(im.crop(rect).convert('L')).astype(np.float64).std(), 1)

v = Image.open(f'assets/og/{SLUG}-poster.png').convert('RGB')
h = Image.open(f'assets/og/{SLUG}-poster-land.png').convert('RGB')
RV, RH = (870,1448,1024,1536), (1382,936,1536,1024)
print('v std before:', std_of(v, RV), '| h std before:', std_of(h, RH))
v = remove_watermark(v, RV)
h = remove_watermark(h, RH)
print('v std after:', std_of(v, RV), '| h std after:', std_of(h, RH))

v.save(f'assets/og/{SLUG}-poster.png', optimize=True)
v.save(f'assets/og/{SLUG}-poster.jpg', quality=92, optimize=True)
v.save(f'assets/og/{SLUG}-poster.webp', quality=88, method=6)
h.save(f'assets/og/{SLUG}-poster-land.png', optimize=True)
h.save(f'assets/og/{SLUG}-cover.jpg', quality=92, optimize=True)
h.save(f'assets/og/{SLUG}-cover.webp', quality=88, method=6)
og = h.resize((1200,800), Image.LANCZOS).crop((0,0,1200,630))
og.save(f'assets/og/{SLUG}.jpg', quality=92, optimize=True)
og.save(f'assets/og/{SLUG}.webp', quality=88, method=6)
for f in [f'{SLUG}-poster.png',f'{SLUG}-poster.jpg',f'{SLUG}-poster.webp',f'{SLUG}-poster-land.png',
          f'{SLUG}-cover.jpg',f'{SLUG}-cover.webp',f'{SLUG}.jpg',f'{SLUG}.webp']:
    p=f'assets/og/{f}'; print(f, Image.open(p).size, os.path.getsize(p))
# 角落目檢圖
v.crop((770,1350,1024,1536)).resize((762,558), Image.LANCZOS).save('tools/_wmchk_dv.png')
h.crop((1280,850,1536,1024)).resize((768,522), Image.LANCZOS).save('tools/_wmchk_dh.png')
print('done')
