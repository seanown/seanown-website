# -*- coding: utf-8 -*-
"""為 num 122 做一張「更多專欄」卡片專用封面（1200×630，橫幅）。

沿用 num 121 的版面邏輯與中央安全區設計。

🔴 三個必須處理的問題：
1. 版面重心必須留在中央安全區。這張圖會出現在兩種容器，裁切方式不同——
   · 首頁「更多專欄」卡片 170px高，object-fit:cover 中央裁切
   · 輯頁時間軸 132×88，同樣中央裁切 → 只保留左右各約 45%~55%
   所以主標題與標籤都排在中間偏左（x=232 起），不可推到 x=104，
   否則輯頁縮圖會把標籤與主標題左半切掉。
2. ImageGen 產圖右下角自帶「AI生成」水印，必須用 PIL 清除。
3. 素材是 PNG，需轉 RGB 後才可貼到 RGB 底圖上。
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'images', 'posts', '122-cover.jpg')
SRC = os.path.join(ROOT, 'assets', 'images', 'posts',
                   'Photograph_of_an_elegant_forma_2026-10-08T12-35-50.png')
FONT = 'C:/Windows/Fonts/NotoSansTC-VF.ttf'

W, H = 1200, 630
BG_DEEP = (7, 46, 33)
BG_MID = (11, 61, 46)
AMBER = (199, 91, 18)
AMBER_L = (240, 160, 80)
CREAM = (247, 243, 234)
DIM = (168, 190, 176)

# 中央安全區（1200×630 中央裁切後保留約 x=200~1000）
X0 = 232
TAG_X = 264


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


def clear_watermark(img):
    """清除 ImageGen 右下角的「AI 生成」水印。
    手法：從左側同高度區域取樣，覆蓋右下角約 170×60。
    之所以可行，是因為該區域是深色幕布／地板，紋理均勻。"""
    w, h = img.size
    bw, bh = 170, 58
    bx, by = w - bw - 6, h - bh - 4
    patch = img.crop((max(0, bx - 260), by, max(0, bx - 260) + bw, by + bh))
    # 取樣後輕微模糊，消除取樣邊界的接縫
    patch = patch.filter(ImageFilter.GaussianBlur(1.6))
    img.paste(patch, (bx, by))
    return img


def main():
    base = vgrad(W, H, BG_DEEP, BG_MID)
    d = ImageDraw.Draw(base)

    # ---- 右側：典禮場合照，壓暗並向左淡出，讓左側文字清楚 ----
    photo = Image.open(SRC).convert('RGB')
    photo = clear_watermark(photo)
    pw, ph = photo.size
    scale = H / ph
    photo = photo.resize((int(pw * scale), H), Image.LANCZOS)
    photo = photo.crop((photo.size[0] - W, 0, photo.size[0], H))
    photo = photo.filter(ImageFilter.GaussianBlur(1.2))
    photo = Image.blend(Image.new('RGB', (W, H), BG_MID), photo, 0.58)
    base.paste(photo, (0, 0))

    # 整體壓暗 + 左側加深（確保文字對比）
    veil = Image.new('L', (W, 1))
    vd = ImageDraw.Draw(veil)
    for x in range(W):
        if x < X0:
            v = 234 - (x / max(X0, 1)) * 14
        elif x < 900:
            v = 212 - ((x - X0) / max(900 - X0, 1)) * 96
        else:
            v = 116 - ((x - 900) / max(W - 900, 1)) * 56
        vd.point((x, 0), fill=int(max(20, min(242, v))))
    mask = veil.resize((W, H))
    base.paste(Image.new('RGB', (W, H), BG_DEEP), (0, 0), mask)
    d = ImageDraw.Draw(base)

    # ---- 左側金色豎線（落在中央安全區左緣）----
    d.rectangle([X0 - 32, 96, X0 - 24, 268], fill=AMBER)

    # ---- 標籤 ----
    f_tag = font(30)
    tag = '第二堂 · 商務禮儀與典禮 SOP'
    tw = d.textlength(tag, font=f_tag)
    d.rounded_rectangle([TAG_X, 100, TAG_X + tw + 48, 156], radius=28, fill=AMBER)
    d.text((TAG_X + 24, 109), tag, font=f_tag, fill=(7, 46, 33))

    # ---- 主標題（兩行）----
    # 字級經計算：72px 時「是讓每個人被舒服地對待」寬792px，x=232→1024，
    # 超出中央安全區右緣（x≈1000），輯頁縮圖會切掉末兩字 → 降到 66px，
    # 寬約726px，落在 x=232→958，安全區內。
    f_t = font(66)
    d.text((X0, 206), '禮儀不是形式，', font=f_t, fill=CREAM)
    d.text((X0, 292), '是讓每個人被舒服地對待', font=f_t, fill=AMBER_L)

    # ---- 副標一行 ----
    f_s = font(32, False)
    d.text((X0 + 2, 404), '右為尊、中為大、左右左——排位置的鐵律', font=f_s, fill=DIM)

    # ---- 底部作者列 ----
    d.line([(X0, H - 122), (X0 + 656, H - 122)], fill=(40, 86, 66), width=2)
    d.text((X0, H - 100), '翁振軒  Sean Own  ·  青年實戰', font=font(34), fill=CREAM)
    d.text((X0, H - 56), '附完整 SOP 與五種典禮流程', font=font(27, False), fill=DIM)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    base.save(OUT, 'JPEG', quality=86, optimize=True, progressive=True)
    print('輸出 %s  (%.0f KB)' % (OUT, os.path.getsize(OUT) / 1024))


if __name__ == '__main__':
    main()