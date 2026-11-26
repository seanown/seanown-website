# -*- coding: utf-8 -*-
"""擷取「全部文章」頁兩區結構截圖（桌面＋手機），用於視覺驗收。

用法：python tools/_shot_articles_sections.py
輸出：_shots/articles_sections_*.png
"""
import os
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(os.path.join(ROOT, '_shots'))
if not os.path.isdir(OUT):
    os.makedirs(OUT)
URL = 'file:///' + os.path.join(ROOT, 'articles', 'index.html').replace('\\', '/')

with sync_playwright() as pw:
    br = pw.chromium.launch()

    # ── 桌面版：專欄文章區 ──
    d = br.new_page(viewport={'width': 1280, 'height': 1400})
    d.goto(URL, wait_until='networkidle')
    d.wait_for_timeout(500)

    # 🔴 頁面有 html{scroll-behavior:smooth}，scrollTo 會動畫跳轉，
    #    截圖前必須先關掉平滑並等待，否則會拍到捲動途中的畫面。
    d.evaluate("() => {document.documentElement.style.scrollBehavior='auto'}")
    d.evaluate("() => {const e=document.querySelector('#sec-columns');window.scrollTo(0,e.offsetTop-60)}")
    d.wait_for_timeout(600)
    d.screenshot(path=os.path.join(OUT, 'articles_sections_desktop_columns.png'))

    # ── 桌面版：電影觀後感區 ──
    d.evaluate("() => {const e=document.querySelector('#sec-reviews');window.scrollTo(0,e.offsetTop-60)}")
    d.wait_for_timeout(600)
    d.screenshot(path=os.path.join(OUT, 'articles_sections_desktop_reviews.png'))

    # ── 桌面版：整頁高度概覽（縮圖） ──
    d.screenshot(path=os.path.join(OUT, 'articles_sections_desktop_full.png'),
                 full_page=True)

    # ── 手機版 ──
    m = br.new_page(viewport={'width': 390, 'height': 844})
    m.goto(URL, wait_until='networkidle')
    m.wait_for_timeout(500)
    m.evaluate("() => {document.documentElement.style.scrollBehavior='auto'}")
    m.evaluate("() => {const e=document.querySelector('#sec-columns');window.scrollTo(0,e.offsetTop-60)}")
    m.wait_for_timeout(600)
    m.screenshot(path=os.path.join(OUT, 'articles_sections_mobile_columns.png'))
    m.evaluate("() => {const e=document.querySelector('#sec-reviews');window.scrollTo(0,e.offsetTop-60)}")
    m.wait_for_timeout(600)
    m.screenshot(path=os.path.join(OUT, 'articles_sections_mobile_reviews.png'))

    # ── 量測：卡片高度是否一致、摘要是否截斷 ──
    stats = d.evaluate("""() => {
      const col = document.querySelectorAll('#colgrid .lc-card');
      const rev = document.querySelectorAll('#revgrid .rev-card');
      const h = Array.from(col).map(c => Math.round(c.getBoundingClientRect().height));
      const rh = Array.from(rev).map(c => Math.round(c.getBoundingClientRect().height));
      const ps = Array.from(document.querySelectorAll('#colgrid .lc-card p'))
        .map(p => ({clamped: p.scrollHeight > p.clientHeight + 1,
                    lines: Math.round(p.scrollHeight / 23)}));
      return {colCount: col.length, revCount: rev.length,
              colHeights: h, revHeights: rh,
              colMin: Math.min(...h), colMax: Math.max(...h),
              revMin: Math.min(...rh), revMax: Math.max(...rh),
              clampedCount: ps.filter(x => x.clamped).length,
              lineStats: ps.reduce((a,x)=>{a[x.lines]=(a[x.lines]||0)+1;return a},{})};
    }""")
    print('專欄卡 %d 張｜高度 %d–%d' % (stats['colCount'], stats['colMin'], stats['colMax']))
    print('電影卡 %d 張｜高度 %d–%d' % (stats['revCount'], stats['revMin'], stats['revMax']))
    print('專欄各卡高度：', stats['colHeights'])
    print('電影各卡高度：', stats['revHeights'])
    print('摘要被 line-clamp 截斷：%d／%d 張' % (stats['clampedCount'], stats['colCount']))
    print('摘要行數分佈：', stats['lineStats'])

    br.close()
print('shots saved to', OUT)
