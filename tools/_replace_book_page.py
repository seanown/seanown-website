# -*- coding: utf-8 -*-
"""替換《守燈人影記》某一頁的 WebP（保持全書解析度／品質一致）

用法: python _replace_book_page.py <頁碼> <來源圖> [--pdf <PDF 路徑> --pdf-page <頁碼>]

為什麼要這支：
  網站翻閱器的 274 張 WebP 是統一規格（1102×1563、q=72）。
  軒哥新給的版權頁是 150dpi PNG（875×1241），比例一致但解析度不同，
  直接改會讓那一頁在翻頁時看起來比其它頁糊／大，所以統一縮放回全書規格。

同步處理兩處：
  1) assets/book/sy-deng-ren/pages/pNNN.webp   ← 網站翻閱器用
  2) H:\\桌面\\影評書\\守燈人影記完成稿\\pages_webp\\pNNN.webp ← 來源素材目錄
"""
import os
import sys
from PIL import Image

# 全書統一規格（由 tools/_render_book_pages.py 產生）
TARGET_W = 1102
Q = 72

REPO = r"C:\Users\user\WorkBuddy\Seanown.org"
PAGES_WEBP = os.path.join(REPO, "assets", "book", "sy-deng-ren", "pages")
SRC_PAGES = r"H:\桌面\影評書\守燈人影記完成稿\pages_webp"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    pageno = int(sys.argv[1])
    src = sys.argv[2]

    im = Image.open(src).convert("RGB")
    sw, sh = im.size
    # 等比縮放到全書寬度（版權頁是整頁文字稿，不會有裁切風險）
    if sw != TARGET_W:
        th = round(sh * TARGET_W / sw)
        im = im.resize((TARGET_W, th), Image.LANCZOS)

    out_name = "p%03d.webp" % pageno
    targets = [os.path.join(PAGES_WEBP, out_name),
               os.path.join(SRC_PAGES, out_name)]

    for p in targets:
        if not os.path.isdir(os.path.dirname(p)):
            print("  [skip] 目錄不存在：%s" % os.path.dirname(p))
            continue
        im.save(p, "WEBP", quality=Q, method=4)
        kb = os.path.getsize(p) / 1024
        print("  [ok] %s  %.1f KB  %dx%d" % (p, kb, im.size[0], im.size[1]))


if __name__ == "__main__":
    main()