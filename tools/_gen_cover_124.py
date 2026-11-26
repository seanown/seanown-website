# -*- coding: utf-8 -*-
# 為 num 124《在南孔聖地，聽兩岸的聲音——一個回家的龍遊人》生成 og 封面（1200×630）。
#
# 沿用網站既有的 og 版面（參 assets/og/etiquette-is-not-form.jpg）：
#   深藍底 + 金色標籤 + 藍金幾何色塊 + 左側金色直線 + 底部作者資訊
# 版面重心留中央安全區（首頁卡片與輯頁縮圖會做中央裁切）。
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'og', 'quzhou-nankong-returning-home.jpg')
FONT = 'C:/Windows/Fonts/NotoSansTC-VF.ttf'

W, H = 1200, 630

# 取自網站主色
BLUE_D = (10, 32, 84)
BLUE_M = (16, 52, 128)
GOLD = (253, 181, 21)
CREAM = (247, 248, 251)
GREY = (150, 168, 205)

TAG_X = 84
TITLE_X = 84


def font(size):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_name('Bold')
    except Exception:
        pass
    return f


def vgrad(w, h, top, bot):
    """垂直漸層底色"""
    img = Image.new('RGB', (1, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.point((0, y), fill=(
            int(top[0] + (bot[0] - top[0]) * t),
            int(top[1] + (bot[1] - top[1]) * t),
            int(top[2] + (bot[2] - top[2]) * t)))
    return img.resize((w, h), Image.BICUBIC)


def fit(draw, text, maxw, start, minsize=26):
    """自動縮字：確保標題不超過 maxw"""
    s = start
    while s > minsize:
        f = font(s)
        if draw.textlength(text, font=f) <= maxw:
            return f
        s -= 2
    return font(minsize)


def main():
    img = vgrad(W, H, BLUE_D, (6, 22, 58)).convert('RGB')
    d = ImageDraw.Draw(img, 'RGBA')

    # ---- 背景斜切色塊（右下，藍→金，與既有 og 同一語彙）----
    poly = [(W, H), (W - 210, H), (W, H - 210)]
    d.polygon(poly, fill=(22, 66, 150, 255))
    poly2 = [(W, H), (W - 118, H), (W, H - 118)]
    d.polygon(poly2, fill=GOLD + (255,))

    # 右上淡藍弧（增加層次但不搶視覺）
    d.ellipse([W - 330, -230, W + 90, 190], fill=(30, 80, 178, 46))

    # ---- 左側金色直線 ----
    d.rectangle([58, 84, 66, 236], fill=GOLD + (255,))

    # ---- 分類標籤（膠囊）----
    tag = '生活隨筆'
    ft = font(30)
    tw = d.textlength(tag, font=ft)
    d.rounded_rectangle([TAG_X, 92, TAG_X + tw + 62, 152], radius=30,
                        fill=GOLD + (255,))
    d.text((TAG_X + 31, 100), tag, font=ft, fill=(8, 26, 66, 255))

    # ---- 日期 ----
    fd = font(27)
    d.text((TAG_X + tw + 84, 105), '2026-06-13', font=fd, fill=GREY + (255,))

    # ---- 主標題（最多兩行）----
    lines = ['在南孔聖地，', '聽兩岸的聲音']
    maxw = W - TITLE_X - 110
    f1 = fit(d, lines[0], maxw, 74)
    f2 = fit(d, lines[1], maxw, 74)
    d.text((TITLE_X, 196), lines[0], font=f1, fill=CREAM + (255,))
    d.text((TITLE_X, 288), lines[1], font=f2, fill=CREAM + (255,))

    # ---- 副標 ----
    fs = font(30)
    d.text((TITLE_X, 386), '一個回家的龍遊人', font=fs, fill=GOLD + (255,))

    # ---- 分隔線 ----
    d.rectangle([TAG_X, 452, W - 92, 456], fill=(120, 150, 205, 130))

    # ---- 作者資訊 ----
    d.text((TAG_X, 486), '翁振軒  Sean Own', font=font(35), fill=CREAM + (255,))
    d.text((TAG_X, 538), 'seanown.org  ·  澳門產業觀察與數位出海',
           font=font(26), fill=GREY + (255,))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, 'JPEG', quality=88, optimize=True)
    print('已輸出 %s' % OUT)
    print('尺寸 %dx%d  大小 %.1f KB'
          % (W, H, os.path.getsize(OUT) / 1024))


if __name__ == '__main__':
    main()
