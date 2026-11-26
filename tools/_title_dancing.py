# -*- coding: utf-8 -*-
"""電影海報片名疊字工具。
沿用前作規格：米白色 distressed 粗體全大寫、居中、橫跨上方、帶磨舊顆粒感。
以 PIL 疊字實作（不用 ImageGen，避免 AI 切字）。
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

FONT = 'C:/Windows/Fonts/ROCK.TTF'
CREAM = (238, 231, 214)


def fit_font(text, max_w, start_size):
    """二分找最大字級使文字寬度 <= max_w。回傳 (font, size)。"""
    lo, hi = 12, start_size
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        f = ImageFont.truetype(FONT, mid)
        w = f.getbbox(text)[2]
        if w <= max_w:
            best = f
            lo = mid + 1
        else:
            hi = mid - 1
    return best or ImageFont.truetype(FONT, start_size)


def add_title(img, text, top_ratio=0.055, max_w_ratio=0.88, lines=None):
    W, H = img.size
    d = ImageDraw.Draw(img)

    words = text.split(' ')
    if lines is None:
        lines = [text] if len(text) <= 14 else words

    max_w = int(W * max_w_ratio)
    size = int(H * 0.068)
    forln = None
    for ln in lines:
        f = fit_font(ln, max_w, size)
        b = f.getbbox(ln)
        if forln is None or (b[3] - b[1]) > (forln[1].getbbox(ln)[3] - forln[1].getbbox(ln)[1]):
            pass
    # 統一字級：取各行所需字級最小者，視覺一致
    fonts = []
    for ln in lines:
        f = fit_font(ln, max_w, size)
        fonts.append(f)
    line_h = max(f.getbbox(ln)[3] for f, ln in zip(fonts, lines))
    GAP = int(H * 0.020)
    total_h = line_h * len(lines) + GAP * (len(lines) - 1)

    y = int(H * top_ratio)

    # 先畫一層極淡的暗色底，讓字在淺色天空上也讀得出來
    for f, ln in zip(fonts, lines):
        w = f.getbbox(ln)[2]
        x = (W - w) // 2
        d.text((x + 3, y + 4), ln, font=f, fill=(8, 12, 16))
    # 主體米白
    for f, ln in zip(fonts, lines):
        w = f.getbbox(ln)[2]
        x = (W - w) // 2
        d.text((x, y), ln, font=f, fill=CREAM)
        y += line_h + GAP
    return img


def distress(img, box, strength=0.55, seed=7):
    """在指定框內加磨舊顆粒：隨機剔除部分米白像素 + 輕微暗斑。"""
    random.seed(seed)
    x0, y0, x1, y1 = box
    px = img.load()
    W, H = img.size
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            r, g, b = px[x, y]
            # 米白特徵
            if r > 214 and g > 205 and b > 188:
                if random.random() < strength * 0.22:
                    # 挖成底色（暗）
                    px[x, y] = (r - 90, g - 92, b - 96)
                elif random.random() < strength * 0.30:
                    # 稍微壓暗＝磨舊
                    px[x, y] = (r - 40, g - 42, b - 44)
    return img


if __name__ == '__main__':
    TITLE = 'DANCING IN THE SEA BREEZE'

    # 直版 1024x1536：片名兩行
    p = Image.open('generated-images/_dancing-poster-v4.png').convert('RGB')
    p2 = add_title(p, TITLE, top_ratio=0.028, lines=['DANCING', 'IN THE SEA', 'BREEZE'])
    p2 = distress(p2, (150, 30, 880, 350))
    p2.save('generated-images/_dancing-poster-final.png')
    print('直版完成')

    # 橫版 1536x1024：片名單行置中偏上
    l = Image.open('generated-images/_dancing-land-v5.png').convert('RGB')
    l2 = add_title(l, TITLE, top_ratio=0.075, lines=['DANCING IN THE SEA BREEZE'])
    l2 = distress(l2, (120, 60, 1420, 200))
    l2.save('generated-images/_dancing-land-final.png')
    print('橫版完成')
