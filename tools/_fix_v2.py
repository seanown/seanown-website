import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

v = Image.open('assets/og/lets-sing-2021-poster.png').convert('RGB')

# ---- 1. 抹掉剛才貼歪的淡綠豎條 (560,46)-(590,108)，用同寬黑背景覆蓋 ----
# T-S 間隙下半 y 118-180 是乾淨黑背景，1:1 取帶
band = v.crop((560, 118, 590, 180)).transpose(Image.FLIP_TOP_BOTTOM)  # 30x62
v.paste(band, (560, 46))
print('豎條已抹除')

# ---- 2. 重貼撇號：傾斜圓角塊狀，材質取 T 頂部同高度 ----
# T 字母 x 502-557，其頂部橫筆 y 46-108 是同高度漸變材質
tex = v.crop((505, 46, 553, 106))   # 48x60
PW, PH = 26, 54                      # 撇號尺寸
tex = tex.resize((PW, PH), Image.LANCZOS)

# mask：圓角豎塊，頂部全圓、底部略窄，向右傾 7°
m = Image.new('L', (PW*3, PH*3), 0)
d = ImageDraw.Draw(m)
w3, h3 = PW*3, PH*3
d.rounded_rectangle([w3*0.18, h3*0.02, w3*0.82, h3*0.80], radius=w3*0.32, fill=255)
d.polygon([(w3*0.30, h3*0.80), (w3*0.70, h3*0.80), (w3*0.56, h3*1.0)], fill=255)
m = m.resize((PW, PH), Image.LANCZOS).rotate(7, expand=True, fillcolor=0, resample=Image.BICUBIC)
m = m.filter(ImageFilter.GaussianBlur(0.5))

PX, PY = 562, 46
ma = np.asarray(m).astype(np.float64)/255.0
mh, mw = ma.shape
va = np.asarray(v).astype(np.float64)
ta = np.asarray(tex).astype(np.float64)
# tex 是 48x60 裁自 T 頂部；m 旋轉後可能大於 (PW,PH)——從 tex 對應位置取
# 簡化：把 tex 擴展到 m 的尺寸（中心裁）
tex2 = tex.resize((mw, mh), Image.LANCZOS)
ta = np.asarray(tex2).astype(np.float64)
region = va[PY:PY+mh, PX:PX+mw, :]
for c in range(3):
    region[:,:,c] = ta[:,:,c]*ma + region[:,:,c]*(1-ma)
va[PY:PY+mh, PX:PX+mw, :] = region
v2 = Image.fromarray(va.clip(0,255).astype(np.uint8))
v2.save('assets/og/lets-sing-2021-poster.png')
print('撇號 v2 已貼', PX, PY, 'mask', mw, 'x', mh)

v2.crop((320, 10, 724, 220)).resize((1212, 630), Image.LANCZOS).save('tools/_fix_vtitle2.png')
print('done')
