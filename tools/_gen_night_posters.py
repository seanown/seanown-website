# -*- coding: utf-8 -*-
"""#154 night-comes-for-us-2018 poster pipeline: rename, de-watermark, export 6 files."""
import os
import numpy as np
from PIL import Image

OG_DIR = r"C:/Users/user/WorkBuddy/Seanown.org/assets/og"
SLUG = "night-comes-for-us-2018"

SRC_P = os.path.join(OG_DIR, "Mondo_alternative_movie_poster_2026-10-31T09-16-22.png")
SRC_L = os.path.join(OG_DIR, "Mondo_alternative_movie_poster_2026-10-31T09-16-34.png")
DST_P = os.path.join(OG_DIR, SLUG + "-poster.png")
DST_L = os.path.join(OG_DIR, SLUG + "-poster-land.png")

os.replace(SRC_P, DST_P)
os.replace(SRC_L, DST_L)
print("renamed ok")


def de_watermark_darken(path):
    """就地壓暗：右下角浮水印區域內比暗部亮的像素壓到區域暗色中位值。"""
    img = Image.open(path).convert("RGB")
    a = np.asarray(img).astype(np.float64)
    h, w, _ = a.shape
    x0, y0 = int(w * 0.80), int(h * 0.90)
    region = a[y0:, x0:]
    gray = region.mean(axis=2)
    thr = max(np.percentile(gray, 30) + 28, 60)
    mask = (gray > thr).astype(np.float64)
    # 鄰域膨脹抓抗鋸齒邊緣（3x3 兩輪）
    from scipy import ndimage  # noqa
    for _ in range(2):
        mask = ndimage.binary_dilation(mask > 0, iterations=1).astype(np.float64)
    dark = np.percentile(region.reshape(-1, 3), 30, axis=0)
    m = mask[..., None]
    region_out = region * (1 - m) + dark[None, None, :] * m
    a[y0:, x0:] = region_out
    out = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    out.save(path)
    print(f"dewatermark {os.path.basename(path)} done, thr={thr:.0f}, dark={dark.astype(int)}")
    return out


def main():
    try:
        import scipy  # noqa
        HAS_SCIPY = True
    except ImportError:
        HAS_SCIPY = False

    for p in (DST_P, DST_L):
        if HAS_SCIPY:
            de_watermark_darken(p)
        else:
            # 無 scipy：手寫 3x3 膨脹（numpy 平移最大值）
            img = Image.open(p).convert("RGB")
            a = np.asarray(img).astype(np.float64)
            h, w, _ = a.shape
            x0, y0 = int(w * 0.80), int(h * 0.90)
            region = a[y0:, x0:]
            gray = region.mean(axis=2)
            thr = max(np.percentile(gray, 30) + 28, 60)
            mask = (gray > thr).astype(np.float64)
            for _ in range(2):
                pad = np.pad(mask, 1)
                mask = np.max(np.stack([
                    pad[:-2, :-2], pad[:-2, 1:-1], pad[:-2, 2:],
                    pad[1:-1, :-2], pad[1:-1, 1:-1], pad[1:-1, 2:],
                    pad[2:, :-2], pad[2:, 1:-1], pad[2:, 2:],
                ]), axis=0)
            dark = np.percentile(region.reshape(-1, 3), 30, axis=0)
            m = mask[..., None]
            a[y0:, x0:] = region * (1 - m) + dark[None, None, :] * m
            Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(p)
            print(f"dewatermark {os.path.basename(p)} done (numpy), thr={thr:.0f}")

    # ---- 產出 jpg / webp / og ----
    poster = Image.open(DST_P).convert("RGB")
    land = Image.open(DST_L).convert("RGB")
    assert poster.size == (1024, 1536), poster.size
    assert land.size == (1536, 1024), land.size

    poster.save(os.path.join(OG_DIR, SLUG + "-poster.jpg"), quality=92)
    land.save(os.path.join(OG_DIR, SLUG + "-poster-land.jpg"), quality=92)
    poster.save(os.path.join(OG_DIR, SLUG + "-poster.webp"), quality=82)
    land.save(os.path.join(OG_DIR, SLUG + "-poster-land.webp"), quality=82)

    # OG：1200x630，全寬頂部對齊（1536x1024 -> 1200x800 -> 裁上段 630）
    og = land.resize((1200, 800), Image.LANCZOS).crop((0, 0, 1200, 630))
    og.save(os.path.join(OG_DIR, SLUG + ".jpg"), quality=92)
    og.save(os.path.join(OG_DIR, SLUG + ".webp"), quality=82)
    print("exported 6 files for", SLUG)


if __name__ == "__main__":
    main()
