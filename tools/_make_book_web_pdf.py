# -*- coding: utf-8 -*-
"""《守燈人影記》合訂本 -> 網頁輕量版 PDF

原版 30MB / 274 頁，其中 34 張內嵌插圖佔 22MB。
網頁版不需要印刷級解析度（1024px ÷ 148mm ≈ 176dpi，本來就有餘），
所以只做一件事：把內嵌圖降解析 + 重壓成 JPEG。
文字向量完全保留 -> 搜尋、選取、放大、書籤、SEO 全部照舊。

陷阱備忘（實測踩過）：
1. 不能用 doc.update_stream() 直接換圖片位元組。
   原檔圖是 ICCBased 色彩空間（33/34 張），換掉 stream 後 ICC 與新的
   JPEG 不匹配，render 出來整頁全黑。必須用 Page.replace_image()
   讓 PyMuPDF 走完整物件流程（含色彩空間／長度／filter 重算）。
2. replace_image 是「整份文件範圍」：傳 xref 即可，它會自動找出所有
   引用該 xref 的頁面一併替換。
3. doc.subset_fonts() 對 Type3 字體無效（回傳 None），字體壓不動。

用法: python _make_book_web_pdf.py [max_w] [quality]
"""
import io, os, sys, time
import pymupdf
from PIL import Image

BASE = r"H:\桌面\影評書\守燈人影記完成稿"
SRC = os.path.join(BASE, "守燈人影記_合訂本V6.pdf")
OUT = os.path.join(BASE, "守燈人影記_網頁版.pdf")

MAX_W = int(sys.argv[1]) if len(sys.argv) > 1 else 760   # 插圖最大寬 px
Q = int(sys.argv[2]) if len(sys.argv) > 2 else 68        # JPEG 品質
MIN_SAVE = 4096

doc = pymupdf.open(SRC)
orig = os.path.getsize(SRC)

xrefs = set()
for i in range(doc.page_count):
    for im in doc.get_page_images(i):
        xrefs.add(im[0])

# xref -> 負責的頁面
xref2page = {}
for i in range(doc.page_count):
    for im in doc.get_page_images(i):
        xref2page.setdefault(im[0], i)

replaced = saved = 0
t0 = time.time()
for xref in sorted(xrefs):
    try:
        raw = doc.extract_image(xref)["image"]
    except Exception as e:
        print("  skip", xref, e)
        continue
    if len(raw) <= MIN_SAVE:
        continue
    try:
        im = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        print("  open fail", xref, e)
        continue
    if im.width > MAX_W:
        im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
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
    print("  xref %-6d p%-4d %6dKB -> %5dKB  %dx%d" % (
        xref, xref2page[xref] + 1, len(raw) // 1024, len(nb) // 1024,
        im.width, im.height))

doc.save(OUT, garbage=4, deflate=True, deflate_images=True, deflate_fonts=True)
doc.close()
new = os.path.getsize(OUT)
print("-" * 66)
print("max_w=%d q=%d  replaced %d/%d imgs" % (MAX_W, Q, replaced, len(xrefs)))
print("%.1f MB -> %.1f MB  (%.0f%%)  in %.0fs" % (
    orig / 1048576, new / 1048576, new / orig * 100, time.time() - t0))
print(OUT)
