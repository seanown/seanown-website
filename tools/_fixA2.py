import numpy as np
from PIL import Image, ImageFilter

im = Image.open('assets/og/_v3_clean.png').convert('RGB')
X0,Y0,X1,Y1 = 62, 520, 157, 581
a = np.asarray(im.crop((X0,Y0,X1,Y1))).astype(np.float64)

# 逐列均值填充（保留招牌橫向光影漸變）+ 低頻垂直漸變
h, w, _ = a.shape
colmean = a.mean(axis=0)                      # 每列均值 (w,3)
fill = np.tile(colmean, (h,1,1))
# 噪點
noise = np.asarray(Image.effect_noise((w,h), 9).convert('L')).astype(np.float64) - 128
out = fill + noise[:,:,None]*0.9
out = out.clip(0,255).astype(np.uint8)

# 與原區域羽化混合（邊緣 6px 漸變，避免直邊）
orig = a.astype(np.float64)
mask = np.ones((h,w), dtype=np.float64)
F=6
for yy in range(h):
    for xx in range(w):
        d = min(xx, w-1-xx, yy, h-1-yy)
        if d < F: mask[yy,xx] = d/F
mask3 = mask[:,:,None]
blend = out*mask3 + orig*(1-mask3)
im.paste(Image.fromarray(blend.clip(0,255).astype(np.uint8)), (X0,Y0))
im.save('assets/og/_v3_clean.png')
im.crop((40,470,210,610)).resize((850,700), Image.LANCZOS).save('tools/_fixA2.png')
print('done')
