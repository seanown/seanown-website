# -*- coding: utf-8 -*-
# 生成《宮》Mondo 風海報：極簡／金色細框／皇冠徽記／優雅襯線 GOONG
# 規格：僅英文片名，禁中文、禁 logo、禁 rating box
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math

ASSETS = 'C:/Users/user/WorkBuddy/Seanown.org/assets/og'
FONT_B = 'C:/Windows/Fonts/georgiab.ttf'
FONT_R = 'C:/Windows/Fonts/georgia.ttf'

GOLD = (212, 178, 92)
GOLD_SOFT = (185, 155, 95)
CREAM = (244, 234, 202)


def vgradient(w, h, top, bot):
    g = Image.new('RGB', (1, h))
    px = g.load()
    for y in range(h):
        t = y / (h - 1)
        r = int(top[0] + (bot[0] - top[0]) * t)
        gg = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        px[0, y] = (r, gg, b)
    return g.resize((w, h))


def add_glow(img, cx, cy, R):
    mask = Image.new('L', (2 * R, 2 * R), 0)
    mp = mask.load()
    for y in range(2 * R):
        for x in range(2 * R):
            dx = x - R
            dy = y - R
            d = math.sqrt(dx * dx + dy * dy)
            if d < R:
                f = 1 - d / R
                mp[x, y] = int(120 * f * f)
    gold = Image.new('RGB', mask.size, GOLD_SOFT)
    img.paste(gold, (cx - R, cy - R), mask)
    return img


def draw_crown(d, cx, cy, w, h):
    color = GOLD
    lw = max(3, int(w * 0.012))
    band_h = h * 0.30
    d.rectangle([cx - w / 2, cy, cx + w / 2, cy + band_h], outline=color, width=lw)
    sp = h * 0.72
    tris = [
        ((cx - w / 2, cy), (cx - w / 2 + w * 0.20, cy - sp), (cx - w / 2 + w * 0.40, cy)),
        ((cx - w * 0.20, cy), (cx, cy - sp * 1.18), (cx + w * 0.20, cy)),
        ((cx + w / 2 - w * 0.40, cy), (cx + w / 2 - w * 0.20, cy - sp), (cx + w / 2, cy)),
    ]
    for tri in tris:
        d.polygon(tri, fill=color)
    for (ox, oy) in [(cx - w / 2 + w * 0.20, cy - sp), (cx, cy - sp * 1.18), (cx + w / 2 - w * 0.20, cy - sp)]:
        r = max(4, w * 0.018)
        d.ellipse([ox - r, oy - r, ox + r, oy + r], fill=color)


def make_poster(w, h, title, subtitle, crown=True):
    img = vgradient(w, h, (11, 31, 58), (58, 14, 30))
    cx = w // 2
    glow_cy = int(h * 0.14)
    img = add_glow(img, cx, glow_cy, int(min(w, h) * 0.20))
    d = ImageDraw.Draw(img)
    b1, b2 = int(w * 0.035), int(w * 0.045)
    d.rectangle([b1, b1, w - b1, h - b1], outline=GOLD, width=3)
    d.rectangle([b2, b2, w - b2, h - b2], outline=GOLD, width=1)
    if crown:
        draw_crown(d, cx, int(h * 0.15), int(w * 0.30), int(h * 0.10))
    title_center = int(h * 0.46)
    fsz = int(w * 0.18)
    f = ImageFont.truetype(FONT_B, fsz)
    bb = d.textbbox((0, 0), title, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = cx - tw / 2 - bb[0]
    ty = title_center - th / 2 - bb[1]
    d.text((tx, ty), title, font=f, fill=CREAM)
    ry = ty + th + int(h * 0.05)
    sf = ImageFont.truetype(FONT_R, int(w * 0.05))
    sb = d.textbbox((0, 0), subtitle, font=sf)
    sw = sb[2] - sb[0]
    d.text((cx - sw / 2 - sb[0], ry + int(h * 0.02)), subtitle, font=sf,
           fill=CREAM, stroke=2, stroke_fill=(18, 14, 28))
    return img


p = make_poster(1024, 1536, "GOONG", "PRINCESS HOURS", crown=True)
p.save(os.path.join(ASSETS, 'goong-princess-hours-cover.jpg'), quality=92)
p.save(os.path.join(ASSETS, 'goong-princess-hours-poster.jpg'), quality=92)
o = make_poster(1200, 630, "GOONG", "PRINCESS HOURS", crown=True)
o.save(os.path.join(ASSETS, 'goong-princess-hours.jpg'), quality=92)
o.save(os.path.join(ASSETS, 'goong-princess-hours-poster-land.jpg'), quality=92)
print('posters written: cover/poster/og/land')
