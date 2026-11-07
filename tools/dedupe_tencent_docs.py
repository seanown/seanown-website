#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dedupe_tencent_docs.py — 清理騰訊文檔鏡像資料夾內的重複檔案

背景（2026-11-07 實測）：
  首次匯入時「已存在則略過」的判斷寫錯（比對的是空間節點 id，不是實體資料夾 id），
  導致第二次重跑把 94 個檔案重複匯入一次，共留下 95 個重複檔案。

  清理規則：同一群組資料夾內，同名檔案只保留 **建立時間最早** 的一份，
  其餘移入回收站。⚠️ 只動本次匯入的鏡像資料夾（02文件（WorkBuddy 文档镜像）），
  其餘首頁資料夾完全不碰。

用法：
  python dedupe_tencent_docs.py --dry-run   # 只列將刪哪些
  python dedupe_tencent_docs.py --apply     # 實際刪除
"""

import os
import sys
import json

sys.path.insert(0, r"C:\Users\user\WorkBuddy\02_文件\工作區\_TRASH_C_保留區")
from import_docs_to_tencent import tdoc  # noqa: E402

MIRROR_TITLE = "02文件（WorkBuddy 文档镜像）"


def list_folder(folder_id, cap=800):
    """分頁列出資料夾內容。"""
    out = []
    start = 0
    while True:
        r = tdoc("tencent-docs", "manage.folder_list",
                 {"folder_id": folder_id, "start": start, "limit": 100})
        lst = r.get("list") or []
        if not lst:
            break
        out.extend(lst)
        start += len(lst)
        if start >= cap:
            break
    return out


def list_root(cap=800):
    out = []
    start = 0
    while True:
        r = tdoc("tencent-docs", "manage.folder_list", {"start": start, "limit": 100})
        lst = r.get("list") or []
        if not lst:
            break
        out.extend(lst)
        start += len(lst)
        if start >= cap:
            break
    return out


def main():
    apply = "--apply" in sys.argv

    root = list_root()
    mirror = next((it for it in root if it.get("is_folder") and it.get("title") == MIRROR_TITLE),
                   None)
    if not mirror:
        print("[錯誤] 找不到鏡像資料夾")
        return
    mirror_id = mirror["id"]

    subs = [it for it in list_folder(mirror_id) if it.get("is_folder")]
    print("[資訊] 鏡像資料夾下 %d 個群組資料夾" % len(subs))

    plan = []
    for f in subs:
        items = list_folder(f["id"])
        # 以標題分組；同標題保留 modify_time 最小者（最早建立）
        by_title = {}
        for it in items:
            if it.get("is_folder"):
                continue
            by_title.setdefault(it.get("title"), []).append(it)
        for title, group in by_title.items():
            if len(group) < 2:
                continue
            group.sort(key=lambda x: (x.get("modify_time") or 0))
            keep = group[0]
            for extra in group[1:]:
                plan.append({
                    "folder": f["title"], "title": title,
                    "keep_id": keep.get("id"), "del_id": extra.get("id"),
                    "del_time": extra.get("modify_time"), "keep_time": keep.get("modify_time"),
                })

    print()
    print("===== 將移除的重複檔案：%d 個 =====" % len(plan))
    from collections import Counter
    c = Counter(p["folder"] for p in plan)
    for k, v in c.items():
        print("  %-16s %d 個" % (k, v))
    for p in plan[:5]:
        print("   例：%s／%s" % (p["folder"], p["title"]))

    if not plan:
        print("\n[結果] 沒有重複檔案，無需清理。")
        return

    if not apply:
        print("\n[乾跑] 未刪除任何檔案。確認後加 --apply 執行。")
        return

    print("\n===== 開始清理 =====", flush=True)
    ok = 0
    fail = 0
    for p in plan:
        try:
            tdoc("tencent-docs", "manage.delete_file",
                 {"file_id": p["del_id"], "delete_type": "origin"})
            ok += 1
        except Exception as e:
            fail += 1
            print("   [失敗] %s／%s → %s" % (p["folder"], p["title"], str(e)[:110]), flush=True)

    print("\n===== 清理完成 =====")
    print("已移入回收站 %d 個，失敗 %d 個（每組同名只保留最早建立的一份）" % (ok, fail))
    print("空間連結：https://docs.qq.com/space/DQnpCckhmSWVhY090")


if __name__ == "__main__":
    main()
