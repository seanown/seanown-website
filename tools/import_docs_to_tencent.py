#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_docs_to_tencent.py — 本機文檔 → 騰訊文檔（空間節點）批量匯入

流程（每個檔案）：
  1. manage.pre_import   → 取 upload_url / file_key / task_id
  2. curl PUT 檔案到 upload_url
  3. manage.async_import → 觸發匯入
  4. manage.import_progress 輪詢 → progress=100 得 file_id

空間結構：
  个人空间 (BzBrHfIeacOt)
    └─ 02文件（WorkBuddy 文档镜像）  ← 頂層資料夾
         └─ 6 組文檔各一個子資料夾

用法：
  python import_docs_to_tencent.py --dry-run    # 只列清單，不上傳
  python import_docs_to_tencent.py --apply      # 實際匯入
"""

import os
import sys
import json
import time
import hashlib
import subprocess

SKILL_DIR = r"C:\Users\user\.workbuddy\plugins\cache\workbuddy-builtin\tencent-docs-plugin\5.9.3-wb.42398134.gd4692421.h480e8d1fee0f\skills\tencent-docs"
TDOC = os.path.join(SKILL_DIR, "tencentdocs.py")
SRC_ROOT = r"C:\Users\user\WorkBuddy\02_文件\工作區\_TRASH_C_保留區"
SPACE_ID = "BzBrHfIeacOt"
ROOT_NODE_ID = "BOFPjDynwDzG"   # 02文件（WorkBuddy 文档镜像）

# 6 組文檔：資料夾名 → 顯示名稱
GROUPS = [
    ("2026-09-07-23-16-12", "澳門財政文章"),
    ("2026-09-09-22-38-08", "軒哥AI學習檔"),
    ("2026-09-10-01-15-41", "seanown-ip-deck"),
    ("2026-11-03-18-03-11", "macaotube QR"),
    ("2026-09-04-01-51-06", "lys"),
    ("2026-09-04-01-54-46", "lys 網站副本"),
]

# 跳過的目錄（暫存物／依賴／版本控制）
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".workbuddy",
             ".tmp", ".venv", "venv", ".idea", ".vscode"}
SKIP_EXT = (".pyc", ".pyo", ".log", ".tmp", ".DS_Store")

# 單檔大小上限（bytes）——超過就跳過並報告，避免大檔卡住
# 騰訊文檔實測：58MB 的 al_2023_accounts.pdf 會被服務端拒收
# （code 320125 drivecgi Service Error），且會卡住整批匯入。
# 超過此值的檔案改由「先 zip 再傳」或留待其他雲端（百度網盤已有完整副本）。
MAX_SIZE = 20 * 1024 * 1024


def tdoc(service, tool, args, timeout=60):
    """呼叫騰訊文檔 MCP 工具，回傳 structuredContent。"""
    cmd = ["python", TDOC, "tdoc_call", service, tool, json.dumps(args, ensure_ascii=False)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    out = r.stdout.strip()
    if not out:
        raise RuntimeError("無回應：%s | %s" % (r.stderr[:200], r.returncode))
    d = json.loads(out)
    if "error" in d and d.get("error"):
        raise RuntimeError(json.dumps(d["error"], ensure_ascii=False)[:300])
    res = d.get("result", {})
    if res.get("isError"):
        raise RuntimeError("工具回報錯誤：" + json.dumps(res, ensure_ascii=False)[:300])
    sc = res.get("structuredContent")
    if isinstance(sc, dict):
        return sc
    txt = ""
    for c in res.get("content", []):
        if c.get("type") == "text":
            txt = c.get("text", "")
            break
    try:
        return json.loads(txt)
    except Exception:
        return {"_raw": txt}


def create_folder(title, parent_node_id):
    args = {
        "title": title,
        "node_type": "wiki_folder",
        "space_id": SPACE_ID,
        "wiki_folder_node": {"title": title},
    }
    if parent_node_id:
        args["parent_node_id"] = parent_node_id
    r = tdoc("tencent-docs", "create_space_node", args)
    return r["node_info"]["node_id"]


def collect_files(group_dir):
    """收集一個群組內要匯入的檔案（相對路徑 + 絕對路徑 + 大小）。"""
    out = []
    for root, dirs, files in os.walk(group_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.startswith("._") or fn.endswith(SKIP_EXT):
                continue
            ap = os.path.join(root, fn)
            try:
                sz = os.path.getsize(ap)
            except OSError:
                continue
            if sz == 0:
                continue
            out.append((os.path.relpath(ap, group_dir).replace("\\", "/"), ap, sz))
    return out


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def import_one(path, name):
    """匯入單一檔案，回傳 (file_id, file_url)。"""
    size = os.path.getsize(path)
    if size > MAX_SIZE:
        raise RuntimeError("檔案 %.1f MB 超過單檔上限 %.0f MB，跳過"
                           % (size / 1024 / 1024, MAX_SIZE / 1024 / 1024))
    md5 = md5_of(path)

    pre = tdoc("tencent-docs", "manage.pre_import", {
        "file_name": name, "file_size": size, "file_md5": md5})
    upload_url = pre.get("upload_url") or pre.get("uploadUrl")
    file_key = pre.get("file_key")
    task_id = pre.get("task_id")
    if not upload_url or not file_key or not task_id:
        raise RuntimeError("pre_import 回應缺欄位：%s" % json.dumps(pre, ensure_ascii=False)[:300])

    # PUT 上傳（簽名含 content-length，必須明確帶上，否則 COS 拒簽）
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
           "-X", "PUT", "-H", "Content-Length: %d" % size,
           "--upload-file", path, upload_url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    code = (r.stdout or "").strip()
    if code not in ("200", "201", "204"):
        raise RuntimeError("上傳失敗 HTTP %s" % code)

    tdoc("tencent-docs", "manage.async_import", {
        "file_key": file_key, "file_name": name,
        "file_md5": md5, "file_size": size, "task_id": task_id})

    # 輪詢（首次 2 秒後即查，多數檔案 5 秒內完成；最多 40 次 = 約 100 秒）
    for i in range(40):
        if i == 0:
            time.sleep(2)
        else:
            time.sleep(3)
        p = tdoc("tencent-docs", "manage.import_progress", {"task_id": task_id})
        prog = p.get("progress", 0)
        if prog == 100 or p.get("file_id"):
            return p.get("file_id"), p.get("file_url")
    raise RuntimeError("匯入逾時未完成（progress 未達 100）")


def list_children(folder_id):
    """列出資料夾下的直接子項（回傳 [{id,title,type}]）。"""
    try:
        r = tdoc("tencent-docs", "manage.folder_list",
                 {"folder_id": folder_id, "max_depth": 1, "limit": 200})
        items = r.get("list") or r.get("items") or []
        out = []
        for it in items:
            out.append({
                "id": it.get("id") or it.get("node_id") or it.get("folder_id") or it.get("file_id"),
                "title": it.get("title") or it.get("name") or "",
                "type": it.get("type") or it.get("node_type") or "",
            })
        return out
    except Exception:
        return []


def ensure_folder(title, parent_node_id):
    """取得（或建立）指定名稱的子資料夾，回傳 node_id。"""
    for it in list_children(parent_node_id):
        if it["title"] == title:
            print("   [沿用] 資料夾已存在：%s（%s）" % (title, it["id"]), flush=True)
            return it["id"]
    return create_folder(title, parent_node_id)


def main():
    apply = "--apply" in sys.argv
    total_files = 0
    plan = []

    for dirname, label in GROUPS:
        gdir = os.path.join(SRC_ROOT, dirname)
        if not os.path.isdir(gdir):
            print("[略過] 找不到 %s" % gdir)
            continue
        files = collect_files(gdir)
        plan.append((dirname, label, files))
        total_files += len(files)

    print("===== 匯入計畫 =====")
    for dirname, label, files in plan:
        tot = sum(f[2] for f in files)
        print("\n■ %s  (%s)  — %d 檔, %.1f MB"
              % (label, dirname, len(files), tot / 1024 / 1024))
        for rel, ap, sz in files[:60]:
            print("    %-52s %8.1f KB" % (rel[:52], sz / 1024))
        if len(files) > 60:
            print("    ...（另 %d 檔）" % (len(files) - 60))
    print("\n合計：%d 個檔案" % total_files)

    if not apply:
        print("\n[乾跑] 未上傳任何檔案。確認後加 --apply 執行。")
        return

    # 大檔優先：避免單一大檔卡在最後拖長整批時間
    for dirname, label, files in plan:
        files.sort(key=lambda x: -x[2])

    print("\n===== 開始匯入 =====", flush=True)
    ok = 0
    fail = 0
    created_folders = 0

    for dirname, label, files in plan:
        try:
            fid = ensure_folder(label, ROOT_NODE_ID)
            created_folders += 1
            print("\n■ 資料夾：%s（%s）" % (label, fid), flush=True)
        except Exception as e:
            print("\n■ 建立資料夾失敗：%s → %s" % (label, e), flush=True)
            fail += len(files)
            continue

        existing = {it["title"] for it in list_children(fid)}
        for rel, ap, sz in files:
            name = "%s__%s" % (dirname, rel.replace("/", "_"))
            if name in existing:
                print("   [略過] 已存在：%s" % rel[:50], flush=True)
                continue
            try:
                file_id, url = import_one(ap, name)
                ok += 1
                existing.add(name)
                print("   [成功] %-50s → %s" % (rel[:50], file_id), flush=True)
            except Exception as e:
                fail += 1
                print("   [失敗] %-50s → %s" % (rel[:50], e), flush=True)

    print("\n===== 匯入完成 =====")
    print("成功 %d 檔，失敗 %d 檔，新建資料夾 %d 個" % (ok, fail, created_folders))
    print("空間連結：https://docs.qq.com/space/DQnpCckhmSWVhY090")


if __name__ == "__main__":
    main()
