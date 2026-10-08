# -*- coding: utf-8 -*-
"""把 ImageGen 產生的素材轉成簡報用乾淨版：
   1. 清除右下角「AI 生成」水印（從左側同高度取樣覆蓋）
   2. 轉 RGB、壓成簡報需要的尺寸、存 JPEG

用法：python _prep_assets.py
"""
import os
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))

JOBS = [
    # (來源, 輸出, 目標寬度)
    ('Elegant_ribbon_cutting_ceremon_2026-10-08T12-42-50.png', 'ribbon.jpg', 1280),
    ('Formal_Chinese_business_banque_2026-10-08T12-43-52.png', 'banquet.jpg', 1280),
]


def clear_watermark(img):
    """從左側同高度區域取樣覆蓋右下角水印，覆蓋後輕微模糊消除接縫。"""
    w, h = img.size
    bw, bh = 170, 58
    bx, by = w - bw - 6, h - bh - 4
    sx = max(0, bx - 300)
    patch = img.crop((sx, by, sx + bw, by + bh))
    patch = patch.filter(ImageFilter.GaussianBlur(1.8))
    img.paste(patch, (bx, by))
    return img


def main():
    for src, dst, tw in JOBS:
        sp = os.path.join(HERE, 'assets', src)
        if not os.path.exists(sp):
            print('略過（找不到來源）:', src)
            continue
        im = Image.open(sp).convert('RGB')
        im = clear_watermark(im)
        if im.width > tw:
            im = im.resize((tw, int(im.height * tw / im.width)), Image.LANCZOS)
        dp = os.path.join(HERE, 'assets', dst)
        im.save(dp, 'JPEG', quality=84, optimize=True, progressive=True)
        print('%s  %dx%d  %.0f KB' % (dst, im.width, im.height,
                                       os.path.getsize(dp) / 1024))
        # 原始 PNG 刪掉，簡報只需 JPEG
        os.remove(sp)


if __name__ == '__main__':
    main()