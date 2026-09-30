import numpy as np
from PIL import Image, ImageFilter

im = Image.open('assets/og/Mondo_alternative_movie_poster_2026-09-30T03-47-06.png').convert('RGB')

# 標語牌區域（牌子邊框內）
X0, Y0, X1, Y1 = 128, 185, 302, 302
region = im.crop((X0, Y0, X1, Y1))
a = np.asarray(region).astype(np.int16)
r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]

# 紅棕描邊特徵：r 明顯大於 g（牌子底色 r≈g 黃綠）
stroke = (r - g > 22) & (r > 90)
print('描邊像素:', stroke.sum(), '/', stroke.size)

bg = a[~stroke & (g > 60)]   # 牌子底色（排除牌子外的深色）
mean = bg.mean(axis=0)
print('牌子底色均值:', mean.round(1))
a[stroke] = mean

region2 = Image.fromarray(a.clip(0,255).astype(np.uint8))
blurred = region2.filter(ImageFilter.GaussianBlur(1.0))
m = Image.fromarray((stroke*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
region2 = Image.composite(blurred, region2, m)
noise = np.asarray(Image.effect_noise(region2.size, 8).convert('L')).astype(np.int16) - 128
a2 = np.asarray(region2).astype(np.int16)
sub = (np.asarray(m).astype(np.int16) // 255)
for c in range(3):
    a2[:,:,c] += noise * sub // 9
region2 = Image.fromarray(a2.clip(0,255).astype(np.uint8))
im.paste(region2, (X0, Y0))
im.save('assets/og/Mondo_alternative_movie_poster_2026-09-30T03-47-06.png')

chk = np.asarray(im.crop((X0,Y0,X1,Y1)).convert('L')).astype(np.float64)
print('修補區 std: %.1f' % chk.std())
im.crop((100, 160, 340, 330)).resize((960, 680), Image.LANCZOS).save('tools/_fix_sign2.png')
print('done')
