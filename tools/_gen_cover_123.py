# -*- coding: utf-8 -*-
"""為 num 123 做「更多專欄」卡片專用封面（1200×630）。

沿用 num 121／122 的版面邏輯與中央安全區設計。

🔴 必須處理的問題：
1. 版面重心留在中央安全區（首頁卡片 170px 高、輯頁縮圖 132×88，都做中央裁切）
2. ImageGen 產圖右下角有「AI 生成」水印，必須用 PIL 清除
3. 素材是 PNG，需轉 RGB 後才可貼到底圖上
4. 字級要實測寬度，避免超出安全區（num 122 曾因未實測而超出）
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'images', 'posts', '123-cover.jpg')
FONT = 'C:/Windows/Fonts/NotoSansTC-VF.ttf'

W, H = 1200, 630
BG_DEEP = (7, 46, 33)
BG_MID = (11, 61, 46)
AMBER = (199, 91, 18)
AMBER_L = (240, 160, 80)
CREAM = (247, 243, 234)
DIM = (168, 190, 176)

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
    """清除右下角「AI 生成」水印：從左側同高度取樣覆蓋，覆蓋後輕微模糊消除接縫。
    可行原因：該區域是深色幕布／地板，紋理均勻。"""
    w, h = img.size
    bw, bh = 170, 58
    bx, by = w - bw - 6, h - bh - 4
    sx = max(0, bx - 300)
    patch = img.crop((sx, by, sx + bw, by + bh))
    patch = patch.filter(ImageFilter.GaussianBlur(1.6))
    img.paste(patch, (bx, by))
    return img


def main():
    base = vgrad(W, H, BG_DEEP, BG_MID)
    d = ImageDraw.Draw(base)

    photo = Image.open(OUT.replace('123-cover.jpg',
                                   'Elegant_graduation_ceremony_ha_2026-10-08T13-45-19.png')
                       ).convert('RGB')
    photo = clear_watermark(photo)
    pw, ph = photo.size
    scale = H / ph
    photo = photo.resize((int(pw * scale), H), Image.LANCZOS)
    photo = photo.crop((photo.size[0] - W, 0, photo.size[0], H))
    photo = photo.filter(ImageFilter.GaussianBlur(1.2))
    photo = Image.blend(Image.new('RGB', (W, H), BG_MID), photo, 0.60)
    base.paste(photo, (0, 0))

    veil = Image.new('L', (W, 1))
    vd = ImageDraw.Draw(veil)
    for x in range(W):
        if x < X0:
            v = 236 - (x / max(X0, 1)) * 14
        elif x < 900:
            v = 214 - ((x - X0) / max(900 - X0, 1)) * 98
        else:
            v = 118 - ((x - 900) / max(W - 900, 1)) * 58
        vd.point((x, 0), fill=int(max(20, min(242, v))))
    mask = veil.resize((W, H))
    base.paste(Image.new('RGB', (W, H), BG_DEEP), (0, 0), mask)
    d = ImageDraw.Draw(base)

    # 標籤（先量寬度，決定字級）
    d.rectangle([X0 - 32, 96, X0 - 24, 268], fill=AMBER)

    tag = '第三堂 · 商會幹部領導力與危機管理'
    f_tag = font(26)
    tw = d.textlength(tag, font=f_tag)
    if X0 + 32 + tw > 960:                       # 標籤過寬則降字級
        f_tag = font(23)
        tw = d.textlength(tag, font=f_tag)
    d.rounded_rectangle([TAG_X, 100, TAG_X + tw + 44, 154], radius=27, fill=AMBER)
    d.text((TAG_X + 22, 110), tag, font=f_tag, fill=(7, 46, 33))

    # 主標題：先量寬，決定字級（教訓：num 122 曾因未實測而超出安全區）
    lines = ['領導是做對的事，', '管理是把事做對']
    for size in (66, 62, 58):
        f_t = font(size)
        widths = [d.textlength(t, font=f_t) for t in lines]
        if X0 + max(widths) <= 966:
            break
    d.text((X0, 204), lines[0], font=f_t, fill=CREAM)
    d.text((X0, 290), lines[1], font=f_t, fill=AMBER_L)

    f_s = font(31, False)
    d.text((X0 + 2, 404), '組織的資產不是錢、不是場地，是信任', font=f_s, fill=DIM)

    d.line([(X0, H - 122), (X0 + 656, H - 122)], fill=(40, 86, 66), width=2)
    d.text((X0, H - 100), '翁振軒  Sean Own  ·  青年實戰', font=font(33), fill=CREAM)
    d.text((X0, H - 56), '附完整 SOP 與五個基本功', font=font(26, False), fill=DIM)

    base.save(OUT, 'JPEG', quality=86, optimize=True, progressive=True)
    print('輸出 %s  (%.0f KB)  主標題字級 %dpx' %
          (OUT, os.path.getsize(OUT) / 1024, size))


if __name__ == '__main__':
    main()