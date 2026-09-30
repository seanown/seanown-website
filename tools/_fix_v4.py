import numpy as np
from PIL import Image, ImageFilter

v = Image.open('assets/og/lets-sing-2021-poster.png').convert('RGB')

# ---- 1. 修 T 橫筆右臂缺口 (560,46)-(585,104)：從 T 橫筆左段 (505,46)-(530,104) 1:1 貼 ----
v.paste(v.crop((505, 46, 530, 104)), (560, 46))
print('T 右臂已補')

# ---- 2. 清掉橫筆下緣以下的撇號殘影 (552,104)-(592,120)：取頂部黑帶 ----
v.paste(v.crop((545, 0, 585, 16)), (552, 104))
print('殘影已清')

# ---- 3. 輕微混合邊界：對三個貼補矩形外緣 2px 做一次 0.5px 模糊，避免直邊 ----
# 已是真實同質材質 1:1，通常無痕；整體輕微無操作

v.save('assets/og/lets-sing-2021-poster.png')
v.crop((480, 30, 700, 200)).resize((880, 680), Image.LANCZOS).save('tools/_fix_v4.png')
v.crop((300, 20, 724, 320)).resize((848, 600), Image.LANCZOS).save('tools/_fix_v4full.png')
print('done')
