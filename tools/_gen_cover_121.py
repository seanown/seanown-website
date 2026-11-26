# -*- coding: utf-8 -*-
"""為 num 121 做一張「更多專欄」卡片專用封面（1200×630，橫幅）。

為什麼不用現有素材：
- assets/images/posts/deck-meeting-sop/deck-01.jpg 是 PPT 封面，直式大標題在
  170px 高的卡片裡被裁成看不清。
- assets/og/meeting-ends-things-begin.jpg 是 1200×630 OG 圖，但那是給微信/
  Line 分享用的，卡片裡字會偏小。

這裡專門排一版橫式：左側大標題、右側視覺，170px 高度下仍讀得清楚。

🔴 版面重心必須留在「中央安全區」：
這張圖會出現在兩種容器，裁切方式不同——
  · 首頁「更多專欄」卡片 170px 高，object-fit:cover 中央裁切
  · 輯頁時間軸 132×88，同樣中央裁切 → 只保留左右各約 45%~55%
所以主標題與標籤都排在中間偏左（x=232 起），不可再推到 x=104，
否則輯頁縮圖會把「第一堂」標籤與主標題左半切掉。
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'images', 'posts', '121-cover.jpg')
DECK_COVER = os.path.join(ROOT, 'slides', 'meeting-sop', 'assets', 'cover_table.jpg')
FONT = 'C:/Windows/Fonts/NotoSansTC-VF.ttf'

W, H = 1200, 630
BG_DEEP = (7, 46, 33)
BG_MID = (11, 61, 46)
AMBER = (199, 91, 18)
AMBER_L = (240, 160, 80)
CREAM = (247, 243, 234)
DIM = (168, 190, 176)

# 中央安全區（1200×630 中央裁切後保留約 x=200~1000）
X0 = 232          # 文字左起
TAG_X = 264       # 標籤左起（在 X0 右側，讓 gold 豎線落在安全區邊緣）


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


def main():
    base = vgrad(W, H, BG_DEEP, BG_MID)
    d = ImageDraw.Draw(base)

    # ---- 右側：會議桌照片，壓暗並向左淡出，讓左側文字清楚 ----
    photo = Image.open(DECK_COVER).convert('RGB')
    pw, ph = photo.size
    scale = H / ph
    photo = photo.resize((int(pw * scale), H), Image.LANCZOS)
    photo = photo.crop((photo.size[0] - W, 0, photo.size[0], H))
    photo = photo.filter(ImageFilter.GaussianBlur(1.2))
    photo = Image.blend(Image.new('RGB', (W, H), BG_MID), photo, 0.62)
    base.paste(photo, (0, 0))

    # 整體壓暗 + 左側加深（確保文字對比）
    # 對比集中在 x≈232-890（中央安全區），讓左右兩側都能當純色底
    veil = Image.new('L', (W, 1))
    vd = ImageDraw.Draw(veil)
    for x in range(W):
        # 以 X0（232）為文字起點做分段：左側極暗、中段亮到 210、右側收回 60
        if x < X0:
            v = 232 - (x / max(X0, 1)) * 12
        elif x < 900:
            v = 210 - ((x - X0) / max(900 - X0, 1)) * 90
        else:
            v = 120 - ((x - 900) / max(W - 900, 1)) * 60
        vd.point((x, 0), fill=int(max(20, min(240, v))))
    mask = veil.resize((W, H))
    base.paste(Image.new('RGB', (W, H), BG_DEEP), (0, 0), mask)
    d = ImageDraw.Draw(base)

    # ---- 左側金色豎線（落在中央安全區左緣）----
    d.rectangle([X0 - 32, 96, X0 - 24, 268], fill=AMBER)

    # ---- 標籤 ----
    f_tag = font(30)
    tag = '第一堂 · 高效會議主持 SOP'
    tw = d.textlength(tag, font=f_tag)
    d.rounded_rectangle([TAG_X, 100, TAG_X + tw + 48, 156], radius=28, fill=AMBER)
    d.text((TAG_X + 24, 109), tag, font=f_tag, fill=(7, 46, 33))

    # ---- 主標題（兩行）----
    f_t = font(76)
    d.text((X0, 200), '會議結束了，', font=f_t, fill=CREAM)
    d.text((X0, 292), '事情才開始', font=f_t, fill=AMBER_L)

    # ---- 副標一行 ----
    f_s = font(34, False)
    d.text((X0 + 2, 404), '把會議從流程，還原成一筆要交付結果的交易', font=f_s, fill=DIM)

    # ---- 底部作者列 ----
    d.line([(X0, H - 122), (X0 + 656, H - 122)], fill=(40, 86, 66), width=2)
    d.text((X0, H - 100), '翁振軒  Sean Own  ·  青年實戰', font=font(34), fill=CREAM)
    d.text((X0, H - 56), '附完整 SOP 與 14 頁演講稿', font=font(27, False), fill=DIM)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    base.save(OUT, 'JPEG', quality=86, optimize=True, progressive=True)
    print('輸出 %s  (%.0f KB)' % (OUT, os.path.getsize(OUT) / 1024))


if __name__ == '__main__':
    main()