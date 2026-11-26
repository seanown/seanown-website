# -*- coding: utf-8 -*-
"""《與你相遇的日子》Mondo 版海報浮水印移除。

背景有兩種材質，必須分區處理、用不同門檻：
  · 深灰地面（水印為半透明白，與背景差~160階）
  · 米色邊帶（水印為近純白，與米色差~45階）
方法統一用「逐行水平修復」：偵測異常亮像素 → 用同列左右最近有效像素水平回填，
保留地面橫向紋理，不會出現鏡像鬼影或純色色塊。
"""
from PIL import Image
import numpy as np

# (x, y, w, h, thr, dilate)
JOBS = [
    dict(dst='generated-images/_dancing-poster-v6.png',
         src='generated-images/_dancing-poster-v5.png',
         regions=[
             (880, 1452, 144, 64, 120, 2),    # 深灰地面區（AI生成 + WORKBUDDY 上半）
             (880, 1516, 144, 20, 26, 2),     # 米色邊帶區（WORKBUDDY 下半）
         ]),
    dict(dst='generated-images/_dancing-land-v9.png',
         src='generated-images/_dancing-land-v8.png',
         regions=[
             (1356, 928, 180, 96, 70, 2),     # 石板地面區
         ]),
]


def dil(mask, n):
    for _ in range(n):
        p = np.pad(mask, 1)
        mask = np.maximum.reduce([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:], p[1:-1, 1:-1]])
    return mask


def inpaint_h(a, x, y, w, h, thr):
    reg = a[y:y + h, x:x + w].copy()
    # 背景階調：用左右各200px 同列區域的中位（乾淨材質）
    ctx = np.concatenate([a[y:y + h, max(0, x - 220):x], a[y:y + h, x + w:x + w + 200]], axis=1)
    base = np.median(ctx.reshape(h, -1, 3), axis=1)      # (h,3)
    dist = reg - base[:, None, :]
    lum = dist.mean(axis=2)
    mask = ((dist.min(axis=2) > thr * 0.35) & (lum > thr)).astype(np.uint8)
    mask = dil(mask, 2)
    for i in range(h):
        bad = mask[i].astype(bool)
        good = ~bad
        if not bad.any() or not good.any():
            continue
        idx = np.arange(w)
        fl = np.where(good, idx, -1)
        fwd = np.maximum.accumulate(fl)
        bwd = np.minimum.accumulate(np.where(good, idx, w)[::-1])[::-1]
        for c in range(3):
            ch = reg[i, :, c].astype(float)
            v = np.nanmean(np.vstack([
                np.where(fwd >= 0, ch[np.clip(fwd, 0, w - 1)], np.nan),
                np.where(bwd < w, ch[np.clip(bwd, 0, w - 1)], np.nan)]), axis=0)
            v = np.nan_to_num(v, nan=float(np.median(ch)))
            ch[bad] = v[bad]
            reg[i, :, c] = ch
    a[y:y + h, x:x + w] = reg
    return a, int(mask.sum())


if __name__ == '__main__':
    for j in JOBS:
        im = Image.open(j['src']).convert('RGB')
        a = np.asarray(im, float)
        tot = 0
        for r in j['regions']:
            x, y, w, h, thr, dl = r
            a, n = inpaint_h(a, x, y, w, h, thr)
            tot += n
        Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(j['dst'])
        print(j['dst'], '修復像素', tot)