"""
Remove WorkBuddy watermark from Poker King (2009) AI posters
and export the 8-piece set for assets/og.
"""
import sys, os, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
try:
    import cv2
except Exception as e:
    print("ERROR: cv2 not available:", e)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
OG_DIR = ROOT / "assets" / "og"
GEN_DIR = ROOT / "generated-images"
SLUG = "chase-at-the-canidrome-1965"

# First-generation pair; title verified correct, no Chinese/Portuguese signage
V_SRC = GEN_DIR / "Mondo_style_limited_edition_sc_2026-09-29T21-54-54.png"
H_SRC = GEN_DIR / "Mondo_style_limited_edition_sc_2026-09-29T21-53-06.png"


def feather_mask(shape, rects, radius=5):
    h, w = shape[:2]
    mask = np.zeros((h, w), np.uint8)
    for (x1, y1, x2, y2) in rects:
        y1, y2 = max(0, y1), min(h, y2)
        x1, x2 = max(0, x1), min(w, x2)
        mask[y1:y2, x1:x2] = 255
    if radius:
        mask = cv2.GaussianBlur(mask, (radius * 2 + 1, radius * 2 + 1), 0)
    return mask


def inpaint_region(img, rects, radius=5, iter=1):
    arr = np.asarray(img).copy()
    mask = feather_mask(arr.shape, rects, radius=radius)
    mask = cv2.dilate(mask, np.ones((7, 7), np.uint8), iterations=1)
    for _ in range(iter):
        arr = cv2.inpaint(arr, mask, inpaintRadius=5, flags=cv2.INPAINT_NS)
    return Image.fromarray(arr)


def add_noise(img, rects, sigma=3):
    arr = np.asarray(img).astype(np.int16)
    h, w = arr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    for (x1, y1, x2, y2) in rects:
        y1, y2 = max(0, y1), min(h, y2)
        x1, x2 = max(0, x1), min(w, x2)
        mask[y1:y2, x1:x2] = 255
    noise = np.random.normal(0, sigma, arr.shape)
    arr[mask == 255] = np.clip(arr[mask == 255] + noise[mask == 255], 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def verify_no_watermark_region(img, rect):
    a = np.asarray(img.crop(rect)).astype(float)
    std = a.std(axis=(0, 1)).mean()
    print(f"  region {rect} mean={a.mean(axis=(0,1)).round(1)} std={a.std(axis=(0,1)).round(1)} overall_std={std:.2f}")
    return std


def main():
    print("Loading source images...")
    v = Image.open(V_SRC).convert("RGB")
    h = Image.open(H_SRC).convert("RGB")
    print(f"  vertical size {v.size}, horizontal size {h.size}")

    # Rectangles covering the observed WorkBuddy watermark (bottom-right dark band)
    v_wm = (940, 1460, 1024, 1536)
    h_wm = (1290, 910, 1536, 1024)

    print("Inpainting vertical watermark...")
    v = inpaint_region(v, [v_wm], radius=5, iter=3)
    v = add_noise(v, [v_wm], sigma=3)

    print("Inpainting horizontal watermark...")
    h = inpaint_region(h, [h_wm], radius=5, iter=3)
    h = add_noise(h, [h_wm], sigma=3)

    # Verify smoothness in the repaired region (lower std than noisy watermark)
    print("Verification (post-repair):")
    v_std = verify_no_watermark_region(v, v_wm)
    h_std = verify_no_watermark_region(h, h_wm)
    if v_std > 25 or h_std > 45:
        print("WARNING: residual texture high; inspect visually.")

    # 8-piece export
    print("Exporting 8-piece set...")
    OG_DIR.mkdir(parents=True, exist_ok=True)

    # vertical poster
    v_path_png = OG_DIR / f"{SLUG}-poster.png"
    v_path_jpg = OG_DIR / f"{SLUG}-poster.jpg"
    v_path_webp = OG_DIR / f"{SLUG}-poster.webp"
    v.save(v_path_png, "PNG")
    v.save(v_path_jpg, "JPEG", quality=95, optimize=True)
    v.save(v_path_webp, "WEBP", quality=88, method=6)

    # horizontal poster (hero / cover)
    h_path_png = OG_DIR / f"{SLUG}-poster-land.png"
    h_path_jpg = OG_DIR / f"{SLUG}-cover.jpg"
    h_path_land_jpg = OG_DIR / f"{SLUG}-poster-land.jpg"
    h_path_webp = OG_DIR / f"{SLUG}-cover.webp"
    h.save(h_path_png, "PNG")
    h.save(h_path_jpg, "JPEG", quality=95, optimize=True)
    h.save(h_path_land_jpg, "JPEG", quality=95, optimize=True)
    h.save(h_path_webp, "WEBP", quality=88, method=6)

    # OG 1200x630 top-aligned crop (title often sits near top)
    h_resize = h.resize((1200, 800), Image.LANCZOS)
    og = h_resize.crop((0, 0, 1200, 630))
    og_path_jpg = OG_DIR / f"{SLUG}.jpg"
    og_path_webp = OG_DIR / f"{SLUG}.webp"
    og.save(og_path_jpg, "JPEG", quality=95, optimize=True)
    og.save(og_path_webp, "WEBP", quality=88, method=6)

    print("Files written:")
    for p in [
        v_path_png, v_path_jpg, v_path_webp,
        h_path_png, h_path_jpg, h_path_land_jpg, h_path_webp,
        og_path_jpg, og_path_webp,
    ]:
        print(" ", p, "size", p.stat().st_size)

    # Spot-check dimensions
    for p, expected in [
        (v_path_jpg, (1024, 1536)),
        (h_path_jpg, (1536, 1024)),
        (og_path_jpg, (1200, 630)),
    ]:
        im = Image.open(p)
        assert im.size == expected, f"{p} size {im.size} != {expected}"
        print(f"  dimension OK {p}: {im.size}")

    print("DONE")


if __name__ == "__main__":
    main()
