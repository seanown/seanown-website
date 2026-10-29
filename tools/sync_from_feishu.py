#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_from_feishu.py — 飛書多維表格 → seanown.org 文章同步腳本

設計原則（非常重要）：
  飛書表格只存放「可編輯的 11 個欄位」（title/date/category/series/slug/
  location/lead/body/images/status/num）。而 posts.json 裡還有 movieInfo、
  filmYear、subtitle、raw_html、no_focus… 等「非飛書欄位」，這些是澳門電影
  專輯的關鍵資料（89 篇有 movieInfo）。

  所以本腳本「合併」而非「覆寫」：
    1. 讀取現有 data/posts.json（保留所有非飛書欄位）。
    2. 抓取飛書表格全部紀錄，對每篇現有文章用 num（其次 slug）比對：
         - 比對到 → 用飛書的 11 欄覆寫該篇（其餘欄位原樣保留）。
         - 比對不到且為新 num/slug → 視為「飛書新增文章」，附加到結尾。
    3. 現有文章若其 num 與 slug 都不在飛書表格中 → 視為「飛書已刪除」，
       從 posts.json 移除（達成「飛書刪列即網站刪文」）。
    4. 寫回 data/posts.json（先備份），不改動其它欄位。

用法：
  python tools/sync_from_feishu.py            # 真正同步並寫入 posts.json
  python tools/sync_from_feishu.py --dry-run  # 只報告異動，不寫入（安全預覽）
  python tools/sync_from_feishu.py --build    # 同步後順便重跑 build_articles.py
  python tools/sync_from_feishu.py --build --push
        # 同步 → 重建文章頁 → git add/commit/push（一鍵上線，Netlify 自動部署）
        # 注意：push 只納入 data/ article/ articles/ tools/sync_from_feishu.py
        #       與 .gitignore，絕不會送出 tools/.feishu_secret.json（已 gitignore）。

憑證來源（二擇一，皆不寫入版控）：
  A. 環境變數 FEISHU_APP_ID / FEISHU_APP_SECRET
  B. 本機檔 tools/.feishu_secret.json = {"app_id":"...","app_secret":"..."}
     （該檔已列入 .gitignore，請勿手動提交）
"""

import os
import sys
import json
import ast
import time
import datetime
import subprocess
import urllib.request

# ---------- 設定（非機密，僅表格識別碼）----------
APP_TOKEN = "XpwfbyCtFacq03suX6zcOZelnaf"   # 飛書多維表格 app_token
TABLE_ID = "tblTeUu5Hducz0m2"               # 主用表 table_id
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_JSON = os.path.join(ROOT, "data", "posts.json")
BUILD_SCRIPT = os.path.join(ROOT, "tools", "build_articles.py")
SECRET_FILE = os.path.join(ROOT, "tools", ".feishu_secret.json")


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
    print("[錯誤] 找不到飛書憑證：請設定環境變數 FEISHU_APP_ID / FEISHU_APP_SECRET，"
          "或在 tools/.feishu_secret.json 放入 app_id/app_secret。")
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
    """分頁抓取表格全部紀錄（每頁最多 100 筆）。"""
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


def ts_to_date(v):
    """飛書日期欄是 Unix 秒戳（UTC），轉回 YYYY-MM-DD 字串。"""
    if isinstance(v, (int, float)):
        return datetime.datetime.fromtimestamp(int(v), datetime.timezone.utc).strftime("%Y-%m-%d")
    if isinstance(v, str) and v.strip():
        s = v.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except Exception:
                pass
        try:
            return datetime.datetime.utcfromtimestamp(int(s)).strftime("%Y-%m-%d")
        except Exception:
            pass
    return ""


def parse_images(v):
    """飛書 images 欄存成 Python 列表字串，例如 "['a.jpg','b.jpg']"。"""
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    if not s:
        return []
    try:
        val = ast.literal_eval(s)
        if isinstance(val, (list, tuple)):
            return [str(x).strip() for x in val if str(x).strip()]
    except Exception:
        pass
    parts = [p.strip().strip("'\"") for p in s.replace("\n", ",").split(",")]
    return [p for p in parts if p]


def norm_num(v):
    """num 標準化：純數字補零至至少 2 位，便於與現有 posts.json 比對。"""
    s = str(v or "").strip()
    if s.isdigit():
        return s.zfill(max(2, len(s)))
    return s


def norm_key(post):
    """比對鍵：回傳 (num_int_or_None, slug)。"""
    n = norm_num(post.get("num"))
    num_int = int(n) if n.isdigit() else None
    slug = (post.get("slug") or "").strip()
    return num_int, slug


def merge_fields(base, f):
    """把飛書欄位 f 合併到 base（原地修改 base），回傳有變動的欄位清單。"""
    changed = []
    mapping = [
        ("title", "title", str, lambda x: x.strip()),
        ("slug", "slug", str, lambda x: x.strip()),
        ("series", "series", str, lambda x: x.strip()),
        ("category", "category", str, lambda x: x.strip()),
        ("location", "location", str, lambda x: x.strip()),
        ("status", "status", str, lambda x: x.strip()),
        ("lead", "lead", str, lambda x: x.strip()),
        ("body", "body", str, lambda x: x),
    ]
    for fk, pk, cast, proc in mapping:
        if fk in f and base.get(pk) != proc(cast(f[fk])):
            base[pk] = proc(cast(f[fk]))
            changed.append(pk)
    # date
    if "date" in f:
        nd = ts_to_date(f["date"])
        if base.get("date") != nd:
            base["date"] = nd
            changed.append("date")
    # images
    if "images" in f:
        ni = parse_images(f["images"])
        if base.get("images") != ni:
            base["images"] = ni
            changed.append("images")
    # num
    if "num" in f:
        fn = norm_num(f["num"])
        if norm_num(base.get("num")) != fn:
            base["num"] = fn
            changed.append("num")
    return changed


def make_new_post(f):
    """飛書新增文章：只有 11 個可編輯欄，其餘留預設。"""
    p = {}
    p["num"] = norm_num(f.get("num"))
    p["title"] = str(f.get("title", "")).strip()
    p["subtitle"] = None
    p["slug"] = str(f.get("slug", "")).strip()
    p["series"] = str(f.get("series", "")).strip()
    p["category"] = str(f.get("category", "")).strip()
    p["date"] = ts_to_date(f.get("date"))
    p["location"] = str(f.get("location", "")).strip()
    p["status"] = str(f.get("status", "")).strip()
    p["images"] = parse_images(f.get("images"))
    p["lead"] = str(f.get("lead", "")).strip()
    p["body"] = str(f.get("body", ""))
    return p


def main():
    dry_run = "--dry-run" in sys.argv
    do_build = "--build" in sys.argv
    do_push = "--push" in sys.argv

    app_id, app_secret = load_creds()
    token = get_tenant_token(app_id, app_secret)
    records = list_all_records(token)
    print("[資訊] 飛書表格共抓到 %d 筆紀錄。" % len(records))

    if not os.path.exists(POSTS_JSON):
        print("[錯誤] 找不到 %s" % POSTS_JSON)
        sys.exit(1)
    with open(POSTS_JSON, encoding="utf-8") as fh:
        data = json.load(fh)
    existing = data.get("posts", [])
    print("[資訊] 現有 posts.json 共 %d 篇。" % len(existing))

    # 整理飛書紀錄為索引結構
    feishu = []
    for rec in records:
        f = rec.get("fields", {})
        fnum = norm_num(f.get("num"))
        fnum_int = int(fnum) if fnum.isdigit() else None
        fslug = (f.get("slug") or "").strip()
        feishu.append({"f": f, "num_int": fnum_int, "slug": fslug, "consumed": False})
    by_num = {}
    by_slug = {}
    for i, fr in enumerate(feishu):
        if fr["num_int"] is not None:
            by_num.setdefault(fr["num_int"], i)
        if fr["slug"]:
            by_slug.setdefault(fr["slug"], i)
    feishu_num_set = {fr["num_int"] for fr in feishu if fr["num_int"] is not None}
    feishu_slug_set = {fr["slug"] for fr in feishu if fr["slug"]}

    final = []
    adds, updates, deletes = [], [], []

    # 第一輪：依現有順序處理，比對飛書
    for p in existing:
        ni, sl = norm_key(p)
        in_feishu = (ni in feishu_num_set) or (sl in feishu_slug_set)
        if not in_feishu:
            deletes.append(p.get("slug") or p.get("num"))
            continue
        idx = None
        if ni is not None and ni in by_num:
            idx = by_num[ni]
        elif sl and sl in by_slug:
            idx = by_slug[sl]
        if idx is None or feishu[idx]["consumed"]:
            # 理論上不會發生；保險起見原樣保留
            final.append(p)
            continue
        fr = feishu[idx]
        changed = merge_fields(p, fr["f"])
        if changed:
            updates.append((p.get("slug") or p.get("num"), changed))
        final.append(p)
        fr["consumed"] = True

    # 第二輪：未被 consume 的飛書紀錄 = 新增文章
    for fr in feishu:
        if not fr["consumed"]:
            np = make_new_post(fr["f"])
            final.append(np)
            adds.append(np.get("slug") or np.get("num"))

    data["posts"] = final

    # 報表
    print("\n===== 同步預覽 =====")
    print("現有篇數：%d → 輸出篇數：%d" % (len(existing), len(final)))
    print("新增（飛書有、posts.json 無）：%d 篇" % len(adds))
    for a in adds:
        print("  + %s" % a)
    print("刪除（飛書已移除）：%d 篇" % len(deletes))
    for d in deletes:
        print("  - %s" % d)
    print("內容更新（飛書欄位變動）：%d 篇" % len(updates))
    for u, ch in updates[:20]:
        print("  ~ %s : %s" % (u, ",".join(ch)))
    if len(updates) > 20:
        print("  …（其餘 %d 篇略）" % (len(updates) - 20))

    # 保全檢查
    mi = sum(1 for x in final if x.get("movieInfo"))
    fy = sum(1 for x in final if x.get("filmYear"))
    print("\n[保全] 含 movieInfo：%d 篇 / 含 filmYear：%d 篇" % (mi, fy))

    if dry_run:
        print("\n[乾跑] 未寫入任何檔案。確認無誤後去掉 --dry-run 再執行。")
        return

    # 備份 + 寫入
    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = os.path.join(ROOT, "data", "posts.json.bak_%s" % ts)
    with open(bak, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print("\n[備份] 舊檔已備份至 %s" % bak)

    with open(POSTS_JSON, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print("[寫入] 已更新 %s（%d 篇）" % (POSTS_JSON, len(final)))

    if do_build:
        print("[建置] 執行 build_articles.py …")
        subprocess.run([sys.executable, BUILD_SCRIPT], check=True)
        print("[建置] 完成。")

    if do_push:
        print("[推送] git add / commit / push …")
        subprocess.run(
            ["git", "add", "-A", "data/", "article/", "articles/",
             "tools/sync_from_feishu.py", ".gitignore"], check=True)
        msg = ("sync: 飛書 CMS 同步 %d 篇（新增 %d / 刪除 %d / 更新 %d）"
               % (len(final), len(adds), len(deletes), len(updates)))
        subprocess.run(["git", "commit", "-m", msg], check=True)
        subprocess.run(["git", "push", "origin", "HEAD"], check=True)
        print("[推送] 完成，Netlify 將自動部署。")


if __name__ == "__main__":
    main()
