# -*- coding: utf-8 -*-
"""把 markitdown 抽出的 docx 草稿，轉成 seanown.org 文章頁可用的繁體 markdown 正文。

處理：
- 抽出 標題 / 副標 / 作者 三行（檔首 1/3/5 行）
- 刪除「目錄」整塊（含 PDF 頁碼，網頁用不到）
- 章節標題降一級：# -> ## 、## -> ###（md_to_html 只認 2~4 個 #）
- 清單 •　 -> - （markdown 有序/無序列表語法）
- opencc s2t 轉繁體
輸出 tools/_body_125.md（供校對），並印出抽出的中繼資料。
"""
import re
import io
import os
import opencc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFT = r'C:/Users/user/WorkBuddy/_invest_draft/draft_125_raw.md'
BODY_OUT = os.path.join(ROOT, 'tools', '_body_125.md')

cc = opencc.OpenCC('s2t')


def shift_heading(line):
    m = re.match(r'^(#+)\s+(.*)$', line)
    if m:
        return '#' + line  # 整體降一級
    return line


def fix_bullet(line):
    if re.match(r'^\s*[•·]', line, flags=re.U):
        return re.sub(r'^\s*[•·]\s*', '- ', line, flags=re.U)
    return line


def main():
    lines = io.open(DRAFT, encoding='utf-8').read().split('\n')
    lines = [l.rstrip() for l in lines]

    # ---- 抽出檔首三行 ----
    title_raw = lines[0].strip()
    subtitle_raw = lines[2].strip()
    author_raw = lines[4].strip()

    title = re.sub(r'\*\*', '', title_raw.split('第一堂.')[-1]).strip()
    subtitle = '第一堂 · 大象投資學｜' + subtitle_raw
    parts = [p.strip() for p in author_raw.split('・')]
    byline = parts[0].replace('翁振軒SEAN', '翁振軒 SEAN') + ' ・ ' + parts[1]

    # ---- 刪 TOC、取正文區塊 ----
    toc_start = next(i for i, l in enumerate(lines) if l.lstrip().startswith('#') and '目錄' in l)
    chap_start = next(i for i, l in enumerate(lines)
                      if i > toc_start and re.match(r'^#+\s+\*\*?一、', l))
    body_src = lines[6:toc_start] + lines[chap_start:]

    # ---- 結構處理 ----
    out = []
    for ln in body_src:
        ln = shift_heading(ln)
        ln = fix_bullet(ln)
        out.append(ln)

    body_simpl = '\n'.join(out).strip()
    body = cc.convert(body_simpl)

    io.open(BODY_OUT, 'w', encoding='utf-8').write(body + '\n')

    print('=== 抽出中繼資料（已 s2t）===')
    print('TITLE   :', cc.convert(title))
    print('SUBTITLE:', cc.convert(subtitle))
    print('BYLINE  :', cc.convert(byline))
    print('TOC 刪除區間: 行 %d ~ %d（保留引言 %d 行 + 章節）' % (toc_start + 1, chap_start + 1, toc_start - 6))
    print('BODY 字數(約):', len(body))
    print('BODY 輸出 ->', BODY_OUT)


if __name__ == '__main__':
    main()
