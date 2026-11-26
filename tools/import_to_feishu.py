#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_to_feishu.py — 本機 posts.json → 飛書多維表格（補登錄／回填）

用途：
  2026-10-30～10-31 新增的 11 篇澳門電影專輯文章（num 144–154）當初只寫進
  本機 data/posts.json 並上線，未登錄到飛書後台。造成「飛書 126 筆 / 本機 137 篇」
  的落差 —— 任何人從飛書按一鍵發佈，腳本會判定這 11 篇「飛書已移除」而刪除，
  DELETE_GUARD=3 擋下 → 整批中止。

  本腳本把「本機有、飛書沒有」的文章補登錄到飛書，讓兩邊對齊。
  只新增、不修改、不刪除飛書既有紀錄。

安全機制：
  - 預設 --dry-run，只報告將補哪幾篇，不寫入。
  - --apply 才實際寫入飛書。
  - 遇到「飛書已有同 num 或同 slug」的，一律跳過不覆寫。
  - 圖片走文字 images 欄（與現有 126 筆同格式），不上傳附件，
    故不會動到 assets/images/posts/，也不會覆蓋既有圖檔。
  - 憑證絕不進版控（讀 tools/.feishu_secret.json，該檔已 gitignore）。

用法：
  python tools/import_to_feishu.py            # 乾跑，列出將補登錄的篇目
  python tools/import_to_feishu.py --apply    # 實際寫入飛書
"""

import os
import sys
import json
import datetime
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_JSON = os.path.join(ROOT, "data", "posts.json")
SECRET_FILE = os.path.join(ROOT, "tools", ".feishu_secret.json")

APP_TOKEN = "XpwfbyCtFacq03suX6zcOZelnaf"
TABLE_ID = "tblTeUu5Hducz0m2"

# 飛書表格欄位（只登錄這些，其餘如 movieInfo/filmYear/subtitle 留在本機，
# 由 sync_from_feishu.py 的「合併式」機制保全）
TEXT_FIELDS = ["title", "category", "series", "slug", "location",
               "lead", "body", "images", "status"]


def load_creds():
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    if app_id and app_secret:
        return app_id, app_secret
    if os.path.exists(SECRET_FILE):
        try:
            d = json.load(open(SECRET_FILE, encoding="utf-8"))
            return d.get("app_id", ""), d.get("app_secret", "")
        except Exception as e:
            print("[警告] 讀取 %s 失敗：%s" % (SECRET_FILE, e))
    print("[錯誤] 找不到飛書憑證。")
    sys.exit(1)


def feishu_post(url, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer %s" % token
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def feishu_get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer %s" % token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_tenant_token(app_id, app_secret):
    r = feishu_post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        {"app_id": app_id, "app_secret": app_secret})
    if r.get("code") != 0:
        print("[錯誤] 取得 tenant_access_token 失敗：%s" % r)
        sys.exit(1)
    return r["tenant_access_token"]


def list_all_records(token):
    out = []
    page_token = ""
    while True:
        url = ("https://open.feishu.cn/open-apis/bitable/v1/apps/%s/tables/%s/records"
               "?page_size=100" % (APP_TOKEN, TABLE_ID))
        if page_token:
            url += "&page_token=%s" % page_token
        r = feishu_get(url, token)
        if r.get("code") != 0:
            print("[錯誤] 讀取表格失敗：%s" % r)
            sys.exit(1)
        out.extend(r["data"]["items"])
        if r["data"].get("has_more") and r["data"].get("page_token"):
            page_token = r["data"]["page_token"]
        else:
            break
    return out


def date_to_ts(s):
    """YYYY-MM-DD → UTC 午夜 Unix 秒戳（與 sync_from_feishu.py 的 ts_to_date 互逆）。"""
    if not s:
        return None
    try:
        d = datetime.datetime.strptime(str(s).strip()[:10], "%Y-%m-%d")
        return int(d.replace(tzinfo=datetime.timezone.utc).timestamp())
    except Exception:
        return None


def norm_num(v):
    s = str(v or "").strip()
    if s.isdigit():
        return s.zfill(max(2, len(s)))
    return s


def build_fields(post):
    """把本機一篇 post 轉成飛書欄位 dict。"""
    f = {}
    for k in TEXT_FIELDS:
        v = post.get(k)
        if k == "images":
            # 現有 126 筆的 images 欄是 Python 列表字串，格式必須一致
            f[k] = str(v if v is not None else [])
        else:
            f[k] = "" if v is None else str(v)
    ts = date_to_ts(post.get("date"))
    if ts is not None:
        f["date"] = ts
    n = norm_num(post.get("num"))
    if n.isdigit():
        f["num"] = int(n)
    return f


def main():
    apply = "--apply" in sys.argv

    app_id, app_secret = load_creds()
    token = get_tenant_token(app_id, app_secret)

    data = json.load(open(POSTS_JSON, encoding="utf-8"))
    posts = data["posts"] if isinstance(data, dict) else data

    records = list_all_records(token)
    feishu_nums = set()
    feishu_slugs = set()
    for it in records:
        fl = it.get("fields") or {}
        n = fl.get("num")
        if n is not None:
            feishu_nums.add(str(int(n)))
        s = fl.get("slug")
        if s:
            feishu_slugs.add(str(s).strip())

    print("[資訊] 飛書現有紀錄：%d 筆" % len(records))
    print("[資訊] 本機 posts.json：%d 篇" % len(posts))
    print()

    todo = []
    for p in posts:
        n = norm_num(p.get("num"))
        s = str(p.get("slug") or "").strip()
        if n in feishu_nums or s in feishu_slugs:
            continue
        todo.append(p)

    if not todo:
        print("[結果] 兩邊已完全對齊，沒有需要補登錄的文章。")
        return

    print("===== 將補登錄到飛書的文章（%d 篇）=====" % len(todo))
    for p in todo:
        print("  num=%s | %s | %s | slug=%s"
              % (norm_num(p.get("num")), p.get("title"),
                 p.get("date"), p.get("slug")))

    if not apply:
        print()
        print("[乾跑] 未寫入任何資料。確認無誤後加上 --apply 再執行。")
        return

    print()
    ok = 0
    fail = 0
    for p in todo:
        f = build_fields(p)
        url = ("https://open.feishu.cn/open-apis/bitable/v1/apps/%s/tables/%s/records"
               % (APP_TOKEN, TABLE_ID))
        r = feishu_post(url, {"fields": f}, token)
        if r.get("code") == 0:
            ok += 1
            print("  [成功] num=%s | %s" % (norm_num(p.get("num")), p.get("title")))
        else:
            fail += 1
            print("  [失敗] num=%s | %s | %s"
                  % (norm_num(p.get("num")), p.get("title"), r.get("msg")))
        # 避免瞬間打太猛觸發飛書限流
        import time
        time.sleep(0.3)

    print()
    print("[結果] 補登錄完成：成功 %d 篇，失敗 %d 篇。" % (ok, fail))
    print("[下一步] 執行 python tools/sync_from_feishu.py --dry-run 確認兩邊對齊。")


if __name__ == "__main__":
    main()
