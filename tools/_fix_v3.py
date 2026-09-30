import numpy as np
from PIL import Image, ImageDraw, ImageFilter

v = Image.open('assets/og/lets-sing-2021-poster.png').convert('RGB')

# ---- 1. 抹掉貼錯位的撇號 (560,46)-(600,104)：用 S 右側同高黑背景 1:1 覆蓋 ----
v.paste(v.crop((622, 46, 662, 104)), (560, 46))   # 40x58 真實背景
print('錯位撇號已抹除')

# ---- 2. 重貼：間隙 T(右緣540) 與 S(左緣568) 之間 → x 541-566, y 47-102 ----
tex = v.crop((505, 47, 553, 107))   # T 頂部同高材質 48x60
PW, PH = 24, 55
tex = tex.resize((PW, PH), Image.LANCZOS)

m = Image.new('L', (PW*3, PH*3), 0)
d = ImageDraw.Draw(m)
w3, h3 = PW*3, PH*3
d.rounded_rectangle([w3*0.16, h3*0.02, w3*0.84, h3*0.72], radius=w3*0.34, fill=255)
d.polygon([(w3*0.32, h3*0.72), (w3*0.72, h3*0.72), (w3*0.60, h3*0.98)], fill=255)
m = m.resize((PW, PH), Image.LANCZOS).rotate(6, expand=True, fillcolor=0, resample=Image.BICUBIC)
m = m.filter(ImageFilter.GaussianBlur(0.5))

PX, PY = 542, 47
ma = np.asarray(m).astype(np.float64)/255.0
mh, mw = ma.shape
tex2 = tex.resize((mw, mh), Image.LANCZOS)
ta = np.asarray(tex2).astype(np.float64)
va = np.asarray(v).astype(np.float64)
region = va[PY:PY+mh, PX:PX+mw, :]
for c in range(3):
    region[:,:,c] = ta[:,:,c]*ma + region[:,:,c]*(1-ma)
va[PY:PY+mh, PX:PX+mw, :] = region
v2 = Image.fromarray(va.clip(0,255).astype(np.uint8))
v2.save('assets/og/lets-sing-2021-poster.png')
print('撇號 v3 已貼', PX, PY, 'mask', mw, 'x', mh)
v2.crop((330, 15, 700, 215)).resize((1110, 600), Image.LANCZOS).save('tools/_fix_vtitle3.png')
print('done')
