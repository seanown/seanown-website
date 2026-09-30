import numpy as np
from PIL import Image, ImageFilter

SLUG = 'lets-sing-2021'
h = Image.open('assets/og/LANDSCAPE_widescreen_compositi_2026-09-30T03-50-34.png').convert('RGB')
RH = (1382, 936, 1536, 1024)
x0, y0, x1, y1 = RH
w, hh = x1 - x0, y1 - y0

band = h.crop((x0 - w, y0, x0, y1)).transpose(Image.FLIP_LEFT_RIGHT)
b = np.asarray(band).astype(np.float64)

# 噪點打散鏡像對稱
ns = np.asarray(Image.effect_noise((w, hh), 11).convert('L')).astype(np.float64) - 128
b = b + ns[:, :, None] * 1.1

# 羽化 alpha：上緣 26px 漸變、左緣 18px 漸變，其餘全貼
alpha = np.ones((hh, w), dtype=np.float64)
FX, FY = 18, 26
for yy in range(hh):
    for xx in range(w):
        a = 1.0
        if yy < FY: a = min(a, yy / FY)
        if xx < FX: a = min(a, xx / FX)
        alpha[yy, xx] = a
alpha = alpha[:, :, None]

region = np.asarray(h.crop(RH)).astype(np.float64)
patched = b * alpha + region * (1 - alpha)
h.paste(Image.fromarray(patched.clip(0, 255).astype(np.uint8)), (x0, y0))


a = np.asarray(h.crop(RH).convert('L')).astype(np.float64)
print('h wm std after:', round(a.std(), 1))

h.save(f'assets/og/{SLUG}-poster-land.png', optimize=True)
h.save(f'assets/og/{SLUG}-cover.jpg', quality=92, optimize=True)
h.save(f'assets/og/{SLUG}-cover.webp', quality=88, method=6)
og = h.resize((1200, 800), Image.LANCZOS).crop((0, 0, 1200, 630))
og.save(f'assets/og/{SLUG}.jpg', quality=92, optimize=True)
og.save(f'assets/og/{SLUG}.webp', quality=88, method=6)
h.crop((1280, 850, 1536, 1024)).resize((768, 522), Image.LANCZOS).save('tools/_wmchk_h2.png')
print('done')
