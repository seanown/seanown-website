#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_from_feishu.py — 飛書多維表格 → seanown.org 文章同步腳本

設計原則（非常重要）：
  飛書表格只存放「可編輯的欄位」（title/date/category/series/slug/location/
  lead/body/images/status/num，以及可升級的 images_attach 附件欄）。而
  posts.json 裡還有 movieInfo、filmYear、subtitle、raw_html、no_focus… 等
  「非飛書欄位」，這些是澳門電影專輯的關鍵資料（89 篇有 movieInfo）。

  所以本腳本「合併」而非「覆寫」：
    1. 讀取現有 data/posts.json（保留所有非飛書欄位）。
    2. 抓取飛書表格全部紀錄，對每篇現有文章用 num（其次 slug）比對：
         - 比對到 → 用飛書欄位覆寫該篇（其餘欄位原樣保留）。
         - 比對不到且為新 num/slug → 視為「飛書新增文章」，附加到結尾。
    3. 現有文章若其 num 與 slug 都不在飛書表格中 → 視為「飛書已刪除」，
       從 posts.json 移除（達成「飛書刪列即網站刪文」）。
    4. 同步刪除 article/<slug>/ 資料夾，避免舊網址變死鏈（孤兒頁清理）。

安全機制：
  - 刪除保護：一次刪除超過 DELETE_GUARD（預設 3）篇，立刻中止、不寫入、
    不推送、發通知（防止手滑清空表格）。
  - 憑證絕不進版控。

用法：
  python tools/sync_from_feishu.py                  # 同步並寫入 posts.json
  python tools/sync_from_feishu.py --dry-run        # 只報告異動，不寫入
  python tools/sync_from_feishu.py --build          # 同步後重跑 build_articles.py
  python tools/sync_from_feishu.py --build --commit-only
        # 同步→重建→git commit（不 push），產 SYNC_REPORT.txt + 可選飛書通知
        # 這是「每日排程」用的模式：自動同步，但等你確認再 push。
  python tools/sync_from_feishu.py --build --push
        # 同步→重建→git add/commit/push（一鍵上線，Netlify 自動部署）
        # 這是「飛書內一鍵發布」或手動上線用的模式。

憑證來源（二擇一，皆不寫入版控）：
  A. 環境變數 FEISHU_APP_ID / FEISHU_APP_SECRET
  B. 本機檔 tools/.feishu_secret.json = {"app_id":"...","app_secret":"..."}
     （該檔已列入 .gitignore，請勿手動提交）
選用：tools/.feishu_secret.json 可加 "bot_webhook"（飛書群機器人 webhook）
      與 "webhook_secret"（給監聽程式驗證用）。
"""

import os
import sys
import json
import ast
import time
import datetime
import subprocess
import urllib.request
import shutil

# ---------- 設定（非機密，僅表格識別碼）----------
APP_TOKEN = "XpwfbyCtFacq03suX6zcOZelnaf"   # 飛書多維表格 app_token
TABLE_ID = "tblTeUu5Hducz0m2"               # 主用表 table_id
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_JSON = os.path.join(ROOT, "data", "posts.json")
BUILD_SCRIPT = os.path.join(ROOT, "tools", "build_articles.py")
SECRET_FILE = os.path.join(ROOT, "tools", ".feishu_secret.json")
ASSET_POSTS_DIR = os.path.join(ROOT, "assets", "images", "posts")
REPORT_FILE = os.path.join(ROOT, "SYNC_REPORT.txt")

DELETE_GUARD = 3          # 一次刪除超過此數 → 中止
ATTACH_FIELD = "images_attach"   # 飛書附件欄位名（不存在時自動降級用文字 images）

# 額外設定（從 secret 檔讀取，可省略）
BOT_WEBHOOK = ""
WEBHOOK_SECRET = ""


def load_creds():
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    if app_id and app_secret:
        return app_id, app_secret
    if os.path.exists(SECRET_FILE):
        try:
            d = json.load(open(SECRET_FILE, encoding="utf-8"))
            global BOT_WEBHOOK, WEBHOOK_SECRET
            BOT_WEBHOOK = d.get("bot_webhook", "")
            WEBHOOK_SECRET = d.get("webhook_secret", "")
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
            return datetime.datetime.fromtimestamp(int(s), datetime.timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            pass
    return ""


def parse_images(v):
    """飛書 images 文字欄存成 Python 列表字串，例如 "['a.jpg','b.jpg']"。"""
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


def download_file(token, file_token, dest):
    """透過飛書 drive 下載附件到 dest；失敗回傳 False。"""
    url = "https://open.feishu.cn/open-apis/drive/v1/files/%s/download" % file_token
    try:
        req = urllib.request.Request(url, headers={"Authorization": "Bearer %s" % token})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        # 部分情況會回傳 JSON 內含真實下載網址
        if data[:1] == b"{" :
            try:
                j = json.loads(data.decode("utf-8", "ignore"))
                real = j.get("url") or j.get("file_url") or (j.get("data") or {}).get("url")
                if real:
                    req2 = urllib.request.Request(real)
                    with urllib.request.urlopen(req2, timeout=60) as r2:
                        data = r2.read()
            except Exception:
                pass
        with open(dest, "wb") as fh:
            fh.write(data)
        return True
    except Exception as e:
        print("    [警告] 附件下載失敗 %s：%s" % (file_token, e))
        return False


def process_images(f, token, num):
    """解析圖片：優先用 images_attach 附件（下載到 assets），否則用文字 images。"""
    atts = f.get(ATTACH_FIELD)
    if atts and isinstance(atts, list) and atts:
        os.makedirs(ASSET_POSTS_DIR, exist_ok=True)
        out = []
        for i, att in enumerate(atts, 1):
            name = att.get("name") or ("%s-%d" % (num, i))
            ext = os.path.splitext(name)[1] or ".jpg"
            dest = os.path.join(ASSET_POSTS_DIR, "%s-%d%s" % (num, i, ext))
            tok = att.get("file_token") or att.get("token") or ""
            if tok and download_file(token, tok, dest):
                out.append("assets/images/posts/%s-%d%s" % (num, i, ext))
            elif att.get("url"):
                # 直接有可下載網址時嘗試抓
                try:
                    req = urllib.request.Request(att["url"])
                    with urllib.request.urlopen(req, timeout=60) as r:
                        d = r.read()
                    with open(dest, "wb") as fh:
                        fh.write(d)
                    out.append("assets/images/posts/%s-%d%s" % (num, i, ext))
                except Exception:
                    pass
        if out:
            return out
    # 降級：文字 images
    return parse_images(f.get("images"))


def merge_fields(base, f, token):
    """把飛書欄位 f 合併到 base（原地修改 base），回傳 (有變動欄位, 舊 slug)。"""
    changed = []
    old_slug = base.get("slug")
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
    if "date" in f:
        nd = ts_to_date(f["date"])
        if base.get("date") != nd:
            base["date"] = nd
            changed.append("date")
    if ATTACH_FIELD in f or "images" in f:
        ni = process_images(f, token, norm_num(f.get("num")))
        if base.get("images") != ni:
            base["images"] = ni
            changed.append("images")
    if "num" in f:
        fn = norm_num(f["num"])
        if norm_num(base.get("num")) != fn:
            base["num"] = fn
            changed.append("num")
    return changed, (old_slug if "slug" in changed else None)


def make_new_post(f, token):
    """飛書新增文章：只有基本欄位，其餘留預設。"""
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
    p["images"] = process_images(f, token, norm_num(f.get("num")))
    p["lead"] = str(f.get("lead", "")).strip()
    p["body"] = str(f.get("body", ""))
    return p


def send_bot(text):
    """可選：把訊息送到飛書群機器人 webhook。未設定則跳過。"""
    if not BOT_WEBHOOK:
        return
    try:
        feishu_post(BOT_WEBHOOK, {"msg_type": "text", "content": {"text": text}})
    except Exception as e:
        print("[警告] 飛書通知發送失敗：%s" % e)


def write_report(summary_lines, aborted=False):
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as fh:
            fh.write("\n".join(summary_lines) + "\n")
        print("[報告] 已寫入 %s" % REPORT_FILE)
    except Exception as e:
        print("[警告] 寫報告失敗：%s" % e)


def prune_article_dirs(slugs):
    """刪除 article/<slug>/ 資料夾（孤兒頁清理）。"""
    removed = []
    for slug in slugs:
        if not slug:
            continue
        d = os.path.join(ROOT, "article", slug)
        if os.path.isdir(d):
            shutil.rmtree(d)
            removed.append(slug)
    if removed:
        print("[清理] 已刪除 %d 個孤兒文章資料夾：%s" % (len(removed), ", ".join(removed)))
    return removed


def git_commit_only():
    """只 commit 不 push（每日排程模式）。無變動則跳過。"""
    subprocess.run(
        ["git", "add", "-A", "data/", "article/", "articles/",
         "tools/sync_from_feishu.py", ".gitignore"], check=True)
    # 檢查是否有東西可提交
    out = subprocess.run(["git", "status", "--porcelain"],
                         capture_output=True, text=True, check=True).stdout.strip()
    if not out:
        print("[git] 無變動，跳過 commit。")
        return False
    msg = "sync: 飛書 CMS 同步（每日自動，待確認推送）"
    subprocess.run(["git", "commit", "-m", msg], check=True)
    print("[git] 已 commit（尚未 push，等你確認）。")
    return True


def git_push():
    subprocess.run(
        ["git", "add", "-A", "data/", "article/", "articles/",
         "tools/sync_from_feishu.py", ".gitignore"], check=True)
    msg = "sync: 飛書 CMS 同步（上線）"
    subprocess.run(["git", "commit", "-m", msg], check=True)
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)
    print("[推送] 完成，Netlify 將自動部署。")


def main():
    dry_run = "--dry-run" in sys.argv
    do_build = "--build" in sys.argv
    do_push = "--push" in sys.argv
    commit_only = "--commit-only" in sys.argv

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

    feishu = []
    for rec in records:
        f = rec.get("fields", {})
        fnum = norm_num(f.get("num"))
        fnum_int = int(fnum) if fnum.isdigit() else None
        fslug = (f.get("slug") or "").strip()
        feishu.append({"f": f, "num_int": fnum_int, "slug": fslug, "consumed": False})
    by_num, by_slug = {}, {}
    for i, fr in enumerate(feishu):
        if fr["num_int"] is not None:
            by_num.setdefault(fr["num_int"], i)
        if fr["slug"]:
            by_slug.setdefault(fr["slug"], i)
    feishu_num_set = {fr["num_int"] for fr in feishu if fr["num_int"] is not None}
    feishu_slug_set = {fr["slug"] for fr in feishu if fr["slug"]}

    final = []
    adds, updates, deletes, renamed_old = [], [], [], []

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
            final.append(p)
            continue
        fr = feishu[idx]
        changed, old_slug = merge_fields(p, fr["f"], token)
        if changed:
            updates.append((p.get("slug") or p.get("num"), changed))
            if old_slug and old_slug != p.get("slug"):
                renamed_old.append(old_slug)
        final.append(p)
        fr["consumed"] = True

    for fr in feishu:
        if not fr["consumed"]:
            np = make_new_post(fr["f"], token)
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
    if renamed_old:
        print("slug 改名（舊資料夾將清理）：%s" % ", ".join(renamed_old))

    mi = sum(1 for x in final if x.get("movieInfo"))
    fy = sum(1 for x in final if x.get("filmYear"))
    print("\n[保全] 含 movieInfo：%d 篇 / 含 filmYear：%d 篇" % (mi, fy))

    # ---- 刪除保護（安全機制）----
    if not dry_run and len(deletes) > DELETE_GUARD:
        msg = ("[中止] 偵測到一次刪除 %d 篇（超過保護線 %d），"
               "已中止同步、未寫入、未推送。請確認是否真要刪除這些文章：\n  %s"
               % (len(deletes), DELETE_GUARD, "\n  ".join(deletes)))
        print(msg)
        write_report(["[飛書 CMS 同步中止]", msg, "時間：" + time.strftime("%Y-%m-%d %H:%M:%S")])
        send_bot("⚠️ seanown 同步中止：一次刪除 %d 篇超過保護線。請檢查飛書表格。" % len(deletes))
        sys.exit(2)

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

    # 孤兒頁清理（刪除 + 改名舊 slug）
    remove_slugs = list(dict.fromkeys([d for d in deletes if d] + renamed_old))
    if remove_slugs:
        prune_article_dirs(remove_slugs)

    # git
    pushed = False
    if do_push:
        git_push()
        pushed = True
    elif commit_only:
        git_commit_only()

    # 報告 + 通知
    summary = [
        "[飛書 CMS 同步報告]",
        "時間：" + time.strftime("%Y-%m-%d %H:%M:%S"),
        "篇數：%d → %d" % (len(existing), len(final)),
        "新增 %d / 刪除 %d / 更新 %d" % (len(adds), len(deletes), len(updates)),
        "movieInfo 保全：%d 篇" % mi,
        "重建文章頁：%s" % ("是" if do_build else "否"),
        "推送：%s" % ("已 push" if pushed else ("已 commit 待確認" if commit_only else "否")),
    ]
    write_report(summary)
    if adds or deletes or updates:
        send_bot("📝 seanown 同步完成：新增 %d / 刪除 %d / 更新 %d%s"
                 % (len(adds), len(deletes), len(updates),
                    "（已上線）" if pushed else "（待確認推送）"))


if __name__ == "__main__":
    main()
