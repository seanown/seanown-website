#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_sources.py — 澳門週報多來源新聞抓取器（零依賴，只用標準庫）

抓取來源（2026-09-28 驗證可用）：
  1. 正報      : 靜態 HTML  — https://www.chengpou.com.mo/news.html
  2. 濠江日報  : JSON API  — https://hkdaily-api.bpprojects.com/v1/section_news/headline
  3. 旅遊局    : JSON API  — https://www.macaotourism.gov.mo/api/enf/whatson?lang=zh-hant
  4. DSEC 統計局: 靜態 HTML — https://www.dsec.gov.mo/zh-MO/Statistic/News（Playwright 渲染）
  5. 力報 Exmoo: 靜態 HTML — https://www.exmoo.com/ 首頁 article/<id>.html（2026-09-28 驗證可用）
  6. 澳門日報  : 圖片型電子報 — https://www.macaodaily.com/（每日下載整版圖，AI 讀圖抽標題）

備註：
  - 澳門日報為「圖片型電子報」：詳情頁無 <p> 正文、版面用 <area> 熱點圖，
    每版一整張 JPEG（/page/<n>/<YYYY-MM>/<DD>/<SEC>/<id>.jpg），全站統一 398×584，
    無文字層、無高清版本（_big/_l/_h 皆 404）、無 PDF。→ 純 HTML/OCR 內文不可行；
    可行的是「下載整版圖 → 由多模態 AI 讀圖抽各版標題」（大標題可讀，內文因解析度不足不可讀）。
    本抓取器每日下載前 N 版（預設 2：A01 要聞 + A02）整版圖，並記錄當日全部版次數量。
  - 週範圍語意：--week <出報日(週一)> 表示「該週一出報」，統計的是「剛結束的那一週」，
    故抓取視窗 = 出報日-7天 ~ 出報日-1天（上週一至週日），與 SKILL「統計週 = 上週一至週日」一致。

產出：
  tools/weekly-content/<出報日>.sources.json
  {
    "generated_at": <ISO>,
    "week_range": {"start","end","label"},
    "sources": { <來源名>: {"status","count","note","items":[...]} },
    "all_items": [ 扁平化、依日期倒序，供週報直接引用 ]
  }

  單筆 item schema:
    { "source","title","url","date"(YYYY-MM-DD|null),"summary"(null|str),
      "category"(null|str),"extra":{...} }

用法：
  python fetch_sources.py                      # 預設抓「上週一~週日」
  python fetch_sources.py --week 2026-09-28    # 指定出報日（週一），統計該週
  python fetch_sources.py --days 7             # 抓最近 N 天（忽略週邊界）
  python fetch_sources.py --out myfile.json    # 自訂輸出檔
"""

import os
import re
import sys
import json
import argparse
import datetime
import urllib.request
import urllib.error

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# ---------- 基礎工具 ----------

def fetch(url, accept=None, timeout=20):
    """回傳 (text, http_code)。失敗回 ('', 0)。"""
    headers = {"User-Agent": UA}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            # 嘗試以 utf-8 解碼，失敗用 errors=ignore
            return raw.decode("utf-8", errors="ignore"), resp.getcode()
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        return body, e.code
    except Exception as e:
        return "", 0

def clean(txt):
    if not txt:
        return ""
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"&[a-z]+;", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def norm_date(s):
    """盡量把各種日期格式轉成 YYYY-MM-DD；失敗回 None。"""
    if not s:
        return None
    s = s.strip()
    m = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{1,2})月(\d{1,2})日", s)
    if m:
        y = datetime.date.today().year
        return f"{y}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None

def in_range(date_str, start, end):
    if not date_str:
        return True  # 無日期不過濾
    try:
        d = datetime.date.fromisoformat(date_str)
        return start <= d <= end
    except Exception:
        return True

# ---------- 各來源抓取 ----------

def fetch_zhengpao(week_start, week_end):
    """正報：列表取連結+標題，再抓前 N 筆詳情取日期+摘要。"""
    items = []
    note = ""
    base = "https://www.chengpou.com.mo"
    text, code = fetch(base + "/news.html")
    if code != 200 or not text:
        return {"status": "error", "count": 0, "note": f"列表頁 HTTP {code}", "items": []}
    links = re.findall(r'<a[^>]*href="(/dailynews/\d+\.html)"[^>]*>(.*?)</a>', text, re.S)
    seen, top = set(), []
    for href, atxt in links:
        if href in seen:
            continue
        seen.add(href)
        title = clean(atxt)
        if len(title) < 4:
            continue
        top.append((base + href, title))
        if len(top) >= 14:
            break
    # 抓詳情取日期 + 摘要
    for url, title in top:
        date, summary = None, None
        dtext, dcode = fetch(url)
        if dtext:
            # 日期：找第一個 20xx-xx-xx 或 x月x日
            date = norm_date(re.search(r"(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}月\d{1,2}日)", dtext).group(1)) \
                if re.search(r"(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}月\d{1,2}日)", dtext) else None
            # 摘要：第一個較長的 <p> 文字
            paras = re.findall(r"<p[^>]*>(.*?)</p>", dtext, re.S)
            for p in paras:
                c = clean(p)
                if len(c) > 25:
                    summary = c[:160]
                    break
        items.append({
            "source": "正報", "title": title, "url": url,
            "date": date, "summary": summary, "category": None, "extra": {}
        })
    cnt = len(items)
    note = f"列表 {len(top)} 則，詳情抓取 {cnt} 則"
    return {"status": "ok", "count": cnt, "note": note, "items": items}


def fetch_houkong(week_start, week_end):
    """濠江日報：JSON API。headline + 澳門新聞欄目。"""
    items = []
    base = "https://hkdaily-api.bpprojects.com"
    # 1) headline
    text, code = fetch(base + "/v1/section_news/headline", accept="application/json")
    if code != 200 or not text:
        return {"status": "error", "count": 0, "note": f"headline API HTTP {code}", "items": []}
    try:
        data = json.loads(text).get("data", [])
    except Exception:
        return {"status": "error", "count": 0, "note": "JSON 解析失敗", "items": []}
    for it in data:
        items.append({
            "source": "濠江日報",
            "title": it.get("title", ""),
            "url": it.get("html_url") or f"{base}/v1/section_news/{it.get('id')}/html?lang=zh",
            "date": norm_date(it.get("published_at", "")[:10]),
            "summary": clean(it.get("subtitle", "")) or None,
            "category": None,
            "extra": {"id": it.get("id"), "views": it.get("views")}
        })
    # 2) 補抓「澳門新聞」欄目（categories 中標題含 澳門 者）
    ctext, _ = fetch(base + "/v1/section_news/categories", accept="application/json")
    try:
        cats = json.loads(ctext).get("data", []) if ctext else []
    except Exception:
        cats = []
    macau_ids = [c.get("id") for c in cats if "澳門" in (c.get("title", "") or "")][:2]
    for sid in macau_ids:
        stext, _ = fetch(f"{base}/v1/section_news?section_id={sid}", accept="application/json")
        try:
            sdata = json.loads(stext).get("data", []) if stext else []
        except Exception:
            sdata = []
        have = {i["extra"].get("id") for i in items}
        for it in sdata:
            if it.get("id") in have:
                continue
            items.append({
                "source": "濠江日報",
                "title": it.get("title", ""),
                "url": it.get("html_url") or f"{base}/v1/section_news/{it.get('id')}/html?lang=zh",
                "date": norm_date(it.get("published_at", "")[:10]),
                "summary": clean(it.get("subtitle", "")) or None,
                "category": None,
                "extra": {"id": it.get("id"), "views": it.get("views")}
            })
    # 3) 補摘要：前 8 則若無 summary，抓詳情頁取首段 <p>
    for it in items[:8]:
        if it.get("summary"):
            continue
        dtext, _ = fetch(it["url"])
        if dtext:
            paras = re.findall(r"<p[^>]*>(.*?)</p>", dtext, re.S)
            for p in paras:
                c = clean(p)
                if len(c) > 25:
                    it["summary"] = c[:160]
                    break
    return {"status": "ok", "count": len(items), "note": f"headline + 澳門欄目共 {len(items)} 則", "items": items}


def fetch_tourism(week_start, week_end):
    """旅遊局：JSON API /api/enf/whatson?lang=zh-hant。"""
    items = []
    url = "https://www.macaotourism.gov.mo/api/enf/whatson?lang=zh-hant"
    text, code = fetch(url, accept="application/json")
    if code != 200 or not text:
        return {"status": "error", "count": 0, "note": f"whatson API HTTP {code}", "items": []}
    try:
        data = json.loads(text)
        results = data.get("results", [])
    except Exception:
        return {"status": "error", "count": 0, "note": "JSON 解析失敗", "items": []}
    # 篩選本週有活動的（eventDateRange 與週範圍相交）
    def overlaps(ev):
        rng = ev.get("eventDateRange") or []
        for pair in rng:
            try:
                d0 = datetime.date.fromisoformat(pair[0]); d1 = datetime.date.fromisoformat(pair[1])
            except Exception:
                continue
            if d0 <= week_end and d1 >= week_start:
                return True
        return False
    picked = [r for r in results if overlaps(r)]
    if len(picked) < 8:  # 本週活動太少則退回前 15 筆
        picked = results[:15]
    for it in picked:
        locs = [l.get("name") for l in it.get("location", []) if isinstance(l, dict)]
        items.append({
            "source": "旅遊局",
            "title": it.get("name", ""),
            "url": "https://www.macaotourism.gov.mo/zh-hant/events/whatson",
            "date": None,
            "summary": clean(it.get("shortDesc", ""))[:160] or None,
            "category": "活動/盛事",
            "extra": {
                "showDate": it.get("showDate"),
                "eventDate": it.get("eventDate"),
                "location": locs,
                "types": [t.get("name") for t in it.get("types", []) if isinstance(t, dict)]
            }
        })
    return {"status": "ok", "count": len(items),
            "note": f"whatson 共 {len(results)} 筆，選取 {len(items)} 筆（本週活動優先）", "items": items}


def fetch_dsec(week_start, week_end):
    """DSEC：新聞列表為 JS 動態載入，靜態 HTML 抓不到。
    改用 Playwright 無頭渲染，抽取 #statistic-news-list 下每則
    (.db-statistic-news-cell__title / __content__inner / __period)。
    Playwright 不可用時優雅降級為 partial。
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"status": "partial", "count": 0,
                "note": "未安裝 playwright，DSEC 需無頭瀏覽器渲染（pip install playwright && playwright install chromium）",
                "items": []}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--no-sandbox"])
            pg = b.new_page()
            pg.goto("https://www.dsec.gov.mo/zh-MO/Statistic/News",
                    wait_until="networkidle", timeout=30000)
            pg.wait_for_timeout(2500)
            nodes = pg.eval_on_selector_all(
                "a.db-statistic-news-cell-link",
                """els => els.map(e => ({
                    title: (e.querySelector('.db-statistic-news-cell__title')||{}).innerText || '',
                    summary: (e.querySelector('.statistic-news-cell__content__inner')||{}).innerText || '',
                    period: (e.querySelector('.db-statistic-news-cell__period')||{}).innerText || ''
                }))"""
            )
            b.close()
    except Exception as e:
        return {"status": "partial", "count": 0, "note": f"Playwright 渲染失敗：{e}", "items": []}

    items = []
    for n in nodes:
        title = clean(n.get("title"))
        summary = clean(n.get("summary"))
        date = norm_date((n.get("period") or "").replace("/", "-"))
        if len(title) < 4:
            continue
        items.append({
            "source": "DSEC",
            "title": title,
            "url": "https://www.dsec.gov.mo/zh-MO/Statistic/News",
            "date": date,
            "summary": (summary[:200] if summary else None),
            "category": "統計發布",
            "extra": {}
        })
    if not items:
        return {"status": "partial", "count": 0,
                "note": "Playwright 渲染後仍無新聞節點（選擇器可能已變動）", "items": []}
    return {"status": "ok", "count": len(items),
            "note": f"Playwright 渲染取得新聞 {len(items)} 筆", "items": items}


def fetch_exmoo(week_start, week_end):
    """力報 Exmoo：靜態 HTML。首頁抽 /article/<id>.html 連結+標題，逐筆抓詳情取
    H1 標題 + 日期（class=date 元素，DD/MM/YYYY）+ 摘要（og:description meta）。"""
    items = []
    base = "https://www.exmoo.com"
    text, code = fetch(base + "/")
    if code != 200 or not text:
        return {"status": "error", "count": 0, "note": f"首頁 HTTP {code}", "items": []}
    # 首頁 article 連結（含完整域名；去重、保留順序）
    links = re.findall(r'href="(https?://www\.exmoo\.com/article/\d+\.html)"', text)
    seen, top = set(), []
    for href in links:
        if href in seen:
            continue
        seen.add(href)
        top.append(href)
        if len(top) >= 16:
            break
    for url in top:
        dtext, dcode = fetch(url)
        if not dtext:
            continue
        # 標題：<h1>
        h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", dtext, re.S)
        title = clean(h1[0]) if h1 else None
        if not title or len(title) < 4:
            continue
        # 日期：class 含 date 的元素，格式 DD/MM/YYYY
        date = None
        dm = re.search(r'class="[^"]*date[^"]*"[^>]*>(\d{2})/(\d{2})/(\d{4})<', dtext)
        if dm:
            date = f"{int(dm.group(3)):04d}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}"
        else:
            # 兜底：正文內 20xx-xx-xx
            ymd = re.search(r"(20\d{2}-\d{2}-\d{2})", dtext)
            date = ymd.group(1) if ymd else None
        # 摘要：og:description
        og = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"', dtext)
        if not og:
            og = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', dtext)
        summary = None
        if og:
            s = og.group(1)
            s = s.replace("&ldquo;", "「").replace("&rdquo;", "」").replace("&hellip;", "…")
            s = re.sub(r"&[a-z]+;", " ", s).strip()
            summary = s[:200] if s else None
        items.append({
            "source": "力報",
            "title": title,
            "url": url,
            "date": date,
            "summary": summary,
            "category": None,
            "extra": {}
        })
    cnt = len(items)
    note = f"首頁抽 {len(top)} 則，詳情抓取 {cnt} 則"
    return {"status": "ok" if cnt else "error", "count": cnt, "note": note, "items": items}


def fetch_bytes(url, timeout=30):
    """下載二進位（圖片）。回 (bytes, http_code)。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(), resp.getcode()
    except urllib.error.HTTPError as e:
        return b"", e.code
    except Exception:
        return b"", 0


def fetch_macaodaily(week_start, week_end, pages_per_day=3, img_root=None):
    """澳門日報（圖片型電子報）：逐日下載整版圖供 AI 讀圖抽標題。

    結構：/html/YYYY-MM/DD/node_<N>.htm 為各版次索引；每版對應一張整版 JPEG
          /page/<n>/<YYYY-MM>/<DD>/<SEC>/<id>.jpg（SEC 如 A01），全站統一 398×584。
    作法：逐日枚舉 node_X → 解析各版次圖片 URL 與文章數（<area> 熱點數）→
          下載前 pages_per_day 個版次（依版次排序，預設 A01+A02+A03）整版圖到 img_root/<date>/。
    限制：內文因原圖解析度不足不可讀（該站無文字層／無高清圖／無 PDF），
          故 item.summary 留空並標 extra.needs_vision=True，交由 AI 讀圖補標題。
    """
    base = "https://www.macaodaily.com"
    items = []
    days_ok = 0
    imgs_saved = 0
    d = week_start
    while d <= week_end:
        day = d.isoformat()
        db = f"{base}/html/{d:%Y-%m}/{d:%d}"
        n1, code = fetch(db + "/node_1.htm")
        if not n1:
            d += datetime.timedelta(days=1)
            continue
        node_set = set(int(x) for x in re.findall(r"node_(\d+)\.htm", n1)) | {1}
        pages = {}  # sec -> (img_url, article_count)
        for n in sorted(node_set):
            h = n1 if n == 1 else fetch(db + f"/node_{n}.htm")[0]
            if not h:
                continue
            im = re.search(r"(\.\./\.\./\.\./page/[\d/\-A-Za-z]+/\d+\.jpg)", h)
            if not im:
                continue
            rel = im.group(1)
            sm = re.search(r"/([A-Z]\d{2})/", rel)
            sec = sm.group(1) if sm else "?"
            cnt = len(set(re.findall(r'href=["\'](content_\d+\.htm)["\']', h)))
            url = base + "/" + rel.replace("../../../", "")
            if sec not in pages or cnt > pages[sec][1]:
                pages[sec] = (url, cnt)
        days_ok += 1
        secs = sorted(pages.keys())
        picked = secs[:pages_per_day] if pages_per_day else secs[:3]
        # 下載整版圖（僅 picked 版次）
        if img_root and pages_per_day:
            daydir = os.path.join(img_root, day)
            os.makedirs(daydir, exist_ok=True)
            for sec in secs[:pages_per_day]:
                url, _cnt = pages[sec]
                raw, c = fetch_bytes(url)
                if raw:
                    with open(os.path.join(daydir, f"{sec}.jpg"), "wb") as f:
                        f.write(raw)
                    imgs_saved += 1
        for sec in picked:
            url, cnt = pages[sec]
            local = os.path.join(img_root, day, f"{sec}.jpg") if img_root else None
            items.append({
                "source": "澳門日報",
                "title": f"澳門日報 {day} {sec}版",
                "url": url,
                "date": day,
                "summary": None,
                "category": "澳門日報",
                "extra": {
                    "sec": sec, "articles": cnt, "all_secs": len(secs),
                    "image_url": url, "image": local, "needs_vision": True,
                },
            })
        d += datetime.timedelta(days=1)
    note = (f"圖片型電子報：{days_ok} 天，每日下載前 {pages_per_day} 版整版圖"
            f"（共 {imgs_saved} 張）；各版次已列，內文需 AI 讀圖（無文字層/高清/PDF）")
    return {"status": "ok" if items else "error", "count": len(items), "note": note, "items": items}


# ---------- 主流程 ----------

def compute_week(issue_monday=None, days=None):
    """回傳「抓取視窗」(start, end)。

    - --days N：最近 N 天（end=今天）。
    - --week <出報日(週一)>：該週一出報，統計剛結束的那週 → 視窗 = 出報日-7 ~ 出報日-1（上週一至週日）。
    - 預設（無參數）：上週一至週日（同 SKILL 統計週定義）。
    """
    today = datetime.date.today()
    if days:
        end = today
        start = today - datetime.timedelta(days=days - 1)
        return start, end
    if issue_monday:
        mon = datetime.date.fromisoformat(issue_monday)
    else:
        # 最近一個週一（今天若為週一即今天）
        mon = today - datetime.timedelta(days=today.weekday())
        mon = mon - datetime.timedelta(days=7)  # 上週一
    # 出報週一 → 剛結束的那週
    end = mon - datetime.timedelta(days=1)        # 週日
    start = end - datetime.timedelta(days=6)       # 週一
    return start, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", help="出報日(週一) YYYY-MM-DD")
    ap.add_argument("--days", type=int, help="最近 N 天")
    ap.add_argument("--out", help="輸出 JSON 路徑")
    ap.add_argument("--md-pages", type=int, default=3,
                    help="澳門日報每日下載前 N 版整版圖（預設 2：A01+A02；0=只記錄版次不下載）")
    args = ap.parse_args()

    start, end = compute_week(args.week, args.days)
    label = f"{start.strftime('%Y.%m.%d')} — {end.strftime('%Y.%m.%d')}"

    print(f"▶ 抓取保守範圍：{label}")

    here = os.path.dirname(os.path.abspath(__file__))
    wc = os.path.join(here, "weekly-content")

    # 先決定出報日（檔名以出報日＝週一 命名），以便放置澳門日報圖片
    if args.out:
        out_path = args.out
        issue = os.path.splitext(os.path.basename(args.out))[0]
    else:
        if args.week:
            issue = args.week
        else:
            # 出報日 = 抓取視窗週日 + 1 天（即本週一）
            issue = (end + datetime.timedelta(days=1)).isoformat()
        os.makedirs(wc, exist_ok=True)
        out_path = os.path.join(wc, f"{issue}.sources.json")

    # 澳門日報整版圖存放目錄：weekly-content/<出報日>/macaodaily/<日期>/<SEC>.jpg
    md_img_root = os.path.join(wc, issue, "macaodaily")

    sources = {
        "正報": fetch_zhengpao(start, end),
        "濠江日報": fetch_houkong(start, end),
        "旅遊局": fetch_tourism(start, end),
        "DSEC": fetch_dsec(start, end),
        "力報": fetch_exmoo(start, end),
        "澳門日報": fetch_macaodaily(start, end, pages_per_day=args.md_pages, img_root=md_img_root),
    }

    # 扁平化 + 依日期倒序（無日期排後）
    flat = []
    for name, s in sources.items():
        flat.extend(s["items"])
    def sortkey(x):
        return (x.get("date") or "0000-00-00", x["source"])
    flat.sort(key=sortkey, reverse=True)

    out = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "week_range": {"start": start.isoformat(), "end": end.isoformat(), "label": label},
        "sources": sources,
        "all_items": flat,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # 終端摘要
    print("\n=== 抓取結果 ===")
    for name, s in sources.items():
        flag = {"ok": "✅", "partial": "⚠️", "error": "❌"}.get(s["status"], "·")
        print(f"  {flag} {name}: {s['count']} 筆 — {s['note']}")
    print(f"\n總計 {len(flat)} 筆 → 已寫入 {out_path}")


if __name__ == "__main__":
    main()
