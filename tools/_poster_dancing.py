# -*- coding: utf-8 -*-
"""《與你相遇的日子》海報八件套：poster/cover + OG。
OG＝橫版 cover裁出 1200x630（依 memory 鐵律，絕不可跑 tools/build_og.py）。
"""
import os
from PIL import Image

SLUG = 'dancing-in-the-sea-breeze-2024'
SRC_P = 'generated-images/_dancing-poster-final.png'
SRC_L = 'generated-images/_dancing-land-final.png'
OUT = 'assets/og'

os.makedirs(OUT, exist_ok=True)

p = Image.open(SRC_P).convert('RGB')
l = Image.open(SRC_L).convert('RGB')

# 1) poster 直版
p.save(f'{OUT}/{SLUG}-poster.png')
p.save(f'{OUT}/{SLUG}-poster.jpg', quality=92)

# 2) cover 橫版
l.save(f'{OUT}/{SLUG}-poster-land.png')
l.save(f'{OUT}/{SLUG}-poster-land.jpg', quality=92)

# 3) OG 1200x630：從橫版中央裁出（片名在上方，故取上偏 1/3 保持建築主體）
TW, TH = 1200, 630
src_w, src_h = l.size
# 橫版 1536x1024 -> 目標 1200x630，比例 1.905:1。取寬 1400、高 735 的區域
cw = 1400
ch = int(cw * TH / TW)          # 735
# 垂直位置略偏上，保留建築與天空
left = (src_w - cw) // 2
top = max(0, int((src_h - ch) * 0.06))
og = l.crop((left, top, left + cw, top + ch)).resize((TW, TH), Image.LANCZOS)
og.save(f'{OUT}/{SLUG}.png')
og.save(f'{OUT}/{SLUG}.jpg', quality=92)

# 4) 給 build 用的小圖（若需要）
for name, im in [('poster', p), ('poster-land', l)]:
    s = im.copy()
    s.thumbnail((1000, 1000), Image.LANCZOS)
    s.save(f'generated-images/_dancing-{name}-small.jpg', quality=88)

print('八件套完成')
for f in sorted(os.listdir(OUT)):
    if SLUG in f:
        print(' ', f, os.path.getsize(os.path.join(OUT, f)), 'bytes')
print('OG裁切來源:', (left, top, left + cw, top + ch))
