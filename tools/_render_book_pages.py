# -*- coding: utf-8 -*-
"""《守燈人影記》279 頁 -> WebP 逐頁圖（給網站翻閱用）

2026-11-10 更新：源由 V6(已刪) 換成 V34 合訂本；輸出改到暫存目錄
_pages_v34，頁序比對無誤後才切換到 assets/book/sy-deng-ren/pages/。

2026-11-14 更新（軒哥交付 V35、指示「用 35 替代 34 然後上線」）：
  - 來源改用軒哥 11-14 提供的桌面版 V35（已備份到書專案 pdf 目錄，
    檔名 守燈人影記_合訂本V35_軒哥提供_20261114.pdf）。
  - 輸出暫存改為 _pages_v35；**不直接覆蓋線上 pages/**。
  - 逐頁比對結果：V34→V35 只有 PDF p6/p7/p8（名家推薦）變動，
    其餘 276 頁文字與畫面完全相同；而 p6–p8 落在線上試讀未收錄的
    書前頁（PDF p3–p14），故線上 274 張 WebP 無須重換、頁序不動。
  - 線上映射（實測）：p001=自製封面；p002/p003=PDF p1/p2；
    p010..p272=PDF p15..p277；書前 p004..p009 為網站另製頁。

為什麼不做「把 PDF 塞進網頁」：
  原版 30MB，PyMuPDF rewrite_images 壓到 20MB 還是太重
  （Type3 字體的設計語言無 FontFile 串，subset_fonts() 無效，壓不動）。
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

# 2026-11-10: 舊路徑 H:\桌面\影評書\守燈人影記完成稿\ 已刪除，專案搬到 澳門電影書專案。
# 輸出先用暫存目錄 _pages_v34，與線上 274 頁比對無誤後才替換 pages/。
B = r"H:\澳門電影書專案\影評書\pdf"
SRC = os.path.join(B, "守燈人影記_合訂本V35_軒哥提供_20261114.pdf")
# 暫存目錄：與工具同級的 tools/_pages_v35，不碰線上 assets/book/.../pages/
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pages_v35")
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
