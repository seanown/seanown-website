# -*- coding: utf-8 -*-
"""從123 封面右側裁出簡報用的乾淨視覺圖。

為什麼不另外生成：封面右側（x=620~1200）本來就是無文字的視覺區
（傳承交接的雙手與證書），裁切放大即可，省一次 ImageGen。
"""
import os
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'assets', 'images', 'posts', '123-cover.jpg')
DST_DIR = os.path.join(HERE, '商會幹部領導力', 'assets')
OUT = os.path.join(DST_DIR, 'hero.jpg')


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    im = Image.open(SRC).convert('RGB')

    #🔴 裁切起點必須避開封面上的文字。
    #實測：封面主標題 66px，「領導是做對的事，」從 x=232 到 x=760，
    #底部作者列與副標也在同一區域 → 裁切必須從 x=790 之後開始，
    #否則簡報背景會殘留淡淡的封面文字（第一版裁 620 造成）。
    LEFT = 790
    r = im.crop((LEFT, 0, 1200, 630))
    s = 1280 / r.width
    big = r.resize((1280, int(r.height * s)), Image.LANCZOS)
    top = (big.height - 720) // 2
    hero = big.crop((0, top, 1280, top + 720))
    hero = hero.filter(ImageFilter.GaussianBlur(0.5))
    # 稍微提亮，讓簡報的視覺看得出來
    from PIL import ImageEnhance
    hero = ImageEnhance.Brightness(hero).enhance(1.22)
    hero = ImageEnhance.Contrast(hero).enhance(1.06)
    hero.save(OUT, 'JPEG', quality=84, optimize=True, progressive=True)
    print('hero.jpg  %dx%d  %.0f KB  (裁切起點 x=%d)'
          % (hero.width, hero.height, os.path.getsize(OUT) / 1024, LEFT))


if __name__ == '__main__':
    main()