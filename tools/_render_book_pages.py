# -*- coding: utf-8 -*-
"""《守燈人影記》274 頁 -> WebP 逐頁圖（給網站翻閱用）

為什麼不做「把 PDF 塞進網頁」：
  原版 30MB，PyMuPDF rewrite_images 壓到 20MB 還是太重
  （206 個 Type3 字體壓不動，佔掉 ~8MB）。
  改成「頁面渲染成圖 + 網頁延遲載入」：
  讀者翻到第幾頁才抓第幾頁，首屏只抓 1-2 張 → 體感接近瞬時。

解析度取捨：
  A5 148×210mm。1100px 寬 ≈ 189dpi，螢幕 2x 螢幕看得很清楚，
  印刷才需要 300dpi（1786px），網頁不需要。

用法: python _render_book_pages.py [max_w] [quality]
"""
import os, sys, time
import pymupdf
from PIL import Image

B = r"H:\桌面\影評書\守燈人影記完成稿"
SRC = os.path.join(B, "守燈人影記_合訂本V6.pdf")
OUTDIR = os.path.join(B, "pages_webp")
os.makedirs(OUTDIR, exist_ok=True)

MAX_W = int(sys.argv[1]) if len(sys.argv) > 1 else 1100
Q = int(sys.argv[2]) if len(sys.argv) > 2 else 72

doc = pymupdf.open(SRC)
n = doc.page_count
# 依頁面實際 pt 尺寸算 dpi，統一寬度
pt_w = doc[0].rect.width
dpi = int(MAX_W / pt_w * 72 + 0.5)

t0 = time.time()
sizes = []
for i in range(n):
    pm = doc[i].get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    p = os.path.join(OUTDIR, "p%03d.webp" % (i + 1))
    im.save(p, "WEBP", quality=Q, method=4)
    sizes.append(os.path.getsize(p))
    if (i + 1) % 20 == 0 or i == 0:
        print("  %3d/%d  %.1f KB  (%.0fs)" % (
            i + 1, n, sizes[-1] / 1024, time.time() - t0))

doc.close()
tot = sum(sizes)
print("-" * 62)
print("%d pages  max_w=%d q=%d  %.1f KB avg  %.1f MB total  in %.0fs" % (
    n, MAX_W, Q, tot / n / 1024, tot / 1048576, time.time() - t0))
print(OUTDIR)
