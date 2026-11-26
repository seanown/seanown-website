#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pre_publish_lint.py — 發布前內容預檢（品牌字卡關）
被 sync_from_feishu.py 在 build 之後、git commit/push 之前呼叫。

掃描目標（來源 + 成品雙重把關）：
  1. data/posts.json        文章本體來源（品牌字錯誤改這裡才根治）
  2. article/                build 生成的文章頁 HTML（最終成品把關）
  3. 根目錄 *.html           首頁 / 關於 / 輯集 / 路線等靜態頁
  4. drafts/                 若存在，未發布草稿
  5. tools/ 下 *.md          飛書同步前的草稿本體（_body_*.md / _draft_*.md）

規則：直接複用 content_lint.py。
  - BRAND 類（龍游→龍遊）為 ERROR → 整體回傳 1（擋下發布）
  - 其餘 WARN 類（節慶/粵語/洩漏詞/自辯）只列印提醒，不擋
    （留給人工依『對誰說』判準覆核）
  - 預檢工具本身無法執行 → 回傳 2（fail-closed，安全起見擋下）

退出碼：0 淨空 / 1 有 BRAND 錯誤 / 2 工具異常
"""

import os
import sys
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINT = os.path.join(ROOT, "tools", "content_lint.py")
POSTS_JSON = os.path.join(ROOT, "data", "posts.json")


def collect_targets():
    ts = []
    # 1. 文章本體來源
    if os.path.isfile(POSTS_JSON):
        ts.append(POSTS_JSON)
    # 2. 生成文章頁目錄（遞迴掃 index.html）
    art = os.path.join(ROOT, "article")
    if os.path.isdir(art):
        ts.append(art)
    # 3. 根目錄靜態 .html（非遞迴，避免與 article/ 重複）
    for nm in sorted(os.listdir(ROOT)):
        fp = os.path.join(ROOT, nm)
        if nm.endswith(".html") and os.path.isfile(fp):
            ts.append(fp)
    # 4. drafts/（若存在，未發布草稿）
    dr = os.path.join(ROOT, "drafts")
    if os.path.isdir(dr):
        ts.append(dr)
    # 5. tools/ 下草稿本體 .md（非遞迴）
    tools_dir = os.path.join(ROOT, "tools")
    if os.path.isdir(tools_dir):
        for nm in sorted(os.listdir(tools_dir)):
            if nm.endswith(".md"):
                ts.append(os.path.join(tools_dir, nm))
    return ts


def main():
    if not os.path.isfile(LINT):
        print("[預檢] 找不到 content_lint.py，無法執行預檢。")
        sys.exit(2)

    targets = collect_targets()
    print("[預檢] 掃描目標：")
    for t in targets:
        print("    • %s" % t)

    rc = 0
    for t in targets:
        try:
            r = subprocess.run([sys.executable, LINT, t],
                               capture_output=False)
        except Exception as e:  # 工具本身跑不起來 → fail-closed
            print("[預檢] content_lint 執行異常：%s" % e)
            sys.exit(2)
        if r.returncode == 1:
            rc = 1
        elif r.returncode not in (0, 1):
            rc = 2

    if rc == 0:
        print("[預檢] 品牌字檢查通過，無 BRAND 錯誤。")
    elif rc == 1:
        print("[預檢] 發現 BRAND 品牌字錯誤，將擋下發布。")
    else:
        print("[預檢] 預檢工具異常，基於安全擋下發布。")
    sys.exit(rc)


if __name__ == "__main__":
    main()
