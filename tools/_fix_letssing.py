import random
import numpy as np
from PIL import Image, ImageFilter, ImageChops

random.seed(11)

# ============ 1. 橫版：抹掉戲院拱形橫幅上的金色「新馬路」三字 ============
h = Image.open('assets/og/lets-sing-2021-poster-land.png').convert('RGB')
X0, Y0, X1, Y1 = 1218, 195, 1350, 282   # 字帶區域（含邊距）
region = h.crop((X0, Y0, X1, Y1))
a = np.asarray(region).astype(np.int16)

r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]
# 金字特徵：綠分量明顯高於紅底（紅底 g≈40-70，金字 g≈120-200）
gold = (g > 100) & (r > 120)
# 紅底均值（非金字像素）
bg = a[~gold]
print('金字像素:', gold.sum(), '/', gold.size, '| 紅底均值:', bg.mean(axis=0).round(1))
mean_r, mean_g, mean_b = bg.mean(axis=0)
a[gold] = [mean_r, mean_g, mean_b]

# 邊緣過渡：金字周邊 1px 也輕微調暗（去金暈）
halo = (g > 85) & ~gold
a[halo] = [mean_r*0.96, mean_g*0.9, mean_b*0.9]

region2 = Image.fromarray(a.clip(0,255).astype(np.uint8))
# 輕微模糊打散替換痕跡，再與原區混合只模糊替換過的像素
blurred = region2.filter(ImageFilter.GaussianBlur(0.8))
m = Image.fromarray(((gold | halo)*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
region2 = Image.composite(blurred, region2, m)
# 加噪打散
noise = np.asarray(Image.effect_noise(region2.size, 7).convert('L')).astype(np.int16) - 128
a2 = np.asarray(region2).astype(np.int16)
sub = np.asarray(m).astype(np.int16) // 255
for c in range(3):
    a2[:,:,c] += (noise * sub // 10)
region2 = Image.fromarray(a2.clip(0,255).astype(np.uint8))
h.paste(region2, (X0, Y0))
h.save('assets/og/lets-sing-2021-poster-land.png')

# 修補區 std 檢查
chk = np.asarray(h.crop((X0, Y0, X1, Y1)).convert('L')).astype(np.float64)
print('橫版修補區 std: %.1f' % chk.std())

# ============ 2. 直版：把橫版撇號移植過來 ============
v = Image.open('assets/og/lets-sing-2021-poster.png').convert('RGB')

# 2a. 從橫版取撇號形狀（米色字 vs 深棕背景 → 灰度閾值）
apos = h.crop((568, 30, 604, 82))       # 橫版 LET'S 的撇號（含少量背景）
ag = np.asarray(apos.convert('L')).astype(np.int16)
shape = (ag > 120).astype(np.uint8)
ys, xs = np.where(shape)
shape = shape[ys.min():ys.max()+1, xs.min():xs.max()+1]
sh_img = Image.fromarray((shape*255).astype(np.uint8))
print('撇號形狀原始尺寸:', sh_img.size)

# 2b. 縮放到直版間隙大小（T 與 S 之間，目標約 30x62）
target = (30, 62)
sh = sh_img.resize(target, Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
sh_a = (np.asarray(sh).astype(np.float64) / 255)

# 2c. 從直版第一行 S 字母表面取綠色顆粒材質
tex = v.crop((604, 76, 664, 140))       # S 上半部綠色區
tex = tex.resize(target, Image.LANCZOS)

# 2d. 貼到 T(右緣~557) 與 S(左緣~595) 之間：x 560-590, y 46-108
PX, PY = 560, 46
va = np.asarray(v).astype(np.float64)
ta = np.asarray(tex).astype(np.float64)
for c in range(3):
    va[PY:PY+target[1], PX:PX+target[0], c] = (
        ta[:,:,c]*sh_a + va[PY:PY+target[1], PX:PX+target[0], c]*(1-sh_a))
v2 = Image.fromarray(va.clip(0,255).astype(np.uint8))
v2.save('assets/og/lets-sing-2021-poster.png')
print('撇號已貼於', PX, PY)

# ============ 3. 放大複檢圖 ============
h.crop((1150, 150, 1500, 420)).resize((1050, 810), Image.LANCZOS).save('tools/_fix_sign.png')
v.crop((320, 10, 724, 220)).resize((1212, 630), Image.LANCZOS).save('tools/_fix_vtitle.png')
print('done')
