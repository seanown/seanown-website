#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把文章頁與專輯頁的「文末 CTA + 舊錨點」統一（對應 tools/build_articles.py 模板改動）
=================================================================================
背景：audit P1-3 指名「更多文章」這種按鈕文字沒說明點下去會到哪裡。
      這裡把 107 篇文章頁與 5 個專輯頁一次同步，並修掉殘留的 {#sec-author} 舊錨點。

用法：python tools/fix_article_cta.py [--apply]
"""
import re
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = '--apply' in sys.argv

OLD_CTA = '''<div class="cta">
<h2>想進一步交流？</h2>
<p>無論是數位出海、文化 IP 合作，或青年跨界連結，都歡迎與我聊聊。</p>
<a class="btn" href="{S}/contact/">洽談合作</a>
<a class="btn ghost" href="{S}/articles/">更多文章</a>
</div>'''

NEW_CTA = '''<div class="cta">
<h2>想進一步交流？</h2>
<p>這裡是我的觀點與判斷，不是服務說明書。要合作請到服務頁看具體能做什麼、怎麼合作、怎麼計價。</p>
<a class="btn" href="{S}/contact/">前往聯絡表單 →</a>
<a class="btn ghost" href="{S}/services/">前往服務與合作 →</a>
</div>'''

SERIES_CTA = '''<div class="end-cta" id="series-cta">
<h2>想看更多產業觀點，或直接談合作？</h2>
<p>專輯是按主題整理的選讀；全部 107 篇在專欄頁，可搜尋、可篩選。</p>
<div class="end-cta-btns">
<a class="b1" href="/contact/">前往聯絡表單 →</a>
<a class="b2" href="/articles/">前往專欄全部文章 →</a>
</div>
</div>'''

END_CTA_CSS = """
/* ===== 頁尾統一行動區 ===== */
.end-cta{max-width:1080px;margin:52px auto 0;background:linear-gradient(135deg,#002676 0%,#010133 100%);color:#fff;border-radius:22px;padding:42px 40px;text-align:center}
.end-cta h2{font-size:25px;font-weight:800;margin-bottom:10px;line-height:1.45}
.end-cta p{color:rgba(255,255,255,.82);margin-bottom:22px;font-size:15px;max-width:660px;margin-left:auto;margin-right:auto;line-height:1.8}
.end-cta-btns{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
.end-cta-btns a{padding:13px 30px;border-radius:999px;font-size:15px;font-weight:700;transition:all .2s;display:inline-block}
.end-cta-btns .b1{background:#FDB515;color:#010133}
.end-cta-btns .b1:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(253,181,21,.28)}
.end-cta-btns .b2{border:2px solid rgba(255,255,255,.7);color:#fff}
.end-cta-btns .b2:hover{background:#fff;color:#002676}
@media(max-width:760px){.end-cta{padding:32px 20px}.end-cta h2{font-size:21px}.end-cta-btns a{width:100%;text-align:center}}
"""

SITES = ('https://seanown.org', 'http://seanown.org', '')


def fix_article(s, site):
    old = OLD_CTA.format(S=site)
    new = NEW_CTA.format(S=site)
    if old in s:
        s = s.replace(old, new, 1)
    # 舊錨點 → /about/
    s = s.replace(f'{site}/#sec-author', f'{site}/about/')
    s = s.replace(f'{site}/#sec-contact', f'{site}/contact/')
    return s


def inject_end_cta(s):
    """注入 .end-cta 的 CSS 與 DOM。

    注意：必須先判斷 DOM 是否存在，再注入 CSS。
    若順序寫反（先注入 CSS 再判斷 'end-cta' in s），CSS 會讓條件恆為真，
    導致 DOM 永遠插不進去 —— 這就是本函式第一版的 bug。
    """
    has_dom = 'class="end-cta"' in s
    has_css = '.end-cta{' in s
    if has_dom and has_css:
        return s
    if not has_css and '<style>' in s:
        s = s.replace('</style>', END_CTA_CSS + '</style>', 1)
    if not has_dom:
        m = re.search(r'<div class="foot"', s)
        if m:
            s = s[:m.start()] + SERIES_CTA + '\n\n' + s[m.start():]
        else:
            s = s.replace('</body>', SERIES_CTA + '\n</body>', 1)
    return s


def main():
    arts = os.path.join(ROOT, 'article')
    files = []
    for name in sorted(os.listdir(arts)):
        p = os.path.join(arts, name, 'index.html')
        if os.path.exists(p):
            files.append(p)

    changed = []
    for p in files:
        s = open(p, encoding='utf-8').read()
        o = s
        for site in SITES:
            s = fix_article(s, site)
        if s != o:
            changed.append(p)
            if APPLY:
                open(p, 'w', encoding='utf-8').write(s)

    print('=== 文章頁 CTA + 舊錨點 ===')
    print('文章頁 %d 篇，變更 %d 篇' % (len(files), len(changed)))
    left = 0
    for p in files:
        s = open(p, encoding='utf-8').read()
        if '更多文章</a>' in s or 'sec-author' in s or 'sec-contact' in s:
            left += 1
            print('  [殘留] ' + os.path.relpath(p, ROOT))
    print('殘留舊文案：%d 篇' % left)

    # 專輯頁（5 個子專輯）
    ser = os.path.join(ROOT, 'series')
    sc = []
    for name in sorted(os.listdir(ser)):
        p = os.path.join(ser, name, 'index.html')
        if not os.path.exists(p):
            continue
        s = open(p, encoding='utf-8').read()
        o = s
        s = inject_end_cta(s)
        if s != o:
            sc.append(name)
            if APPLY:
                open(p, 'w', encoding='utf-8').write(s)
    print('專輯頁變更：%s' % (', '.join(sc) if sc else '無'))

    if APPLY:
        print('\n已寫入：文章 %d 篇、專輯 %d 頁' % (len(changed), len(sc)))
    else:
        print('\n（dry-run，加 --apply 執行）')


if __name__ == '__main__':
    main()