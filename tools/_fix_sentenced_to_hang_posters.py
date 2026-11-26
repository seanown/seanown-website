#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix poster for Sentenced to Hang (1989).
- Remove DRIVING sign on the right wall of the landscape poster.
- Remove AI watermark from bottom-right of both posters.
- Output clean versions and the 8-piece set under assets/og/.
"""
import os
from PIL import Image, ImageFilter
import numpy as np
import cv2

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_V = os.path.join(BASE, "generated-images", "Mondo_alternative_movie_poster_2026-09-29T18-43-19.png")
SRC_H = os.path.join(BASE, "generated-images", "LANDSCAPE_widescreen_compositi_2026-09-29T18-43-17.png")
OUT_DIR = os.path.join(BASE, "generated-images")
OG_DIR = os.path.join(BASE, "assets", "og")
SLUG = "sentenced-to-hang-1989"


def feather_mask(shape, rects, radius=5):
    """Create a smoothed mask from a list of (x1,y1,x2,y2)."""
    h, w = shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    for x1, y1, x2, y2 in rects:
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        mask[y1:y2, x1:x2] = 255
    if radius:
        mask = cv2.GaussianBlur(mask, (2 * radius + 1, 2 * radius + 1), radius)
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    return mask


def inpaint_region(img, rects, radius=5, iter=1):
    """Inpaint the union of rects in a PIL RGB image."""
    arr = np.asarray(img).copy()
    mask = feather_mask(arr.shape, rects, radius=radius)
    # Expand mask slightly so edges blend
    mask = cv2.dilate(mask, np.ones((7, 7), np.uint8), iterations=1)
    for _ in range(iter):
        arr = cv2.inpaint(arr, mask, inpaintRadius=5, flags=cv2.INPAINT_NS)
    return Image.fromarray(arr)


def add_noise(img, rects, sigma=4):
    """Add subtle noise to inpainted regions to match Mondo grain."""
    arr = np.asarray(img).astype(np.float32)
    mask = np.zeros((arr.shape[0], arr.shape[1]), dtype=np.uint8)
    for x1, y1, x2, y2 in rects:
        mask[y1:y2, x1:x2] = 1
    if mask.sum() == 0:
        return img
    noise = np.random.normal(0, sigma, arr.shape[:2])
    for c in range(3):
        arr[:, :, c] += noise * mask
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def remove_watermark_mirror(img, rect, src_xy, feather=16):
    """Replace rectangular region with mirrored source, with vertical/horizontal feather."""
    x1, y1, x2, y2 = rect
    sx, sy = src_xy
    w, h = x2 - x1, y2 - y1
    arr = np.asarray(img).copy()
    patch = arr[sy:sy + h, sx:sx + w].copy()
    # Simple horizontal mirror if destination overlaps source on right edge
    if sx + w > x1:
        patch = np.fliplr(patch)
    arr[y1:y2, x1:x2] = patch
    # Feather edges
    if feather:
        tmp = Image.fromarray(arr)
        mask = np.zeros((tmp.height, tmp.width), dtype=np.uint8)
        mask[y1:y2, x1:x2] = 255
        mask = Image.fromarray(mask).filter(ImageFilter.GaussianBlur(feather / 2))
        mask = np.asarray(mask, dtype=np.float32) / 255.0
        mask = mask[:, :, None]
        orig = np.asarray(img).astype(np.float32)
        mod = np.asarray(tmp).astype(np.float32)
        blended = orig * (1 - mask) + mod * mask
        arr = blended.astype(np.uint8)
    return Image.fromarray(arr)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def main():
    ensure_dir(OUT_DIR)
    ensure_dir(OG_DIR)

    v = Image.open(SRC_V).convert("RGB")
    h = Image.open(SRC_H).convert("RGB")

    # --- Vertical poster fixes ---
    # Bottom-right AI watermark region (keep repair conservative)
    v_wm_rect = (860, 1438, 1024, 1536)
    v = inpaint_region(v, [v_wm_rect], radius=5, iter=3)
    v = add_noise(v, [v_wm_rect], sigma=3)
    v.save(os.path.join(OUT_DIR, f"{SLUG}-poster.png"))

    # --- Landscape poster fixes ---
    # 1) DRIVING sign on the right wall: red sign + text, replace with wall texture
    driving_rect = (1195, 395, 1405, 560)
    # 2) Bottom-right AI watermark
    h_wm_rect = (1290, 910, 1536, 1024)
    h = inpaint_region(h, [driving_rect], radius=7, iter=5)
    h = inpaint_region(h, [h_wm_rect], radius=5, iter=3)
    h = add_noise(h, [driving_rect, h_wm_rect], sigma=3)
    h.save(os.path.join(OUT_DIR, f"{SLUG}-poster-land.png"))

    # --- Generate 8-piece set ---
    # 1) poster PNG (1024x1536) already as v
    # 2) poster JPG
    v_jpg = os.path.join(OG_DIR, f"{SLUG}-poster.jpg")
    v.save(v_jpg, quality=95)
    # 3) poster WEBP
    v_webp = os.path.join(OG_DIR, f"{SLUG}-poster.webp")
    v.save(v_webp, quality=90)

    # 4) landscape cover PNG (1536x1024) -> we also save as landscape poster source
    # 5) landscape JPG (cover uses same resolution as land)
    h_jpg = os.path.join(OG_DIR, f"{SLUG}-poster-land.jpg")
    h.save(h_jpg, quality=95)
    # 6) landscape WEBP
    h_webp = os.path.join(OG_DIR, f"{SLUG}-cover.webp")
    h.save(h_webp, quality=90)

    # 7) OG 1200x630 from landscape, top-crop because title is at top
    r = h.resize((1200, 800), Image.LANCZOS)
    og = r.crop((0, 0, 1200, 630))
    og_jpg = os.path.join(OG_DIR, f"{SLUG}.jpg")
    og.save(og_jpg, quality=95)
    # 8) OG WEBP
    og_webp = os.path.join(OG_DIR, f"{SLUG}.webp")
    og.save(og_webp, quality=90)

    print(f"Saved 8-piece set for {SLUG}")
    print(f"  vertical: {v_jpg}, {v_webp}")
    print(f"  landscape: {h_jpg}, {h_webp}")
    print(f"  og: {og_jpg}, {og_webp}")


if __name__ == "__main__":
    main()
