# -*- coding: utf-8 -*-
"""擷取新文章頁排版截圖（桌面版開頭 + 手機版）。"""
import os
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(os.path.join(ROOT, '_shots'))
if not os.path.isdir(OUT):
    os.makedirs(OUT)
URL = 'file:///' + os.path.join(ROOT, 'article',
                                'quzhou-nankong-returning-home',
                                'index.html').replace('\\', '/')

with sync_playwright() as pw:
    br = pw.chromium.launch()

    # 桌面版：文章開頭
    d = br.new_page(viewport={'width': 1280, 'height': 1200})
    d.goto(URL, wait_until='networkidle')
    d.wait_for_timeout(400)
    d.screenshot(path=os.path.join(OUT, 'qz_desktop_top.png'))

    # 桌面版：粗體六句心得段落
    d.evaluate("""() => {
      const t = Array.from(document.querySelectorAll('strong'))
        .find(e => e.innerText.includes('沒有強大的軍事'));
      if (t) t.scrollIntoView({block: 'center'});
    }""")
    d.wait_for_timeout(400)
    d.screenshot(path=os.path.join(OUT, 'qz_desktop_bold.png'))

    # 手機版
    m = br.new_page(viewport={'width': 390, 'height': 844})
    m.goto(URL, wait_until='networkidle')
    m.wait_for_timeout(400)
    m.screenshot(path=os.path.join(OUT, 'qz_mobile_top.png'))

    br.close()

print('輸出：%s' % OUT)
for f in sorted(os.listdir(OUT)):
    if f.startswith('qz_'):
        print('  ' + f)