#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
content_lint.py — 發布前內容檢查清單自動化（文案事實類清零）
掃描 .md / .html / .txt 草稿，命中 5 類問題並分級：
  1. BRAND    品牌字（繁體正確性）：傳統「龍」+ 簡體「游」(氵) → 應為「龍遊」(辶)
            [ERROR, --fix 可自動修；純簡體「龙游」與白名單「龙游传媒」不判錯]
  2. FESTIVAL 節慶/日期：出現節慶詞但未確認當年公曆日期      [WARN]
  3. CANTONESE 粵語語法助詞：標準書面語禁用                  [WARN]
  4. LEAK     對外文案洩漏詞：公開頁不應出現                  [WARN, 用「對誰說」判準覆核]
  5. SELFDEF  事實不自辯：層級辨析/職性質註/屆次依據          [WARN]

用法：
  python content_lint.py <file|dir> [--fix] [--strict] [--ext md,html,txt]
    <file|dir>  要掃描的檔案或目錄（目錄遞迴）
    --fix       自動修復 BRAND 類（品牌字改 遊），寫回原檔
    --strict    WARN 也視為不通過（預設只有 ERROR 擋關）
    --ext       目錄模式下的副檔名過濾（逗號分隔，預設 md,html,txt）

退出碼：有 ERROR（或 --strict 下有 WARN）→ 1；全淨 → 0。
注意：WARN 類需人工依「對誰說」判準覆核，腳本不替你拍板。
"""

import sys
import os
import re
import argparse

# ---------- 規則定義 ----------
# 1. 品牌字（繁體正確性）：傳統「龍」後接簡體「游」(氵) → 應為「龍遊」(辶)。
#    原則（使用者 2026-11-04 拍板）：境外繁體內容必須用辶走字旁；大陸簡體
#    引用（如「龙游传媒」「风雅龙游」用简体「龙」）依簡體慣例保留氵，不判錯。
#    故本規則只抓「繁體龍 ＋ 簡體游」的繁簡混寫錯字（例：龍游縣志→龍遊縣志），
#    不抓純簡體「龙游」；並對「游」後接「传媒」者再開白名單（防龍游传媒誤擋）。
BRAND_BAD = re.compile(r'龍游(?!传媒)')
BRAND_FIX = lambda m: m.group(1) + '遊'

# 2. 節慶詞（出現即提醒查證當年農曆對應公曆）
FESTIVALS = ['中秋', '春節', '端午', '重陽', '冬至', '元宵', '除夕',
             '農曆新年', '踏青', '盂蘭', '中元']

# 3. 粵語語法助詞（標準書面語禁用；在地文化詞不在此列）
#    注意：只收「絕不會出現在標準中文或人名」的詞。
#    已剔除：架（標準字：三腳架/腳手架/架機）、仲/冇（人名碰撞：程仲森/張仲文/冇姐）。
CANTONESE = ['乜嘢', '點樣', '佢哋', '喺', '咗', '唔', '呢個', '咁',
             '嘅', '啲', '邊度', '幾時', '咩']

# 4. 對外文案洩漏詞（公開頁不應出現的「自我暴露弱點」詞；須用「對誰說」判準覆核）
#    注意：收窄到此清單——「未經實地查證/Subzin/IMDb」等屬讀者可信度註（應保留），不在此列。
LEAK_WORDS = ['查不到來源', '站內自述', '未納入', '證據不足', '其中.*可查證']

# 5. 事實不自辯（層級辨析/職性質註/屆次依據）
SELF_DEFENSE = ['非理事會', r'非.{0,4}成員', r'僅.{0,4}職銜', '屆次',
                '判斷依據', '自我辯解', '層級辨析']

SEV_LABEL = {'ERROR': '✗ 錯誤', 'WARN': '! 提醒'}


def scan_line(line, ln):
    """回傳該行的所有發現：(cat, sev, ln, snippet, suggestion)"""
    out = []
    # 1 BRAND
    for m in BRAND_BAD.finditer(line):
        out.append(('BRAND', 'ERROR', ln, line.strip(),
                    '品牌字應為「%s遊」（辶），非「%s游」（氵）' % (m.group(1), m.group(1))))
    # 2 FESTIVAL
    for f in FESTIVALS:
        if f in line:
            out.append(('FESTIVAL', 'WARN', ln, line.strip(),
                        '確認「%s」當年農曆對應公曆日期，不確定請改中性描述' % f))
    # 3 CANTONESE
    for c in CANTONESE:
        if c in line:
            out.append(('CANTONESE', 'WARN', ln, line.strip(),
                        '標準書面語禁用粵語助詞「%s」；在地文化詞請保留＋旁補普通話' % c))
    # 4 LEAK
    for w in LEAK_WORDS:
        if re.search(w, line):
            out.append(('LEAK', 'WARN', ln, line.strip(),
                        '公開頁不應出現此詞，請用「對誰說」判準覆核'))
    # 5 SELFDEF
    for pat in SELF_DEFENSE:
        if re.search(pat, line):
            out.append(('SELFDEF', 'WARN', ln, line.strip(),
                        '事實聲明不需辯護；職稱只寫事實本身'))
    return out


def lint_file(path, fix):
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            lines = fh.readlines()
    except Exception as e:
        return None, ['讀檔失敗：%s' % e]

    findings = []
    changed = False
    brand_fixed = 0
    new_lines = []
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip('\n')
        brand_hits = list(BRAND_BAD.finditer(line))
        scan_target = line
        if fix and brand_hits:
            line = BRAND_BAD.sub(BRAND_FIX, line)
            changed = True
            brand_fixed += len(brand_hits)
            scan_target = line  # 修復後再掃，BRAND 不再計錯
        findings.extend(scan_line(scan_target, i))
        new_lines.append(line + '\n' if raw.endswith('\n') else line)

    if fix and changed:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.writelines(new_lines)
    if fix and brand_fixed:
        return findings, ['（已自動修復 %d 處品牌字）' % brand_fixed]
    return findings, []


def main():
    ap = argparse.ArgumentParser(description='發布前內容檢查清單')
    ap.add_argument('target', help='檔案或目錄')
    ap.add_argument('--fix', action='store_true', help='自動修復品牌字')
    ap.add_argument('--strict', action='store_true', help='WARN 也視為不通過')
    ap.add_argument('--ext', default='md,html,txt', help='目錄模式副檔名過濾')
    args = ap.parse_args()

    exts = ['.' + e.strip().lstrip('.') for e in args.ext.split(',')]

    files = []
    if os.path.isdir(args.target):
        for root, _, names in os.walk(args.target):
            for nm in names:
                if any(nm.endswith(e) for e in exts):
                    files.append(os.path.join(root, nm))
    else:
        files = [args.target]

    total_err = 0
    total_warn = 0
    for fp in files:
        findings, notes = lint_file(fp, args.fix)
        if findings is None:
            print('• %s' % fp)
            for n in notes:
                print('    %s' % n)
            continue
        if not findings and not notes:
            continue
        print('• %s' % fp)
        for n in notes:
            print('    %s' % n)
        for cat, sev, ln, snippet, sug in findings:
            if sev == 'ERROR':
                total_err += 1
            else:
                total_warn += 1
            print('    [%s] %s L%d: %s' % (SEV_LABEL[sev], cat, ln, snippet[:60]))
            print('         → %s' % sug)

    print('\n=== 總結：ERROR %d / WARN %d（檔案 %d）===' % (total_err, total_warn, len(files)))
    if total_err or (args.strict and total_warn):
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
