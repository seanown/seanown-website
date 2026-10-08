# -*- coding: utf-8 -*-
"""驗證封面在兩種裁切容器下的表現：
  1. 首頁「更多專欄」卡片  170px 高，object-fit:cover 中央裁切
  2. 輯頁時間軸 132×88，同樣中央裁切
中央裁切會保留左右各約 45%~55%，所以關鍵字必須落在中間區域。
"""
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT, 'assets', 'images', 'posts', '122-cover.jpg')
OUTD = os.path.join(ROOT, '_shots')
os.makedirs(OUTD, exist_ok=True)

im = Image.open(SRC).convert('RGB')
W, H = im.size
print('原圖 %dx%d' % (W, H))

# object-fit:cover 的中央裁切：先按比例縮放到容器高度，再從中心取寬度
cases = [('card-170', 400, 170), ('timeline-132x88', 132, 88)]
for name, cw, ch in cases:
    scale = ch / H
    # 容器寬度不足時，cover 會放大到「至少」蓋滿容器
    scale2 = cw / W
    s = max(scale, scale2)
    nh, nw = int(H * s), int(W * s)
    big = im.resize((nw, nh), Image.LANCZOS)
    left = (nw - cw) // 2
    cropped = big.crop((left, 0, left + cw, ch))
    p = os.path.join(OUTD, 'cover-test-%s.png' % name)
    cropped.save(p)
    # 檢查是否有非純色像素（文字）落在邊緣 5%
    px = cropped.load()
    edge_text = 0
    for x in range(cw):
        for y in range(ch):
            r, g, b = px[x, y]
            # 琥珀金 (199,91,18) 或米白 (247,243,234) 的高亮像素＝文字
            if (r > 180 and g > 140 and b < 120) or (r > 235 and g > 230 and b > 220):
                if x < cw * 0.06 or x > cw * 0.94:
                    edge_text += 1
    print('%s  裁切後 %dx%d  邊緣文字像素 %d %s'
          % (name, cw, ch, edge_text, 'OK' if edge_text == 0 else '← 有文字被切'))
    print('  → %s' % p)