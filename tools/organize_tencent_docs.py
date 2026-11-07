#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
organize_tencent_docs.py — 把首頁根目錄的匯入檔案搬進對應群組資料夾

背景（2026-11-07 實測）：
  `manage.async_import` 一律把檔案匯入到**首頁根目錄**，與 `create_space_node`
  建立的空間節點無關。要分組必須再用 `manage.move_file`（target_folder_id）
  搬進實體資料夾。

  檔名格式：`<群組日期目錄>__<相對路徑>`（斜線已換成底線），
  例如 `2026-09-07-23-16-12__tmp_macau_i21_p024.png` → 群組「澳門財政文章」。

用法：
  python organize_tencent_docs.py --dry-run   # 只列計畫
  python organize_tencent_docs.py --apply     # 實際搬移
"""

import os
import sys
import json

SKILL_DIR = r"C:\Users\user\.workbuddy\plugins\cache\workbuddy-builtin\tencent-docs-plugin\5.9.3-wb.42398134.gd4692421.h480e8d1fee0f\skills\tencent-docs"
sys.path.insert(0, r"C:\Users\user\WorkBuddy\02_文件\工作區\_TRASH_C_保留區")
from import_docs_to_tencent import tdoc  # noqa: E402

ROOT_FOLDER_TITLE = "02文件（WorkBuddy 文档镜像）"

# 群組日期目錄 → 顯示名稱（與匯入腳本的 GROUPS 對應）
GROUPS = {
    "2026-09-07-23-16-12": "澳門財政文章",
    "2026-09-09-22-38-08": "軒哥AI學習檔",
    "2026-09-10-01-15-41": "seanown-ip-deck",
    "2026-11-03-18-03-11": "macaotube QR",
    "2026-09-04-01-51-06": "lys",
    "2026-09-04-01-54-46": "lys 網站副本",
}


def list_root():
    """列出首頁根目錄全部項目（分頁）。"""
    out = []
    start = 0
    while True:
        r = tdoc("tencent-docs", "manage.folder_list", {"start": start, "limit": 100})
        lst = r.get("list") or []
        if not lst:
            break
        out.extend(lst)
        start += len(lst)
        if start >= 1000:
            break
    return out


def main():
    apply = "--apply" in sys.argv

    root_items = list_root()
    folders = {it["title"]: it["id"] for it in root_items if it.get("is_folder")}
    files = [it for it in root_items if not it.get("is_folder")]

    print("[資訊] 首頁根目錄：%d 個資料夾、%d 個檔案" % (len(folders), len(files)))

    mirror_id = folders.get(ROOT_FOLDER_TITLE)
    if not mirror_id:
        print("[錯誤] 找不到鏡像資料夾：%s" % ROOT_FOLDER_TITLE)
        return

    # 鏡像資料夾下的子資料夾（群組）
    sub = tdoc("tencent-docs", "manage.folder_list",
               {"folder_id": mirror_id, "max_depth": 1, "limit": 100})
    group_ids = {it["title"]: it["id"] for it in (sub.get("list") or []) if it.get("is_folder")}
    print("[資訊] 群組資料夾：%s" % "、".join(group_ids.keys()))

    # 依檔名前綴分組
    buckets = {}
    unmapped = []
    for it in files:
        title = it.get("title", "")
        prefix = title.split("__")[0]
        if prefix in GROUPS and GROUPS[prefix] in group_ids:
            buckets.setdefault(GROUPS[prefix], []).append(it)
        else:
            unmapped.append(it)

    print()
    print("===== 分組結果 =====")
    for label in group_ids:
        n = len(buckets.get(label, []))
        print("  %-16s %d 檔" % (label, n))
    if unmapped:
        print("  （未對應到群組，留在原地：%d 個）" % len(unmapped))
        for it in unmapped[:10]:
            print("     ", it.get("title"))

    total = sum(len(v) for v in buckets.values())
    print("\n合計待搬移：%d 檔" % total)

    if not apply:
        print("\n[乾跑] 未搬移任何檔案。確認後加 --apply 執行。")
        return

    print("\n===== 開始搬移 =====", flush=True)
    ok = 0
    fail = 0
    for label, items in buckets.items():
        gid = group_ids[label]
        print("\n■ %s → %s" % (label, gid), flush=True)
        for it in items:
            fid = it.get("id")
            try:
                tdoc("tencent-docs", "manage.move_file",
                     {"file_id": fid, "target_folder_id": gid})
                ok += 1
            except Exception as e:
                fail += 1
                print("   [失敗] %-45s → %s" % (str(it.get("title"))[:45], str(e)[:120]),
                      flush=True)
        print("   已搬移 %d 檔" % len(items), flush=True)

    print("\n===== 搬移完成 =====")
    print("成功 %d 檔，失敗 %d 檔" % (ok, fail))
    print("空間連結：https://docs.qq.com/space/DQnpCckhmSWVhY090")


if __name__ == "__main__":
    main()
