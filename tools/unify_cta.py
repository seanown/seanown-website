#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各頁末尾 CTA 一致化
===================
原則（依 audit P1-3）：
  1. 每頁末尾都要有明確的行動按鈕，不只寫「更多」。
  2. 按鈕文字必須說明「點下去會到哪裡」——例如「前往服務與合作 →」而不是「看更多」。
  3. 主 CTA 固定為「前往聯絡表單 →」（/contact/）。
  4. 次 CTA 依頁面性質給「上一層」路徑，讓訪客知道自己在哪、往哪走。

用法：
  python tools/unify_cta.py           # dry-run
  python tools/unify_cta.py --apply
"""
import re
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = '--apply' in sys.argv

# 每頁的 (錨點id, 主標, 說明, 主CTA文字, 次CTA文字, 次CTA路徑)
# path 留空代表不放次 CTA
PLANS = {
    'series/index.html': {
        'anchor': 'series-cta',
        'title': '想看更多產業觀點，或直接談合作？',
        'desc': '專輯是按主題整理的選讀；全部 107 篇在專欄頁，可搜尋、可篩選。',
        'cta2': '前往專欄全部文章 →',
        'cta2href': '/articles/',
    },
    'macau-35-plan-report.html': {
        'anchor': 'report-cta',
        'title': '想針對報告內容深入討論？',
        'desc': '報告是公開的完整論述；若有要合作推動的項目，可以直接談。',
        'cta2': '先看服務與合作範圍 →',
        'cta2href': '/services/',
    },
    'articles/index.html': {
        'anchor': 'articles-cta',
        'title': '讀完有想討論的，或想談合作？',
        'desc': '專欄文章是我的觀點與判斷，不是服務說明書。要合作請到服務頁看具體能做什麼。',
        'cta2': '前往服務與合作 →',
        'cta2href': '/services/',
    },
}

CTA_CSS = """
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


def build_cta(p):
    b2 = ''
    if p.get('cta2'):
        b2 = '\n<a class="b2" href="%s">%s</a>' % (p['cta2href'], p['cta2'])
    return '''<div class="end-cta" id="%s">
<h2>%s</h2>
<p>%s</p>
<div class="end-cta-btns">
<a class="b1" href="/contact/">前往聯絡表單 →</a>%s
</div>
</div>''' % (p['anchor'], p['title'], p['desc'], b2)


def inject_css(s):
    if '.end-cta{' in s:
        return s
    if '<style>' in s:
        return s.replace('</style>', CTA_CSS + '</style>', 1)
    # 沒有 style 標籤的頁面：插在 </head> 前
    return s.replace('</head>', '<style>' + CTA_CSS + '</style>\n</head>', 1)


def insert_cta(s, block):
    if 'class="end-cta"' in s:
        return s
    # 優先插在 <footer 前；若無 footer，插在 </body> 前
    m = re.search(r'<div class="foot"', s)
    if m:
        return s[:m.start()] + block + '\n\n' + s[m.start():]
    m2 = re.search(r'<footer', s)
    if m2:
        return s[:m2.start()] + block + '\n\n' + s[m2.start():]
    return s.replace('</body>', block + '\n</body>', 1)


def main():
    changed = []
    for rel, plan in PLANS.items():
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print('  [略過] %s 不存在' % rel)
            continue
        s = open(path, encoding='utf-8').read()
        orig = s
        s = inject_css(s)
        s = insert_cta(s, build_cta(plan))
        if s != orig:
            changed.append(rel)
            if APPLY:
                open(path, 'w', encoding='utf-8').write(s)

    print('=== 頁尾 CTA 一致化 ===')
    print('處理 %d 頁，變更 %d 頁' % (len(PLANS), len(changed)))
    for c in changed:
        print(('  [改] ' if APPLY else '  [將改] ') + c)
    if not APPLY and changed:
        print('\n（dry-run，加 --apply 執行）')
    elif APPLY:
        print('\n已寫入 %d 個檔案' % len(changed))


if __name__ == '__main__':
    main()