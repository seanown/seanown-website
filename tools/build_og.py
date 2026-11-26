# -*- coding: utf-8 -*-
"""
為每篇文章生成 1200x630 的 Open Graph 分享封面圖（Berkeley 藍金雜誌風）
輸出：assets/og/<slug>.jpg
朋友圈 / Line / WhatsApp 轉發時顯示完整標題卡片。
"""
import io, os, re, json
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, 'data', 'posts.json')
OUT = os.path.join(ROOT, 'assets', 'og')
FONT = 'C:/Windows/Fonts/NotoSansTC-VF.ttf'

W, H = 1200, 630
BG_TOP = (1, 1, 51)        # #010133
BG_BOT = (0, 38, 118)      # #002676
GOLD = (253, 181, 21)
WHITE = (255, 255, 255)
DIM = (170, 186, 214)


def font(size, bold=True):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_name('Bold' if bold else 'Regular')
    except Exception:
        pass
    return f


def wrap(draw, text, f, max_w):
    """中英混排換行：中文逐字、英文單詞不斷開"""
    if not text:
        return ['']
    lines, cur = [], ''
    for ch in text:
        if ch == '\n':
            lines.append(cur); cur = ''; continue
        t = cur + ch
        if draw.textlength(t, font=f) > max_w and cur:
            lines.append(cur); cur = ch
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def gradient():
    img = Image.new('RGB', (W, H), BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(H):
        r = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(
            int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * r),
            int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * r),
            int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * r)))
    return img


def build(slug, title, cat, date):
    img = gradient()
    d = ImageDraw.Draw(img)

    # 右下角金色幾何裝飾（雜誌感斜塊）
    d.polygon([(W, H - 250), (W, H), (W - 260, H)], fill=(2, 46, 132))
    d.polygon([(W, H - 150), (W, H), (W - 150, H)], fill=GOLD)

    # 左側金色豎線
    d.rectangle([64, 92, 70, 232], fill=GOLD)

    # 分類標籤
    f_cat = font(30)
    if cat:
        tw = d.textlength(cat, font=f_cat)
        d.rounded_rectangle([92, 96, 92 + tw + 44, 152], radius=28, fill=GOLD)
        d.text((114, 105), cat, font=f_cat, fill=(1, 1, 51))
        d.text((92 + tw + 44 + 26, 106), date or '', font=font(26, False), fill=DIM)

    # 標題（最多 3 行，字號自適應）
    size = 64
    f_t = font(size)
    max_w = W - 190
    while size > 40:
        f_t = font(size)
        lines = wrap(d, title, f_t, max_w)
        if len(lines) <= 3:
            break
        size -= 4
    lines = wrap(d, title, f_t, max_w)[:3]
    if len(wrap(d, title, f_t, max_w)) > 3:
        lines[-1] = lines[-1][:-1] + '…'

    y = 208
    lh = int(size * 1.42)
    for ln in lines:
        d.text((92, y), ln, font=f_t, fill=WHITE)
        y += lh

    # 底部作者欄
    d.line([(92, H - 128), (W - 92, H - 128)], fill=(60, 84, 148), width=2)
    d.text((92, H - 104), '翁振軒  Sean Own', font=font(36), fill=WHITE)
    d.text((92, H - 56), 'seanown.org  ·  澳門產業觀察與數位出海', font=font(25, False), fill=DIM)

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, slug + '.jpg')
    img.save(p, 'JPEG', quality=86, optimize=True, progressive=True)
    return os.path.getsize(p)


def main():
    data = json.load(io.open(POSTS, encoding='utf-8'))
    posts = [p for p in data['posts'] if p.get('status') != '整理中']
    n = 0
    for p in posts:
        slug = p.get('slug') or ('post-' + str(p.get('num')))
        title = re.sub(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]', '', (p.get('title') or '').strip())
        title = title.strip('｜| -—')
        build(slug, title, p.get('category', ''), p.get('date', ''))
        n += 1
    # 專欄列表頁共用 OG 圖
    build('articles', '翁振軒專欄：澳門產業觀察與數位出海', '專欄文章', '')
    # 首頁 OG 圖
    build('seanown-home', '翁振軒 Sean Own｜澳門產業觀察｜AI 數位服務出海', '首頁', '')
    print('og images generated: %d -> %s' % (n + 2, OUT))


if __name__ == '__main__':
    main()
