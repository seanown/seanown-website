# -*- coding: utf-8 -*-
"""為 num 143（軒哥課堂 AI 系列《AI 的終局：平台只剩兩件事，泡沫在二〇三〇年見真章》）做封面 + OG 圖。

1200×630 橫幅。海軍藍漸層 ＋ 暖金 ＋ 金色細邊框（沿用移交包「深藍底＋金色細邊框」規格，
與 126 封面同一家族）。右側金色上升折線收在一顆空心圓＝「泡沫見真章」的軌跡隱喻，
純幾何、無人物、無外部照片。

同一張設計同時輸出：
  · assets/images/posts/143-cover.jpg / .webp （文章頁封面 images[0]；首頁卡片 wsrc() 讀 .webp）
  · assets/og/ai-zhongju.jpg                  （社群分享 OG 圖，build 以 slug 取用）
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_COVER_JPG = os.path.join(ROOT, 'assets', 'images', 'posts', '143-cover.jpg')
OUT_COVER_WEBP = os.path.join(ROOT, 'assets', 'images', 'posts', '143-cover.webp')
OUT_OG = os.path.join(ROOT, 'assets', 'og', 'ai-zhongju.jpg')
FONT = 'C:/Windows/Fonts/NotoSansTC-VF.ttf'

W, H = 1200, 630

NAVY_DEEP = (10, 31, 61)     # 0A1F3D
NAVY_MID = (16, 42, 78)      # 102A4E
GOLD = (201, 154, 63)        # C99A3F
GOLD_L = (224, 188, 120)     # E0BC78
CREAM = (247, 243, 234)      # F7F3EA
DIM = (170, 184, 205)        # AAB8CD

X0 = 232          # 文字左起（左側金色豎線右側）
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

    # ---- 右側幾何動機：金色上升折線收在一顆空心圓（泡沫軌跡）----
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    pts = [(812, 486), (886, 420), (952, 446), (1032, 330)]
    ld.line(pts, fill=(201, 154, 63, 72), width=3)
    for p in pts:
        ld.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], fill=(201, 154, 63, 110))
    # 終點空心圓＝泡沫
    bx, by, br = 1082, 282, 30
    ld.ellipse([bx - br, by - br, bx + br, by + br], outline=(201, 154, 63, 150), width=3)
    base = Image.alpha_composite(base, layer).convert('RGB')
    d = ImageDraw.Draw(base)

    # ---- 金色細邊框（移交包規格：深藍底＋金色細邊框）----
    d.rectangle([22, 22, W - 22, H - 22], outline=GOLD, width=2)

    # ---- 左側金色豎線 ----
    d.rectangle([X0 - 32, 96, X0 - 24, 268], fill=GOLD)

    # ---- 標籤（金色文字，同 126 封面家族）----
    d.text((TAG_X, 104), 'AI 觀察 · SEAN OWN', font=font(30), fill=GOLD_L)

    # ---- 主標題（兩行）----
    f_t = font(72)
    d.text((X0, 192), 'AI 的終局', font=f_t, fill=CREAM)
    d.text((X0, 284), '平台只剩兩件事', font=f_t, fill=GOLD_L)

    # ---- 副標一行 ----
    d.text((X0 + 2, 398), '泡沫在二〇三〇年見真章', font=font(34, False), fill=DIM)

    # ---- 座右銘 ----
    d.text((X0 + 2, 456), '財 自 道 生 ， 利 緣 義 取', font=font(26, False), fill=GOLD)

    # ---- 底部作者列 ----
    d.line([(X0, H - 118), (X0 + 560, H - 118)], fill=(40, 70, 110), width=2)
    d.text((X0, H - 98), '翁振軒  SEAN OWN  ·  龍遊集團創辦人', font=font(30), fill=CREAM)
    d.text((X0, H - 54), '軒哥課堂 AI 系列 · 單篇完整課程八講', font=font(24, False), fill=DIM)

    return base


def main():
    base = render()
    os.makedirs(os.path.dirname(OUT_COVER_JPG), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_OG), exist_ok=True)
    for p in (OUT_COVER_JPG, OUT_OG):
        base.save(p, 'JPEG', quality=86, optimize=True, progressive=True)
        print('輸出 %s  (%.0f KB)' % (p, os.path.getsize(p) / 1024))
    base.save(OUT_COVER_WEBP, 'WEBP', quality=82, method=6)
    print('輸出 %s  (%.0f KB)' % (OUT_COVER_WEBP, os.path.getsize(OUT_COVER_WEBP) / 1024))


if __name__ == '__main__':
    main()
