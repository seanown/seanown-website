# -*- coding: utf-8 -*-
"""《守燈人影記》合訂本 -> 網頁輕量版 PDF

原版 29.1MB / 279 頁，其中 33 張內嵌插圖佔大部分體積。
網頁版不需要印刷級解析度（1024px ÷ 148mm ≈ 176dpi，本來就有餘），
所以只做一件事：把內嵌圖降解析 + 重壓成 JPEG。
文字向量完全保留 -> 搜尋、選取、放大、書籤、SEO 全部照舊。

2026-11-10 更新：
  - 源由 V6(已刪) 換成 V34；輸出到暫存 tools/，不碰線上。
  - pymupdf 2.1 移除了 Document.replace_image()，改用內建 rewrite_images()。
    新版反而更安全：它自己走完整物件流程（含色彩空間／長度／filter 重算），
    不需要再手動 xref_set_key(SMask) 或逐 xref 換 stream，也不會踩
    舊版「ICCBased 色彩空間換 stream 後整頁全黑」的坑。
  - 保留 replace_image 分支以向後相容舊 pymupdf（< 2.0）。

陷阱備忘（舊版實測，保留供查）：
1. 舊版不能用 doc.update_stream() 直接換圖片位元組 — 整頁全黑。
2. doc.subset_fonts() 對 Type3 字體無效（回傳 None），字體壓不動 — 新版同樣，
   但文字是向量，不需壓。

用法: python _make_book_web_pdf.py [dpi_target] [quality]
"""
import io, os, sys, time
import pymupdf
from PIL import Image

SRC_DIR = r"H:\澳門電影書專案\影評書\pdf"
SRC = os.path.join(SRC_DIR, "守燈人影記_合訂本V34.pdf")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "守燈人影記_網頁版V34.pdf")

DPI_TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 176  # 插圖目標 DPI
Q = int(sys.argv[2]) if len(sys.argv) > 2 else 68            # JPEG 品質
MIN_SAVE = 4096

doc = pymupdf.open(SRC)
orig = os.path.getsize(SRC)
t0 = time.time()

if hasattr(doc, "rewrite_images"):
    # pymupdf >= 2.0：內建重寫，自動處理色彩空間，一行搞定
    # pymupdf 2.1 要求 dpi_target < dpi_threshold。
    # 閾值取 300（只動高於印刷密度的圖），目標 176（網頁足夠）。
    doc.rewrite_images(
        dpi_threshold=300,
        dpi_target=DPI_TARGET,
        quality=Q,
        lossy=True, lossless=True, bitonal=True, color=True, gray=True,
    )
    replaced = "n/a (rewrite_images handled internally)"
    saved = 0
else:
    # 舊 pymupdf：逐 xref 換（保留原邏輯）
    xrefs = set()
    xref2page = {}
    for i in range(doc.page_count):
        for im in doc.get_page_images(i):
            xrefs.add(im[0])
            xref2page.setdefault(im[0], i)
    replaced = saved = 0
    for xref in sorted(xrefs):
        try:
            raw = doc.extract_image(xref)["image"]
        except Exception as e:
            print("  skip", xref, e); continue
        if len(raw) <= MIN_SAVE:
            continue
        try:
            im = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as e:
            print("  open fail", xref, e); continue
        max_w = int(DPI_TARGET / 72 * 148 / 25.4 * 100)  # 約 1024px @176dpi
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=Q, optimize=True, progressive=True)
        nb = buf.getvalue()
        if len(nb) >= len(raw):
            continue
        try:
            doc.xref_set_key(xref, "SMask", "null")
        except Exception:
            pass
        doc.replace_image(xref, stream=nb)
        replaced += 1
        saved += len(raw) - len(nb)
        print("  xref %-6d p%-4d %6dKB -> %5dKB" % (
            xref, xref2page[xref] + 1, len(raw)//1024, len(nb)//1024))

doc.save(OUT, garbage=4, deflate=True, deflate_images=True, deflate_fonts=True)
doc.close()
new = os.path.getsize(OUT)
print("-" * 66)
print("dpi_target=%d q=%d  replaced=%s" % (DPI_TARGET, Q, replaced))
print("%.1f MB -> %.1f MB  (%.0f%%)  in %.0fs" % (
    orig / 1048576, new / 1048576, new / orig * 100, time.time() - t0))
print(OUT)
