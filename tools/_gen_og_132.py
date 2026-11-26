# -*- coding: utf-8 -*-
"""為 num 132《「琉光璃彩」淄博琉璃藝術展澳門開幕》生成 OG 分享圖。

體例對齊先例（129 黃埔島／131 一縷銀光）：OG＝現場照裁切，非設計卡。
取 132-1.jpg（開幕主視覺，1320×990，換抬頭後即 hero）：等比縮到 1200×900 後自上偏裁
(0,40,1200,670)，保住「LUMINOUS BRILLIANCE／琉光璃彩／開幕典禮／淄博琉璃
藝術展」整組標題鎖排與上方主辦方 logo 行。新 og 檔不需升 OG_VER。
"""
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'images', 'posts', '132-1.jpg')
OUT = os.path.join(ROOT, 'assets', 'og', 'luminous-brilliance-zibo-liuli.jpg')

TW, TH = 1200, 630


def main():
    im = Image.open(SRC).convert('RGB')
    w, h = im.size
    im = im.resize((TW, round(h * TW / w)), Image.LANCZOS)
    # 目標高度 900；裁 y=40..670（保住 logo 行＋標題鎖排）
    top = 40
    assert im.size[1] - top >= TH, 'source too short: %s' % (im.size,)
    og = im.crop((0, top, TW, top + TH))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    og.save(OUT, 'JPEG', quality=88, optimize=True, progressive=True)
    print('輸出 %s  %dx%d  %.0f KB' % (OUT, og.size[0], og.size[1], os.path.getsize(OUT) / 1024))


if __name__ == '__main__':
    main()
