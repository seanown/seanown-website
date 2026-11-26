#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把「澳門週訊最新一期」同步到首頁的週訊卡片
=============================================
原因：首頁的週訊卡片若要靠人手改，之後每週出新一期都會忘記更新 ——
      首頁就會一直顯示舊期數、舊數據，等於假資訊。

做法：解析 macau-weekly/index.html 的期數總覽（該頁由 build_weekly.py 自動生成），
      取第一條（最新期）+ 該期 HTML 裡的三個 highlight-chip 數據，
      寫回首頁的 .weekly-card。

用法：
  python tools/sync_weekly_home.py            # dry-run，印出將寫入的內容
  python tools/sync_weekly_home.py --apply    # 實際寫入

設計約束：
  - 只改「wk-issue / wk-period / 三個 wk-stat / 兩個連結」這幾處，
    不動首頁其他版面（避免與手工調版互相覆蓋）。
  - 若解析失敗，報錯並中止，不寫入半套資料。
"""
import re
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WK_INDEX = os.path.join(ROOT, 'macau-weekly', 'index.html')
HOME = os.path.join(ROOT, 'index.html')
APPLY = '--apply' in sys.argv


def parse_latest():
    """從期數總覽頁解析最新一期。回傳 dict。"""
    s = open(WK_INDEX, encoding='utf-8').read()
    m = re.search(
        r'<a class="issue-card" href="([^"]+)">\s*'
        r'<span class="issue-no">([^<]+)</span>\s*'
        r'<span class="issue-date">([^<]+?)(?:<span class="latest-chip">[^<]*</span>)?</span>\s*'
        r'<span class="issue-range">([^<]+)</span>',
        s)
    if not m:
        raise SystemExit('[ABORT] 期數總覽頁解析失敗（issue-card 結構變了？）')
    href, no, date, rng = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
    # 日期：2026年10月5日 → 2026.10.05
    dm = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date)
    if not dm:
        raise SystemExit('[ABORT] 日期格式無法解析：%r' % date)
    iso = '%s-%02d-%02d' % (dm.group(1), int(dm.group(2)), int(dm.group(3)))
    # date 原文含「出報」後綴、range 原文含「統計週 」前綴（源頁就這樣寫的）。
    # 顯示時組成「統計週 X（2026年10月5日 出報）」需要乾淨的日期，故把「出報」剝掉。
    date_clean = re.sub(r'\s*出報\s*$', '', date).strip()
    return {
        'href': '/macau-weekly/' + href,
        'no': no,
        'date_cn': date_clean,
        'iso': iso,
        'range': rng,
    }


def parse_stats(issue):
    """從該期 HTML 抓 highlight-chip 的三個數字。"""
    path = os.path.join(ROOT, 'macau-weekly', os.path.basename(issue['href']))
    s = open(path, encoding='utf-8').read()
    body = s[s.find('<body'):]
    chips = re.findall(
        r'<div class="highlight-chip">\s*'
        r'<div class="num">([^<]+)</div>\s*'
        r'<div class="label">([^<]*)</div>\s*'
        r'<div class="desc">([^<]+)</div>',
        body)
    if len(chips) < 3:
        raise SystemExit('[ABORT] %s 只抓到 %d 個 highlight-chip（預期至少 3）'
                         % (path, len(chips)))
    return [{'n': a.strip(), 'l': b.strip(), 'd': c.strip()} for a, b, c in chips[:3]]


def main():
    issue = parse_latest()
    stats = parse_stats(issue)

    print('=== 澳門週訊 → 首頁同步 ===')
    print('  最新一期：%s（%s）%s' % (issue['no'], issue['iso'], issue['range']))
    print('  連結：%s' % issue['href'])
    for st in stats:
        print('    %s %s｜%s' % (st['n'], st['l'], st['d']))

    if not os.path.exists(HOME):
        raise SystemExit('[ABORT] 找不到首頁 index.html')
    h = open(HOME, encoding='utf-8').read()

    if 'class="weekly-card"' not in h:
        raise SystemExit('[ABORT] 首頁找不到 .weekly-card 區塊')

    before = h

    # ---- 期數 / 出報日 ----
    # 注意：range 原文已含「統計週 」前綴、date 原文已含「出報」後綴，
    # 直接套用即可，不要再加一次（否則會出現「統計週 統計週 … 出報 出報」）。
    h = re.sub(r'(<span class="wk-issue" id="wk-issue">)[^<]*(</span>)',
               r'\g<1>%s\g<2>' % issue['no'], h, count=1)
    h = re.sub(r'(<span class="wk-period" id="wk-period">)[^<]*(</span>)',
               lambda mm: mm.group(1) + '%s（%s 出報）' % (issue['range'], issue['date_cn']) + mm.group(2),
               h, count=1)

    # ---- 三個數據卡 ----
    blocks = ''.join(
        '<div class="wk-stat"><span class="n">%s</span><span class="l">%s｜%s</span></div>\n    '
        % (st['n'], st['l'], st['d']) for st in stats)
    h, n = re.subn(r'(<div class="wk-right">.*?<div class="wk-right-t">[^<]*</div>\n)\s*(?:<div class="wk-stat">.*?</div>\s*)+',
                   lambda mm: mm.group(1) + '    ' + blocks,
                   h, count=1, flags=re.S)
    if n != 1:
        raise SystemExit('[ABORT] 數據卡替換失敗（n=%d）' % n)

    # ---- 兩個連結 ----
    h = re.sub(r'(<a class="wk-main" href=")[^"]*(">)',
               r'\g<1>%s\g<2>' % issue['href'], h, count=1)

    if h == before:
        print('\n首頁已是最新，無需變更。')
        return

    if APPLY:
        open(HOME, 'w', encoding='utf-8').write(h)
        print('\n已寫入首頁。')
    else:
        print('\n（dry-run，加 --apply 寫入）')


if __name__ == '__main__':
    main()