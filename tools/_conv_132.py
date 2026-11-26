# -*- coding: utf-8 -*-
"""把「琉光璃彩」開幕典禮的 29 張現場照轉入 assets/images/posts/132-N.jpg。

來源：本輪對話附件的 blob 落盤（00:32:28 批次，mtime 順序＝訊息中的
@image#1..#29 順序，已抽驗 #1=陳莉致辭、#29=開幕主視覺）。
規格對齊先例（129 黃埔島 29 圖／131 一縷銀光 10 圖）：
  長邊 1320、JPEG quality 86、progressive；EXIF 方向先轉正再縮。
"""
import io
import os
import sys

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, 'temp', '_batch32.txt')
OUT_DIR = os.path.join(ROOT, 'assets', 'images', 'posts')
NUM = 132
LONG_SIDE = 1320
QUALITY = 86


def main():
    srcs = [l.strip() for l in io.open(LIST, encoding='utf-8') if l.strip()]
    assert len(srcs) == 29, '批次應為 29 張，實得 %d' % len(srcs)
    os.makedirs(OUT_DIR, exist_ok=True)
    total_in = total_out = 0
    for i, src in enumerate(srcs, 1):
        blob = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            '.workbuddy', 'blobs', src) if not os.path.isabs(src) else src
        # _batch32.txt 記的是相對於 blobs/ 的路徑（./80/xxx.jpg）
        blob = os.path.join('C:/Users/user/.workbuddy/blobs', src.lstrip('./'))
        if not os.path.isfile(blob):
            print('MISSING', blob)
            sys.exit(1)
        im = Image.open(blob)
        im = ImageOps.exif_transpose(im)  # 手機照先轉正
        im = im.convert('RGB')
        w, h = im.size
        if max(w, h) > LONG_SIDE:
            if w >= h:
                im = im.resize((LONG_SIDE, round(h * LONG_SIDE / w)), Image.LANCZOS)
            else:
                im = im.resize((round(w * LONG_SIDE / h), LONG_SIDE), Image.LANCZOS)
        out = os.path.join(OUT_DIR, '%d-%d.jpg' % (NUM, i))
        im.save(out, 'JPEG', quality=QUALITY, optimize=True, progressive=True)
        si, so = os.path.getsize(blob), os.path.getsize(out)
        total_in += si
        total_out += so
        print('%2d %-28s -> %dx%d  %.0fKB -> %.0fKB' % (i, os.path.basename(src)[:28], im.size[0], im.size[1], si / 1024, so / 1024))
    print('done: 29 files, %.1fMB -> %.1fMB' % (total_in / 1e6, total_out / 1e6))


if __name__ == '__main__':
    main()
