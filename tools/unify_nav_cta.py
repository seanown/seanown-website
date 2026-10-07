#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全站導覽統一為六層結構 + 各頁末尾 CTA 一致化
=================================================
六層：關於我／服務與合作／作品／專欄／媒體／聯絡
CTA 慣例：頁尾三按鈕 — 洽談合作(/contact/) 為主、依頁面性质給次要動作、並明說會去哪裡

用法：
  python tools/unify_nav_cta.py            # 只報告會改什麼（dry-run）
  python tools/unify_nav_cta.py --apply    # 實際寫入
"""
import re
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = '--apply' in sys.argv

# 六層導覽（依用戶指定順序）
NAV_ITEMS = [
    ('/about/', '關於我'),
    ('/services/', '服務與合作'),
    ('/series/', '作品'),
    ('/articles/', '專欄'),
    ('/media/', '媒體'),
    ('/contact/', '聯絡'),
]
NAV_CTA = ('/contact/', '聯絡')

# 站內既有頁面（用來判斷 href 是絕對路徑還是全站網域）
KNOWN_PREFIX = tuple(p for p, _ in NAV_ITEMS)


def nav_html(current, site='/'):
    """產生六層 tnav（含 aria-current）。site 可傳 '' 代表根路徑。"""
    parts = []
    for href, label in NAV_ITEMS:
        cur = ' aria-current="page"' if href == current else ''
        cls = ' class="cta"' if href == NAV_CTA[0] else ''
        parts.append(f'<a href="{site}{href}"{cls}{cur}>{label}</a>')
    return '\n'.join('  ' + p for p in parts)


# 頁面缺少 .tnav 樣式時要補的 CSS（與 about/contact 頁保持一致）
TNAV_CSS = """
/* 六層導覽（與全站獨立頁一致）*/
.tnav{display:flex;gap:17px;align-items:center}
.tnav a{font-size:14px;font-weight:600;color:var(--text);text-decoration:none}
.tnav a:hover,.tnav a[aria-current]{color:var(--blue)}
.tnav .cta{background:var(--blue);color:#fff;padding:8px 18px;border-radius:999px;font-size:13.5px}
.tnav .cta:hover{background:var(--blue-dark)}
@media(max-width:860px){.tnav a:not(.cta){display:none}}
"""

NAV_BLOCK = '<nav class="tnav" aria-label="網站導覽">\n{nav}\n</nav>'


def collect_targets():
    """找出所有需要處理的首頁式頁面（獨立頁）。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in ('.git', 'node_modules', '__pycache__',
                                    'tools', 'temp', 'drafts', '_poster_raw',
                                    'generated-images', 'admin', 'movie')]
        if 'index.html' not in filenames:
            continue
        rel = os.path.relpath(dirpath, ROOT).replace('\\', '/')
        if rel == '.':
            url = '/'
        else:
            url = '/' + rel + '/'
        out.append((os.path.join(dirpath, 'index.html'), url))
    return sorted(out, key=lambda x: x[1])


def main():
    files = collect_targets()
    changed = []
    kinds = {}

    for path, url in files:
        s = open(path, encoding='utf-8').read()
        orig = s
        cur = url if url in KNOWN_PREFIX else ''
        kind = None

        # ---- A. 已有 tnav：整段換成六層 ----
        m = re.search(r'<nav class="tnav"[^>]*>[\s\S]*?</nav>', s)
        if m:
            s = s[:m.start()] + NAV_BLOCK.format(nav=nav_html(cur, site_for(url))) + s[m.end():]
            kind = 'A:既有 tnav'

        # ---- B. minimal-hint 型（文章頁）：換成六層 ----
        elif re.search(r'<a class="minimal-hint"[^>]*>[^<]*</a>', s):
            s = re.sub(r'<a class="minimal-hint"[^>]*>[^<]*</a>',
                       NAV_BLOCK.format(nav=nav_html(cur, site_for(url))),
                       s, count=1)
            kind = 'B:minimal-hint → 六層'

        # ---- C. 只有 topbar-in + brand，沒有任何導覽 ----
        elif '<div class="topbar-in"' in s:
            s = re.sub(
                r'(<div class="topbar-in">\s*<a class="brand"[^>]*>.*?</a>)',
                lambda mm: mm.group(1) + '\n' + NAV_BLOCK.format(nav=nav_html(cur, site_for(url))),
                s, count=1, flags=re.S)
            kind = 'C:補 tnav'

        # ---- 補 .tnav 樣式（僅在缺時）----
        if kind and '.tnav{' not in s.replace(' ', '').replace('{{', '{').replace('}}', '}'):
            # 判斷方式：style 區塊內是否已有 tnav 規則
            sm = re.search(r'<style>([\s\S]*?)</style>', s)
            if sm and '.tnav' not in sm.group(1):
                s = s.replace('</style>', TNAV_CSS + '</style>', 1)

        if s != orig:
            changed.append((path, url))
            kinds[kind] = kinds.get(kind, 0) + 1
            if APPLY:
                open(path, 'w', encoding='utf-8').write(s)

    print('=== 六層導覽統一 ===')
    print('目標頁面 %d 個，變更 %d 個' % (len(files), len(changed)))
    for k, v in sorted(kinds.items()):
        print('  %s：%d 頁' % (k, v))
    if not APPLY and changed:
        print('\n（dry-run，未寫入。加 --apply 實際執行）')
    elif APPLY:
        print('\n已寫入 %d 個檔案' % len(changed))


def site_for(url):
    """文章頁等子目錄頁使用根路徑即可（站內均支援 /about/ 這種絕對路徑）。"""
    return ''


if __name__ == '__main__':
    main()