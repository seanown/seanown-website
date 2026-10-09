# -*- coding: utf-8 -*-
"""為 num 125（大象投資學第一堂 · 跟 Paulo Andrez 學天使投資）做封面 + OG 圖。

1200×630 橫幅。海軍藍 #0A1F3D ＋ 暖金 #C99A3F ＋ 宣紙米 #F7F3EA。
不用外部照片（避免真人肖像版權與裁切問題），改以「零風險靶心」同心圓
＋右側上升柱狀，呼應「鎖在資產上的四層防線」主題，純幾何、可控、可複用。

同一張設計同時輸出：
  · assets/images/posts/125-cover.jpg   （文章頁封面 images[0]）
  · assets/og/paulo-andrez-angel-investing.jpg  （社群分享 OG 圖）
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_COVER = os.path.join(ROOT, 'assets', 'images', 'posts', '125-cover.jpg')
OUT_OG = os.path.join(ROOT, 'assets', 'og', 'paulo-andrez-angel-investing.jpg')
FONT = 'C:/Windows/Fonts/NotoSansTC-VF.ttf'

W, H = 1200, 630

NAVY_DEEP = (10, 31, 61)    # 0A1F3D
NAVY_MID = (16, 42, 78)     # 102A4E
GOLD = (201, 154, 63)       # C99A3F
GOLD_L = (224, 188, 120)    # E0BC78
CREAM = (247, 243, 234)     # F7F3EA
DIM = (170, 184, 205)       # AAB8CD

X0 = 232          # 文字左起
TAG_X = 264       # 標籤左起


def font(size, bold=True):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_name('Bold' if bold else 'Regular')
    except Exception:
        pass
    return f


def vgrad(w, h, top, bot):
    img = Image.new('RGB', (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        r = y / max(h - 1, 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * r) for i in range(3)))
    return img


def render():
    base = vgrad(W, H, NAVY_DEEP, NAVY_MID).convert('RGBA')
    d = ImageDraw.Draw(base)

    # ---- 右側幾何動機：零風險靶心（同心圓）＋ 上升柱狀 ----
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cx, cy = 980, 300
    for r in (220, 168, 116, 64):
        ld.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(201, 154, 63, 38), width=2)
    ld.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=(201, 154, 63, 200))
    # 上升柱狀（右下落腳，象徵資產成長；避開底部作者列分隔線，不重疊）
    bars = [(120, 60), (160, 95), (200, 130)]
    bx = 820
    for i, (bw, bh) in enumerate(bars):
        x = bx + i * (bw + 22)
        ld.rectangle([x, H - 70 - bh, x + bw, H - 70], fill=(224, 188, 120, 150))
    base = Image.alpha_composite(base, layer).convert('RGB')
    d = ImageDraw.Draw(base)

    # ---- 左側金色豎線（落在中央安全區左緣）----
    d.rectangle([X0 - 32, 96, X0 - 24, 268], fill=GOLD)

    # ---- 標籤 ----
    f_tag = font(30)
    tag = '第一堂 · 大象投資學'
    tw = d.textlength(tag, font=f_tag)
    d.rounded_rectangle([TAG_X, 100, TAG_X + tw + 48, 156], radius=28, fill=GOLD)
    d.text((TAG_X + 24, 109), tag, font=f_tag, fill=NAVY_DEEP)

    # ---- 主標題（兩行）----
    f_t = font(76)
    d.text((X0, 200), '跟 Paulo Andrez', font=f_t, fill=CREAM)
    d.text((X0, 292), '學天使投資', font=f_t, fill=GOLD_L)

    # ---- 副標一行 ----
    f_s = font(32, False)
    d.text((X0 + 2, 406), '零風險，不是天賦，是一門可以學習的紀律', font=f_s, fill=DIM)

    # ---- 底部作者列 ----
    d.line([(X0, H - 122), (X0 + 540, H - 122)], fill=(40, 70, 110), width=2)
    d.text((X0, H - 100), '翁振軒  SEAN(大象)  ·  龍遊集團創辦人', font=font(32), fill=CREAM)
    d.text((X0, H - 56), '附四層防線與六個條款清單', font=font(26, False), fill=DIM)

    return base


def main():
    base = render()
    os.makedirs(os.path.dirname(OUT_COVER), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_OG), exist_ok=True)
    for p in (OUT_COVER, OUT_OG):
        base.save(p, 'JPEG', quality=86, optimize=True, progressive=True)
        print('輸出 %s  (%.0f KB)' % (p, os.path.getsize(p) / 1024))


if __name__ == '__main__':
    main()
