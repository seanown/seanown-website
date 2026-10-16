# -*- coding: utf-8 -*-
"""把多寶交付的 30 張合輯橫幅（temp/banner31/seanown電影header/，3128×1340 PNG）烘焙成
assets/images/places/ 下 1600×685 JPG，供 collection/ 各頁 hero 背景帶使用。

QC 結論（2026-10-16）：30 張中 13 張帶 AI 亂碼／假店名文字（年代 1920-1990 七張、
影人 02/07/13/15 四張、入口 hub 與 era-golden 兩張），違反任務單「空白招牌」硬規則。
處理＝高失焦（bokeh 化）亂碼區，保留主體清晰（羽化矩形 sharp zone）；1970 全幅失焦。
其餘 17 張無文字，原样縮放。

映射：
  00_合集總覽 → hub.jpg（先裁頂 30% 去掉亂碼標題，再失焦地圖）
  01_早期1969前 → era-early.jpg；02_港產黃金1970-1999 → era-golden.jpg；03_千禧後2000起 → era-milli.jpg
  1920…2020年代 → decade-1920…decade-2020.jpg
  01_方中信…16_萬梓良 → person-01…person-16.jpg（編號與網站 person_pages 順序已核驗一致）

冪等：重跑覆寫同名 JPG，不動 place-01…24（上一批，空白招牌版）。
"""
import io
import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'temp', 'banner31', 'seanown電影header')
OUT = os.path.join(ROOT, 'assets', 'images', 'places')

TW, TH = 1600, 685  # 與 place-01…24 同規格（源圖 3128×1340 正好 2.336:1）

# 去焦規格：name -> (blur_radius, [sharp_rect 比例 (x0,y0,x1,y1)...], feather_px)
DEFOCUS = {
    'era-golden':  (18, [(0.18, 0.64, 0.82, 1.00)], 80),
    'decade-1920': (16, [(0.05, 0.66, 0.95, 1.00)], 80),
    'decade-1930': (16, [(0.30, 0.38, 0.72, 1.00)], 90),
    'decade-1950': (18, [(0.00, 0.68, 1.00, 1.00)], 70),
    'decade-1960': (16, [(0.03, 0.58, 0.70, 1.00), (0.84, 0.60, 1.00, 1.00)], 70),
    'decade-1970': (18, [], 0),  # 亂碼遍布全幅（含車牌 19-76），全失焦
    'decade-1980': (18, [(0.22, 0.55, 0.85, 1.00)], 80),
    'decade-1990': (18, [(0.00, 0.80, 1.00, 1.00)], 50),
    'person-02':   (18, [(0.38, 0.50, 0.65, 1.00)], 70),
    'person-07':   (20, [(0.38, 0.52, 0.66, 1.00)], 80),
    'person-13':   (18, [(0.40, 0.46, 0.60, 1.00)], 70),
    'person-15':   (20, [(0.42, 0.56, 0.60, 1.00)], 70),
}

MAP = [
    ('03_分類入口頁', '00_合集總覽.png', 'hub'),
    ('03_分類入口頁', '01_早期1969前.png', 'era-early'),
    ('03_分類入口頁', '02_港產黃金1970-1999.png', 'era-golden'),
    ('03_分類入口頁', '03_千禧後2000起.png', 'era-milli'),
]
MAP += [('01_年代頁', '%d年代.png' % y, 'decade-%d' % y)
        for y in (1920, 1930, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020)]
_PERSONS = ['方中信', '梁朝偉', '黃秋生', '任達華', '何超儀', '劉德華', '張家輝', '林雪',
            '羅蘭', '劉青雲', '古天樂', '周潤發', '成龍', '李鵬飛', '王晶', '萬梓良']
MAP += [('02_影人頁', '%02d_%s.png' % (i + 1, n), 'person-%02d' % (i + 1))
        for i, n in enumerate(_PERSONS)]


def defocus(im, radius, rects, feather):
    """全圖高斯失焦；rects 內用羽化 mask 貼回清晰原圖。"""
    if radius <= 0:
        return im
    W, H = im.size
    blurred = im.filter(ImageFilter.GaussianBlur(radius))
    if not rects:
        return blurred
    mask = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(mask)
    for x0, y0, x1, y1 in rects:
        d.rectangle([int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)], fill=255)
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))
    return Image.composite(im, blurred, mask)


def bake(gname, fname, name):
    im = Image.open(os.path.join(SRC, gname, fname)).convert('RGB')
    if name == 'hub':
        # 頂 30% 是亂碼標題（L'o新新澳門 Difo…）→ 裁掉；地圖滿佈亂碼標籤 → 失焦
        W, H = im.size
        im = im.crop((0, int(H * 0.30), W, H))
        im = defocus(im, 16, [], 0)
        # 回復 2.336:1（置中裁寬）
        w, h = im.size
        cw = int(h * TW / TH)
        if cw < w:
            x0 = (w - cw) // 2
            im = im.crop((x0, 0, x0 + cw, h))
    elif name in DEFOCUS:
        r, rects, f = DEFOCUS[name]
        im = defocus(im, r, rects, f)
    out = im.resize((TW, TH), Image.LANCZOS)
    dst = os.path.join(OUT, name + '.jpg')
    out.save(dst, 'JPEG', quality=87, progressive=True, optimize=True)
    return dst, os.path.getsize(dst)


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for gname, fname, name in MAP:
        p = os.path.join(SRC, gname, fname)
        assert os.path.isfile(p), '缺檔：' + p
        dst, sz = bake(gname, fname, name)
        n += 1
        print('%-12s <- %s/%s  %6.1f KB' % (name + '.jpg', gname, fname, sz / 1024))
    assert n == 30, '應為 30 張，實得 %d' % n
    print('OK 30 張 →', OUT)


if __name__ == '__main__':
    main()
